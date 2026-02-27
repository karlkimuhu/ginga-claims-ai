from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sqlite3
import uuid

app = FastAPI(title="Ginja AI Claims API")

# --- 1. Database Setup ---
def init_db():
    # Connects to a local file named 'claims.db'
    conn = sqlite3.connect("claims.db")
    cursor = conn.cursor()
    # Create the table as per 'clean claim schema' requirement
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS claims (
            claim_id TEXT PRIMARY KEY,
            member_id TEXT,
            provider_id TEXT,
            diagnosis_code TEXT,
            procedure_code TEXT,
            claim_amount REAL,
            status TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# --- 2. Mock Data ---
# Hardcoded data to simulate a real health system
members = {"M123": {"active": True}, "M456": {"active": False}}
procedures = {"P001": {"avg_cost": 20000}, "P002": {"avg_cost": 5000}}

# --- 3. Data Models ---
class ClaimInput(BaseModel):
    member_id: str
    provider_id: str
    diagnosis_code: str
    procedure_code: str
    claim_amount: float

# --- 4. The Logic (POST /claims) ---
@app.post("/claims")
async def submit_claim(claim: ClaimInput):
    # Retrieve member and procedure data
    member = members.get(claim.member_id)
    procedure = procedures.get(claim.procedure_code)
    
    # Error Handling: Check if data exists
    if not member or not procedure:
        raise HTTPException(status_code=404, detail="Member or Procedure not found")

    # Validation Rules
    is_eligible = member["active"]
    under_limit = claim.claim_amount <= 40000
    # Fraud rule: Is amount > 2x the average cost?
    is_suspicious = claim.claim_amount > (procedure["avg_cost"] * 2)

    # Decision Logic
    if not is_eligible:
        status = "Rejected"
    elif not under_limit or is_suspicious:
        status = "Partial"
    else:
        status = "Approved"

    claim_id = f"C{uuid.uuid4().hex[:4].upper()}"

    # Save to Database
    conn = sqlite3.connect("claims.db")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO claims VALUES (?, ?, ?, ?, ?, ?, ?)",
        (claim_id, claim.member_id, claim.provider_id, claim.diagnosis_code, 
         claim.procedure_code, claim.claim_amount, status)
    )
    conn.commit()
    conn.close()

    return {"claim_id": claim_id, "status": status}

# --- 5. Get Status (GET /claims/{id}) ---
@app.get("/claims/{claim_id}")
async def get_claim(claim_id: str):
    conn = sqlite3.connect("claims.db")
    cursor = conn.cursor()
    cursor.execute("SELECT claim_id, status FROM claims WHERE claim_id = ?", (claim_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Claim not found")
    
    return {"claim_id": row[0], "status": row[1]}
    