import json
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.config import get_settings
from app.models.user import User, Role
from app.models.doctor import Doctor, DoctorStatus
from app.models.symptom_analysis import SymptomAnalysis
from app.schemas.ai import SymptomAnalysisRequest, SymptomAnalysisResponse, SymptomAnalysisHistory
from app.services.auth import require_role
from app.services.ai import ai_service, SUPPORTED_SPECIALIZATIONS
from app.services.settings import is_ai_symptom_analysis_enabled

settings = get_settings()
router = APIRouter(prefix="/api/ai", tags=["ai"])


@router.post("/symptom-analysis", response_model=SymptomAnalysisResponse)
async def analyze_symptoms(
    payload: SymptomAnalysisRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(Role.PATIENT)),
):
    if not is_ai_symptom_analysis_enabled(db):
        raise HTTPException(
            status_code=403,
            detail="AI symptom analysis is currently disabled by the administrator.",
        )

    result, error = await ai_service.analyze_symptoms(payload.symptoms)

    if error:
        raise HTTPException(status_code=503, detail=f"AI service unavailable: {error}")

    matching_doctors = db.query(Doctor).filter(
        Doctor.specialization == result["recommended_specialization"],
        Doctor.status == DoctorStatus.ACTIVE,
    ).all()

    doctor_list = [
        {
            "id": d.id,
            "full_name": d.full_name,
            "specialization": d.specialization,
            "qualification": d.qualification,
            "experience_years": d.experience_years,
            "consultation_fee": float(d.consultation_fee),
            "available_days": d.available_days,
            "start_time": d.start_time,
            "end_time": d.end_time,
        }
        for d in matching_doctors
    ]

    analysis = SymptomAnalysis(
        patient_id=current_user.id,
        input_text=payload.symptoms,
        detected_symptoms=json.dumps(result["detected_symptoms"]),
        recommended_specialization=result["recommended_specialization"],
        recommendation_reason=result["recommendation_reason"],
        urgency=result["urgency"],
        ai_model=settings.OLLAMA_MODEL,
    )
    db.add(analysis)
    db.commit()
    db.refresh(analysis)

    return SymptomAnalysisResponse(
        analysis_id=analysis.id,
        detected_symptoms=result["detected_symptoms"],
        recommended_specialization=result["recommended_specialization"],
        recommendation_reason=result["recommendation_reason"],
        urgency=result["urgency"],
        warning_signs=result["warning_signs"],
        matching_doctors=doctor_list,
        disclaimer="This AI assistant provides general guidance and does not provide a medical diagnosis. Always consult a qualified healthcare professional.",
    )


@router.get("/symptom-analysis/my", response_model=list[SymptomAnalysisHistory])
def my_analysis_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(Role.PATIENT)),
):
    analyses = db.query(SymptomAnalysis).filter(
        SymptomAnalysis.patient_id == current_user.id
    ).order_by(SymptomAnalysis.created_at.desc()).limit(20).all()

    results = []
    for a in analyses:
        try:
            symptoms = json.loads(a.detected_symptoms) if a.detected_symptoms else []
        except (json.JSONDecodeError, TypeError):
            symptoms = []
        results.append(SymptomAnalysisHistory(
            id=a.id,
            input_text=a.input_text,
            detected_symptoms=symptoms,
            recommended_specialization=a.recommended_specialization or "",
            recommendation_reason=a.recommendation_reason or "",
            urgency=a.urgency.value if hasattr(a.urgency, 'value') else str(a.urgency),
            ai_model=a.ai_model,
            created_at=str(a.created_at),
        ))
    return results
