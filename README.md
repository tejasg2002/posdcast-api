# Realistic Conversational Podcast Generator API

An API service that transforms monologue scripts into natural-sounding podcast conversations using AI and text-to-speech technology.

## Features

- Convert monologue scripts into dynamic dialogues
- Generate natural-sounding conversations with overlapping speech
- Support for multiple speakers with different voices
- Customizable tone and language settings
- High-quality audio output using ElevenLabs TTS

## Setup

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a `.env` file with your API keys:
   ```
   ELEVENLABS_API_KEY=your_key_here
   OPENAI_API_KEY=your_key_here
   ```
4. Run the server:
   ```bash
   uvicorn app.main:app --reload
   ```

## API Usage

### Generate Podcast

```http
POST /generate-podcast
Content-Type: application/json

{
  "script": "Your full monologue script goes here...",
  "speaker_names": ["Alice", "Bob"],
  "tone": "casual",
  "language": "en"
}
```

### Response

```json
{
  "status": "success",
  "audio_url": "https://yourdomain.com/podcast/episode1.mp3",
  "duration": "4m32s"
}
```

## Environment Variables

- `ELEVENLABS_API_KEY`: Your ElevenLabs API key
- `OPENAI_API_KEY`: Your OpenAI API key
- `MAX_REQUESTS_PER_MINUTE`: Rate limiting (default: 10)

## License

MIT 