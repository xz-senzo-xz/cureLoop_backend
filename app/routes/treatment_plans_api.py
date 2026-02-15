"""
Treatment Plans API - CRUD operations for treatment plans and medications
Handles creation, retrieval, update, and deletion of treatment plans with their associated medications
"""

from flask import Blueprint, request, jsonify
from app import db
from app.models.models import TreatmentPlan, Medication, Consultation
from datetime import date

treatment_plans_bp = Blueprint('treatment_plans', __name__)


@treatment_plans_bp.route('/', methods=['POST'])
def create_treatment_plan():
    """
    Create a new treatment plan with medications
    
    Expected JSON:
    {
        "consultation_id": 1,
        "instructions": "General treatment instructions...",
        "start_date": "2024-01-15",
        "end_date": "2024-02-15",
        "is_validated": false,
        "medications": [
            {
                "name": "Amoxicillin",
                "dosage": "500mg",
                "frequency": "3x/day",
                "timing": "morning, afternoon, evening",
                "duration_days": 7,
                "instructions": "Take with food"
            }
        ]
    }
    """
    if not request.is_json:
        return jsonify({"success": False, "error": "Content-Type must be application/json"}), 400
    
    data = request.get_json()
    
    # Validate required fields
    if 'consultation_id' not in data:
        return jsonify({"success": False, "error": "consultation_id is required"}), 400
    
    # Verify consultation exists
    consultation = Consultation.query.get(data['consultation_id'])
    if not consultation:
        return jsonify({"success": False, "error": "Consultation not found"}), 404
    
    # Check if treatment plan already exists for this consultation
    existing_plan = TreatmentPlan.query.filter_by(consultation_id=data['consultation_id']).first()
    if existing_plan:
        return jsonify({"success": False, "error": "Treatment plan already exists for this consultation"}), 400
    
    try:
        # Parse dates
        start_date = date.fromisoformat(data['start_date']) if 'start_date' in data else date.today()
        end_date = date.fromisoformat(data['end_date']) if 'end_date' in data else None
        
        # Create treatment plan
        treatment_plan = TreatmentPlan(
            consultation_id=data['consultation_id'],
            instructions=data.get('instructions'),
            start_date=start_date,
            end_date=end_date,
            is_validated=data.get('is_validated', False)
        )
        
        db.session.add(treatment_plan)
        db.session.flush()  # Get the treatment_plan.id
        
        # Add medications if provided
        medications_data = data.get('medications', [])
        medications = []
        
        for med_data in medications_data:
            if 'name' not in med_data or 'dosage' not in med_data or 'frequency' not in med_data:
                db.session.rollback()
                return jsonify({"success": False, "error": "Each medication must have name, dosage, and frequency"}), 400
            
            medication = Medication(
                treatment_plan_id=treatment_plan.id,
                name=med_data['name'],
                dosage=med_data['dosage'],
                frequency=med_data['frequency'],
                timing=med_data.get('timing'),
                duration_days=med_data.get('duration_days'),
                instructions=med_data.get('instructions'),
                start_date=date.fromisoformat(med_data['start_date']) if 'start_date' in med_data else None,
                end_date=date.fromisoformat(med_data['end_date']) if 'end_date' in med_data else None
            )
            db.session.add(medication)
            medications.append(medication)
        
        db.session.commit()
        
        return jsonify({
            "success": True,
            "treatment_plan": {
                "id": treatment_plan.id,
                "consultation_id": treatment_plan.consultation_id,
                "instructions": treatment_plan.instructions,
                "start_date": treatment_plan.start_date.isoformat() if treatment_plan.start_date else None,
                "end_date": treatment_plan.end_date.isoformat() if treatment_plan.end_date else None,
                "is_validated": treatment_plan.is_validated,
                "created_at": treatment_plan.created_at.isoformat() if treatment_plan.created_at else None,
                "medications": [{
                    "id": med.id,
                    "name": med.name,
                    "dosage": med.dosage,
                    "frequency": med.frequency,
                    "timing": med.timing,
                    "duration_days": med.duration_days,
                    "instructions": med.instructions,
                    "start_date": med.start_date.isoformat() if med.start_date else None,
                    "end_date": med.end_date.isoformat() if med.end_date else None
                } for med in medications]
            }
        }), 201
        
    except ValueError as e:
        return jsonify({"success": False, "error": f"Invalid date format: {str(e)}"}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": f"Failed to create treatment plan: {str(e)}"}), 500


@treatment_plans_bp.route('/', methods=['GET'])
def get_treatment_plans():
    """
    Get all treatment plans with optional filters
    
    Query params:
    - consultation_id: Filter by consultation
    - is_validated: Filter by validation status (true/false)
    - limit: Limit number of results (default: 50)
    - offset: Pagination offset (default: 0)
    """
    query = TreatmentPlan.query
    
    # Apply filters
    consultation_id = request.args.get('consultation_id', type=int)
    is_validated = request.args.get('is_validated')
    limit = request.args.get('limit', 50, type=int)
    offset = request.args.get('offset', 0, type=int)
    
    if consultation_id:
        query = query.filter_by(consultation_id=consultation_id)
    if is_validated is not None:
        query = query.filter_by(is_validated=is_validated.lower() == 'true')
    
    # Get total count before pagination
    total = query.count()
    
    # Apply pagination
    plans = query.order_by(TreatmentPlan.created_at.desc()).limit(limit).offset(offset).all()
    
    return jsonify({
        "success": True,
        "total": total,
        "count": len(plans),
        "treatment_plans": [{
            "id": plan.id,
            "consultation_id": plan.consultation_id,
            "instructions": plan.instructions,
            "start_date": plan.start_date.isoformat() if plan.start_date else None,
            "end_date": plan.end_date.isoformat() if plan.end_date else None,
            "is_validated": plan.is_validated,
            "created_at": plan.created_at.isoformat() if plan.created_at else None,
            "medications": [{
                "id": med.id,
                "name": med.name,
                "dosage": med.dosage,
                "frequency": med.frequency,
                "timing": med.timing,
                "duration_days": med.duration_days,
                "instructions": med.instructions
            } for med in plan.medications]
        } for plan in plans]
    }), 200


@treatment_plans_bp.route('/<int:plan_id>', methods=['GET'])
def get_treatment_plan(plan_id):
    """Get a single treatment plan by ID with all medications"""
    plan = TreatmentPlan.query.get(plan_id)
    
    if not plan:
        return jsonify({"success": False, "error": "Treatment plan not found"}), 404
    
    return jsonify({
        "success": True,
        "treatment_plan": {
            "id": plan.id,
            "consultation_id": plan.consultation_id,
            "instructions": plan.instructions,
            "start_date": plan.start_date.isoformat() if plan.start_date else None,
            "end_date": plan.end_date.isoformat() if plan.end_date else None,
            "is_validated": plan.is_validated,
            "created_at": plan.created_at.isoformat() if plan.created_at else None,
            "medications": [{
                "id": med.id,
                "name": med.name,
                "dosage": med.dosage,
                "frequency": med.frequency,
                "timing": med.timing,
                "duration_days": med.duration_days,
                "instructions": med.instructions,
                "start_date": med.start_date.isoformat() if med.start_date else None,
                "end_date": med.end_date.isoformat() if med.end_date else None
            } for med in plan.medications]
        }
    }), 200


@treatment_plans_bp.route('/<int:plan_id>', methods=['PUT'])
def update_treatment_plan(plan_id):
    """
    Update an existing treatment plan
    
    Can update: instructions, start_date, end_date, is_validated
    To add/remove medications, use separate medication endpoints
    """
    plan = TreatmentPlan.query.get(plan_id)
    
    if not plan:
        return jsonify({"success": False, "error": "Treatment plan not found"}), 404
    
    if not request.is_json:
        return jsonify({"success": False, "error": "Content-Type must be application/json"}), 400
    
    data = request.get_json()
    
    try:
        # Update fields if provided
        if 'instructions' in data:
            plan.instructions = data['instructions']
        if 'start_date' in data:
            plan.start_date = date.fromisoformat(data['start_date'])
        if 'end_date' in data:
            plan.end_date = date.fromisoformat(data['end_date']) if data['end_date'] else None
        if 'is_validated' in data:
            plan.is_validated = data['is_validated']
        
        db.session.commit()
        
        return jsonify({
            "success": True,
            "treatment_plan": {
                "id": plan.id,
                "consultation_id": plan.consultation_id,
                "instructions": plan.instructions,
                "start_date": plan.start_date.isoformat() if plan.start_date else None,
                "end_date": plan.end_date.isoformat() if plan.end_date else None,
                "is_validated": plan.is_validated,
                "created_at": plan.created_at.isoformat() if plan.created_at else None
            }
        }), 200
        
    except ValueError as e:
        return jsonify({"success": False, "error": f"Invalid date format: {str(e)}"}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": f"Failed to update treatment plan: {str(e)}"}), 500


@treatment_plans_bp.route('/<int:plan_id>', methods=['DELETE'])
def delete_treatment_plan(plan_id):
    """Delete a treatment plan (cascades to medications)"""
    plan = TreatmentPlan.query.get(plan_id)
    
    if not plan:
        return jsonify({"success": False, "error": "Treatment plan not found"}), 404
    
    try:
        db.session.delete(plan)
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": f"Treatment plan {plan_id} and associated medications deleted successfully"
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": f"Failed to delete treatment plan: {str(e)}"}), 500


# ═══════════════════════════════════════════════
#  MEDICATION ENDPOINTS
# ═══════════════════════════════════════════════

@treatment_plans_bp.route('/<int:plan_id>/medications', methods=['POST'])
def add_medication(plan_id):
    """
    Add a medication to an existing treatment plan
    
    Expected JSON:
    {
        "name": "Ibuprofen",
        "dosage": "200mg",
        "frequency": "2x/day",
        "timing": "morning & evening",
        "duration_days": 5,
        "instructions": "Take with food"
    }
    """
    plan = TreatmentPlan.query.get(plan_id)
    
    if not plan:
        return jsonify({"success": False, "error": "Treatment plan not found"}), 404
    
    if not request.is_json:
        return jsonify({"success": False, "error": "Content-Type must be application/json"}), 400
    
    data = request.get_json()
    
    if 'name' not in data or 'dosage' not in data or 'frequency' not in data:
        return jsonify({"success": False, "error": "name, dosage, and frequency are required"}), 400
    
    try:
        medication = Medication(
            treatment_plan_id=plan_id,
            name=data['name'],
            dosage=data['dosage'],
            frequency=data['frequency'],
            timing=data.get('timing'),
            duration_days=data.get('duration_days'),
            instructions=data.get('instructions'),
            start_date=date.fromisoformat(data['start_date']) if 'start_date' in data else None,
            end_date=date.fromisoformat(data['end_date']) if 'end_date' in data else None
        )
        
        db.session.add(medication)
        db.session.commit()
        
        return jsonify({
            "success": True,
            "medication": {
                "id": medication.id,
                "treatment_plan_id": medication.treatment_plan_id,
                "name": medication.name,
                "dosage": medication.dosage,
                "frequency": medication.frequency,
                "timing": medication.timing,
                "duration_days": medication.duration_days,
                "instructions": medication.instructions,
                "start_date": medication.start_date.isoformat() if medication.start_date else None,
                "end_date": medication.end_date.isoformat() if medication.end_date else None
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": f"Failed to add medication: {str(e)}"}), 500


@treatment_plans_bp.route('/medications/<int:medication_id>', methods=['DELETE'])
def delete_medication(medication_id):
    """Delete a specific medication"""
    medication = Medication.query.get(medication_id)
    
    if not medication:
        return jsonify({"success": False, "error": "Medication not found"}), 404
    
    try:
        db.session.delete(medication)
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": f"Medication {medication_id} deleted successfully"
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": f"Failed to delete medication: {str(e)}"}), 500


@treatment_plans_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "treatment-plans-api"
    }), 200
