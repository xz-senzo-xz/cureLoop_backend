# Speech-to-Text API Documentation

## Overview
Simple REST API for audio transcription using ElevenLabs.

## Endpoint

### POST `/api/speech/transcribe`
Transcribe an audio file to text.

**Request:**
- Method: `POST`
- Content-Type: `multipart/form-data`
- Body: Audio file with key `audio`

**Supported Audio Formats:**
- MP3
- WAV
- WEBM
- M4A
- OGG
- FLAC

**File Size Limit:** 25MB

**Response:**
```json
{
  "success": true,
  "transcript": "The transcribed text from the audio",
  "timestamp": "2026-02-14T10:30:00.123456"
}
```

**Error Response:**
```json
{
  "success": false,
  "error": "Error message describing what went wrong"
}
```

### GET `/api/speech/health`
Check if the service is running.

**Response:**
```json
{
  "status": "healthy",
  "service": "speech-to-text",
  "available": true
}
```

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up `.env` file:
```
ELEVENLABS_API_KEY=your_api_key_here
```

3. Run the server:
```bash
python app.py
```

Server will run on `http://localhost:5001`

## Testing

Run the test script:
```bash
python test_transcription_api.py
```
