import os
from pydub import AudioSegment
from typing import List, Tuple
import tempfile
import uuid
import shutil
from datetime import timedelta
import logging
import re

logger = logging.getLogger(__name__)

class AudioProcessor:
    def __init__(self):
        self.output_dir = os.path.join(os.getcwd(), "output")
        os.makedirs(self.output_dir, exist_ok=True)
        self.MIN_DURATION_MS = 60 * 1000  # 1 minute in milliseconds
        self.MAX_DURATION_MS = 30 * 60 * 1000  # 30 minutes in milliseconds
        self.OVERLAP_DURATION = 1000  # 1 second overlap in milliseconds

    def _should_overlap(self, text: str) -> bool:
        """Check if the segment should overlap based on text markers."""
        return "[overlap]" in text.lower()

    async def merge_audio(self, audio_files: List[str], dialogue: List[Tuple[str, str]] = None) -> str:
        """
        Merge multiple audio files into a single podcast track with natural overlaps.
        Returns the path to the merged audio file.
        """
        if not audio_files:
            raise ValueError("No audio files provided")

        try:
            # Load all audio segments
            segments = []
            for i, file_path in enumerate(audio_files):
                logger.info(f"Loading audio segment: {file_path}")
                segment = AudioSegment.from_mp3(file_path)
                
                # Add fade in/out for smoother transitions
                segment = segment.fade_in(100).fade_out(100)
                
                # Store segment with its dialogue text if available
                if dialogue and i < len(dialogue):
                    segments.append((segment, dialogue[i][1]))
                else:
                    segments.append((segment, ""))

            # Create the final track
            final_track = AudioSegment.empty()
            current_position = 0  # Position in milliseconds

            for i, (segment, text) in enumerate(segments):
                if i == 0:
                    # First segment always starts at the beginning
                    final_track = segment
                    current_position = len(segment)
                else:
                    if self._should_overlap(text):
                        # If marked for overlap, start this segment before the previous one ends
                        overlap_position = max(0, current_position - self.OVERLAP_DURATION)
                        
                        # Create a temporary track up to the overlap point
                        temp_track = final_track[:overlap_position]
                        
                        # Overlay the current segment with crossfade
                        overlap_segment = segment.fade_in(300)  # Smooth fade in for overlap
                        
                        # Mix the overlapping portions instead of replacing
                        overlap_portion = final_track[overlap_position:current_position]
                        mixed_overlap = overlap_portion.overlay(overlap_segment[:self.OVERLAP_DURATION])
                        
                        # Combine the tracks
                        final_track = temp_track + mixed_overlap + segment[self.OVERLAP_DURATION:]
                    else:
                        # Add a small gap between non-overlapping segments
                        gap = AudioSegment.silent(duration=300)  # 300ms gap
                        final_track = final_track + gap + segment

                    current_position = len(final_track)

            # Check and adjust duration
            duration_ms = len(final_track)
            
            if duration_ms < self.MIN_DURATION_MS:
                silence_needed = self.MIN_DURATION_MS - duration_ms
                silence = AudioSegment.silent(duration=silence_needed)
                final_track = final_track + silence
            elif duration_ms > self.MAX_DURATION_MS:
                final_track = final_track[:self.MAX_DURATION_MS]
                final_track = final_track.fade_out(2000)  # 2 second fade out

            # Generate a unique filename
            filename = f"podcast_{uuid.uuid4()}.mp3"
            output_path = os.path.join(self.output_dir, filename)
            
            # Export the final track with higher quality
            logger.info(f"Saving merged audio to: {output_path}")
            final_track.export(output_path, format="mp3", bitrate="320k")

            # Clean up temporary files
            for file_path in audio_files:
                try:
                    if os.path.exists(file_path):
                        os.remove(file_path)
                        logger.info(f"Cleaned up temporary file: {file_path}")
                except Exception as e:
                    logger.warning(f"Failed to clean up temporary file {file_path}: {str(e)}")

            return output_path

        except Exception as e:
            logger.error(f"Error merging audio: {str(e)}")
            raise

    async def save_audio(self, audio_path: str) -> str:
        """
        Save the audio file to a permanent location and return the URL.
        """
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
            
        # The file is already in the output directory, just return the URL
        filename = os.path.basename(audio_path)
        return f"/audio/{filename}"

    async def get_audio_duration(self, audio_path: str) -> str:
        """
        Get the duration of the audio file in a human-readable format.
        """
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
            
        audio = AudioSegment.from_mp3(audio_path)
        duration_ms = len(audio)
        duration = timedelta(milliseconds=duration_ms)
        
        # Format as "XmYs"
        minutes = duration.seconds // 60
        seconds = duration.seconds % 60
        return f"{minutes}m{seconds}s"

    def cleanup_old_files(self, max_age_hours: int = 24):
        """
        Clean up audio files older than max_age_hours.
        """
        import time
        current_time = time.time()
        
        for filename in os.listdir(self.output_dir):
            filepath = os.path.join(self.output_dir, filename)
            if os.path.isfile(filepath):
                file_age = current_time - os.path.getmtime(filepath)
                if file_age > (max_age_hours * 3600):
                    try:
                        os.remove(filepath)
                        logger.info(f"Cleaned up old file: {filepath}")
                    except Exception as e:
                        logger.warning(f"Failed to clean up old file {filepath}: {str(e)}") 