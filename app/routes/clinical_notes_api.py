"""
Clinical Notes Extraction API
Extracts structured clinical information from raw medical transcription text
and integrates with patient medical history for comprehensive documentation.

Process:
1. First LLM call extracts basic clinical data from transcription
2. Patient medical history is loaded from records
3. Second LLM call combines and summarizes history, focusing on:
   - Chronic conditions
   - Long-term medications
   - Relevant anomalies that may affect treatment
"""

from flask import Blueprint, request, jsonify
from ..helpers.clinical_notes import extract_clinical_notes

# Create Blueprint
clinical_notes_bp = Blueprint('clinical_notes', __name__)


@clinical_notes_bp.route('/extract-clinical-notes', methods=['POST'])
def extract_notes():
    """
    Extract structured clinical notes from transcribed text with medical history integration

    Expects:
        JSON body with:
        - 'text': transcribed medical consultation (required)
        - 'patient_id': patient ID to load medical history (optional)

    Returns:
        JSON with structured clinical notes:
        {
            "success": true,
            "clinical_notes": {
                "chief_complaint": "Main reason for visit",
                "history": "Structured, scannable format with sections: CHRONIC CONDITIONS, CURRENT MEDICATIONS, ALLERGIES & WARNINGS, RECENT MEDICAL HISTORY, RISK FLAGS - designed for quick doctor review",
                "examination": "Physical examination findings",
                "diagnosis": "Doctor's diagnosis or assessment",
                "plan": "Treatment plan and recommendations",
                "additional_observations": "Other relevant notes"
            }
        }
    """
    # Validate request
    if not request.is_json:
        return jsonify({
            "success": False,
            "error": "Content-Type must be application/json"
        }), 400

    data = request.get_json()

    # Check if text is provided
    if 'text' not in data:
        return jsonify({
            "success": False,
            "error": "Missing 'text' field in request body"
        }), 400

    raw_text = data['text']
    patient_id = data.get('patient_id')

    # Validate text is not empty
    if not raw_text or not raw_text.strip():
        return jsonify({
            "success": False,
            "error": "Text field cannot be empty"
        }), 400

    try:
        # Extract clinical notes with medical history integration
        clinical_notes = extract_clinical_notes(raw_text, patient_id)

        return jsonify({
            "success": True,
            "clinical_notes": clinical_notes
        }), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Failed to extract clinical notes: {str(e)}"
        }), 500


@clinical_notes_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "clinical-notes-extraction"
    }), 200
