from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from schemas import Diabetes
from database import get_db
from utils import get_current_user
from models import Diagnotics , DiagnoticsResults,User

import joblib
import pandas as pd

router = APIRouter(prefix="/analysis", tags=["analysis"])

@router.post("/")
async def analysis(request:Diabetes,user=Depends(get_current_user),db:Session=Depends(get_db)):
    loaded_scaler = joblib.load('./models/scaler.pkl')
    loaded_model  = joblib.load('./models/knn_best_model.pkl')

    data = [i for i in request.model_dump().values()]
    test_values = [data]

    cols = ['Pregnancies', 'Glucose', 'BloodPressure', 'SkinThickness',
            'Insulin', 'BMI', 'DiabetesPedigreeFunction', 'Age']

    sample        = pd.DataFrame(test_values, columns=cols)
    sample_scaled = loaded_scaler.transform(sample)
    predictions   = loaded_model.predict(sample_scaled)
    return {"message": predictions}