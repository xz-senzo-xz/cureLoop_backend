# Cureloop Backend - Quick Start

## Setup

1. **Install dependencies**:
```bash
pip install -r requirements.txt
```

2. **Configure environment** (`.env` file):
```env
ELEVENLABS_API_KEY=your_api_key_here
FLASK_ENV=development
FLASK_DEBUG=True
```

3. **Run the server**:
```bash
python app.py
```

Server will start at: `http://localhost:5000`

## API Endpoints

### Speech-to-Text API
Base URL: `http://localhost:5000/api/speech`

- **POST** `/transcribe-chunk` - Transcribe audio chunks (for simulated real-time)
- **POST** `/transcribe-file` - Transcribe complete audio file
- **GET** `/health` - Health check

📖 **Full Documentation**: See `SPEECH_TO_TEXT_API.md` for detailed API docs and frontend integration guide

## Quick Test

```bash
# Health check
curl http://localhost:5000/api/speech/health

# Transcribe an audio file
curl -X POST http://localhost:5000/api/speech/transcribe-chunk \
  -F "audio=@your_audio.mp3" \
  -F "chunk_index=0"
```

## Project Structure

```
backend/
├── app.py                      # Main Flask application
├── routes/
│   └── speech_to_text.py      # Speech-to-text API routes
├── data/                       # Data files
├── requirements.txt            # Python dependencies
├── .env                        # Environment variables
├── README.md                   # This file
└── SPEECH_TO_TEXT_API.md      # Complete API documentation
```
