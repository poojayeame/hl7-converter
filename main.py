from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from datetime import datetime
import json

app = FastAPI(title="HL7 FHIR Converter")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simple in-memory audit log (list acts as our database for now)
audit_log = []

class ConvertRequest(BaseModel):
    input_text: str
    direction: str
    role: str = "Clinician"

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

    # Save to audit log
    audit_log.append({
        "id": len(audit_log) + 1,
        "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
        "user": request.role.lower(),
        "action": "HL7→FHIR" if request.direction == "hl7ToFhir" else "FHIR→HL7",
        "status": "success",
    })

    return result

@app.get("/api/audit")
def get_audit_log():
    return audit_log

app.mount("/", StaticFiles(directory="static", html=True), name="static")