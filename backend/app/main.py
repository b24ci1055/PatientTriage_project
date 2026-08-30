from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

from .store import store
from .sample_data import PATIENTS, random_surge_patient

app = FastAPI(title="PatientTriage.ai — Prototype API", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class IntakeRequest(BaseModel):
    name: str
    age: float
    chief_complaint: str
    heart_rate: Optional[float] = None
    resp_rate: Optional[float] = None
    spo2: Optional[float] = None
    temp_c: Optional[float] = None
    systolic_bp: Optional[float] = None
    has_history: bool = False


class OverrideRequest(BaseModel):
    new_level: int
    nurse_name: str
    reason: str


class VitalsUpdateRequest(BaseModel):
    heart_rate: Optional[float] = None
    resp_rate: Optional[float] = None
    spo2: Optional[float] = None
    temp_c: Optional[float] = None
    systolic_bp: Optional[float] = None


class AdvanceTimeRequest(BaseModel):
    minutes: int = 15


class SurgeRequest(BaseModel):
    count: int = 16  # ~3x normal capacity of 8


@app.on_event("startup")
def seed_data():
    if store.patients:
        return
    for p in PATIENTS:
        store.add_patient(
            name=p["name"], age=p["age"], chief_complaint=p["chief_complaint"],
            vitals=p["vitals"], has_history=p["has_history"],
        )


@app.get("/api/queue")
def get_queue():
    return {
        "virtual_time": store.virtual_now.isoformat(),
        "load_ratio": round(store._load_ratio(), 2),
        "queue": store.queue_snapshot(),
    }


@app.post("/api/patients")
def add_patient(req: IntakeRequest):
    vitals = {
        "heart_rate": req.heart_rate, "resp_rate": req.resp_rate, "spo2": req.spo2,
        "temp_c": req.temp_c, "systolic_bp": req.systolic_bp,
    }
    patient = store.add_patient(
        name=req.name, age=req.age, chief_complaint=req.chief_complaint,
        vitals=vitals, has_history=req.has_history,
    )
    return patient.to_dict()


@app.post("/api/patients/{patient_id}/override")
def override_patient(patient_id: int, req: OverrideRequest):
    if patient_id not in store.patients:
        raise HTTPException(404, "Patient not found")
    if not (1 <= req.new_level <= 5):
        raise HTTPException(400, "ESI level must be 1-5")
    patient = store.override(patient_id, req.new_level, req.nurse_name, req.reason)
    return patient.to_dict()


@app.post("/api/patients/{patient_id}/vitals")
def update_vitals(patient_id: int, req: VitalsUpdateRequest):
    if patient_id not in store.patients:
        raise HTTPException(404, "Patient not found")
    patient = store.update_vitals(patient_id, req.dict())
    return patient.to_dict()


@app.post("/api/advance-time")
def advance_time(req: AdvanceTimeRequest):
    flagged = store.advance_time(req.minutes)
    return {"virtual_time": store.virtual_now.isoformat(), "escalated_patient_ids": flagged}


@app.post("/api/simulate-surge")
def simulate_surge(req: SurgeRequest):
    added = store.simulate_surge(req.count, random_surge_patient)
    return {"added_patient_ids": added, "load_ratio": round(store._load_ratio(), 2)}


@app.get("/api/audit-log")
def get_audit_log():
    return {"entries": store.audit_snapshot()}


@app.get("/api/health")
def health():
    return {"status": "ok"}
