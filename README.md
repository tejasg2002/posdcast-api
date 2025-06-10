# Realistic Conversational Podcast Generator API

An API service that transforms monologue scripts into natural-sounding podcast conversations using AI and text-to-speech technology, with special support for Indian English accents and podcast styles.

## Features

- Convert monologue scripts into dynamic dialogues
- Generate natural-sounding conversations with overlapping speech
- Support for multiple speakers with different voices
- Indian English accent support with natural speech patterns
- Customizable tone and language settings
- Duration control for precise podcast length
- High-quality audio output using ElevenLabs TTS
- Natural Indian podcast-style introductions and transitions

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
POST /generate
Content-Type: application/json

{
  "topic": "Technology in India",
  "script": "Your full monologue script goes here...",
  "speakers": [
    {
      "name": "Rahul",
      "role": "host",
      "voice_id": "AZnzlk1XvdvUeBnXmlld"  // Indian male accent
    },
    {
      "name": "Priya",
      "role": "guest",
      "voice_id": "EXAVITQu4vr4xnSDxMaL"  // Indian female accent
    }
  ],
  "tone": "professional",
  "duration_minutes": 15
}
```

### Response

```json
{
  "status": "success",
  "audio_url": "https://yourdomain.com/podcast/episode1.mp3",
  "duration": "15m00s"
}
```

## Features in Detail

### Indian Accent Support
- Natural Indian English speech patterns
- Warm, engaging conversation style
- Hindi phrases naturally integrated
- Indian podcast-style introductions
- Common Indian expressions and speech patterns

### Audio Processing
- Smooth overlapping speech transitions
- Natural pauses and interruptions
- High-quality audio output (320kbps)
- Professional fade in/out effects
- Dynamic audio mixing for multiple speakers

### Dialogue Generation
- Topic-focused conversations
- Structured introductions
- Natural interruptions and overlaps
- Duration-controlled content
- Customizable tone and style

## Environment Variables

- `ELEVENLABS_API_KEY`: Your ElevenLabs API key
- `OPENAI_API_KEY`: Your OpenAI API key
- `MAX_REQUESTS_PER_MINUTE`: Rate limiting (default: 10)

## License

MIT 