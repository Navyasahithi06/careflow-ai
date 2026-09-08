import json
import re
import httpx
from app.config import get_settings

settings = get_settings()

SUPPORTED_SPECIALIZATIONS = [
    "General Physician",
    "Cardiology",
    "Dermatology",
    "Pediatrics",
    "Orthopedics",
    "ENT",
    "Ophthalmology",
    "Neurology",
    "Gastroenterology",
    "Pulmonology",
    "Gynecology",
    "Psychiatry",
    "Urology",
    "Dentistry",
]

SYSTEM_PROMPT = """You are a medical symptom analysis assistant for CareFlow AI hospital platform.

CRITICAL RULES:
1. You are NOT a doctor. You do NOT provide medical diagnosis.
2. You analyze symptoms and recommend a specialist department.
3. You must return ONLY a valid JSON object, no other text.
4. Never prescribe medication or suggest treatments.
5. Never claim certainty about any condition.
6. Always include appropriate urgency level.
7. Always identify warning signs that require urgent care.

OUTPUT FORMAT: Return ONLY a JSON object with these fields:
{{
  "detected_symptoms": ["symptom1", "symptom2"],
  "recommended_specialization": "Specialization Name",
  "recommendation_reason": "Brief explanation of why this specialist is appropriate",
  "urgency": "ROUTINE or PRIORITY or URGENT",
  "warning_signs": ["warning1"] or []
}}

URGENCY LEVELS:
- ROUTINE: Standard symptoms, can wait for regular appointment
- PRIORITY: Symptoms that should be seen within 1-2 days
- URGENT: Symptoms requiring immediate medical attention

WARNING SIGNS that should trigger URGENT:
- Difficulty breathing or shortness of breath
- Severe chest pain
- Uncontrolled bleeding
- Loss of consciousness
- Severe allergic reaction
- High fever with stiff neck
- Sudden severe headache
- Signs of stroke (face drooping, arm weakness, speech difficulty)

AVAILABLE SPECIALIZATIONS (use ONLY these exact names):
{specializations}

IMPORTANT:
- Return ONLY the JSON object. No explanation text before or after.
- Do not wrap in markdown code blocks.
- Do not add commentary outside the JSON.
- If symptoms are unclear, recommend General Physician.
- If symptoms suggest emergency, set urgency to URGENT and list warning signs.
"""


def build_analysis_prompt(symptoms: str) -> str:
    spec_list = "\n".join(f"- {s}" for s in SUPPORTED_SPECIALIZATIONS)
    system = SYSTEM_PROMPT.format(specializations=spec_list)
    return f"{system}\n\nPatient symptoms: {symptoms}\n\nJSON response:"


def parse_ai_response(raw_response: str) -> dict:
    """Parse and validate AI response, extracting JSON."""
    text = raw_response.strip()

    json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    return {
        "detected_symptoms": ["Unable to parse symptoms"],
        "recommended_specialization": "General Physician",
        "recommendation_reason": "Could not process AI analysis. Please consult a general physician.",
        "urgency": "ROUTINE",
        "warning_signs": [],
    }


def validate_ai_result(data: dict) -> dict:
    """Validate and normalize AI result."""
    result = {
        "detected_symptoms": [],
        "recommended_specialization": "General Physician",
        "recommendation_reason": "Please consult a specialist.",
        "urgency": "ROUTINE",
        "warning_signs": [],
    }

    if isinstance(data.get("detected_symptoms"), list):
        result["detected_symptoms"] = [str(s) for s in data["detected_symptoms"][:10]]

    if isinstance(data.get("recommended_specialization"), str):
        spec = data["recommended_specialization"]
        if spec in SUPPORTED_SPECIALIZATIONS:
            result["recommended_specialization"] = spec

    if isinstance(data.get("recommendation_reason"), str):
        result["recommendation_reason"] = data["recommendation_reason"][:500]

    if isinstance(data.get("urgency"), str) and data["urgency"] in ["ROUTINE", "PRIORITY", "URGENT"]:
        result["urgency"] = data["urgency"]

    if isinstance(data.get("warning_signs"), list):
        result["warning_signs"] = [str(w) for w in data["warning_signs"][:5]]

    return result


class AIService:
    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL
        self.model = settings.OLLAMA_MODEL

    async def chat(self, prompt: str) -> str:
        """Send a prompt to Ollama and return the response."""
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.3,
                            "num_predict": 512,
                        },
                    }
                )
                if response.status_code == 200:
                    return response.json().get("response", "No response from AI")
                return f"AI service error: {response.status_code}"
        except httpx.TimeoutException:
            return "AI service timeout: Please try again"
        except Exception as e:
            return f"AI service unavailable: {str(e)}"

    async def analyze_symptoms(self, symptoms: str) -> dict:
        """Analyze symptoms and return structured result."""
        prompt = build_analysis_prompt(symptoms)
        raw_response = await self.chat(prompt)

        if raw_response.startswith("AI service error:") or raw_response.startswith("AI service unavailable:") or raw_response.startswith("AI service timeout:"):
            return None, raw_response

        parsed = parse_ai_response(raw_response)
        validated = validate_ai_result(parsed)
        return validated, None

    async def health_check(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                return response.status_code == 200
        except Exception:
            return False


ai_service = AIService()
