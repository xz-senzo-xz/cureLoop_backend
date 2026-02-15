"""
Consultations API - CRUD operations for medical consultations
Handles creation, retrieval, update, and deletion of consultation records
"""

from flask import Blueprint, request, jsonify
from app import db
from app.models.models import Consultation, DoctorProfile, PatientProfile
from datetime import datetime

consultations_bp = Blueprint('consultations', __name__)


@consultations_bp.route('/', methods=['POST'])
def create_consultation():
    """
    Create a new consultation
    
    Expected JSON:
    {
        "doctor_id": 1,
        "patient_id": 1,
        "chief_complaint": "Patient complains of...",
        "examination": "Physical exam findings...",
        "diagnosis": "Doctor's diagnosis...",
        "notes": "Additional notes..."
    }
    """
    if not request.is_json:
        return jsonify({"success": False, "error": "Content-Type must be application/json"}), 400
    
    data = request.get_json()
    
    # Validate required fields
    if 'doctor_id' not in data or 'patient_id' not in data:
        return jsonify({"success": False, "error": "doctor_id and patient_id are required"}), 400
    
    # Verify doctor and patient exist
    doctor = DoctorProfile.query.get(data['doctor_id'])
    patient = PatientProfile.query.get(data['patient_id'])
    
    if not doctor:
        return jsonify({"success": False, "error": "Doctor not found"}), 404
    if not patient:
        return jsonify({"success": False, "error": "Patient not found"}), 404
    
    try:
        consultation = Consultation(
            doctor_id=data['doctor_id'],
            patient_id=data['patient_id'],
            chief_complaint=data.get('chief_complaint'),
            examination=data.get('examination'),
            diagnosis=data.get('diagnosis'),
            notes=data.get('notes'),
            status=data.get('status', 'in_progress')
        )
        
        db.session.add(consultation)
        db.session.commit()
        
        return jsonify({
            "success": True,
            "consultation": {
                "id": consultation.id,
                "doctor_id": consultation.doctor_id,
                "patient_id": consultation.patient_id,
                "status": consultation.status,
                "chief_complaint": consultation.chief_complaint,
                "examination": consultation.examination,
                "diagnosis": consultation.diagnosis,
                "notes": consultation.notes,
                "started_at": consultation.started_at.isoformat() if consultation.started_at else None,
                "created_at": consultation.created_at.isoformat() if consultation.created_at else None
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": f"Failed to create consultation: {str(e)}"}), 500


@consultations_bp.route('/', methods=['GET'])
def get_consultations():
    """
    Get all consultations with optional filters
    
    Query params:
    - doctor_id: Filter by doctor
    - patient_id: Filter by patient
    - status: Filter by status (in_progress, completed)
    - limit: Limit number of results (default: 50)
    - offset: Pagination offset (default: 0)
    """
    query = Consultation.query
    
    # Apply filters
    doctor_id = request.args.get('doctor_id', type=int)
    patient_id = request.args.get('patient_id', type=int)
    status = request.args.get('status')
    limit = request.args.get('limit', 50, type=int)
    offset = request.args.get('offset', 0, type=int)
    
    if doctor_id:
        query = query.filter_by(doctor_id=doctor_id)
    if patient_id:
        query = query.filter_by(patient_id=patient_id)
    if status:
        query = query.filter_by(status=status)
    
    # Get total count before pagination
    total = query.count()
    
    # Apply pagination
    consultations = query.order_by(Consultation.created_at.desc()).limit(limit).offset(offset).all()
    
    return jsonify({
        "success": True,
        "total": total,
        "count": len(consultations),
        "consultations": [{
            "id": c.id,
            "doctor_id": c.doctor_id,
            "patient_id": c.patient_id,
            "status": c.status,
            "chief_complaint": c.chief_complaint,
            "examination": c.examination,
            "diagnosis": c.diagnosis,
            "notes": c.notes,
            "started_at": c.started_at.isoformat() if c.started_at else None,
            "ended_at": c.ended_at.isoformat() if c.ended_at else None,
            "created_at": c.created_at.isoformat() if c.created_at else None
        } for c in consultations]
    }), 200


@consultations_bp.route('/<int:consultation_id>', methods=['GET'])
def get_consultation(consultation_id):
    """Get a single consultation by ID"""
    consultation = Consultation.query.get(consultation_id)
    
    if not consultation:
        return jsonify({"success": False, "error": "Consultation not found"}), 404
    
    return jsonify({
        "success": True,
        "consultation": {
            "id": consultation.id,
            "doctor_id": consultation.doctor_id,
            "patient_id": consultation.patient_id,
            "status": consultation.status,
            "chief_complaint": consultation.chief_complaint,
            "examination": consultation.examination,
            "diagnosis": consultation.diagnosis,
            "notes": consultation.notes,
            "started_at": consultation.started_at.isoformat() if consultation.started_at else None,
            "ended_at": consultation.ended_at.isoformat() if consultation.ended_at else None,
            "created_at": consultation.created_at.isoformat() if consultation.created_at else None
        }
    }), 200


@consultations_bp.route('/<int:consultation_id>', methods=['PUT'])
def update_consultation(consultation_id):
    """
    Update an existing consultation
    
    Can update: chief_complaint, examination, diagnosis, notes, status
    """
    consultation = Consultation.query.get(consultation_id)
    
    if not consultation:
        return jsonify({"success": False, "error": "Consultation not found"}), 404
    
    if not request.is_json:
        return jsonify({"success": False, "error": "Content-Type must be application/json"}), 400
    
    data = request.get_json()
    
    try:
        # Update fields if provided
        if 'chief_complaint' in data:
            consultation.chief_complaint = data['chief_complaint']
        if 'examination' in data:
            consultation.examination = data['examination']
        if 'diagnosis' in data:
            consultation.diagnosis = data['diagnosis']
        if 'notes' in data:
            consultation.notes = data['notes']
        if 'status' in data:
            consultation.status = data['status']
            # If status is being set to completed, set ended_at
            if data['status'] == 'completed' and not consultation.ended_at:
                consultation.ended_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            "success": True,
            "consultation": {
                "id": consultation.id,
                "doctor_id": consultation.doctor_id,
                "patient_id": consultation.patient_id,
                "status": consultation.status,
                "chief_complaint": consultation.chief_complaint,
                "examination": consultation.examination,
                "diagnosis": consultation.diagnosis,
                "notes": consultation.notes,
                "started_at": consultation.started_at.isoformat() if consultation.started_at else None,
                "ended_at": consultation.ended_at.isoformat() if consultation.ended_at else None,
                "created_at": consultation.created_at.isoformat() if consultation.created_at else None
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": f"Failed to update consultation: {str(e)}"}), 500


@consultations_bp.route('/<int:consultation_id>', methods=['DELETE'])
def delete_consultation(consultation_id):
    """Delete a consultation"""
    consultation = Consultation.query.get(consultation_id)
    
    if not consultation:
        return jsonify({"success": False, "error": "Consultation not found"}), 404
    
    try:
        db.session.delete(consultation)
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": f"Consultation {consultation_id} deleted successfully"
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": f"Failed to delete consultation: {str(e)}"}), 500


@consultations_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "consultations-api"
    }), 200
