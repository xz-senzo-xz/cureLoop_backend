"""
Test script for Clinical Notes Extraction API
Tests the standalone API endpoint with sample medical text
"""

import requests
import json

# API endpoint
BASE_URL = "http://localhost:5001"
EXTRACT_ENDPOINT = f"{BASE_URL}/api/clinical/extract-clinical-notes"

# Sample medical transcription
sample_consultation = """
Patient is a 45-year-old male presenting with chest pain that started 2 hours ago.
Pain is described as pressure-like, radiating to left arm.
Patient has a history of hypertension and high cholesterol.
Currently taking lisinopril 10mg daily and atorvastatin 20mg at night.
No known drug allergies.

On examination, patient appears anxious and diaphoretic.
Blood pressure is 160/95, heart rate 110, respiratory rate 22, oxygen saturation 96% on room air.
Cardiac exam reveals regular rhythm, no murmurs.
Lungs clear to auscultation bilaterally.

EKG shows ST elevation in leads II, III, and aVF.

Assessment: Acute inferior wall myocardial infarction.

Plan: Immediate transfer to cardiac catheterization lab.
Aspirin 325mg chewed immediately.
Start heparin infusion.
Morphine for pain control.
Cardiology consultation.
Patient and family counseled on diagnosis and treatment plan.

Patient's wife is in the waiting room and has been updated on the situation.
"""

def test_health_check():
    """Test the health endpoint"""
    print("Testing health endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/api/clinical/health")
        print(f"✓ Health check: {response.json()}\n")
    except Exception as e:
        print(f"✗ Health check failed: {e}\n")

def test_extraction():
    """Test the clinical notes extraction"""
    print("Testing clinical notes extraction...")
    print("=" * 80)
    
    try:
        # Make API call
        response = requests.post(
            EXTRACT_ENDPOINT,
            headers={"Content-Type": "application/json"},
            json={"text": sample_consultation}
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get("success"):
                print("\n✓ Extraction successful!\n")
                print("Structured Clinical Notes:")
                print("=" * 80)
                
                clinical_notes = data.get("clinical_notes", {})
                
                for field, value in clinical_notes.items():
                    print(f"\n{field.replace('_', ' ').upper()}:")
                    print("-" * 80)
                    print(value if value else "(empty)")
                
                print("\n" + "=" * 80)
                print("\nRaw JSON Response:")
                print(json.dumps(data, indent=2))
            else:
                print(f"\n✗ Extraction failed: {data.get('error')}")
        else:
            print(f"\n✗ API error (status {response.status_code}): {response.text}")
            
    except Exception as e:
        print(f"\n✗ Request failed: {e}")

def test_error_handling():
    """Test error handling with invalid input"""
    print("\n" + "=" * 80)
    print("Testing error handling...")
    print("=" * 80)
    
    # Test 1: Missing text field
    print("\nTest 1: Missing 'text' field")
    try:
        response = requests.post(
            EXTRACT_ENDPOINT,
            headers={"Content-Type": "application/json"},
            json={}
        )
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 2: Empty text
    print("\nTest 2: Empty text")
    try:
        response = requests.post(
            EXTRACT_ENDPOINT,
            headers={"Content-Type": "application/json"},
            json={"text": ""}
        )
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    print("=" * 80)
    print("CLINICAL NOTES EXTRACTION API TEST")
    print("=" * 80)
    print("\nMake sure the Flask server is running on http://localhost:5001")
    print("Run: python app.py\n")
    
    input("Press Enter to start tests...")
    print()
    
    # Run tests
    test_health_check()
    test_extraction()
    test_error_handling()
    
    print("\n" + "=" * 80)
    print("Tests completed!")
    print("=" * 80)
