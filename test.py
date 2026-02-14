"""
Simple ElevenLabs Speech-to-Text Test
Make sure to install: pip install elevenlabs --break-system-packages
"""

from elevenlabs.client import ElevenLabs

# Initialize the client with your API key
client = ElevenLabs(
    api_key="sk_9029565a2659e7974ad9ea2c07412d31a230efcc8298b720"  # Replace with your actual API key
)

def transcribe_audio(audio_file_path):
    """
    Transcribe an audio file using ElevenLabs Speech-to-Text
    
    Args:
        audio_file_path: Path to the audio file (mp3, wav, etc.)
    """
    try:
        with open(audio_file_path, "rb") as audio_file:
            # Send audio for transcription
            transcript = client.speech_to_text.convert(
                audio=audio_file,
                model_id="eleven_multilingual_v2"  # or "eleven_english_v1"
            )
            
            print("Transcription successful!")
            print(f"Text: {transcript.text}")
            return transcript.text
            
    except Exception as e:
        print(f"Error during transcription: {e}")
        return None

if __name__ == "__main__":
    # Test with your audio file
    audio_path = "test.m4a"  # Replace with your audio file path
    
    result = transcribe_audio(audio_path)
    
    if result:
        print("\n✓ Test completed successfully")
    else:
        print("\n✗ Test failed")
        