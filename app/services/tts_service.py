import os
from elevenlabs import generate, set_api_key, Voice, VoiceSettings
from typing import Dict, Optional
import tempfile
import uuid
import requests
import re

class TTSService:
    def __init__(self):
        api_key = os.getenv("ELEVENLABS_API_KEY")
        if not api_key:
            raise ValueError("ELEVENLABS_API_KEY environment variable is not set")
        set_api_key(api_key)
        self.voice_cache: Dict[str, Voice] = {}
        self._initialize_voice_cache()

    def _initialize_voice_cache(self):
        """Initialize voice cache with default voices for common names"""
        # Map common names to ElevenLabs voice IDs with Indian accents
        voice_mapping = {
            "Alex": "pNInz6obpgDQGcFmaJgB",    # Adam voice (neutral Indian accent)
            "Sarah": "ErXwobaYiN019PkySvjV",    # Nicole voice (Indian female accent)
            "Rahul": "AZnzlk1XvdvUeBnXmlld",    # Domi voice (Indian male accent)
            "Priya": "EXAVITQu4vr4xnSDxMaL",    # Rachel voice (Indian female accent)
            "Arjun": "MF3mGyEYCl7XYWbV9V6O",    # Elli voice (Indian male accent)
        }
        
        for name, voice_id in voice_mapping.items():
            self.voice_cache[name] = Voice(
                voice_id=voice_id,
                settings=VoiceSettings(
                    stability=0.5,
                    similarity_boost=0.75,
                    style=0.5,  # Add some style variation
                    use_speaker_boost=True  # Enhance speaker characteristics
                )
            )

    def _process_text_for_tts(self, text: str) -> str:
        """
        Process text to make it more suitable for TTS:
        1. Remove [overlap] markers
        2. Convert ellipsis to commas or periods for proper pausing
        3. Add SSML-like timing for better pacing
        4. Add Indian English speech patterns
        """
        # Remove [overlap] markers
        text = re.sub(r'\[overlap\]', '', text, flags=re.IGNORECASE)
        
        # Replace ellipsis with appropriate pauses
        text = re.sub(r'\.\.\.\s*', ', ', text)
        
        # Add slight pauses after punctuation for more natural speech
        text = re.sub(r'([.!?])\s+', r'\1, ', text)
        
        # Add Indian English speech patterns
        text = re.sub(r'\b(?:actually|basically|actually)\b', 'actually', text, flags=re.IGNORECASE)
        text = re.sub(r'\b(?:you know|like|right)\b', 'you know', text, flags=re.IGNORECASE)
        
        # Clean up any double commas or spaces
        text = re.sub(r',\s*,', ',', text)
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()

    async def generate_speech(
        self,
        text: str,
        speaker_name: str,
        voice_id: Optional[str] = None
    ) -> str:
        """
        Generate speech for the given text using ElevenLabs API.
        Returns the path to the generated audio file.
        """
        try:
            # Process text for better TTS output
            processed_text = self._process_text_for_tts(text)
            
            # Get or create voice for the speaker
            voice = self._get_voice_for_speaker(speaker_name, voice_id)
            
            # Generate audio using requests instead of the client
            url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice.voice_id}"
            headers = {
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": os.getenv("ELEVENLABS_API_KEY")
            }
            data = {
                "text": processed_text,
                "model_id": "eleven_multilingual_v2",
                "voice_settings": {
                    "stability": voice.settings.stability,
                    "similarity_boost": voice.settings.similarity_boost,
                    "style": voice.settings.style,
                    "use_speaker_boost": voice.settings.use_speaker_boost
                }
            }
            
            response = requests.post(url, json=data, headers=headers)
            response.raise_for_status()
            
            # Save to temporary file
            temp_dir = tempfile.gettempdir()
            filename = f"{uuid.uuid4()}.mp3"
            filepath = os.path.join(temp_dir, filename)
            
            with open(filepath, "wb") as f:
                f.write(response.content)

            return filepath
            
        except Exception as e:
            raise Exception(f"Failed to generate speech: {str(e)}")

    def _get_voice_for_speaker(self, speaker_name: str, voice_id: Optional[str] = None) -> Voice:
        """
        Get or create a voice for the given speaker name.
        """
        if voice_id:
            return Voice(
                voice_id=voice_id,
                settings=VoiceSettings(
                    stability=0.5,
                    similarity_boost=0.75
                )
            )
            
        if speaker_name in self.voice_cache:
            return self.voice_cache[speaker_name]

        # If speaker not in cache, use a default voice
        default_voice = Voice(
            voice_id="EXAVITQu4vr4xnSDxMaL",  # Rachel voice
            settings=VoiceSettings(
                stability=0.5,
                similarity_boost=0.75
            )
        )
        
        self.voice_cache[speaker_name] = default_voice
        return default_voice 