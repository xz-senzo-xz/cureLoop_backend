"""
Simple test script for Speech-to-Text API
Tests the health endpoint and basic functionality
"""

import requests

# API base URL
BASE_URL = "http://localhost:5000/api/speech"


def test_health_check():
    """Test the health check endpoint"""
    print("\n🔍 Testing Health Check...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200:
            print("✅ Health check passed!")
            return True
        else:
            print("❌ Health check failed!")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server. Is it running?")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_transcribe_chunk(audio_file_path):
    """Test the transcribe chunk endpoint"""
    print(f"\n🔍 Testing Transcribe Chunk with: {audio_file_path}")
    
    try:
        with open(audio_file_path, 'rb') as audio_file:
            files = {'audio': audio_file}
            data = {
                'chunk_index': 0,
                'session_id': 'test-session-123'
            }
            
            response = requests.post(
                f"{BASE_URL}/transcribe-chunk",
                files=files,
                data=data
            )
            
            print(f"Status Code: {response.status_code}")
            result = response.json()
            print(f"Response: {result}")
            
            if result.get('success'):
                print(f"\n✅ Transcription successful!")
                print(f"📝 Text: {result.get('text')}")
                return True
            else:
                print(f"\n❌ Transcription failed: {result.get('error')}")
                return False
                
    except FileNotFoundError:
        print(f"❌ File not found: {audio_file_path}")
        print("💡 Please provide a valid audio file path")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def main():
    print("=" * 60)
    print("🎙️  SPEECH-TO-TEXT API TEST")
    print("=" * 60)
    
    # Test 1: Health Check
    health_ok = test_health_check()
    
    if not health_ok:
        print("\n⚠️  Server is not running. Please start it with: python app.py")
        return
    
    # Test 2: Transcribe Chunk (if audio file is provided)
    print("\n" + "-" * 60)
    audio_file = input("\n📁 Enter path to test audio file (or press Enter to skip): ").strip()
    
    if audio_file:
        test_transcribe_chunk(audio_file)
    else:
        print("\n💡 Skipping transcription test")
    
    print("\n" + "=" * 60)
    print("✅ Testing complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
