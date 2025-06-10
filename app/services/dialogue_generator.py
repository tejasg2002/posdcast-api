import os
from openai import AsyncOpenAI
from typing import List, Tuple, Dict
import json
import re

class DialogueGenerator:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def _clean_dialogue_text(self, text: str) -> str:
        """
        Clean the dialogue text by:
        1. Converting action tags to appropriate pauses
        2. Removing spoken descriptions of actions
        3. Removing all action markers including [overlap]
        """
        # Replace action tags with pause markers
        text = re.sub(r'\[(?:pause|thoughtful pause|brief pause)\]', '...', text)
        
        # Remove all action tags including [overlap]
        text = re.sub(r'\[.*?\]', '', text)
        
        # Clean up multiple spaces and ellipsis
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\.{2,}', '...', text)
        text = re.sub(r'\s*\.\.\.\s*', '... ', text)
        
        # Remove words describing actions
        action_words = [
            r'\b(?:pauses?|nods?|nodding)\b',
            r'\b(?:smiles?|smiling)\b',
            r'\b(?:laughs?|laughing)\b',
            r'\b(?:sighs?|sighing)\b',
            r'\b(?:thinks?|thinking)\b',
            r'\b(?:gestures?|gesturing)\b'
        ]
        for word in action_words:
            text = re.sub(word, '', text, flags=re.IGNORECASE)
        
        # Clean up any remaining artifacts
        text = re.sub(r'\s+', ' ', text)  # Remove multiple spaces
        text = re.sub(r'^\s+|\s+$', '', text)  # Trim
        text = re.sub(r'\s*([,.!?])', r'\1', text)  # Fix spacing around punctuation
        
        return text

    async def generate_dialogue(
        self,
        script: str,
        speaker_info: List[Dict[str, str]],
        tone: str = "professional",
        topic: str = "Technology",
        duration_minutes: int = 10
    ) -> List[Dict[str, str]]:
        """
        Generate a natural-sounding dialogue between speakers based on the script.
        """
        try:
            # Extract host and guest information
            host = next((s for s in speaker_info if s.get("role") == "host"), speaker_info[0])
            guest = next((s for s in speaker_info if s.get("role") == "guest"), speaker_info[1])
            
            # Create a structured introduction prompt
            intro_prompt = f"""Create a natural podcast introduction for a {tone} Indian podcast about {topic}.
            Host: {host['name']}
            Guest: {guest['name']}
            
            Include:
            1. A warm welcome in Indian style
            2. Brief introduction of the guest with their background
            3. Today's topic: {topic}
            4. A natural transition to the main conversation
            
            Format: Use [overlap] for natural interruptions and [pause] for dramatic pauses.
            Keep it under 2 minutes.
            
            Example style:
            Host: "Namaste everyone! Welcome to another exciting episode of our podcast. Today we have a very special guest with us..."
            """
            
            # Generate introduction
            intro_response = await self.client.chat.completions.create(
                model="gpt-4-0125-preview",
                messages=[
                    {"role": "system", "content": "You are a professional Indian podcast host."},
                    {"role": "user", "content": intro_prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )
            
            introduction = intro_response.choices[0].message.content.strip()
            
            # Create main conversation prompt
            main_prompt = f"""Create a natural {tone} podcast conversation about {topic} between:
            Host: {host['name']} (Indian host)
            Guest: {guest['name']} (Indian guest)
            
            Based on this script: {script}
            
            Requirements:
            1. Use natural Indian English expressions and speech patterns
            2. Include common Indian podcast phrases like "absolutely", "you know", "right?"
            3. Add natural interruptions and overlaps
            4. Keep responses concise and engaging
            5. Total duration should be around {duration_minutes} minutes
            6. Include some Hindi/Indian language phrases naturally
            7. Add some light humor and personal anecdotes
            
            Format each line as: "Speaker: Text [overlap]"
            Use [overlap] for natural interruptions and [pause] for dramatic pauses.
            
            Example style:
            Host: "That's absolutely fascinating! You know, in India we often see..."
            Guest: "Yes, exactly! And what's interesting is..."
            """
            
            # Generate main conversation
            main_response = await self.client.chat.completions.create(
                model="gpt-4-0125-preview",
                messages=[
                    {"role": "system", "content": "You are a professional Indian podcast host and guest."},
                    {"role": "user", "content": main_prompt}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            main_conversation = main_response.choices[0].message.content.strip()
            
            # Combine introduction and main conversation
            full_dialogue = f"{introduction}\n\n{main_conversation}"
            
            # Parse the dialogue into segments
            dialogue_segments = []
            current_speaker = None
            
            for line in full_dialogue.split('\n'):
                line = line.strip()
                if not line:
                    continue
                    
                # Extract speaker and text
                match = re.match(r'^([^:]+):\s*(.+)$', line)
                if match:
                    speaker, text = match.groups()
                    speaker = speaker.strip()
                    text = text.strip()
                    
                    # Find matching speaker info
                    speaker_data = next(
                        (s for s in speaker_info if s['name'].lower() == speaker.lower()),
                        None
                    )
                    
                    if speaker_data:
                        dialogue_segments.append({
                            "speaker": speaker_data['name'],
                            "text": text,
                            "voice_id": speaker_data['voice_id']
                        })
            
            return dialogue_segments
            
        except Exception as e:
            raise Exception(f"Failed to generate dialogue: {str(e)}")

    def _parse_dialogue_text(self, text: str, speaker_names: List[str]) -> List[Tuple[str, str]]:
        """
        Parse dialogue text into a list of (speaker, text) tuples.
        """
        dialogue = []
        lines = text.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Try to match "Speaker: Text" pattern
            for speaker in speaker_names:
                pattern = f"^{re.escape(speaker)}:\\s*(.+)$"
                match = re.match(pattern, line, re.IGNORECASE)
                if match:
                    dialogue_text = match.group(1).strip()
                    # Clean the dialogue text
                    cleaned_text = self._clean_dialogue_text(dialogue_text)
                    if cleaned_text:  # Only add if there's actual text after cleaning
                        dialogue.append((speaker, cleaned_text))
                    break

        return dialogue 