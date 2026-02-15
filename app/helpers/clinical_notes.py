"""
Clinical Notes Extractor with Medical History Integration
Extracts structured clinical information from transcribed medical consultations
and combines with patient medical history for comprehensive documentation.

API Returns:
{
    "chief_complaint": "Main reason for patient visit",
    "history": "Structured, scannable summary formatted with clear sections:
                - CHRONIC CONDITIONS
                - CURRENT MEDICATIONS  
                - ALLERGIES & WARNINGS
                - RECENT MEDICAL HISTORY
                - RISK FLAGS
                Designed for quick doctor review with bullet points for easy scanning",
    "examination": "Physical examination findings from current consultation",
    "diagnosis": "Doctor's diagnosis or clinical assessment",
    "plan": "Treatment plan, recommendations, and follow-up instructions",
    "additional_observations": "Any other clinically relevant notes or observations"
}

Two-Step LLM Process:
1. Extract basic clinical information from transcription
2. Load patient medical records and use second LLM to create comprehensive history summary
"""

import os
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()


def load_medical_history(patient_id: int = None) -> dict:
    """
    Load patient medical history from JSON file.

    Args:
        patient_id: Optional patient ID to load specific history

    Returns:
        dict containing patient's medical history
    """
    history_path = os.path.join(os.path.dirname(
        __file__), '..', 'data', 'medical_history.json')

    try:
        with open(history_path, 'r') as f:
            data = json.load(f)
            return data.get('consultation', {})
    except FileNotFoundError:
        return {}
    except Exception as e:
        print(f"Warning: Could not load medical history: {str(e)}")
        return {}


def extract_clinical_notes(transcribed_text: str, patient_id: int = None) -> dict:
    """
    Extract structured clinical notes from transcribed consultation.
    Uses two-step LLM process:
    1. Extract basic information from transcription
    2. Combine with medical history and summarize for clinical relevance

    Args:
        transcribed_text: Raw transcribed text from doctor's consultation
        patient_id: Optional patient ID to load specific medical history

    Returns:
        dict with clinical notes structure containing:
        - chief_complaint: Main reason for visit
        - history: Summarized patient history with chronic conditions, medications, and relevant anomalies
        - examination: Physical examination findings
        - diagnosis: Doctor's diagnosis or assessment
        - plan: Treatment plan and recommendations
        - additional_observations: Any other relevant notes
    """
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY not found in environment variables")

    client = Groq(api_key=api_key)

    # Step 1: Extract basic clinical information from transcription
    extraction_prompt = """You are a medical transcription assistant. Extract clinical information from the transcribed text and return it as structured JSON.

Extract these 6 fields:
- chief_complaint: Main reason for visit
- history: Patient's history and present illness details from this consultation
- examination: Physical examination findings
- diagnosis: Doctor's diagnosis or assessment
- plan: Treatment plan and recommendations
- additional_observations: Any other relevant notes or observations

Return ONLY valid JSON with these exact field names. If a field is not mentioned in the text, use an empty string.
Do not include markdown formatting or explanations."""

    try:
        # First LLM call - extract from transcription
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": extraction_prompt},
                {"role": "user", "content": transcribed_text},
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.2,
            max_tokens=1024,
            response_format={"type": "json_object"}
        )

        raw_json = response.choices[0].message.content
        extracted_data = json.loads(raw_json)

        # Load patient medical history
        medical_history = load_medical_history(patient_id)

        # Step 2: Combine history with medical records and summarize
        if medical_history:
            history_summary = _summarize_medical_history(
                client,
                extracted_data.get("history", ""),
                medical_history
            )
        else:
            history_summary = extracted_data.get("history", "")

        # Build final result
        result = {
            "chief_complaint": extracted_data.get("chief_complaint", ""),
            "history": history_summary,
            "examination": extracted_data.get("examination", ""),
            "diagnosis": extracted_data.get("diagnosis", ""),
            "plan": extracted_data.get("plan", ""),
            "additional_observations": extracted_data.get("additional_observations", "")
        }

        return result

    except Exception as e:
        raise Exception(f"Failed to extract clinical notes: {str(e)}")


def _summarize_medical_history(client: Groq, consultation_history: str, medical_records: dict) -> str:
    """
    Second LLM call: Summarize combined consultation history and medical records.
    Creates a structured, scannable format for quick doctor review.

    Args:
        client: Groq client instance
        consultation_history: History extracted from current consultation
        medical_records: Patient's historical medical records

    Returns:
        Structured, concise clinical history summary
    """
    # Prepare medical records context
    records_text = _format_medical_records(medical_records)

    summary_prompt = """You are a clinical documentation specialist. Create a STRUCTURED, SCANNABLE patient history summary that a doctor can review in seconds.

Format the output with clear sections and bullet points:

CHRONIC CONDITIONS:
• List any chronic diseases or ongoing conditions
• Include relevant past diagnoses

CURRENT MEDICATIONS:
• List long-term medications with dosage
• Highlight any warnings or interactions

ALLERGIES & WARNINGS:
• List known allergies
• Note any medication warnings or contraindications

RECENT MEDICAL HISTORY:
• Brief summary of current complaint history
• Relevant recent treatments or issues

RISK FLAGS:
• Any anomalies that could interfere with treatment
• Drug interactions or complications to watch for

Rules:
- Keep each bullet point to ONE line maximum
- Only include clinically relevant information
- Use medical terminology but keep it clear
- If a section has no information, write "None documented"
- Be extremely concise - doctors need to scan this quickly"""

    combined_input = f"""CURRENT CONSULTATION HISTORY:
{consultation_history}

PATIENT MEDICAL RECORDS:
{records_text}

Create a structured, scannable history summary."""

    try:
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": summary_prompt},
                {"role": "user", "content": combined_input},
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.2,
            max_tokens=512
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        print(f"Warning: Could not summarize medical history: {str(e)}")
        return consultation_history


def _format_medical_records(records: dict) -> str:
    """
    Format medical records into readable text for LLM processing.

    Args:
        records: Medical history dictionary

    Returns:
        Formatted text representation of medical records
    """
    if not records:
        return "No previous medical records available."

    parts = []

    # Chief complaint and diagnosis
    if records.get('chief_complaint'):
        parts.append(f"Previous Complaint: {records['chief_complaint']}")
    if records.get('diagnosis'):
        parts.append(f"Diagnosis: {records['diagnosis']}")
    if records.get('notes'):
        parts.append(f"Clinical Notes: {records['notes']}")

    # Treatment plan and medications
    treatment_plan = records.get('treatment_plan', {})
    if treatment_plan:
        medications = treatment_plan.get('medications', [])
        if medications:
            parts.append("\nCurrent Medications:")
            for med in medications:
                med_info = f"- {med.get('name', 'Unknown')} {med.get('dosage', '')} " \
                    f"{med.get('frequency', '')} for {med.get('duration_days', '?')} days"
                if med.get('warning'):
                    med_info += f"\n  Warning: {med['warning']}"
                parts.append(med_info)

        # Risk flags
        risk_flags = treatment_plan.get('risk_flags', [])
        if risk_flags:
            parts.append("\nRisk Flags:")
            for flag in risk_flags:
                parts.append(f"- {flag}")

        # Instructions
        if treatment_plan.get('instructions'):
            parts.append(
                f"\nTreatment Instructions: {treatment_plan['instructions']}")

    return "\n".join(parts) if parts else "No detailed medical records available."
