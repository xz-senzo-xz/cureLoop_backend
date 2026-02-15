# backend/app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os

# Initialize Flask app
app = Flask(__name__)

# ═══════════════════════════════════════════════
# DATABASE CONFIGURATION (SQLite)
# ═══════════════════════════════════════════════
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'cureloop.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# Initialize database
from app import db
db.init_app(app)

# Import models after db initialization
from app.models import models

# Configure CORS to allow all origins (for development)
CORS(app, resources={
    r"/*": {
        "origins": "*",
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": "*"
    }
})

# Import and register blueprints
from app.routes.speech_to_text import speech_to_text_bp
from app.routes.clinical_notes_api import clinical_notes_bp
from app.routes.consultations_api import consultations_bp
from app.routes.treatment_plans_api import treatment_plans_bp
from app.routes.followup_api import followup_bp

app.register_blueprint(speech_to_text_bp, url_prefix='/api/speech')
app.register_blueprint(clinical_notes_bp, url_prefix='/api/clinical')
app.register_blueprint(consultations_bp, url_prefix='/api/consultations')
app.register_blueprint(treatment_plans_bp, url_prefix='/api/treatment-plans')
app.register_blueprint(followup_bp, url_prefix='/api/followup')

# Load mock data
with open('./app/data/patients.json') as f:
    patients = json.load(f)

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy"})




@app.route('/api/safety-check', methods=['POST'])
def safety_check():
    data = request.json
    patient = patients[data['patient_id']]
    treatment = data['proposed_treatment']

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=500,
        messages=[{
            "role": "user",
            "content": f"""Patient history: {patient['history']}
Allergies: {patient['allergies']}
Proposed treatment: {treatment}

Check for drug conflicts. Return JSON with: safe (boolean), warnings (array)"""
        }]
    )

    return jsonify(json.loads(message.content[0].text))


if __name__ == '__main__':
    # Create database tables if they don't exist
    with app.app_context():
        db.create_all()
        print("✓ Database tables created successfully!")
    
    print("✓ Starting Cureloop Backend Server...")
    print("✓ Server running at: http://localhost:5001")
    app.run(debug=True, port=5001)
