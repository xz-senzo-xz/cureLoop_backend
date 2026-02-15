"""
Follow-Up Programs API - CRUD operations for patient follow-up programs and daily check-ins
Handles patient treatment adherence tracking, medication logs, and daily wellness check-ins
"""

from flask import Blueprint, request, jsonify
from app import db
from app.models.models import (
    FollowUpProgram, MedicationLog, DailyCheckIn, 
    PatientProfile, TreatmentPlan, Medication
)
from datetime import date, datetime

followup_bp = Blueprint('followup', __name__)


@followup_bp.route('/programs', methods=['POST'])
def create_follow_up_program():
    """
    Create a new follow-up program for a patient
    
    Expected JSON:
    {
        "treatment_plan_id": 1,
        "patient_id": 1,
        "start_date": "2024-01-15",
        "end_date": "2024-02-15",
        "status": "active"
    }
    """
    if not request.is_json:
        return jsonify({"success": False, "error": "Content-Type must be application/json"}), 400
    
    data = request.get_json()
    
    # Validate required fields
    if 'treatment_plan_id' not in data or 'patient_id' not in data:
        return jsonify({"success": False, "error": "treatment_plan_id and patient_id are required"}), 400
    
    # Verify treatment plan and patient exist
    treatment_plan = TreatmentPlan.query.get(data['treatment_plan_id'])
    patient = PatientProfile.query.get(data['patient_id'])
    
    if not treatment_plan:
        return jsonify({"success": False, "error": "Treatment plan not found"}), 404
    if not patient:
        return jsonify({"success": False, "error": "Patient not found"}), 404
    
    # Check if follow-up program already exists for this treatment plan
    existing_program = FollowUpProgram.query.filter_by(treatment_plan_id=data['treatment_plan_id']).first()
    if existing_program:
        return jsonify({"success": False, "error": "Follow-up program already exists for this treatment plan"}), 400
    
    try:
        # Parse dates
        start_date = date.fromisoformat(data['start_date']) if 'start_date' in data else date.today()
        end_date = date.fromisoformat(data['end_date']) if 'end_date' in data else None
        
        # Create follow-up program
        program = FollowUpProgram(
            treatment_plan_id=data['treatment_plan_id'],
            patient_id=data['patient_id'],
            start_date=start_date,
            end_date=end_date,
            status=data.get('status', 'active')
        )
        
        db.session.add(program)
        db.session.commit()
        
        return jsonify({
            "success": True,
            "follow_up_program": {
                "id": program.id,
                "treatment_plan_id": program.treatment_plan_id,
                "patient_id": program.patient_id,
                "status": program.status,
                "start_date": program.start_date.isoformat() if program.start_date else None,
                "end_date": program.end_date.isoformat() if program.end_date else None,
                "adherence_score": program.adherence_score,
                "created_at": program.created_at.isoformat() if program.created_at else None
            }
        }), 201
        
    except ValueError as e:
        return jsonify({"success": False, "error": f"Invalid date format: {str(e)}"}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": f"Failed to create follow-up program: {str(e)}"}), 500


@followup_bp.route('/programs', methods=['GET'])
def get_follow_up_programs():
    """
    Get all follow-up programs with optional filters
    
    Query params:
    - patient_id: Filter by patient
    - status: Filter by status (active, completed, paused)
    - limit: Limit number of results (default: 50)
    - offset: Pagination offset (default: 0)
    """
    query = FollowUpProgram.query
    
    # Apply filters
    patient_id = request.args.get('patient_id', type=int)
    status = request.args.get('status')
    limit = request.args.get('limit', 50, type=int)
    offset = request.args.get('offset', 0, type=int)
    
    if patient_id:
        query = query.filter_by(patient_id=patient_id)
    if status:
        query = query.filter_by(status=status)
    
    # Get total count before pagination
    total = query.count()
    
    # Apply pagination
    programs = query.order_by(FollowUpProgram.created_at.desc()).limit(limit).offset(offset).all()
    
    return jsonify({
        "success": True,
        "total": total,
        "count": len(programs),
        "follow_up_programs": [{
            "id": prog.id,
            "treatment_plan_id": prog.treatment_plan_id,
            "patient_id": prog.patient_id,
            "status": prog.status,
            "start_date": prog.start_date.isoformat() if prog.start_date else None,
            "end_date": prog.end_date.isoformat() if prog.end_date else None,
            "adherence_score": prog.adherence_score,
            "created_at": prog.created_at.isoformat() if prog.created_at else None
        } for prog in programs]
    }), 200


@followup_bp.route('/programs/<int:program_id>', methods=['GET'])
def get_follow_up_program(program_id):
    """Get a single follow-up program by ID"""
    program = FollowUpProgram.query.get(program_id)
    
    if not program:
        return jsonify({"success": False, "error": "Follow-up program not found"}), 404
    
    return jsonify({
        "success": True,
        "follow_up_program": {
            "id": program.id,
            "treatment_plan_id": program.treatment_plan_id,
            "patient_id": program.patient_id,
            "status": program.status,
            "start_date": program.start_date.isoformat() if program.start_date else None,
            "end_date": program.end_date.isoformat() if program.end_date else None,
            "adherence_score": program.adherence_score,
            "created_at": program.created_at.isoformat() if program.created_at else None
        }
    }), 200


@followup_bp.route('/programs/<int:program_id>', methods=['PUT'])
def update_follow_up_program(program_id):
    """
    Update an existing follow-up program
    
    Can update: status, end_date, adherence_score
    """
    program = FollowUpProgram.query.get(program_id)
    
    if not program:
        return jsonify({"success": False, "error": "Follow-up program not found"}), 404
    
    if not request.is_json:
        return jsonify({"success": False, "error": "Content-Type must be application/json"}), 400
    
    data = request.get_json()
    
    try:
        # Update fields if provided
        if 'status' in data:
            program.status = data['status']
        if 'end_date' in data:
            program.end_date = date.fromisoformat(data['end_date']) if data['end_date'] else None
        if 'adherence_score' in data:
            program.adherence_score = float(data['adherence_score'])
        
        db.session.commit()
        
        return jsonify({
            "success": True,
            "follow_up_program": {
                "id": program.id,
                "treatment_plan_id": program.treatment_plan_id,
                "patient_id": program.patient_id,
                "status": program.status,
                "start_date": program.start_date.isoformat() if program.start_date else None,
                "end_date": program.end_date.isoformat() if program.end_date else None,
                "adherence_score": program.adherence_score,
                "created_at": program.created_at.isoformat() if program.created_at else None
            }
        }), 200
        
    except ValueError as e:
        return jsonify({"success": False, "error": f"Invalid data format: {str(e)}"}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": f"Failed to update follow-up program: {str(e)}"}), 500


@followup_bp.route('/programs/<int:program_id>', methods=['DELETE'])
def delete_follow_up_program(program_id):
    """Delete a follow-up program"""
    program = FollowUpProgram.query.get(program_id)
    
    if not program:
        return jsonify({"success": False, "error": "Follow-up program not found"}), 404
    
    try:
        db.session.delete(program)
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": f"Follow-up program {program_id} deleted successfully"
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": f"Failed to delete follow-up program: {str(e)}"}), 500


# ═══════════════════════════════════════════════
#  MEDICATION LOG ENDPOINTS
# ═══════════════════════════════════════════════

@followup_bp.route('/programs/<int:program_id>/medication-logs', methods=['POST'])
def create_medication_log(program_id):
    """
    Create or update a medication log entry
    
    Expected JSON:
    {
        "medication_id": 1,
        "log_date": "2024-01-15",
        "taken": true,
        "taken_at": "2024-01-15T08:30:00",
        "skipped_reason": "Forgot"
    }
    """
    program = FollowUpProgram.query.get(program_id)
    
    if not program:
        return jsonify({"success": False, "error": "Follow-up program not found"}), 404
    
    if not request.is_json:
        return jsonify({"success": False, "error": "Content-Type must be application/json"}), 400
    
    data = request.get_json()
    
    if 'medication_id' not in data:
        return jsonify({"success": False, "error": "medication_id is required"}), 400
    
    # Verify medication exists
    medication = Medication.query.get(data['medication_id'])
    if not medication:
        return jsonify({"success": False, "error": "Medication not found"}), 404
    
    try:
        log_date = date.fromisoformat(data['log_date']) if 'log_date' in data else date.today()
        
        # Check if log already exists for this medication on this date
        existing_log = MedicationLog.query.filter_by(
            follow_up_program_id=program_id,
            medication_id=data['medication_id'],
            log_date=log_date
        ).first()
        
        if existing_log:
            # Update existing log
            if 'taken' in data:
                existing_log.taken = data['taken']
            if 'taken_at' in data:
                existing_log.taken_at = datetime.fromisoformat(data['taken_at'])
            if 'skipped_reason' in data:
                existing_log.skipped_reason = data['skipped_reason']
            
            db.session.commit()
            
            return jsonify({
                "success": True,
                "medication_log": {
                    "id": existing_log.id,
                    "follow_up_program_id": existing_log.follow_up_program_id,
                    "medication_id": existing_log.medication_id,
                    "log_date": existing_log.log_date.isoformat(),
                    "taken": existing_log.taken,
                    "taken_at": existing_log.taken_at.isoformat() if existing_log.taken_at else None,
                    "skipped_reason": existing_log.skipped_reason,
                    "created_at": existing_log.created_at.isoformat() if existing_log.created_at else None
                }
            }), 200
        
        # Create new log
        med_log = MedicationLog(
            follow_up_program_id=program_id,
            medication_id=data['medication_id'],
            log_date=log_date,
            taken=data.get('taken', False),
            taken_at=datetime.fromisoformat(data['taken_at']) if 'taken_at' in data else None,
            skipped_reason=data.get('skipped_reason')
        )
        
        db.session.add(med_log)
        db.session.commit()
        
        return jsonify({
            "success": True,
            "medication_log": {
                "id": med_log.id,
                "follow_up_program_id": med_log.follow_up_program_id,
                "medication_id": med_log.medication_id,
                "log_date": med_log.log_date.isoformat(),
                "taken": med_log.taken,
                "taken_at": med_log.taken_at.isoformat() if med_log.taken_at else None,
                "skipped_reason": med_log.skipped_reason,
                "created_at": med_log.created_at.isoformat() if med_log.created_at else None
            }
        }), 201
        
    except ValueError as e:
        return jsonify({"success": False, "error": f"Invalid date format: {str(e)}"}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": f"Failed to create medication log: {str(e)}"}), 500


@followup_bp.route('/programs/<int:program_id>/medication-logs', methods=['GET'])
def get_medication_logs(program_id):
    """
    Get medication logs for a follow-up program
    
    Query params:
    - log_date: Filter by specific date (YYYY-MM-DD)
    - medication_id: Filter by medication
    - taken: Filter by taken status (true/false)
    """
    program = FollowUpProgram.query.get(program_id)
    
    if not program:
        return jsonify({"success": False, "error": "Follow-up program not found"}), 404
    
    query = MedicationLog.query.filter_by(follow_up_program_id=program_id)
    
    # Apply filters
    log_date_str = request.args.get('log_date')
    medication_id = request.args.get('medication_id', type=int)
    taken = request.args.get('taken')
    
    if log_date_str:
        try:
            log_date = date.fromisoformat(log_date_str)
            query = query.filter_by(log_date=log_date)
        except ValueError:
            return jsonify({"success": False, "error": "Invalid date format"}), 400
    
    if medication_id:
        query = query.filter_by(medication_id=medication_id)
    if taken is not None:
        query = query.filter_by(taken=taken.lower() == 'true')
    
    logs = query.order_by(MedicationLog.log_date.desc()).all()
    
    return jsonify({
        "success": True,
        "count": len(logs),
        "medication_logs": [{
            "id": log.id,
            "medication_id": log.medication_id,
            "medication_name": log.medication.name if log.medication else None,
            "log_date": log.log_date.isoformat(),
            "taken": log.taken,
            "taken_at": log.taken_at.isoformat() if log.taken_at else None,
            "skipped_reason": log.skipped_reason,
            "created_at": log.created_at.isoformat() if log.created_at else None
        } for log in logs]
    }), 200


# ═══════════════════════════════════════════════
#  DAILY CHECK-IN ENDPOINTS
# ═══════════════════════════════════════════════

@followup_bp.route('/programs/<int:program_id>/checkins', methods=['POST'])
def create_daily_checkin(program_id):
    """
    Create or update a daily check-in
    
    Expected JSON:
    {
        "checkin_date": "2024-01-15",
        "feeling_score": 4,
        "symptoms": "Mild headache",
        "side_effects": "None",
        "notes": "Feeling better today"
    }
    """
    program = FollowUpProgram.query.get(program_id)
    
    if not program:
        return jsonify({"success": False, "error": "Follow-up program not found"}), 404
    
    if not request.is_json:
        return jsonify({"success": False, "error": "Content-Type must be application/json"}), 400
    
    data = request.get_json()
    
    try:
        checkin_date = date.fromisoformat(data['checkin_date']) if 'checkin_date' in data else date.today()
        
        # Check if check-in already exists for this date
        existing_checkin = DailyCheckIn.query.filter_by(
            follow_up_program_id=program_id,
            checkin_date=checkin_date
        ).first()
        
        if existing_checkin:
            # Update existing check-in
            if 'feeling_score' in data:
                existing_checkin.feeling_score = data['feeling_score']
            if 'symptoms' in data:
                existing_checkin.symptoms = data['symptoms']
            if 'side_effects' in data:
                existing_checkin.side_effects = data['side_effects']
            if 'notes' in data:
                existing_checkin.notes = data['notes']
            
            db.session.commit()
            
            return jsonify({
                "success": True,
                "daily_checkin": {
                    "id": existing_checkin.id,
                    "follow_up_program_id": existing_checkin.follow_up_program_id,
                    "checkin_date": existing_checkin.checkin_date.isoformat(),
                    "feeling_score": existing_checkin.feeling_score,
                    "symptoms": existing_checkin.symptoms,
                    "side_effects": existing_checkin.side_effects,
                    "notes": existing_checkin.notes,
                    "created_at": existing_checkin.created_at.isoformat() if existing_checkin.created_at else None
                }
            }), 200
        
        # Create new check-in
        checkin = DailyCheckIn(
            follow_up_program_id=program_id,
            checkin_date=checkin_date,
            feeling_score=data.get('feeling_score'),
            symptoms=data.get('symptoms'),
            side_effects=data.get('side_effects'),
            notes=data.get('notes')
        )
        
        db.session.add(checkin)
        db.session.commit()
        
        return jsonify({
            "success": True,
            "daily_checkin": {
                "id": checkin.id,
                "follow_up_program_id": checkin.follow_up_program_id,
                "checkin_date": checkin.checkin_date.isoformat(),
                "feeling_score": checkin.feeling_score,
                "symptoms": checkin.symptoms,
                "side_effects": checkin.side_effects,
                "notes": checkin.notes,
                "created_at": checkin.created_at.isoformat() if checkin.created_at else None
            }
        }), 201
        
    except ValueError as e:
        return jsonify({"success": False, "error": f"Invalid date format: {str(e)}"}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": f"Failed to create daily check-in: {str(e)}"}), 500


@followup_bp.route('/programs/<int:program_id>/checkins', methods=['GET'])
def get_daily_checkins(program_id):
    """
    Get daily check-ins for a follow-up program
    
    Query params:
    - checkin_date: Filter by specific date (YYYY-MM-DD)
    - limit: Limit number of results (default: 30)
    """
    program = FollowUpProgram.query.get(program_id)
    
    if not program:
        return jsonify({"success": False, "error": "Follow-up program not found"}), 404
    
    query = DailyCheckIn.query.filter_by(follow_up_program_id=program_id)
    
    # Apply filters
    checkin_date_str = request.args.get('checkin_date')
    limit = request.args.get('limit', 30, type=int)
    
    if checkin_date_str:
        try:
            checkin_date = date.fromisoformat(checkin_date_str)
            query = query.filter_by(checkin_date=checkin_date)
        except ValueError:
            return jsonify({"success": False, "error": "Invalid date format"}), 400
    
    checkins = query.order_by(DailyCheckIn.checkin_date.desc()).limit(limit).all()
    
    return jsonify({
        "success": True,
        "count": len(checkins),
        "daily_checkins": [{
            "id": checkin.id,
            "checkin_date": checkin.checkin_date.isoformat(),
            "feeling_score": checkin.feeling_score,
            "symptoms": checkin.symptoms,
            "side_effects": checkin.side_effects,
            "notes": checkin.notes,
            "created_at": checkin.created_at.isoformat() if checkin.created_at else None
        } for checkin in checkins]
    }), 200


@followup_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "followup-api"
    }), 200
