# backend/app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
from routes.speech_to_text import speech_to_text_bp
import json

app = Flask(__name__)

# Configure CORS to allow all origins (for development)
CORS(app, resources={
    r"/*": {
        "origins": "*",
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": "*"
    }
})

# Register blueprints
app.register_blueprint(speech_to_text_bp, url_prefix='/api/speech')

# Load mock data
with open('data/patients.json') as f:
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
    app.run(debug=True, port=5001)
