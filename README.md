# Cureloop Backend

A Flask-based medical consultation platform that provides AI-powered clinical note extraction, speech-to-text transcription, treatment planning, and follow-up management for healthcare providers.

## Features

- **Speech-to-Text Transcription**: Real-time medical consultation transcription with ElevenLabs integration
- **Clinical Notes Extraction**: AI-powered extraction of structured clinical data from consultation transcripts
- **Treatment Plan Management**: Create, track, and manage patient treatment plans
- **Follow-up Tracking**: Schedule and monitor patient follow-up appointments
- **Patient History Integration**: Comprehensive patient medical history management
- **RESTful API**: Clean, documented endpoints for frontend integration

## Requirements

- Python 3.8+
- SQLite (included with Python)
- API Keys:
  - ElevenLabs API key (for speech-to-text)
  - Groq API key (for AI clinical note extraction)
  - MiniMax API key (optional, for additional AI features)

## Installation

1. **Clone the repository**:
```bash
git clone <repository-url>
cd backend
```

2. **Create a virtual environment**:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. **Install dependencies**:
```bash
pip install -r requirements.txt
```

4. **Configure environment variables**:

Create a `.env` file in the project root:
```env
ELEVENLABS_API_KEY=your_elevenlabs_api_key
GROQ_API_KEY=your_groq_api_key
MINIMAX_API_KEY=your_minimax_api_key
MINIMAX_GROUP_ID=your_minimax_group_id
FLASK_ENV=development
FLASK_DEBUG=True
```

5. **Run the application**:
```bash
python app.py
```

The server will start at `http://localhost:5001`

## API Endpoints

### Core Services

- **Health Check**: `GET /api/health`
- **Speech Transcription**: `POST /api/speech/transcribe-chunk`
- **Clinical Notes**: `POST /api/clinical/extract-clinical-notes`
- **Consultations**: `GET|POST /api/consultations`
- **Treatment Plans**: `GET|POST /api/treatment-plans`
- **Follow-ups**: `GET|POST /api/followup`

### Quick Test

```bash
# Check if server is running
curl http://localhost:5001/api/health

# Test speech transcription
curl -X POST http://localhost:5001/api/speech/transcribe-chunk \
  -F "audio=@audio.mp3" \
  -F "chunk_index=0"
```

## Project Structure

```
backend/
├── app.py                          # Main application entry point
├── app/
│   ├── __init__.py                # Database initialization
│   ├── models/
│   │   └── models.py              # SQLAlchemy database models
│   ├── routes/
│   │   ├── speech_to_text.py      # Transcription API
│   │   ├── clinical_notes_api.py  # Clinical notes extraction
│   │   ├── consultations_api.py   # Consultation management
│   │   ├── treatment_plans_api.py # Treatment planning
│   │   └── followup_api.py        # Follow-up tracking
│   ├── helpers/                   # Utility functions
│   └── data/                      # Mock data files
├── cureloop.db                    # SQLite database
├── requirements.txt               # Python dependencies
└── .env                           # Environment variables
```

## Database

The application uses SQLite for data persistence. The database is automatically created on first run with the following tables:

- Patients
- Consultations
- Clinical Notes
- Treatment Plans
- Follow-ups

## Development

To run in development mode with auto-reload:

```bash
python app.py
```

CORS is enabled for all origins in development mode for easy frontend integration.

## License

Proprietary - Cureloop
