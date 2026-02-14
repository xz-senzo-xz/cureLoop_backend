"""
Speech-to-Text API using ElevenLabs
Provides a simple endpoint for audio transcription
"""

import os
from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs

# Load environment variables
load_dotenv()

# Create Blueprint
speech_to_text_bp = Blueprint('speech_to_text', __name__)

# Configuration
UPLOAD_FOLDER = 'uploads/audio'
ALLOWED_EXTENSIONS = {'mp3', 'wav', 'webm', 'm4a', 'ogg', 'flac'}
MAX_FILE_SIZE = 25 * 1024 * 1024  # 25MB

# Ensure upload folder exists
Path(UPLOAD_FOLDER).mkdir(parents=True, exist_ok=True)


class TranscriptionService:
    """Service for handling audio transcription with ElevenLabs"""
    
    def __init__(self):
        api_key = os.getenv("ELEVENLABS_API_KEY")
        if not api_key:
            raise ValueError("ELEVENLABS_API_KEY not found in environment")
        self.client = ElevenLabs(api_key=api_key)
    
    def transcribe(self, audio_file_path: str, model: str = "scribe_v2") -> dict:
        """
        Transcribe audio file to text
        
        Args:
            audio_file_path: Path to the audio file
            model: ElevenLabs model to use
            
        Returns:
            dict with transcription result
        """
        try:
            with open(audio_file_path, "rb") as audio_file:
                transcription = self.client.speech_to_text.convert(
                    file=audio_file,
                    model_id=model
                )
            
            # Extract text from response
            text = self._extract_text(transcription)
            
            return {
                "success": True,
                "text": text,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _extract_text(self, transcription) -> str:
        """Extract text from ElevenLabs response"""
        if hasattr(transcription, 'text'):
            return transcription.text
        elif isinstance(transcription, dict):
            return transcription.get('text', str(transcription))
        return str(transcription)


# Initialize service
try:
    transcription_service = TranscriptionService()
except ValueError as e:
    print(f"Error initializing transcription service: {e}")
    transcription_service = None


def allowed_file(filename: str) -> bool:
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@speech_to_text_bp.route('/transcribe', methods=['POST'])
def transcribe_audio():
    """
    Transcribe audio file to text
    
    Expects:
        - multipart/form-data with 'audio' file
    
    Returns:
        JSON with transcription result
    """
    # Check if service is initialized
    if transcription_service is None:
        return jsonify({
            "success": False,
            "error": "Transcription service not initialized. Check ELEVENLABS_API_KEY."
        }), 500
    
    # Check if audio file is in request
    if 'audio' not in request.files:
        return jsonify({
            "success": False,
            "error": "No audio file provided"
        }), 400
    
    audio_file = request.files['audio']
    
    # Check if file is selected
    if audio_file.filename == '':
        return jsonify({
            "success": False,
            "error": "No file selected"
        }), 400
    
    # Validate file type
    if not allowed_file(audio_file.filename):
        return jsonify({
            "success": False,
            "error": f"Invalid file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        }), 400
    
    try:
        # Save uploaded file
        filename = secure_filename(audio_file.filename)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_filename = f"{timestamp}_{filename}"
        file_path = os.path.join(UPLOAD_FOLDER, unique_filename)
        
        audio_file.save(file_path)
        
        # Get file size
        file_size = os.path.getsize(file_path)
        
        # Check file size
        if file_size > MAX_FILE_SIZE:
            os.remove(file_path)
            return jsonify({
                "success": False,
                "error": f"File too large. Maximum size: {MAX_FILE_SIZE // (1024*1024)}MB"
            }), 400
        
        # Transcribe audio
        result = transcription_service.transcribe(file_path)
        
        # Clean up uploaded file
        try:
            os.remove(file_path)
        except:
            pass
        
        # Return result
        if result["success"]:
            return jsonify({
                "success": True,
                "transcript": result["text"],
                "timestamp": result["timestamp"]
            }), 200
        else:
            return jsonify({
                "success": False,
                "error": result["error"]
            }), 500
            
    except Exception as e:
        # Clean up file if exists
        if 'file_path' in locals():
            try:
                os.remove(file_path)
            except:
                pass
        
        return jsonify({
            "success": False,
            "error": f"Server error: {str(e)}"
        }), 500


@speech_to_text_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "speech-to-text",
        "available": transcription_service is not None
    }), 200
