import logging
import sqlite3
import uuid
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# --- BONUS: LOGGING SETUP ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Ginja AI Claims API")

# --- 1. Database Setup ---
def init_db():
    conn = sqlite3.connect("claims.db")
    cursor = conn.cursor()
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
members = {"M123": {"active": True}, "M456": {"active": False}}
procedures = {"P001": {"avg_cost": 20000}, "P002": {"avg_cost": 5000}}

# --- 3. Data Models ---
class ClaimInput(BaseModel):
    member_id: str
    provider_id: str
    diagnosis_code: str
    procedure_code: str
    claim_amount: float

# --- 4. The Logic ---
@app.post("/claims")
async def submit_claim(claim: ClaimInput):
    logger.info(f"Processing claim for member: {claim.member_id}")
    
    member = members.get(claim.member_id)
    procedure = procedures.get(claim.procedure_code)
    
    if not member or not procedure:
        logger.warning(f"Validation failed: Member/Procedure not found")
        raise HTTPException(status_code=404, detail="Member or Procedure not found")

    is_eligible = member["active"]
    under_limit = claim.claim_amount <= 40000
    is_suspicious = claim.claim_amount > (procedure["avg_cost"] * 2)

    if not is_eligible:
        status = "Rejected"
    elif not under_limit or is_suspicious:
        status = "Partial"
    else:
        status = "Approved"

    claim_id = f"C{uuid.uuid4().hex[:4].upper()}"

    conn = sqlite3.connect("claims.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO claims VALUES (?, ?, ?, ?, ?, ?, ?)",
                   (claim_id, claim.member_id, claim.provider_id, claim.diagnosis_code, 
                    claim.procedure_code, claim.claim_amount, status))
    conn.commit()
    conn.close()

    logger.info(f"Claim {claim_id} created with status: {status}")
    return {"claim_id": claim_id, "status": status}

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