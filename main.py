# GDPR Consent records
consent_records = [
    {"id": "PT-001", "name": "John Doe",       "gdpr": True,  "hipaa": True,  "research": False, "last_updated": "2025-01-15", "status": "active"},
    {"id": "PT-002", "name": "Jane Smith",     "gdpr": True,  "hipaa": True,  "research": True,  "last_updated": "2025-03-22", "status": "active"},
    {"id": "PT-003", "name": "Robert Johnson", "gdpr": False, "hipaa": True,  "research": False, "last_updated": "2024-12-01", "status": "revoked"},
    {"id": "PT-004", "name": "Maria Garcia",   "gdpr": True,  "hipaa": False, "research": True,  "last_updated": "2025-04-10", "status": "pending"},
]

@app.get("/api/consent")
def get_consent():
    return consent_records

class ConsentUpdate(BaseModel):
    field: str
    value: bool

@app.patch("/api/consent/{patient_id}")
def update_consent(patient_id: str, update: ConsentUpdate, role: str = "Clinician"):
    if role not in ["Admin", "Clinician"]:
        return {"error": f"Role '{role}' cannot modify consent"}

    allowed = {"gdpr", "hipaa", "research"}
    if update.field not in allowed:
        return {"error": "Invalid field"}

    for patient in consent_records:
        if patient["id"] == patient_id:
            patient[update.field] = update.value
            patient["last_updated"] = datetime.utcnow().strftime("%Y-%m-%d")
            return {"message": "Updated", "patient": patient}

    return {"error": "Patient not found"}