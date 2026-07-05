from fastapi import FastAPI
from pydantic import BaseModel
import pandas as pd
import joblib
import os

app = FastAPI(title="CareFlow AI API")

# Load Model
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
model_path = os.path.join(BASE_DIR, "models", "wait_time_prediction_model.pkl")
model = joblib.load(model_path)


class Patient(BaseModel):
    patient_gender: int
    patient_age: int
    patient_race: int
    department_referral: int
    patient_admission_flag: int
    patient_satisfaction_score: int = 3
    patients_cm: int
    admission_year: int
    admission_month: int
    admission_day: int
    admission_weekday: int


@app.get("/")
def home():
    return {
        "message": "Welcome to CareFlow AI",
        "status": "API Running Successfully"
    }


@app.post("/predict")
def predict(data: Patient):

    df = pd.DataFrame([[
        data.patient_gender,
        data.patient_age,
        data.patient_race,
        data.department_referral,
        data.patient_admission_flag,
        data.patient_satisfaction_score,
        data.patients_cm,
        data.admission_year,
        data.admission_month,
        data.admission_day,
        data.admission_weekday
    ]], columns=[
        "Patient Gender",
        "Patient Age",
        "Patient Race",
        "Department Referral",
        "Patient Admission Flag",
        "Patient Satisfaction Score",
        "Patients CM",
        "Admission_Year",
        "Admission_Month",
        "Admission_Day",
        "Admission_Weekday"
    ])

    prediction = model.predict(df)

    return {
        "Predicted Waiting Time (Minutes)": round(float(prediction[0]), 2)
    }