
from datetime import datetime, date
from app import db


# ═══════════════════════════════════════════════
#  1. USER & PROFILES
# ═══════════════════════════════════════════════

class User(db.Model):
    __tablename__ = 'users'

    id         = db.Column(db.Integer, primary_key=True)
    email      = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password   = db.Column(db.String(200), nullable=False)
    name       = db.Column(db.String(100), nullable=False)
    phone      = db.Column(db.String(20))
    role       = db.Column(db.String(20), nullable=False, default='patient')  # 'doctor' | 'patient'
    is_active  = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # one-to-one
    doctor_profile  = db.relationship('DoctorProfile',  backref='user', uselist=False)
    patient_profile = db.relationship('PatientProfile', backref='user', uselist=False)
    notifications   = db.relationship('Notification',   backref='user')

    def __repr__(self):
        return f'<User {self.email} ({self.role})>'


class DoctorProfile(db.Model):
    __tablename__ = 'doctor_profiles'

    id             = db.Column(db.Integer, primary_key=True)
    user_id        = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    specialty      = db.Column(db.String(100))   # e.g. "Cardiologie"
    license_number = db.Column(db.String(50))
    hospital       = db.Column(db.String(150))
    city           = db.Column(db.String(100))

    consultations = db.relationship('Consultation', backref='doctor_profile',
                                    foreign_keys='Consultation.doctor_id')

    def __repr__(self):
        return f'<Doctor {self.specialty}>'


class PatientProfile(db.Model):
    __tablename__ = 'patient_profiles'

    id                 = db.Column(db.Integer, primary_key=True)
    user_id            = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    date_of_birth      = db.Column(db.Date)
    gender             = db.Column(db.String(10))          # M / F / Other
    blood_type         = db.Column(db.String(5))           # A+, O-, …
    allergies          = db.Column(db.Text)                 # comma-separated
    chronic_conditions = db.Column(db.Text)                 # e.g. "diabetes, hypertension"
    emergency_contact  = db.Column(db.String(100))
    emergency_phone    = db.Column(db.String(20))

    consultations = db.relationship('Consultation', backref='patient_profile',
                                    foreign_keys='Consultation.patient_id')

    def __repr__(self):
        return f'<Patient {self.user_id}>'


# ═══════════════════════════════════════════════
#  2. CONSULTATION  (doctor side — note is inline)
# ═══════════════════════════════════════════════

class Consultation(db.Model):
    """
    One visit.  The doctor writes the clinical note directly here
    (or the AI fills it via the API — either way it's just text fields).
    """
    __tablename__ = 'consultations'

    id         = db.Column(db.Integer, primary_key=True)
    doctor_id  = db.Column(db.Integer, db.ForeignKey('doctor_profiles.id'), nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient_profiles.id'), nullable=False)

    status     = db.Column(db.String(20), default='in_progress')
    #  in_progress → completed

    # ── inline clinical note ──
    chief_complaint = db.Column(db.Text)       # why the patient came
    examination     = db.Column(db.Text)       # exam findings
    diagnosis       = db.Column(db.Text)       # doctor's diagnosis
    notes           = db.Column(db.Text)       # anything else

    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    ended_at   = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # children
    treatment_plan = db.relationship('TreatmentPlan', backref='consultation', uselist=False)

    def __repr__(self):
        return f'<Consultation #{self.id}>'


# ═══════════════════════════════════════════════
#  3. TREATMENT PLAN & MEDICATIONS
# ═══════════════════════════════════════════════

class TreatmentPlan(db.Model):
    """
    Doctor creates this (manually or after AI-assisted note).
    When is_validated=True  →  a FollowUpProgram is auto-created for the patient.
    """
    __tablename__ = 'treatment_plans'

    id              = db.Column(db.Integer, primary_key=True)
    consultation_id = db.Column(db.Integer, db.ForeignKey('consultations.id'),
                                unique=True, nullable=False)
    instructions    = db.Column(db.Text)                   # general instructions
    start_date      = db.Column(db.Date, default=date.today)
    end_date        = db.Column(db.Date)
    is_validated    = db.Column(db.Boolean, default=False)  # doctor presses "submit"
    created_at      = db.Column(db.DateTime, default=datetime.utcnow)

    # children
    medications      = db.relationship('Medication', backref='treatment_plan',
                                       cascade='all, delete-orphan')
    follow_up_program = db.relationship('FollowUpProgram', backref='treatment_plan',
                                        uselist=False)

    def __repr__(self):
        return f'<TreatmentPlan #{self.id} validated={self.is_validated}>'


class Medication(db.Model):
    __tablename__ = 'medications'

    id                = db.Column(db.Integer, primary_key=True)
    treatment_plan_id = db.Column(db.Integer, db.ForeignKey('treatment_plans.id'), nullable=False)
    name              = db.Column(db.String(150), nullable=False)   # drug name
    dosage            = db.Column(db.String(50),  nullable=False)   # "500 mg"
    frequency         = db.Column(db.String(50),  nullable=False)   # "2x/day"
    timing            = db.Column(db.String(100))                   # "morning & evening"
    duration_days     = db.Column(db.Integer)                       # how many days
    instructions      = db.Column(db.Text)                          # "take after meals"
    start_date        = db.Column(db.Date)
    end_date          = db.Column(db.Date)

    def __repr__(self):
        return f'<Medication {self.name} {self.dosage}>'


# ═══════════════════════════════════════════════
#  4. FOLLOW-UP SYSTEM  (patient side — calendar)
# ═══════════════════════════════════════════════

class FollowUpProgram(db.Model):
    """Auto-created when doctor validates a TreatmentPlan."""
    __tablename__ = 'follow_up_programs'

    id                = db.Column(db.Integer, primary_key=True)
    treatment_plan_id = db.Column(db.Integer, db.ForeignKey('treatment_plans.id'),
                                  unique=True, nullable=False)
    patient_id        = db.Column(db.Integer, db.ForeignKey('patient_profiles.id'), nullable=False)
    status            = db.Column(db.String(20), default='active')  # active | completed | paused
    start_date        = db.Column(db.Date, nullable=False)
    end_date          = db.Column(db.Date)
    adherence_score   = db.Column(db.Float, default=0.0)            # 0-100 %
    created_at        = db.Column(db.DateTime, default=datetime.utcnow)

    # children
    medication_logs = db.relationship('MedicationLog', backref='follow_up_program')
    daily_checkins  = db.relationship('DailyCheckIn',  backref='follow_up_program')
    notifications   = db.relationship('Notification',  backref='follow_up_program')

    patient_profile = db.relationship('PatientProfile', backref='follow_up_programs')

    def __repr__(self):
        return f'<FollowUp #{self.id} adherence={self.adherence_score}%>'


class MedicationLog(db.Model):
    """
    One row = one medication on one day.
    The calendar view: patient clicks a day → sees their meds → marks taken/skipped.
    """
    __tablename__ = 'medication_logs'

    id                  = db.Column(db.Integer, primary_key=True)
    follow_up_program_id = db.Column(db.Integer, db.ForeignKey('follow_up_programs.id'), nullable=False)
    medication_id       = db.Column(db.Integer, db.ForeignKey('medications.id'), nullable=False)
    log_date            = db.Column(db.Date, nullable=False, default=date.today)
    taken               = db.Column(db.Boolean, default=False)
    taken_at            = db.Column(db.DateTime)
    skipped_reason      = db.Column(db.String(200))
    created_at          = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('follow_up_program_id', 'medication_id', 'log_date',
                            name='uq_med_log_per_day'),
    )

    medication = db.relationship('Medication', backref='logs')

    def __repr__(self):
        return f'<MedLog {self.log_date} taken={self.taken}>'


class DailyCheckIn(db.Model):
    """Patient clicks a calendar day → fills this quick form."""
    __tablename__ = 'daily_checkins'

    id                  = db.Column(db.Integer, primary_key=True)
    follow_up_program_id = db.Column(db.Integer, db.ForeignKey('follow_up_programs.id'), nullable=False)
    checkin_date        = db.Column(db.Date, nullable=False, default=date.today)
    feeling_score       = db.Column(db.Integer)            # 1-5
    symptoms            = db.Column(db.Text)
    side_effects        = db.Column(db.Text)
    notes               = db.Column(db.Text)
    created_at          = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('follow_up_program_id', 'checkin_date',
                            name='uq_checkin_per_day'),
    )

    def __repr__(self):
        return f'<CheckIn {self.checkin_date} feeling={self.feeling_score}>'


# ═══════════════════════════════════════════════
#  5. NOTIFICATIONS
# ═══════════════════════════════════════════════

class Notification(db.Model):
    """
    Covers everything:
      • medication reminders  (type='reminder')
      • missed-dose alerts    (type='missed_dose')
      • adherence warnings    (type='adherence_alert')  ← sent to doctor
      • check-in prompts      (type='checkin_prompt')
    """
    __tablename__ = 'notifications'

    id                  = db.Column(db.Integer, primary_key=True)
    user_id             = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    follow_up_program_id = db.Column(db.Integer, db.ForeignKey('follow_up_programs.id'))
    title               = db.Column(db.String(200), nullable=False)
    message             = db.Column(db.Text)
    notification_type   = db.Column(db.String(30), default='reminder')
    is_read             = db.Column(db.Boolean, default=False)
    sent_at             = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Notif #{self.id} {self.notification_type}>'
