from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from models import User, DiagnosticResult, Diagnostic
from schemas import DiabetesRequest
from utils import get_current_user
import joblib
import pandas as pd
from medical_record_service import upsert_medical_record

router = APIRouter(prefix="/analysis", tags=["analysis"])

loaded_scaler = joblib.load('/home/YousefMohamed/graduation-back/models/scaler.pkl')
loaded_model  = joblib.load('/home/YousefMohamed/graduation-back/models/knn_best_model.pkl')

@router.post("/run", status_code=200)
def run_analysis(request: DiabetesRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):

    data = [i for i in request.model_dump(exclude={"gender"}).values()]
    test_values = [data]

    cols = ['Pregnancies', 'Glucose', 'BloodPressure', 'SkinThickness',
            'Insulin', 'BMI', 'DiabetesPedigreeFunction', 'Age']

    sample        = pd.DataFrame(test_values, columns=cols)
    sample_scaled = loaded_scaler.transform(sample)
    predictions   = loaded_model.predict(sample_scaled)

    prediction_value = int(predictions[0])

    diago = Diagnostic(
        **request.model_dump(exclude={"gender"}),
        user_id=current_user.uuid
    )

    result_obj = DiagnosticResult(
        risk_level=str(prediction_value),
        confidence=0.9,
    )

    diago.result = result_obj

    db.add(diago)
    db.commit()
    db.refresh(diago)
    upsert_medical_record(db, current_user.uuid)
    return {"prediction": int(predictions[0]), "confidence": 0.9}
