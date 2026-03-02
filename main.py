import sqlite3
import uuid
from fastapi import FastAPI, HTTPException

app = FastAPI(title="Ginga Claims API")

def setup():
    conn = sqlite3.connect('claims.db')
    curr = conn.cursor()
    curr.execute('CREATE TABLE IF NOT EXISTS claims (claim_id TEXT, member_id TEXT, provider_id TEXT, diag_code TEXT, proc_code TEXT, amount REAL, status TEXT)')
    conn.commit()
    conn.close()

setup()

members = {"M123": True, "M456": False}
costs = {"P001": 20000.0, "P002": 5000.0}

@app.post("/submit_claim")
async def post_claim(data: dict):
    try:
        m_id = data.get("member_id").upper()
        p_id = data.get("provider_id").upper()
        proc = data.get("procedure_code").upper()
        amt = float(data.get("claim_amount"))
        diag = data.get("diagnosis_code")
    except (AttributeError, ValueError, TypeError):
        raise HTTPException(status_code=400, detail="Invalid data format")

    if m_id not in members:
        raise HTTPException(status_code=404, detail="Member not found")
    
    if proc not in costs:
        raise HTTPException(status_code=404, detail="Procedure code not found")

    status = "Approved"
    
    if members[m_id] == False:
        status = "Rejected"
    elif amt > 40000:
        status = "Partial"
    elif amt > (costs[proc] * 2):
        status = "Partial"

    cid = "C-" + str(uuid.uuid4()).upper()[:6]

    try:
        with sqlite3.connect('claims.db') as db:
            cursor = db.cursor()
            cursor.execute("INSERT INTO claims VALUES (?, ?, ?, ?, ?, ?, ?)", 
                           (cid, m_id, p_id, diag, proc, amt, status))
            db.commit()
    except Exception:
        raise HTTPException(status_code=500, detail="Database error")

    return {
        "claim_id": cid,
        "status": status,
        "amount": amt
    }

@app.get("/get_claim/{id}")
async def fetch_claim(id: str):
    with sqlite3.connect('claims.db') as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM claims WHERE claim_id = ?", (id,))
        item = cursor.fetchone()
    
    if item is None:
        raise HTTPException(status_code=404, detail="Claim ID not found")
        
    return dict(item)

@app.get("/check")
def check():
    return {"status": "ok"}