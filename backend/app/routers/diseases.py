from fastapi import APIRouter, Depends, HTTPException

from app.core.security import get_current_user
from app.data.crops import CROPS
from app.data.diseases import DISEASES, SYMPTOMS, diagnose
from app.models.user import User
from app.schemas import DiagnoseRequest

router = APIRouter(prefix="/api/diseases", tags=["diseases"])


@router.get("/symptoms")
def symptoms():
    return [{"key": k, "label": v} for k, v in SYMPTOMS.items()]


@router.get("")
def list_diseases(crop_key: str | None = None):
    items = DISEASES if not crop_key else [d for d in DISEASES if crop_key in d["crops"]]
    return [
        {**d, "crop_names": [CROPS[c]["name"] for c in d["crops"] if c in CROPS]}
        for d in items
    ]


@router.get("/{disease_key}")
def disease_detail(disease_key: str):
    for d in DISEASES:
        if d["key"] == disease_key:
            return {**d, "crop_names": [CROPS[c]["name"] for c in d["crops"] if c in CROPS]}
    raise HTTPException(status_code=404, detail="Disease not found")


@router.post("/diagnose")
def diagnose_problem(payload: DiagnoseRequest, user: User = Depends(get_current_user)):
    if payload.crop_key not in CROPS:
        raise HTTPException(status_code=400, detail="Unknown crop")
    unknown = [s for s in payload.symptoms if s not in SYMPTOMS]
    if unknown:
        raise HTTPException(status_code=400, detail=f"Unknown symptoms: {', '.join(unknown)}")
    results = diagnose(payload.crop_key, payload.symptoms)
    return {
        "crop": CROPS[payload.crop_key]["name"],
        "symptoms": [SYMPTOMS[s] for s in payload.symptoms],
        "results": [
            {
                "key": r["key"],
                "name": r["name"],
                "type": r["type"],
                "confidence": r["confidence"],
                "matched_symptoms": [SYMPTOMS[s] for s in r["matched_symptoms"]],
                "description": r["description"],
                "conditions": r["conditions"],
                "actions": r["actions"],
            }
            for r in results
        ],
    }
