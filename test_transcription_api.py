"""
Test script for Speech-to-Text API
Run this after starting the Flask server (python app.py)
"""

import requests

# API endpoint
API_URL = "http://localhost:5001/api/speech/transcribe"
HEALTH_URL = "http://localhost:5001/api/speech/health"

def test_health_check():
    """Test the health check endpoint"""
    print("Testing health check endpoint...")
    response = requests.get(HEALTH_URL)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}\n")

def test_transcription(audio_file_path):
    """Test audio transcription"""
    print(f"Testing transcription with: {audio_file_path}")
    
    try:
        # Open and send audio file
        with open(audio_file_path, 'rb') as audio_file:
            files = {'audio': audio_file}
            response = requests.post(API_URL, files=files)
        
        print(f"Status: {response.status_code}")
        result = response.json()
        
        if result.get('success'):
            print(f"✅ Success!")
            print(f"Transcript: {result.get('transcript')}")
            print(f"Timestamp: {result.get('timestamp')}")
        else:
            print(f"❌ Error: {result.get('error')}")
            
    except FileNotFoundError:
        print(f"❌ File not found: {audio_file_path}")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    print("="*60)
    print("Speech-to-Text API Test")
    print("="*60 + "\n")
    
    # Test health check
    test_health_check()
    
    # Test transcription (update with your audio file path)
    audio_file = input("Enter audio file path to test (or press Enter to skip): ").strip()
    if audio_file:
        test_transcription(audio_file)
    else:
        print("Skipping transcription test")
