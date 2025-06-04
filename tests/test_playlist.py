import unittest
import sys
import os

# Adjust path to import Playlist from src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.playlist import Playlist

class TestPlaylist(unittest.TestCase):

    def setUp(self):
        self.playlist = Playlist()
        self.track1 = "track1.mp3"
        self.track2 = "track2.mp3"
        self.track3 = "track3.mp3"

    def test_initialization(self):
        self.assertEqual(self.playlist.tracks, [])
        self.assertEqual(self.playlist.current_track_index, -1)
        self.assertFalse(self.playlist.shuffle_mode)
        self.assertEqual(self.playlist.repeat_mode, 'none')
        self.assertEqual(self.playlist.shuffled_indices, [])

    def test_add_track(self):
        self.playlist.add_track(self.track1)
        self.assertEqual(self.playlist.tracks, [self.track1])
        self.assertEqual(self.playlist.current_track_index, 0) # First track added becomes current

        self.playlist.add_track(self.track2)
        self.assertEqual(self.playlist.tracks, [self.track1, self.track2])
        self.assertEqual(self.playlist.current_track_index, 0) # Index should remain on the first track

        # Test adding duplicate track - should not be added
        self.playlist.add_track(self.track1)
        self.assertEqual(self.playlist.tracks, [self.track1, self.track2])

    def test_remove_track(self):
        self.playlist.add_track(self.track1)
        self.playlist.add_track(self.track2)
        self.playlist.add_track(self.track3)
        self.playlist.current_track_index = 1 # Current is track2

        # Remove a track that is not current
        self.playlist.remove_track(self.track1) # remove track1
        self.assertEqual(self.playlist.tracks, [self.track2, self.track3])
        self.assertEqual(self.playlist.current_track_index, 0) # track2 is now at index 0

        # Reset and remove current track
        self.setUp()
        self.playlist.add_track(self.track1)
        self.playlist.add_track(self.track2)
        self.playlist.add_track(self.track3)
        self.playlist.current_track_index = 1 # track2
        self.playlist.remove_track(self.track2)
        self.assertEqual(self.playlist.tracks, [self.track1, self.track3])
        # Current index should ideally point to the track that took the place of the removed one
        # or the next one, or be clamped. Based on current logic:
        self.assertEqual(self.playlist.current_track_index, 1) # track3 is now at index 1

        # Remove last track
        self.playlist.remove_track(self.track3)
        self.assertEqual(self.playlist.tracks, [self.track1])
        self.assertEqual(self.playlist.current_track_index, 0)

        # Remove only track
        self.playlist.remove_track(self.track1)
        self.assertEqual(self.playlist.tracks, [])
        self.assertEqual(self.playlist.current_track_index, -1)

        # Try removing non-existing track
        self.playlist.add_track(self.track1)
        self.playlist.remove_track("non_existing.mp3")
        self.assertEqual(self.playlist.tracks, [self.track1])

    def test_get_current_track(self):
        self.assertIsNone(self.playlist.get_current_track())

        self.playlist.add_track(self.track1)
        self.assertEqual(self.playlist.get_current_track(), self.track1)

        self.playlist.add_track(self.track2)
        self.playlist.current_track_index = 1
        self.assertEqual(self.playlist.get_current_track(), self.track2)

    def test_next_track_simple(self): # No repeat, no shuffle
        self.playlist.add_track(self.track1)
        self.playlist.add_track(self.track2)
        self.playlist.add_track(self.track3)

        self.playlist.current_track_index = 0 # Start at track1
        self.assertEqual(self.playlist.next_track(), self.track2)
        self.assertEqual(self.playlist.current_track_index, 1)
        self.assertEqual(self.playlist.next_track(), self.track3)
        self.assertEqual(self.playlist.current_track_index, 2)
        self.assertIsNone(self.playlist.next_track()) # End of playlist
        self.assertEqual(self.playlist.current_track_index, -1)
        self.assertIsNone(self.playlist.next_track()) # Stays at end
        self.assertEqual(self.playlist.current_track_index, -1)


    def test_previous_track_simple(self): # No repeat, no shuffle
        self.playlist.add_track(self.track1)
        self.playlist.add_track(self.track2)
        self.playlist.add_track(self.track3)

        self.playlist.current_track_index = 2 # Start at track3
        self.assertEqual(self.playlist.previous_track(), self.track2)
        self.assertEqual(self.playlist.current_track_index, 1)
        self.assertEqual(self.playlist.previous_track(), self.track1)
        self.assertEqual(self.playlist.current_track_index, 0)
        # Behavior at start of playlist (current logic goes to -1)
        self.assertIsNone(self.playlist.previous_track())
        self.assertEqual(self.playlist.current_track_index, -1)
        self.assertIsNone(self.playlist.previous_track()) # Stays at -1
        self.assertEqual(self.playlist.current_track_index, -1)


    def test_set_current_track_by_path(self):
        self.playlist.add_track(self.track1)
        self.playlist.add_track(self.track2)

        self.assertTrue(self.playlist.set_current_track_by_path(self.track2))
        self.assertEqual(self.playlist.current_track_index, 1)

        self.assertFalse(self.playlist.set_current_track_by_path("non_existing.mp3"))
        self.assertEqual(self.playlist.current_track_index, 1) # Should not change

    def test_shuffle_mode(self):
        self.playlist.add_track(self.track1)
        self.playlist.add_track(self.track2)
        self.playlist.add_track(self.track3)

        self.playlist.toggle_shuffle() # Shuffle is ON, current_track_index is 0 (for shuffled_indices)
        self.assertTrue(self.playlist.shuffle_mode)
        self.assertEqual(len(self.playlist.shuffled_indices), len(self.playlist.tracks))
        self.assertEqual(self.playlist.current_track_index, 0) # Should start at the beginning of shuffle

        # Play through shuffled list (no repeat)
        played_in_shuffle = set()
        # Iterate N times, expecting N non-None unique tracks
        for i in range(len(self.playlist.tracks)):
            # For the first iteration, use get_current_track(), for others use next_track()
            track = self.playlist.get_current_track() if i == 0 else self.playlist.next_track()

            self.assertIsNotNone(track, f"Track should not be None during iteration {i+1} of {len(self.playlist.tracks)} in shuffle (repeat=none). Played: {played_in_shuffle}")
            self.assertNotIn(track, played_in_shuffle, f"Track {track} was repeated in shuffle mode (repeat=none). Played: {played_in_shuffle}")
            played_in_shuffle.add(track)

        self.assertEqual(len(played_in_shuffle), len(self.playlist.tracks), "Not all unique tracks were played in shuffle mode (repeat=none).")
        self.assertIsNone(self.playlist.next_track(), "Playlist should end after all shuffled tracks are played in shuffle mode (repeat=none).")

        # Test turning shuffle off
        # To robustly test index restoration, set current_track_index to a known valid shuffle index first
        # Let's assume current_track_index is now -1 because we played till the end.
        self.assertEqual(self.playlist.current_track_index, -1)
        self.playlist.toggle_shuffle() # Turn OFF
        self.assertFalse(self.playlist.shuffle_mode)
        self.assertEqual(self.playlist.shuffled_indices, [])
        # When shuffle is turned off and the playlist had ended (index -1), it defaults to index 0.
        self.assertEqual(self.playlist.current_track_index, 0, "Index should be 0 after turning off shuffle if it had ended.")

        # Test restoration from a specific track (if not ended)
        self.setUp() # Reset playlist
        self.playlist.add_track(self.track1); self.playlist.add_track(self.track2); self.playlist.add_track(self.track3)

        # Turn ON shuffle - current_track_index will be 0 (shuffled)
        self.playlist.toggle_shuffle()
        self.assertTrue(self.playlist.shuffle_mode)
        self.assertEqual(self.playlist.current_track_index, 0, "Shuffle should start at index 0.")

        # Play one track, so current_track_index (shuffled) becomes 1.
        first_shuffled_track_path = self.playlist.get_current_track() # This is tracks[shuffled_indices[0]]
        self.assertIsNotNone(first_shuffled_track_path)
        second_shuffled_track_path = self.playlist.next_track()      # This is tracks[shuffled_indices[1]]
        self.assertIsNotNone(second_shuffled_track_path)
        self.assertEqual(self.playlist.current_track_index, 1, "current_track_index for shuffle should be 1 after one next_track() call.")

        # Determine the original index of this second track in the shuffled sequence
        # This is the track that should be current after turning shuffle off.
        original_index_of_second_shuffled_track = self.playlist.shuffled_indices[1]

        self.playlist.toggle_shuffle() # Turn OFF shuffle
        self.assertFalse(self.playlist.shuffle_mode)
        self.assertEqual(self.playlist.shuffled_indices, [])
        # The current_track_index should now be the original index of the track that was current in shuffle mode.
        self.assertEqual(self.playlist.current_track_index, original_index_of_second_shuffled_track, "Index should be restored to the original index of the track that was current in shuffle.")

        # Test add/remove disables shuffle
        self.playlist.toggle_shuffle() # Turn on again
        self.assertTrue(self.playlist.shuffle_mode)
        self.playlist.add_track("track4.mp3")
        self.assertFalse(self.playlist.shuffle_mode) # Shuffle should be off

        self.playlist.toggle_shuffle() # Turn on again
        self.assertTrue(self.playlist.shuffle_mode)
        self.playlist.remove_track(self.track1)
        self.assertFalse(self.playlist.shuffle_mode) # Shuffle should be off

    def test_repeat_mode_none(self):
        self.playlist.add_track(self.track1)
        self.playlist.add_track(self.track2)
        self.playlist.set_repeat_mode('none')

        self.playlist.current_track_index = 0
        self.playlist.next_track() # To track2
        self.assertIsNone(self.playlist.next_track()) # End
        self.assertEqual(self.playlist.current_track_index, -1)

        self.playlist.current_track_index = 0
        self.assertIsNone(self.playlist.previous_track()) # Start
        self.assertEqual(self.playlist.current_track_index, -1)


    def test_repeat_mode_one(self):
        self.playlist.add_track(self.track1)
        self.playlist.add_track(self.track2)
        self.playlist.set_repeat_mode('one')
        self.playlist.current_track_index = 0

        self.assertEqual(self.playlist.next_track(), self.track1)
        self.assertEqual(self.playlist.current_track_index, 0)
        self.assertEqual(self.playlist.previous_track(), self.track1)
        self.assertEqual(self.playlist.current_track_index, 0)

        # If current_track_index is -1, repeat one should select the first track and stick to it.
        self.playlist.current_track_index = -1
        self.assertEqual(self.playlist.next_track(), self.track1)
        self.assertEqual(self.playlist.current_track_index, 0) # Should now point to first track
        self.assertEqual(self.playlist.next_track(), self.track1) # Stays on track1
        self.assertEqual(self.playlist.current_track_index, 0)

        # Previous track when index is -1 and repeat_mode is 'one'
        self.playlist.current_track_index = -1
        self.assertEqual(self.playlist.previous_track(), self.track1) # Should select first track (or last based on prev logic)
                                                                    # Current Playlist.previous_track logic for -1 index goes to last.
                                                                    # For 'one', it should stick to current if valid, else pick one.
                                                                    # Let's adjust this to be consistent: picks first.
        # The previous_track logic for repeat_mode='one' and index=-1 needs to be specific.
        # For now, let's test existing behavior or simplify.
        # Existing: previous_track() when current_track_index = -1 goes to last track.
        # Then repeat_mode='one' makes it stick.
        # So, if playlist is [t1, t2], current=-1, previous_track() should go to t1 (first track).
        self.playlist.current_track_index = -1
        if len(self.playlist.tracks) > 0:
            first_track = self.playlist.tracks[0]
            self.assertEqual(self.playlist.previous_track(), first_track) # Goes to first
            self.assertEqual(self.playlist.current_track_index, 0)      # Index is now 0
            self.assertEqual(self.playlist.previous_track(), first_track) # Stays on first_track
        else:
            self.assertIsNone(self.playlist.previous_track())


    def test_repeat_mode_all(self):
        self.playlist.add_track(self.track1)
        self.playlist.add_track(self.track2)
        self.playlist.set_repeat_mode('all')

        self.playlist.current_track_index = 0
        self.assertEqual(self.playlist.next_track(), self.track2) # To track2
        self.assertEqual(self.playlist.next_track(), self.track1) # Wraps to track1
        self.assertEqual(self.playlist.current_track_index, 0)

        self.assertEqual(self.playlist.previous_track(), self.track2) # Wraps to track2 from track1
        self.assertEqual(self.playlist.current_track_index, 1)


    def test_shuffle_and_repeat_all(self):
        self.playlist.add_track(self.track1)
        self.playlist.add_track(self.track2)
        self.playlist.add_track(self.track3)
        self.playlist.toggle_shuffle()
        self.playlist.set_repeat_mode('all')

        played_once = set()
        for i in range(len(self.playlist.tracks)):
            track = self.playlist.get_current_track() if i == 0 else self.playlist.next_track()
            self.assertIsNotNone(track, f"Track should not be None during iteration {i+1} of first round in shuffle+repeat_all. Played: {played_once}")
            played_once.add(track)
        self.assertEqual(len(played_once), len(self.playlist.tracks), "Not all unique tracks played in first shuffle+repeat_all round.")

        # Next track should wrap and re-shuffle
        self.assertIsNotNone(self.playlist.next_track(), "next_track should wrap on shuffle+repeat_all.")

        # Play through the second time to ensure re-shuffling and continued play
        played_twice = set()
        for i in range(len(self.playlist.tracks)):
            track = self.playlist.get_current_track() if i == 0 else self.playlist.next_track() # Use same loop structure
            self.assertIsNotNone(track, f"Track should not be None during iteration {i+1} of second round in shuffle+repeat_all. Played: {played_twice}")
            played_twice.add(track)
        self.assertEqual(len(played_twice), len(self.playlist.tracks), "Not all unique tracks played in second shuffle+repeat_all round.")


    def test_save_load_playlist_stubs(self):
        # Just check if methods exist and can be called without error
        try:
            self.playlist.save_playlist("dummy_path.json")
            self.playlist.load_playlist("dummy_path.json")
        except Exception as e:
            self.fail(f"save_playlist or load_playlist raised an exception: {e}")

if __name__ == '__main__':
    unittest.main()
