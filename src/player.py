from .playlist import Playlist
import mutagen # For reading metadata
import pygame # For audio playback

class Player:
    def __init__(self):
        pygame.mixer.init()
        self.volume = 0.5  # Default volume
        pygame.mixer.music.set_volume(self.volume)
        self.playlist = Playlist()
        self.current_position = 0  # Playback position in seconds
        self.track_duration = 0  # Total duration of current track in seconds
        self.current_track_loaded_path = None # Path of the track currently loaded by the mixer
        self.is_playing = False
        self.is_paused = False

    def _load_track(self, track_path: str) -> bool:
        """Loads a track into the pygame mixer.
        Returns True if successful, False otherwise."""
        if track_path == self.current_track_loaded_path and pygame.mixer.music.get_busy():
             # If same track is loaded and music is playing/paused, don't reload unless necessary.
             # For simplicity, we might reload if play is called again, but this avoids redundant loads.
             # However, to ensure correct start from beginning or specified position, reloading might be intended.
             # For now, let's assume if it's the same path, and we are asked to load, we load.
             pass

        try:
            pygame.mixer.music.load(track_path)
            self.current_track_loaded_path = track_path
            self.current_position = 0 # Reset position for new track
            # Fetch metadata to update duration, etc.
            self.get_current_track_metadata() # This will also update self.track_duration
            return True
        except pygame.error as e:
            print(f"Error loading track {track_path}: {e}")
            self.current_track_loaded_path = None
            self.is_playing = False
            self.is_paused = False
            return False

    def play(self, track_path: str = None):
        """Plays a specific track or resumes/plays current from playlist."""
        if track_path:
            # Attempt to set this track as current in the playlist
            # This assumes playlist has a method to find and set current track by path
            # For now, we'll directly try to load it. The UI/controller logic
            # would typically ensure playlist is updated.
            if self.playlist.set_current_track_by_path(track_path): # Assumes this method exists
                if self._load_track(track_path):
                    pygame.mixer.music.play()
                    self.is_playing = True
                    self.is_paused = False
                else:
                    self.is_playing = False
                    self.is_paused = False
            else: # Track not in playlist or set_current_track_by_path failed
                # Fallback: try to load it anyway if it's a direct path,
                # but this means playlist and player might be out of sync.
                # For now, strict: if track_path is given, it must be settable in playlist.
                print(f"Track {track_path} not found or couldn't be set in playlist.")
                self.is_playing = False
                self.is_paused = False

        else:  # Resume or play current from playlist
            if self.is_paused and self.current_track_loaded_path:
                pygame.mixer.music.unpause()
                self.is_playing = True
                self.is_paused = False
            else:
                current_track_path_from_playlist = self.playlist.get_current_track()
                if current_track_path_from_playlist:
                    if self.current_track_loaded_path != current_track_path_from_playlist or not pygame.mixer.music.get_busy():
                        # Load if different track or if not busy (e.g. stopped or never started)
                        if not self._load_track(current_track_path_from_playlist):
                            self.is_playing = False # Loading failed
                            self.is_paused = False
                            return # Don't proceed to play

                    # If already loaded and just need to play (or replay after stop)
                    pygame.mixer.music.play()
                    self.is_playing = True
                    self.is_paused = False
                else: # No current track in playlist
                    self.is_playing = False
                    self.is_paused = False
                    print("No current track in playlist to play.")


    def pause(self):
        """Pauses playback."""
        if self.is_playing and not self.is_paused and pygame.mixer.music.get_busy():
            pygame.mixer.music.pause()
            self.is_paused = True
            self.is_playing = False # Not actively playing, but can be resumed

    def stop(self):
        """Stops playback."""
        pygame.mixer.music.stop()
        self.is_playing = False
        self.is_paused = False
        self.current_position = 0
        # self.current_track_loaded_path = None # Keep it to allow "play current" to resume from start of same track
                                            # Or set to None to force fresh load always after stop.
                                            # For now, let's keep it, _load_track handles reload if path changes.

    def next_track(self):
        """Skips to the next track."""
        current_is_playing_or_paused = self.is_playing or self.is_paused
        # self.stop() # Stop current track (also resets current_position)

        new_track_path = self.playlist.next_track()
        if new_track_path:
            # self.play(new_track_path) # play will call _load_track
            # If was playing, start playing new track. If paused, load new track but stay paused.
            self._load_track(new_track_path) # Load the track and metadata
            if current_is_playing_or_paused and not self.is_paused : # if it was playing (not paused)
                self.play() # Start playing the new loaded track
            elif self.is_paused: # if it was paused, remain paused but new track is loaded.
                 # current_position should be 0 for the new track
                 pass
            # If it was stopped, it remains stopped, new track loaded.
        else: # No next track (e.g. playlist empty or error)
            self.stop() # Ensure player is in a stopped state.

    def prev_track(self):
        """Skips to the previous track."""
        current_is_playing_or_paused = self.is_playing or self.is_paused
        # self.stop()

        new_track_path = self.playlist.previous_track()
        if new_track_path:
            # self.play(new_track_path)
            self._load_track(new_track_path)
            if current_is_playing_or_paused and not self.is_paused:
                self.play()
            elif self.is_paused:
                pass
        else:
            self.stop()


    def set_volume(self, volume_level: float):
        """Sets the player's volume.

        Args:
            volume_level: A float between 0.0 and 1.0.
        """
        self.volume = max(0.0, min(1.0, volume_level))  # Clamp between 0.0 and 1.0
        pygame.mixer.music.set_volume(self.volume)

    def get_volume(self) -> float:
        """Returns the current volume level."""
        return self.volume

    def seek(self, position: int):
        """Seeks to a specific position in the track.

        Args:
            position: The position to seek to, in seconds.
        """
        if self.current_track_loaded_path and self.track_duration > 0: # Only seek if a track is loaded and has duration
            try:
                # Clamp position to valid range
                actual_position = max(0, min(position, self.track_duration))

                # Pygame's set_pos takes position in seconds.
                # It works best if music is playing. If paused, behavior can be inconsistent.
                # If stopped, it might not work until play is called.

                if not self.is_playing and not self.is_paused: # If stopped
                    self._load_track(self.current_track_loaded_path) # Reload the track
                    pygame.mixer.music.play(start=actual_position) # Start playing from position
                    pygame.mixer.music.pause() # Immediately pause if it was meant to be a seek in stopped/paused state
                                             # This is a bit of a hack. Better to just set current_position
                                             # and let play() handle it.
                    self.current_position = actual_position
                    # Player remains in "stopped" state regarding is_playing/is_paused flags. Playback will start at seek pos.
                elif self.is_paused:
                    # For some backends/formats, seek while paused might not reflect until unpaused.
                    # Or it might play a short burst.
                    # A common way is to unpause, seek, then re-pause.
                    pygame.mixer.music.unpause()
                    pygame.mixer.music.set_pos(actual_position)
                    pygame.mixer.music.pause()
                    self.current_position = actual_position
                else: # Is playing
                    pygame.mixer.music.set_pos(actual_position)
                    # self.current_position = actual_position # get_pos() should reflect this while playing

                # Update internal position; get_pos might not be accurate immediately or if paused.
                self.current_position = actual_position

            except pygame.error as e:
                print(f"Error seeking to {position}s: {e}")
                # self.current_position remains unchanged or reflects pygame's actual state if possible
        else:
            print("Seek ignored: No track loaded or track duration unknown.")


    def get_current_position(self) -> int:
        """Returns the current playback position in seconds, more accurately."""
        if self.is_playing and pygame.mixer.music.get_busy():
            # get_pos returns milliseconds since play was called
            # For a more robust current position, especially with seeking:
            # self.current_position should be the base seek time.
            # Add time elapsed since last play/seek event.
            # This is complex. Pygame's get_pos() is often sufficient if continuously playing.
            # If seeking or pausing, self.current_position needs to be managed carefully.
            # For now, if playing, use get_pos. If paused, use stored self.current_position.
            return int(pygame.mixer.music.get_pos() / 1000.0)
        return self.current_position # Return stored position if paused or stopped

    def get_track_duration(self) -> int:
        """Returns the total duration of the current track in seconds, from metadata."""
        return self.track_duration # This is updated by _load_track via get_current_track_metadata

    def get_current_track_metadata(self):
        """
        Retrieves metadata for the current track in the playlist.
        This method is also called by _load_track to ensure track_duration is set.
        Returns:
            A dictionary with 'title', 'artist', 'album', 'duration' if a track is loaded and metadata is found.
            Returns None if no track is current or metadata cannot be read.
        """
        # Determine which track's metadata to get: one loaded or one selected in playlist
        # For consistency, usually it's the one loaded or about to be loaded.
        # self.current_track_loaded_path is more reliable if _load_track calls this.
        # If called externally, self.playlist.get_current_track() might be more appropriate.
        # Let's assume it's for the track that IS or WILL BE current for playback.

        track_to_get_meta_for = self.current_track_loaded_path
        if not track_to_get_meta_for:
             # Fallback to playlist's current if nothing is loaded yet by player
            track_to_get_meta_for = self.playlist.get_current_track()

        if not track_to_get_meta_for:
            self.track_duration = 0 # No track, so duration is 0
            return None

        try:
            audio_file = mutagen.File(track_to_get_meta_for, easy=True)
            if not audio_file:
                self.track_duration = 0
                return None

            duration = 0
            if audio_file.info: # Check if info object exists
                 duration = int(audio_file.info.length) if hasattr(audio_file.info, 'length') else 0

            metadata = {
                'title': audio_file.get('title', ['Unknown Title'])[0],
                'artist': audio_file.get('artist', ['Unknown Artist'])[0],
                'album': audio_file.get('album', ['Unknown Album'])[0],
                'duration': duration
            }

            if duration > 0:
                self.track_duration = duration # Update player's knowledge of duration

            return metadata
        except Exception as e:
            print(f"Error reading metadata for {track_to_get_meta_for}: {e}")
            self.track_duration = 0 # Reset duration if error
            return None

    def get_playback_info(self):
        """Returns a dictionary of the current playback state and track info."""
        current_time_ms = 0
        if self.is_playing and pygame.mixer.music.get_busy():
            current_time_ms = pygame.mixer.music.get_pos() # Time in ms

        # Use self.current_position as the primary store for current time,
        # especially when paused or after seeking. get_pos() is only reliable during active play.
        # This logic needs refinement for robust timekeeping.
        # For now, if playing, trust get_pos(). If paused, trust self.current_position.

        actual_current_time_sec = 0
        if self.is_playing:
            actual_current_time_sec = current_time_ms / 1000.0
        elif self.is_paused:
            actual_current_time_sec = self.current_position
        # If stopped, self.current_position is 0.

        return {
            'is_playing': self.is_playing,
            'is_paused': self.is_paused,
            'current_time': actual_current_time_sec,
            'track_duration': self.track_duration,
            'volume': self.volume,
            'current_track_path': self.current_track_loaded_path,
            'current_track_meta': self.get_current_track_metadata() if self.current_track_loaded_path else None
        }
