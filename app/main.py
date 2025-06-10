from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional
import os
from dotenv import load_dotenv
from app.services.dialogue_generator import DialogueGenerator
from app.services.audio_processor import AudioProcessor
from app.services.tts_service import TTSService
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

app = FastAPI(title="Podcast Generator API")

# Create output directory if it doesn't exist
output_dir = os.path.join(os.getcwd(), "output")
os.makedirs(output_dir, exist_ok=True)

# Mount the output directory for static file serving
app.mount("/audio", StaticFiles(directory=output_dir), name="audio")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Speaker(BaseModel):
    role: str  # "host" or "guest"
    name: str
    voice_id: Optional[str] = None

class PodcastRequest(BaseModel):
    topic: str  # The main topic of the podcast
    script: str  # The detailed content/points to discuss
    speakers: List[Speaker]
    tone: str = "conversational"
    duration_minutes: int = 10  # Default duration in minutes

class PodcastResponse(BaseModel):
    status: str
    audio_url: str
    duration: str

@app.post("/generate")
async def generate_podcast(request: PodcastRequest):
    try:
        # Initialize services
        dialogue_generator = DialogueGenerator()
        tts_service = TTSService()
        audio_processor = AudioProcessor()

        # Extract speaker names and roles for dialogue generation
        speaker_info = [(speaker.role, speaker.name) for speaker in request.speakers]

        # Generate dialogue
        dialogue = await dialogue_generator.generate_dialogue(
            request.topic,
            request.script,
            speaker_info,
            request.tone,
            request.duration_minutes
        )

        # Generate audio for each dialogue segment
        audio_files = []
        voice_mapping = {speaker.name: speaker.voice_id for speaker in request.speakers}
        
        for speaker, text in dialogue:
            voice_id = voice_mapping.get(speaker)
            audio_file = await tts_service.generate_speech(text, speaker, voice_id)
            audio_files.append(audio_file)

        # Merge audio files with overlapping support
        output_path = await audio_processor.merge_audio(audio_files, dialogue)

        # Get duration
        duration = await audio_processor.get_audio_duration(output_path)

        # Get URL
        url = await audio_processor.save_audio(output_path)

        return {
            "url": url,
            "duration": duration,
            "dialogue": dialogue
        }

    except Exception as e:
        logger.error(f"Error generating podcast: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy"} 