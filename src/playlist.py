import random

class Playlist:
    def __init__(self):
        self.tracks: list[str] = []
        self.current_track_index: int = -1

        self.shuffle_mode: bool = False
        self.repeat_mode: str = 'none'  # 'none', 'one', 'all'

        # These are used when shuffle_mode is True.
        # self.tracks continues to hold the original order of tracks.
        # self.shuffled_indices stores a list of indices that maps to self.tracks.
        # self.current_track_index, when shuffle is on, refers to an index in self.shuffled_indices.
        self.shuffled_indices: list[int] = []

    def add_track(self, track_path: str):
        """Adds a track (file path) to the playlist."""
        if track_path not in self.tracks:
            self.tracks.append(track_path)
            if self.current_track_index == -1 and len(self.tracks) == 1: # If first track added
                self.current_track_index = 0

    def remove_track(self, track_path: str):
        """Removes a track from the playlist."""
        # If shuffle is on, turn it off before modifying tracks to simplify index management.
        if self.shuffle_mode:
            self.toggle_shuffle() # This will set shuffle_mode to False and clear shuffled_indices

        if track_path in self.tracks:
            try:
                # Preserve current playing track info if possible
                current_track_path_before_removal = None
                if 0 <= self.current_track_index < len(self.tracks):
                     current_track_path_before_removal = self.tracks[self.current_track_index]

                removed_track_original_idx = self.tracks.index(track_path)
                self.tracks.pop(removed_track_original_idx)

                if not self.tracks:  # Playlist is now empty
                    self.current_track_index = -1
                else:
                    # If the removed track was the one playing, or something before it,
                    # we need to adjust the index or try to find the same track again.
                    if current_track_path_before_removal and current_track_path_before_removal != track_path and current_track_path_before_removal in self.tracks:
                        self.current_track_index = self.tracks.index(current_track_path_before_removal)
                    else:
                        # If current track was removed or index needs adjustment
                        if removed_track_original_idx < self.current_track_index :
                            self.current_track_index -=1
                        elif removed_track_original_idx == self.current_track_index:
                            # Current track removed, try to keep index if valid, else point to new end or 0
                            if self.current_track_index >= len(self.tracks) and len(self.tracks) > 0:
                                self.current_track_index = len(self.tracks) -1
                            # If current_track_index is still valid (points to a new track), no change
                            # If list became empty, this is covered by "if not self.tracks"

                        # Ensure index is valid after adjustments
                        if self.current_track_index >= len(self.tracks) and len(self.tracks) > 0 :
                             self.current_track_index = len(self.tracks) -1
                        elif self.current_track_index < 0 and len(self.tracks) > 0 :
                             self.current_track_index = 0
                        elif not self.tracks:
                             self.current_track_index = -1


            except ValueError:  # Should not happen if track_path in self.tracks check passed
                pass

    def add_track(self, track_path: str): # Overwrite the previous add_track to include shuffle handling
        """Adds a track (file path) to the playlist."""
        if self.shuffle_mode:
            self.toggle_shuffle() # Turn off shuffle, then add

        if track_path not in self.tracks:
            self.tracks.append(track_path)
            if self.current_track_index == -1 and len(self.tracks) == 1:  # If first track added
                self.current_track_index = 0

    # --- Methods for Shuffle and Repeat ---

    def toggle_shuffle(self):
        """Toggles shuffle mode on/off."""
        self.shuffle_mode = not self.shuffle_mode

        if self.shuffle_mode:
            if not self.tracks:
                self.shuffle_mode = False  # Cannot shuffle an empty playlist
                return

            # When turning shuffle ON:
            # The self.tracks list (master list) remains in its original order.
            # self.shuffled_indices will store the playback order.
            # Always start shuffle from the beginning of the shuffled list.
            self.shuffled_indices = list(range(len(self.tracks)))
            random.shuffle(self.shuffled_indices)
            self.current_track_index = 0 # Start at the beginning of the shuffled_indices list

            # If playlist became empty somehow, turn shuffle back off
            if not self.tracks:
                 self.current_track_index = -1
                 self.shuffle_mode = False

        else: # Turning shuffle OFF
            if not self.tracks:
                self.current_track_index = -1
                self.shuffled_indices = []
                return

            if 0 <= self.current_track_index < len(self.shuffled_indices):
                # self.current_track_index is an index into self.shuffled_indices
                # The value self.shuffled_indices[self.current_track_index] is the actual index in self.tracks
                actual_track_idx_in_original_list = self.shuffled_indices[self.current_track_index]
                if 0 <= actual_track_idx_in_original_list < len(self.tracks):
                    self.current_track_index = actual_track_idx_in_original_list
                else: # Should not happen with consistent lists
                    self.current_track_index = 0 if self.tracks else -1
            elif self.tracks : # current_track_index was -1 or invalid, default to 0 for original list
                 self.current_track_index = 0
            else: # Playlist empty
                 self.current_track_index = -1

            self.shuffled_indices = []

    def set_repeat_mode(self, mode: str):
        """Sets the repeat mode ('none', 'one', 'all')."""
        if mode in ['none', 'one', 'all']:
            self.repeat_mode = mode
        else:
            self.repeat_mode = 'none' # Default to 'none' if invalid mode given

    # --- Modified track navigation methods ---

    def get_current_track(self) -> str | None: # Overwrite existing
        """Returns the path of the current track based on shuffle and current_track_index."""
        if not self.tracks:
            return None

        if self.shuffle_mode:
            if 0 <= self.current_track_index < len(self.shuffled_indices):
                actual_idx = self.shuffled_indices[self.current_track_index]
                if 0 <= actual_idx < len(self.tracks):
                    return self.tracks[actual_idx]
            return None # Invalid shuffle index or inconsistent state
        else: # Normal mode
            if 0 <= self.current_track_index < len(self.tracks):
                return self.tracks[self.current_track_index]
            return None

    def next_track(self) -> str | None: # Overwrite existing
        """Advances to the next track based on shuffle/repeat modes."""
        if not self.tracks:
            self.current_track_index = -1
            return None

        # Handle repeat_one: if a track is selected, return it.
        # Handle repeat_one: if a track is selected, return it. If no track selected, select first and return.
        if self.repeat_mode == 'one':
            if self.current_track_index == -1: # No track currently selected
                if not self.tracks: return None # Empty playlist
                self.current_track_index = 0 # Select the first track
            return self.get_current_track() # Return current (now possibly first) track

        if self.shuffle_mode:
            if not self.shuffled_indices:
                # This can happen if tracks were empty when shuffle was toggled on.
                # Or if add/remove (which turns off shuffle) was called then state is weird.
                # Safest is to try to re-initialize shuffle or return None.
                if not self.tracks: return None
                self.toggle_shuffle() # This will re-populate shuffled_indices if tracks exist
                if not self.shuffled_indices: return None # Still no tracks/indices

            target_shuffled_pos: int
            if self.current_track_index == -1: # Was stopped or uninitialized
                target_shuffled_pos = 0
            else: # Is currently on a valid shuffled index
                target_shuffled_pos = self.current_track_index + 1

            if target_shuffled_pos >= len(self.shuffled_indices):
                if self.repeat_mode == 'all':
                    self.current_track_index = 0
                    random.shuffle(self.shuffled_indices) # Reshuffle for next round
                else: # 'none'
                    self.current_track_index = -1
                    return None
            else:
                self.current_track_index = target_shuffled_pos

            # After potential update, ensure current_track_index is valid before using
            if self.current_track_index == -1 : return None # Ended
            if not (0 <= self.current_track_index < len(self.shuffled_indices)):
                 # This would be an inconsistent state, maybe playlist became empty during call
                 return None

            actual_track_idx = self.shuffled_indices[self.current_track_index]
            return self.tracks[actual_track_idx]

        else: # Normal (non-shuffled) mode
            if self.current_track_index == -1 and self.repeat_mode == 'none': # Stay at end if already ended
                return None
            elif self.current_track_index == -1:
                self.current_track_index = 0 # Start from beginning if -1 and not 'none' repeat
            else:
                self.current_track_index += 1

            if self.current_track_index >= len(self.tracks):
                if self.repeat_mode == 'all':
                    self.current_track_index = 0
                else: # 'none'
                    self.current_track_index = -1
                    return None # Explicitly return None after setting index to -1

            # If after all logic, index is -1 (e.g. for repeat_mode='none'), return None.
            if self.current_track_index == -1:
                return None
            return self.tracks[self.current_track_index]

    def previous_track(self) -> str | None: # Overwrite existing
        """Moves to the previous track based on shuffle/repeat modes."""
        if not self.tracks:
            self.current_track_index = -1
            return None

        if self.repeat_mode == 'one':
            if self.current_track_index == -1: # No track currently selected
                if not self.tracks: return None
                self.current_track_index = 0 # Select the first track (consistent with next_track for repeat_one)
            return self.get_current_track()

        if self.shuffle_mode:
            if not self.shuffled_indices:
                if not self.tracks: return None
                self.toggle_shuffle()
                if not self.shuffled_indices: return None

            target_shuffled_pos: int
            if self.current_track_index == -1: # Was stopped or uninitialized
                # For previous, typically go to the end of the list
                target_shuffled_pos = len(self.shuffled_indices) - 1
            else: # Is currently on a valid shuffled index
                target_shuffled_pos = self.current_track_index - 1

            if target_shuffled_pos < 0:
                if self.repeat_mode == 'all':
                    self.current_track_index = len(self.shuffled_indices) - 1 if self.shuffled_indices else -1
                    # No re-shuffle when going previous and repeating all from end.
                else: # 'none'
                    self.current_track_index = -1
                    return None
            else:
                self.current_track_index = target_shuffled_pos

            if self.current_track_index == -1 : return None # Ended
            if not (0 <= self.current_track_index < len(self.shuffled_indices)):
                 return None

            actual_track_idx = self.shuffled_indices[self.current_track_index]
            return self.tracks[actual_track_idx]

        else: # Normal (non-shuffled) mode
            if self.current_track_index == -1 and self.repeat_mode == 'none': # Stay at end if already ended
                return None
            elif self.current_track_index == -1: # Start from end if -1 and not 'none' repeat
                 self.current_track_index = len(self.tracks) - 1
            elif self.current_track_index == 0:
                if self.repeat_mode == 'all':
                    self.current_track_index = len(self.tracks) - 1
                else: # 'none'
                    self.current_track_index = -1
                    return None
            else:
                self.current_track_index -= 1

            if self.current_track_index == -1: return None
            return self.tracks[self.current_track_index]

    def set_current_track_by_path(self, track_path: str) -> bool: # Overwrite existing
        """Sets the current track by its path. Considers shuffle mode."""
        try:
            original_list_idx = self.tracks.index(track_path)
        except ValueError:
            return False # Track not in the master list of tracks

        if self.shuffle_mode:
            if not self.shuffled_indices and self.tracks: # Shuffle on, but not initialized (e.g. after add/remove)
                # This state ideally should be prevented by add_track/remove_track turning shuffle off.
                # However, as a fallback, initialize shuffle.
                self.shuffled_indices = list(range(len(self.tracks)))
                random.shuffle(self.shuffled_indices)
                # No current track was playing in shuffle, so set to start of new shuffle.
                # Or try to find original_list_idx in the new shuffle.

            try:
                # Find where the original_list_idx appears in the shuffled_indices
                self.current_track_index = self.shuffled_indices.index(original_list_idx)
                return True
            except ValueError:
                # This means the original_list_idx (which is a valid index for self.tracks)
                # is somehow not in self.shuffled_indices. This indicates a corrupted shuffle state.
                # Safest is to turn shuffle off and set to the original index.
                self.toggle_shuffle() # Turn off shuffle
                self.current_track_index = original_list_idx # Set to original index
                return True # Indicate success, but shuffle state was reset
        else: # Normal mode
            self.current_track_index = original_list_idx
            return True

    def get_playlist_tracks(self) -> list[str]: # Ensure this is the last one from original
        """Returns the list of all tracks in the playlist (original order)."""
        return self.tracks # Original method was correct, the erroneous part was the duplicated block below it.

    # The duplicated block of methods that caused the IndentationError started from here.
    # Removing them by replacing this entire found block with just the correct get_playlist_tracks.
    # The save_playlist and load_playlist stubs are correctly defined after the first block of methods.

    def save_playlist(self, filepath: str):
        """Saves the playlist to a file (stub)."""
        # To be implemented later (e.g., using JSON or text file)
        print(f"Playlist save to {filepath} requested (not implemented).")
        pass

    def load_playlist(self, filepath: str):
        """Loads a playlist from a file (stub)."""
        # To be implemented later
        print(f"Playlist load from {filepath} requested (not implemented).")
        pass
