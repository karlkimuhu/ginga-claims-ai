"""
This is a small FastAPI application for submitting and retrieving insurance claims.
The code is written to be easy to read and understand.
"""

import logging
import os
import sqlite3
import uuid
from contextlib import contextmanager
from typing import Generator, Optional

from fastapi import Depends, FastAPI, HTTPException, Request, status
from pydantic import BaseModel, Field, constr, validator



LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
logging.basicConfig(level=LOG_LEVEL, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("friendly_claims")



app = FastAPI(title="Friendly Claims Service")
DB_FILE = os.getenv("CLAIMS_DB", os.path.join(os.path.dirname(__file__), "claims.db"))
GLOBAL_CLAIM_LIMIT = float(os.getenv("CLAIM_GLOBAL_LIMIT", "40000"))  


def open_connection() -> sqlite3.Connection:
    """
    Open a new SQLite connection. We return Row objects for nicer access.
    Each request should get its own connection.
    """
    conn = sqlite3.connect(DB_FILE, detect_types=sqlite3.PARSE_DECLTYPES)
    conn.row_factory = sqlite3.Row  
    return conn

@contextmanager
def get_cursor():
    """
    Context manager that yields a cursor and ensures commit/close.
    Keeps calling code simple and explicit.
    """
    conn = open_connection()
    cursor = None
    try:
        cursor = conn.cursor()
        yield cursor
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def ensure_database():
    """
    Create the claims table if it doesn't exist.
    TODO: Maybe add indices on member_id and status for faster queries?
    """
    with get_cursor() as cur:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS claims (
                claim_id TEXT PRIMARY KEY,
                member_id TEXT NOT NULL,
                provider_id TEXT NOT NULL,
                diagnosis_code TEXT,
                procedure_code TEXT NOT NULL,
                claim_amount REAL NOT NULL,
                status TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
    log.info("Database initialized at %s", DB_FILE)


ensure_database()




KNOWN_MEMBERS = {"M123": {"active": True}, "M456": {"active": False}}
KNOWN_PROCEDURES = {"P001": {"avg_cost": 20000.0}, "P002": {"avg_cost": 5000.0}}
KNOWN_PROVIDERS = {"PR1": {"name": "Provider One"}, "PR2": {"name": "Provider Two"}}



ShortCode = constr(strip_whitespace=True, min_length=1, max_length=32)

class ClaimInput(BaseModel):
    """
    Claim submission payload.
    Fields are cleaned (uppercased) for consistency.
    """
    member_id: ShortCode
    provider_id: ShortCode
    diagnosis_code: Optional[ShortCode] = None
    procedure_code: ShortCode
    claim_amount: float = Field(..., gt=0.0, lt=1_000_000.0)

    @validator("member_id", "provider_id", "procedure_code", pre=True)
    def normalize_codes(cls, v):
        
        if isinstance(v, str):
            return v.upper().strip()
        return v

class ClaimOutput(BaseModel):
    claim_id: str
    status: str
    claim_amount: float
    created_at: Optional[str] = None


def new_claim_id() -> str:
    """
    Generate a unique claim id. We prefix with 'C' and use a full UUID4 hex
    to avoid collisions in production-like scenarios.
    """
    claim_uuid = uuid.uuid4()
    return "C" + claim_uuid.hex

def decide_status(member_record: dict, procedure_record: dict, amount: float) -> str:
    """
    Decide the claim status using simple rules:
    - If the member is not active -> Rejected
    - If the claim is above the global limit -> Partial
    - If the claim is more than twice the avg cost of the procedure -> Partial
    - Otherwise -> Approved
    
    Note: This is a simplified version. Real adjudication logic would be much more complex.
    """
    
    is_active = member_record.get("active", False)
    if not is_active:
        return "Rejected"
    
    
    if amount > GLOBAL_CLAIM_LIMIT:
        return "Partial"
    
    
    avg_cost = procedure_record.get("avg_cost", 0.0)
    if amount > (avg_cost * 2):
        return "Partial"
    
    return "Approved"


def get_db_connection():
    """
    Dependency that yields a connection and closes it after the request.
    Useful for endpoint-level DB work.
    """
    conn = open_connection()
    try:
        yield conn
    finally:
        conn.close()


@app.post("/claims", response_model=ClaimOutput, status_code=status.HTTP_201_CREATED)
async def submit_claim(claim: ClaimInput, request: Request, conn: sqlite3.Connection = Depends(get_db_connection)):
    """
    Accept a claim, validate it against known members/procedures/providers,
    decide a status, store it, and return the created claim id and status.
    """
    log.info("Submitting claim: member=%s provider=%s procedure=%s amount=%.2f",
             claim.member_id, claim.provider_id, claim.procedure_code, claim.claim_amount)

    
    member = KNOWN_MEMBERS.get(claim.member_id)
    procedure = KNOWN_PROCEDURES.get(claim.procedure_code)
    provider = KNOWN_PROVIDERS.get(claim.provider_id)

    if member is None:
        log.warning("Unknown member: %s", claim.member_id)
        raise HTTPException(status_code=404, detail="Member not found")

    if procedure is None:
        log.warning("Unknown procedure: %s", claim.procedure_code)
        raise HTTPException(status_code=404, detail="Procedure not found")

    if provider is None:
        log.warning("Unknown provider: %s", claim.provider_id)
        raise HTTPException(status_code=404, detail="Provider not found")

    
    status_text = decide_status(member, procedure, claim.claim_amount)
    claim_id = new_claim_id()

    
    try:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO claims
            (claim_id, member_id, provider_id, diagnosis_code, procedure_code, claim_amount, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                claim_id,
                claim.member_id,
                claim.provider_id,
                claim.diagnosis_code,
                claim.procedure_code,
                claim.claim_amount,
                status_text,
            ),
        )
        conn.commit()
    except sqlite3.IntegrityError as e:
        
        log.error("Failed to insert claim (integrity): %s", e)
        raise HTTPException(status_code=500, detail="Could not create claim")
    except Exception as e:
        log.exception("Unexpected DB error while saving claim")
        raise HTTPException(status_code=500, detail="Internal server error")

    log.info("Created claim %s with status %s", claim_id, status_text)
    
    output = ClaimOutput(claim_id=claim_id, status=status_text, claim_amount=claim.claim_amount)
    return output

@app.get("/claims/{claim_id}", response_model=ClaimOutput)
async def get_claim(claim_id: str, conn: sqlite3.Connection = Depends(get_db_connection)):
    """
    Retrieve a claim by id. Returns 404 if not found.
    """
    cur = conn.cursor()
    cur.execute(
        "SELECT claim_id, status, claim_amount, created_at FROM claims WHERE claim_id = ?",
        (claim_id,),
    )
    row = cur.fetchone()
    
    if not row:
        log.info("Claim not found: %s", claim_id)
        raise HTTPException(status_code=404, detail="Claim not found")

    
    result = ClaimOutput(
        claim_id=row["claim_id"],
        status=row["status"],
        claim_amount=row["claim_amount"],
        created_at=row["created_at"],
    )
    return result

@app.get("/health")
async def health_check():
    """
    Simple health check endpoint.
    """
    return {"status": "ok"}