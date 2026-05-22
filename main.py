from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

app = FastAPI(title="HL7 FHIR Converter")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

audit_log = []

consent_records = [
    {"id": "PT-001", "name": "John Doe",       "gdpr": True,  "hipaa": True,  "research": False, "last_updated": "2025-01-15", "status": "active"},
    {"id": "PT-002", "name": "Jane Smith",     "gdpr": True,  "hipaa": True,  "research": True,  "last_updated": "2025-03-22", "status": "active"},
    {"id": "PT-003", "name": "Robert Johnson", "gdpr": False, "hipaa": True,  "research": False, "last_updated": "2024-12-01", "status": "revoked"},
    {"id": "PT-004", "name": "Maria Garcia",   "gdpr": True,  "hipaa": False, "research": True,  "last_updated": "2025-04-10", "status": "pending"},
]

class ConvertRequest(BaseModel):
    input_text: str
    direction: str
    role: Optional[str] = "Clinician"

class ConsentUpdate(BaseModel):
    field: str
    value: bool

@app.get("/health")
def health():
    return {"status": "running"}

@app.post("/api/convert")
def convert(request: ConvertRequest):
    if request.direction == "hl7ToFhir":
        result = {
            "converted": {
                "resourceType": "Patient",
                "id": "12345",
                "name": [{"family": "DOE", "given": ["JOHN"]}],
                "birthDate": "1980-01-01",
                "gender": "male"
            },
            "mappings": [
                {"source": "PID-5", "target": "Patient.name", "confidence": 0.99, "notes": "Patient name field"},
                {"source": "PID-7", "target": "Patient.birthDate", "confidence": 0.98, "notes": "Date of birth"},
                {"source": "PID-8", "target": "Patient.gender", "confidence": 0.97, "notes": "Gender field"}
            ],
            "warnings": [],
            "summary": "Successfully converted ADT message to FHIR Patient resource"
        }
    else:
        result = {
            "converted": "MSH|^~\\&|HOSPITAL|ADT||20240101||ADT^A01|MSG001|P|2.5\nPID|1||12345|||DOE^JOHN||19800101|M",
            "mappings": [
                {"source": "Patient.name", "target": "PID-5", "confidence": 0.99, "notes": "Patient name"},
                {"source": "Patient.birthDate", "target": "PID-7", "confidence": 0.98, "notes": "Date of birth"}
            ],
            "warnings": [],
            "summary": "Successfully converted FHIR Patient to HL7 v2 message"
        }

    audit_log.append({
        "id": len(audit_log) + 1,
        "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
        "user": (request.role or "clinician").lower(),
        "action": "HL7→FHIR" if request.direction == "hl7ToFhir" else "FHIR→HL7",
        "status": "success",
    })

    return result

@app.get("/api/audit")
def get_audit_log():
    return audit_log

@app.get("/api/consent")
def get_consent():
    return consent_records

@app.patch("/api/consent/{patient_id}")
def update_consent(
    patient_id: str,
    update: ConsentUpdate,
    role: str = Query(default="Clinician")
):
    if role not in ["Admin", "Clinician"]:
        return {"error": f"Role '{role}' cannot modify consent"}

    if update.field not in {"gdpr", "hipaa", "research"}:
        return {"error": "Invalid field"}

    for patient in consent_records:
        if patient["id"] == patient_id:
            patient[update.field] = update.value
            patient["last_updated"] = datetime.utcnow().strftime("%Y-%m-%d")
            return {"message": "Updated", "patient": patient}

    return {"error": "Patient not found"}

app.mount("/", StaticFiles(directory="static", html=True), name="static")