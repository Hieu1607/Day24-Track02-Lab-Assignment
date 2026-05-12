# src/api/main.py
from pathlib import Path
from fastapi import Depends, FastAPI, HTTPException
import pandas as pd
from src.access.rbac import get_current_user, require_permission
from src.pii.anonymizer import MedVietAnonymizer

app = FastAPI(title="MedViet Data API", version="1.0.0")
anonymizer = MedVietAnonymizer()
PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DATA_PATH = PROJECT_ROOT / "data" / "raw" / "patients_raw.csv"


def load_patient_data() -> pd.DataFrame:
    if not RAW_DATA_PATH.exists():
        raise HTTPException(status_code=404, detail="Patient dataset not found")
    return pd.read_csv(RAW_DATA_PATH)

# --- ENDPOINT 1 ---
@app.get("/api/patients/raw")
@require_permission(resource="patient_data", action="read")
async def get_raw_patients(
    current_user: dict = Depends(get_current_user)
):
    """
    Trả về raw patient data (chỉ admin được phép).
    Load từ data/raw/patients_raw.csv
    Trả về 10 records đầu tiên dưới dạng JSON.
    """
    df = load_patient_data()
    return df.head(10).to_dict(orient="records")

# --- ENDPOINT 2 ---
@app.get("/api/patients/anonymized")
@require_permission(resource="training_data", action="read")
async def get_anonymized_patients(
    current_user: dict = Depends(get_current_user)
):
    """
    Trả về anonymized data (ml_engineer và admin được phép).
    Load raw data → anonymize → trả về JSON.
    """
    df = load_patient_data()
    df_anon = anonymizer.anonymize_dataframe(df)
    return df_anon.head(10).to_dict(orient="records")

# --- ENDPOINT 3 ---
@app.get("/api/metrics/aggregated")
@require_permission(resource="aggregated_metrics", action="read")
async def get_aggregated_metrics(
    current_user: dict = Depends(get_current_user)
):
    """
    Trả về aggregated metrics (data_analyst, ml_engineer, admin).
    Ví dụ: số bệnh nhân theo từng loại bệnh (không có PII).
    """
    df = load_patient_data()
    condition_counts = (
        df["benh"].value_counts().rename_axis("benh").reset_index(name="so_luong")
    )
    return {
        "total_patients": int(len(df)),
        "by_condition": condition_counts.to_dict(orient="records"),
    }

# --- ENDPOINT 4 ---
@app.delete("/api/patients/{patient_id}")
@require_permission(resource="patient_data", action="delete")
async def delete_patient(
    patient_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Chỉ admin được xóa. Các role khác nhận 403.
    """
    df = load_patient_data()
    if patient_id not in set(df["patient_id"].astype(str)):
        raise HTTPException(status_code=404, detail="Patient not found")
    return {"deleted": True, "patient_id": patient_id}

@app.get("/health")
async def health():
    return {"status": "ok", "service": "MedViet Data API"}
