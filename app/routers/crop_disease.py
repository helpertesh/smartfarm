from fastapi import APIRouter, HTTPException
from app.schemas import DiseaseDiagnosisRequest, DiseaseDiagnosisResponse

router = APIRouter(prefix="/disease-advisory", tags=["Crop Disease Advisory"])

# Knowledge base for common crop issues
DISEASE_KNOWLEDGE_BASE = [
    {
        "crop_name": "tomato",
        "symptom": "yellow leaves",
        "possible_disease": "Tomato Yellow Leaf Curl Virus / Early Blight",
        "symptoms_description": "Leaves start yellowing along the margins, curling upwards, or showing dark concentric spots with yellow halos.",
        "recommended_action": [
            "Apply neem oil or an approved copper-based fungicide.",
            "Remove and safely destroy severely affected leaves.",
            "Ensure proper plant spacing to improve air circulation."
        ]
    },
    {
        "crop_name": "maize",
        "symptom": "yellow leaves",
        "possible_disease": "Nitrogen Deficiency / Maize Lethal Necrosis",
        "symptoms_description": "V-shaped yellowing starting from the leaf tip and moving down the midrib.",
        "recommended_action": [
            "Apply nitrogen-rich fertilizer (e.g., UREA or CAN) as top dressing.",
            "Ensure adequate soil moisture to help nutrient uptake."
        ]
    }
]

@router.post("/diagnose", response_model=DiseaseDiagnosisResponse)
def diagnose_crop_issue(payload: DiseaseDiagnosisRequest):
    crop = payload.crop_name.strip().lower()
    symptom = payload.symptom.strip().lower()
    
    for entry in DISEASE_KNOWLEDGE_BASE:
        if entry["crop_name"] in crop and symptom in entry["symptom"]:
            return entry
            
    raise HTTPException(
        status_code=404, 
        detail="No matching disease or treatment recommendation found for the specified crop and symptom."
    )