from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class SymptomAnalysisRequest(BaseModel):
    symptoms: str = Field(..., min_length=3, max_length=2000, description="Natural language symptom description")


class AIAnalysisResult(BaseModel):
    detected_symptoms: List[str]
    recommended_specialization: str
    recommendation_reason: str
    urgency: str = "ROUTINE"
    warning_signs: List[str] = []


class SymptomAnalysisResponse(BaseModel):
    analysis_id: int
    detected_symptoms: List[str]
    recommended_specialization: str
    recommendation_reason: str
    urgency: str
    warning_signs: List[str]
    matching_doctors: list
    disclaimer: str


class SymptomAnalysisHistory(BaseModel):
    id: int
    input_text: str
    detected_symptoms: List[str]
    recommended_specialization: str
    recommendation_reason: str
    urgency: str
    ai_model: Optional[str] = None
    created_at: str

    class Config:
        from_attributes = True
