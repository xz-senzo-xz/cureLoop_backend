"""
Clinical Note Structurer

Receives raw speech-to-text transcription from a doctor's dictation,
corrects speech errors, and extracts structured clinical data as JSON.
The JSON output maps directly to the frontend consultation form.

Fields like 'observation' and 'medical_plan' are still extracted from speech
but are also editable by the doctor in the frontend form in real time.
"""

import os
import json
from typing import Optional
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Clinical note JSON schema — mirrors the frontend consultation form
# ---------------------------------------------------------------------------
CLINICAL_NOTE_SCHEMA = {
    "patient_info": {
        "full_name": "",
        "age": None,
        "gender": "",
        "date_of_birth": "",
        "phone_number": "",
        "address": "",
    },
    "consultation": {
        "date": "",
        "chief_complaint": "",
        "history_of_present_illness": "",
        "past_medical_history": [],
        "family_history": "",
        "allergies": [],
        "current_medications": [],
    },
    "vitals": {
        "blood_pressure": "",
        "heart_rate": "",
        "temperature": "",
        "respiratory_rate": "",
        "oxygen_saturation": "",
        "weight": "",
        "height": "",
    },
    "physical_examination": "",
    "diagnosis": [],
    "observation": "",          # doctor may override in frontend
    "medical_plan": "",         # doctor may override in frontend
    "prescriptions": [],
    "follow_up": "",
    "additional_notes": "",
}

# ---------------------------------------------------------------------------
# System prompt sent to the LLM
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = f"""You are a medical transcription assistant.
You will receive raw text that was produced by a speech-to-text system during
a doctor's consultation. The text may contain:
  • speech recognition errors (homophones, missing words, wrong punctuation)
  • medical jargon spoken quickly or abbreviated
  • mixed languages or informal phrasing

Your tasks — in order — are:
1. **Correct** the transcription: fix spelling, grammar, and medical
   terminology while preserving the original meaning.
2. **Extract** every piece of clinical information and map it into the
   JSON structure below.  If a field is not mentioned, leave it as its
   default (empty string, empty list, or null).
3. **Return ONLY valid JSON** — no markdown fences, no commentary.

JSON template:
```
{json.dumps(CLINICAL_NOTE_SCHEMA, indent=2)}
```

Rules:
- `past_medical_history`, `allergies`, `current_medications`, `diagnosis`,
  and `prescriptions` must be arrays of strings.
- `age` must be an integer or null.
- Dates should be in YYYY-MM-DD format when possible.
- Vital-sign values should include units (e.g. "120/80 mmHg").
- If the doctor mentions observation notes or a medical/treatment plan,
  populate `observation` and `medical_plan` accordingly — the frontend will
  let the doctor edit them further.
- Always return the full JSON object, even if most fields are empty.
"""


# ---------------------------------------------------------------------------
# Core class
# ---------------------------------------------------------------------------
class ClinicalNoteStructurer:
    """Transforms raw speech text into a structured clinical note JSON."""

    def __init__(self, api_key: Optional[str] = None, model: str = "llama-3.3-70b-versatile"):
        self.api_key = api_key or os.environ.get("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError(
                "GROQ_API_KEY is not set. "
                "Pass it explicitly or add it to your .env file."
            )
        self.client = Groq(api_key=self.api_key)
        self.model = model

    # ---- public -----------------------------------------------------------

    def structure_note(self, raw_text: str) -> dict:
        """
        Send the raw transcription to the LLM and return a structured dict.

        Args:
            raw_text: Unprocessed speech-to-text output.

        Returns:
            A dict matching CLINICAL_NOTE_SCHEMA.
        """
        response = self.client.chat.completions.create(
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": raw_text},
            ],
            model=self.model,
            temperature=0.2,       # low temp for factual extraction
            max_tokens=2048,
            response_format={"type": "json_object"},
        )

        raw_json = response.choices[0].message.content
        return self._parse_and_validate(raw_json)

    # ---- private ----------------------------------------------------------

    @staticmethod
    def _parse_and_validate(raw_json: str) -> dict:
        """
        Parse the LLM response and ensure every expected key exists.
        Missing keys are filled with defaults from CLINICAL_NOTE_SCHEMA.
        """
        try:
            data = json.loads(raw_json)
        except json.JSONDecodeError:
            # If the LLM wraps JSON in markdown fences, strip them
            cleaned = raw_json.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("\n", 1)[1]
            if cleaned.endswith("```"):
                cleaned = cleaned.rsplit("```", 1)[0]
            data = json.loads(cleaned.strip())

        # Deep-merge with the schema so every key is guaranteed to exist
        return _deep_merge(CLINICAL_NOTE_SCHEMA, data)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _deep_merge(defaults: dict, overrides: dict) -> dict:
    """
    Recursively merge *overrides* into a copy of *defaults*.
    Keys present in defaults but missing in overrides keep their default value.
    """
    merged = {}
    for key, default_value in defaults.items():
        if key not in overrides:
            merged[key] = default_value
        elif isinstance(default_value, dict) and isinstance(overrides[key], dict):
            merged[key] = _deep_merge(default_value, overrides[key])
        else:
            merged[key] = overrides[key]
    # Keep any extra keys the LLM may have added
    for key in overrides:
        if key not in defaults:
            merged[key] = overrides[key]
    return merged


def pretty_print(note: dict) -> None:
    """Print a clinical note dict in a readable way."""
    print(json.dumps(note, indent=2, ensure_ascii=False))


# ---------------------------------------------------------------------------
# CLI entry-point — handy for quick testing
# ---------------------------------------------------------------------------

def main():
    print("=" * 60)
    print("  Clinical Note Structurer")
    print("=" * 60)
    print("Paste the raw speech-to-text transcription below.")
    print("Press Enter twice (empty line) to submit.\n")

    lines: list[str] = []
    while True:
        line = input()
        if line == "":
            if lines:
                break
            continue
        lines.append(line)

    raw_text = "\n".join(lines)

    print("\n⏳ Processing transcription…\n")

    try:
        structurer = ClinicalNoteStructurer()
        note = structurer.structure_note(raw_text)
        print("✅ Structured Clinical Note:\n")
        pretty_print(note)
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()
