import os
import json
import time
from elevenlabs import Voice, VoiceSettings, save # Keep Voice, VoiceSettings, save
from elevenlabs.client import ElevenLabs # Import the client
from flask import current_app # To access Flask's app config

def convert_text_to_speech_gemini(text_script, output_audio_path):
    """
    Converts a given text script into natural language speech using ElevenLabs Text-to-Speech.

    Args:
        text_script (str): The text content to convert to speech.
        output_audio_path (str): The full path where the generated audio file will be saved (e.g., .mp3).

    Yields:
        str: JSON string indicating progress or completion for SSE.
    Returns:
        str: The path to the saved audio file on success.
    """

    elevenlabs_api_key = current_app.config.get('ELEVENLABS_API_KEY')
    if not elevenlabs_api_key:
        raise ValueError("ElevenLabs API Key is not configured. Please set it in settings.")

    # Initialize the ElevenLabs client by passing the API key directly
    client = ElevenLabs(api_key=elevenlabs_api_key)

    voice_id_to_use = "pNInz6obpgDQGcFmaJgB" # Voice ID for Adam (male voice)

    print("Starting ElevenLabs Text-to-Speech synthesis...")
    yield json.dumps({'status': 'in_progress', 'progress': 10, 'message': 'Speech: Sending text to ElevenLabs API...'})

    try:
        # Generate audio using the client instance.
        # This returns a generator, even without stream=True, in some versions.
        audio_generator = client.generate(
            text=text_script,
            voice=Voice(voice_id=voice_id_to_use,
                        settings=VoiceSettings(stability=0.75, similarity_boost=0.75, style=0.0, use_speaker_boost=True)),
            model="eleven_multilingual_v2" # Recommended model for general use
        )

        # Collect all chunks from the generator into a single bytes object
        full_audio_bytes = b''
        for chunk in audio_generator:
            full_audio_bytes += chunk
            # Optional: yield progress based on chunks received
            # (Requires knowing total expected chunks which is not directly provided by ElevenLabs)

        yield json.dumps({'status': 'in_progress', 'progress': 70, 'message': 'Speech: Audio received. Saving file...'})

        # Save the complete bytes object to the specified file path
        save(full_audio_bytes, output_audio_path)
        print(f"Audio content written to '{output_audio_path}'")

        yield json.dumps({'status': 'in_progress', 'progress': 100, 'message': 'Speech: File saved.'})

    except Exception as e:
        print(f"Error during ElevenLabs Text-to-Speech synthesis: {e}")
        # ElevenLabs specific error handling might involve checking error codes
        if "rate limit" in str(e).lower():
            raise ValueError("ElevenLabs API rate limit exceeded. Please try again later.")
        elif "invalid api key" in str(e).lower() or "authentication" in str(e).lower():
            raise ValueError("Invalid or unauthorized ElevenLabs API Key. Please check your settings.")
        else:
            raise # Re-raise the general exception for Flask to catch

    # IMPORTANT: Return the audio path instead of yielding a final status message
    # This value will be captured by the `StopIteration` in the calling function.
    return output_audio_path

