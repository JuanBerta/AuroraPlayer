import unittest
from unittest.mock import patch, MagicMock, call
import sys
import os
import pygame # Import pygame for pygame.error

# Adjust path to import Player and Playlist from src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.player import Player
from src.playlist import Playlist

# Dummy audio file paths and metadata
DUMMY_MP3 = "dummy.mp3"
DUMMY_WAV = "dummy.wav"
DUMMY_OGG = "dummy.ogg" # For testing different types if needed

DUMMY_METADATA = {
    DUMMY_MP3: {'title': 'Dummy MP3', 'artist': 'Tester', 'album': 'Test Album', 'duration': 180},
    DUMMY_WAV: {'title': 'Dummy WAV', 'artist': 'Tester', 'album': 'Test Album', 'duration': 120},
    DUMMY_OGG: {'title': 'Dummy OGG', 'artist': 'Tester', 'album': 'Test Album', 'duration': 200},
}

# Helper to create a mock mutagen File object
def create_mock_mutagen_file(filepath, easy=None): # Added easy=None to match call
    mock_file = MagicMock()
    if filepath in DUMMY_METADATA:
        metadata = DUMMY_METADATA[filepath]
        mock_file.info.length = metadata['duration']
        # Mock the .get() method used for easy tags
        mock_file.get.side_effect = lambda key, default: [metadata.get(key.lower(), default[0])] if isinstance(metadata.get(key.lower()), str) else metadata.get(key.lower(), default)

    else: # Default mock if filepath not in DUMMY_METADATA
        mock_file.info.length = 0
        mock_file.get.return_value = ['Unknown']
    return mock_file


class TestPlayer(unittest.TestCase):

    def setUp(self):
        # We will apply mocks per method for clarity, but if all methods needed them,
        # class-level patching or setUp patching would be options.
        self.playlist = Playlist() # Player requires a playlist instance
        # Player initializes pygame.mixer in its __init__
        # So, we need to patch it *before* Player is instantiated if we want to mock init calls.
        # This is tricky with setUp if Player is created in setUp itself.
        # Alternative: patch globally for the class or pass mocks into Player.
        # For now, assume Player() can be called and then mocks are applied for its methods.
        # This means pygame.mixer.init() *will* be called unless Player is instantiated under patch.

        # Let's instantiate Player under patch for __init__ testing
        with patch('src.player.pygame.mixer') as self.mock_pygame_mixer_global, \
             patch('src.player.mutagen.File') as self.mock_mutagen_file_global:

            # Configure the global mock for pygame.mixer.music so it's available during Player init
            # It needs to exist for set_volume during init.
            self.mock_music_global = MagicMock()
            self.mock_pygame_mixer_global.music = self.mock_music_global

            self.player = Player()
            # Assign the test's playlist to the player instance for test control
            self.player.playlist = self.playlist


    @patch('src.player.mutagen.File')
    @patch('src.player.pygame.mixer')
    def test_player_initialization(self, mock_pygame_mixer, mock_mutagen_file):
        # Player is already initialized in setUp under a global patch.
        # This test is to verify those __init__ calls.
        # We use the globally patched mocks from setUp for assertion.

        self.mock_pygame_mixer_global.init.assert_called_once()
        self.mock_music_global.set_volume.assert_called_with(self.player.volume) # Checks default volume set

        self.assertEqual(self.player.volume, 0.5)
        self.assertIsInstance(self.player.playlist, Playlist)
        self.assertFalse(self.player.is_playing)
        self.assertFalse(self.player.is_paused)
        self.assertIsNone(self.player.current_track_loaded_path)

    @patch('src.player.mutagen.File')
    @patch('src.player.pygame.mixer')
    def test_load_track_and_metadata(self, mock_pygame_mixer, mock_mutagen_file):
        mock_music = mock_pygame_mixer.music # Alias for convenience
        mock_mutagen_file.side_effect = create_mock_mutagen_file

        self.assertTrue(self.player._load_track(DUMMY_MP3))

        mock_music.load.assert_called_with(DUMMY_MP3)
        mock_mutagen_file.assert_called_with(DUMMY_MP3, easy=True)
        self.assertEqual(self.player.track_duration, DUMMY_METADATA[DUMMY_MP3]['duration'])
        self.assertEqual(self.player.current_track_loaded_path, DUMMY_MP3)
        self.assertEqual(self.player.current_position, 0)

        # Test loading failure (e.g., pygame.error)
        mock_music.load.side_effect = pygame.error("Failed to load")
        self.assertFalse(self.player._load_track(DUMMY_WAV))
        self.assertIsNone(self.player.current_track_loaded_path)
        self.assertFalse(self.player.is_playing)
        mock_music.load.side_effect = None # Reset side effect

    @patch('src.player.mutagen.File')
    @patch('src.player.pygame.mixer')
    def test_play_new_track(self, mock_pygame_mixer, mock_mutagen_file):
        mock_music = mock_pygame_mixer.music
        mock_mutagen_file.side_effect = create_mock_mutagen_file

        # Add track to playlist, player uses this playlist instance
        self.player.playlist.add_track(DUMMY_MP3)
        # Player's play(track_path) relies on playlist.set_current_track_by_path

        self.player.play(DUMMY_MP3)

        mock_music.load.assert_called_with(DUMMY_MP3)
        mock_music.play.assert_called_once()
        self.assertTrue(self.player.is_playing)
        self.assertFalse(self.player.is_paused)
        self.assertEqual(self.player.playlist.get_current_track(), DUMMY_MP3)
        self.assertEqual(self.player.current_track_loaded_path, DUMMY_MP3)


    @patch('src.player.mutagen.File')
    @patch('src.player.pygame.mixer')
    def test_play_from_playlist_and_pause_resume_stop(self, mock_pygame_mixer, mock_mutagen_file):
        mock_music = mock_pygame_mixer.music
        mock_mutagen_file.side_effect = create_mock_mutagen_file

        self.player.playlist.add_track(DUMMY_MP3)
        self.player.playlist.set_current_track_by_path(DUMMY_MP3) # Set current track

        # Play current from playlist
        self.player.play()
        mock_music.load.assert_called_with(DUMMY_MP3)
        mock_music.play.assert_called_once()
        self.assertTrue(self.player.is_playing)

        # Pause
        mock_music.get_busy.return_value = True # Simulate music playing for pause to take effect
        self.player.pause()
        mock_music.pause.assert_called_once()
        self.assertTrue(self.player.is_paused)
        self.assertFalse(self.player.is_playing)

        # Resume (by calling play without args)
        self.player.play()
        mock_music.unpause.assert_called_once()
        self.assertTrue(self.player.is_playing)
        self.assertFalse(self.player.is_paused)

        # Stop
        self.player.stop()
        mock_music.stop.assert_called_once()
        self.assertFalse(self.player.is_playing)
        self.assertFalse(self.player.is_paused)
        self.assertEqual(self.player.current_position, 0)


    @patch('src.player.mutagen.File')
    @patch('src.player.pygame.mixer')
    def test_next_prev_track_playback(self, mock_pygame_mixer, mock_mutagen_file):
        mock_music = mock_pygame_mixer.music
        mock_mutagen_file.side_effect = create_mock_mutagen_file

        self.player.playlist.add_track(DUMMY_MP3)
        self.player.playlist.add_track(DUMMY_WAV)
        self.player.playlist.add_track(DUMMY_OGG)

        # Play the first track
        self.player.play(DUMMY_MP3)
        mock_music.play.reset_mock() # Reset for next assertions
        mock_music.load.reset_mock()
        # self.player.stop() from next_track calls stop, so this mock needs to be reset or checked carefully

        # Next track
        # Player.next_track() was modified to: _load_track, then if was playing, play()
        # self.player.is_playing is True from above
        self.player.next_track()

        # Check that DUMMY_WAV was loaded (it's next after DUMMY_MP3)
        # The _load_track call for DUMMY_WAV will call music.load()
        mock_music.load.assert_called_with(DUMMY_WAV)
        # And then music.play() should be called by self.play() inside next_track
        mock_music.play.assert_called_once() # Check it played after loading DUMMY_WAV
        self.assertEqual(self.player.current_track_loaded_path, DUMMY_WAV)
        self.assertTrue(self.player.is_playing)

        mock_music.play.reset_mock()
        mock_music.load.reset_mock()

        # Previous track
        self.player.prev_track()
        mock_music.load.assert_called_with(DUMMY_MP3) # Back to MP3
        mock_music.play.assert_called_once()
        self.assertEqual(self.player.current_track_loaded_path, DUMMY_MP3)
        self.assertTrue(self.player.is_playing)


    @patch('src.player.pygame.mixer') # Only mixer needed here
    def test_set_get_volume(self, mock_pygame_mixer):
        mock_music = mock_pygame_mixer.music

        self.player.set_volume(0.7)
        mock_music.set_volume.assert_called_with(0.7)
        self.assertEqual(self.player.get_volume(), 0.7)

        self.player.set_volume(1.5) # Test clamping (upper)
        mock_music.set_volume.assert_called_with(1.0)
        self.assertEqual(self.player.get_volume(), 1.0)

        self.player.set_volume(-0.5) # Test clamping (lower)
        mock_music.set_volume.assert_called_with(0.0)
        self.assertEqual(self.player.get_volume(), 0.0)

    @patch('src.player.mutagen.File')
    @patch('src.player.pygame.mixer')
    def test_seek_functionality(self, mock_pygame_mixer, mock_mutagen_file):
        mock_music = mock_pygame_mixer.music
        mock_mutagen_file.side_effect = create_mock_mutagen_file

        self.player.playlist.add_track(DUMMY_MP3)
        self.player.play(DUMMY_MP3) # This loads the track and sets duration via _load_track

        self.player.track_duration = DUMMY_METADATA[DUMMY_MP3]['duration'] # Ensure duration is set for seek logic

        # Test seek while playing
        self.player.is_playing = True # Assume it's playing
        self.player.is_paused = False
        mock_music.get_busy.return_value = True

        self.player.seek(30)
        mock_music.set_pos.assert_called_with(30)
        self.assertEqual(self.player.current_position, 30)

        # Test seek while paused
        self.player.is_playing = False
        self.player.is_paused = True
        self.player.seek(60)
        # In paused state, set_pos is called after unpause and before pause
        mock_music.unpause.assert_called_once()
        mock_music.set_pos.assert_called_with(60)
        mock_music.pause.assert_called_once()
        self.assertEqual(self.player.current_position, 60)

        # Test seek beyond duration - should clamp to duration
        self.player.seek(DUMMY_METADATA[DUMMY_MP3]['duration'] + 50)
        # Depending on active state, set_pos might be called with clamped value
        # The internal current_position should be clamped.
        # If it was paused, it would call set_pos(clamped_duration)
        clamped_duration = DUMMY_METADATA[DUMMY_MP3]['duration']
        mock_music.set_pos.assert_called_with(clamped_duration)
        self.assertEqual(self.player.current_position, clamped_duration)


    @patch('src.player.mutagen.File') # Not strictly needed for get_playback_info if track already loaded
    @patch('src.player.pygame.mixer')
    def test_get_playback_info(self, mock_pygame_mixer, mock_mutagen_file):
        mock_music = mock_pygame_mixer.music
        mock_mutagen_file.side_effect = create_mock_mutagen_file # For metadata if needed

        # Setup player state
        self.player.playlist.add_track(DUMMY_MP3)
        self.player.play(DUMMY_MP3) # Loads track, sets metadata, starts play

        self.player.is_playing = True
        self.player.is_paused = False
        self.player.volume = 0.6
        # self.player.track_duration set by _load_track
        # self.player.current_track_loaded_path set by _load_track

        mock_music.get_busy.return_value = True
        mock_music.get_pos.return_value = 10000 # 10 seconds in ms

        info = self.player.get_playback_info()

        self.assertTrue(info['is_playing'])
        self.assertFalse(info['is_paused'])
        self.assertEqual(info['current_time'], 10.0)
        self.assertEqual(info['track_duration'], DUMMY_METADATA[DUMMY_MP3]['duration'])
        self.assertEqual(info['volume'], 0.6)
        self.assertEqual(info['current_track_path'], DUMMY_MP3)
        self.assertIsNotNone(info['current_track_meta'])
        self.assertEqual(info['current_track_meta']['title'], DUMMY_METADATA[DUMMY_MP3]['title'])


    @patch('src.player.mutagen.File')
    # No pygame mock needed if not loading/playing
    def test_get_current_track_metadata(self, mock_mutagen_file):
        mock_mutagen_file.side_effect = create_mock_mutagen_file

        # Case 1: No track in playlist
        self.assertIsNone(self.player.get_current_track_metadata())

        # Case 2: Track exists and is current
        self.player.playlist.add_track(DUMMY_MP3)
        self.player.playlist.set_current_track_by_path(DUMMY_MP3)
        # Simulate track being loaded by player (which get_current_track_metadata checks)
        self.player.current_track_loaded_path = DUMMY_MP3

        metadata = self.player.get_current_track_metadata()

        mock_mutagen_file.assert_called_with(DUMMY_MP3, easy=True)
        self.assertIsNotNone(metadata)
        self.assertEqual(metadata['title'], DUMMY_METADATA[DUMMY_MP3]['title'])
        self.assertEqual(metadata['artist'], DUMMY_METADATA[DUMMY_MP3]['artist'])
        self.assertEqual(metadata['album'], DUMMY_METADATA[DUMMY_MP3]['album'])
        self.assertEqual(metadata['duration'], DUMMY_METADATA[DUMMY_MP3]['duration'])
        self.assertEqual(self.player.track_duration, DUMMY_METADATA[DUMMY_MP3]['duration'])

        # Case 3: Mutagen fails to load a file
        self.player.current_track_loaded_path = "broken.mp3"
        mock_mutagen_file.side_effect = Exception("Mutagen load error")
        metadata_broken = self.player.get_current_track_metadata()
        self.assertIsNone(metadata_broken)
        self.assertEqual(self.player.track_duration, 0) # Should reset on error


if __name__ == '__main__':
    # Need to import pygame here if Player init uses it, to handle the error from missing display
    # However, for unit tests with mocks, it shouldn't be an issue.
    # The global patching in setUp should handle pygame.error for mixer.init()
    try:
        import pygame
        # Attempt to initialize parts of pygame that might be needed by mixer.init
        # This is often needed if mixer.init() itself is not fully mocked/prevented.
        # However, our setUp method patches 'src.player.pygame.mixer' before Player init.
    except ImportError:
        print("Pygame not installed, some tests might rely on its presence for unmocked parts.")
    except pygame.error as e:
        if "No available video device" in str(e) or "display Surface" in str(e):
            # Try to set a dummy video driver if on a headless system
            os.environ['SDL_VIDEODRIVER'] = 'dummy'
            try:
                pygame.display.init() # Try to init display with dummy driver
                pygame.display.set_mode((1,1))
            except pygame.error:
                 print("Failed to set dummy video driver for Pygame. Mixer init might still fail if not perfectly mocked.")
        else:
            print(f"Pygame error during setup: {e}")


    unittest.main()
