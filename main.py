import sqlite3
import uuid
import datetime
from fastapi import FastAPI, Request, HTTPException

app = FastAPI()

db_file = "claims.db"

conn = sqlite3.connect(db_file)
conn.execute("CREATE TABLE IF NOT EXISTS claims (id TEXT, pid TEXT, prov TEXT, icd TEXT, amt REAL, status TEXT)")
conn.close()

@app.post("/add")
async def add_claim(req: Request):
    data = await req.json()
    
    patient = data.get("patient_id")
    provider = data.get("provider_id")
    code = data.get("icd")
    amount = data.get("amount")

    if amount > 10000:
        s = "Needs Review"
    else:
        s = "Approved"

    my_id = "ID-" + str(uuid.uuid4())[:8]

    print("Saving claim for patient: " + str(patient))
    
    conn = sqlite3.connect(db_file)
    cur = conn.cursor()
    cur.execute("INSERT INTO claims VALUES (?, ?, ?, ?, ?, ?)", 
                (my_id, patient, provider, code, amount, s))
    conn.commit()
    conn.close()

    return {"id": my_id, "status": s}

@app.get("/get/{id}")
def get_info(id: str):
    conn = sqlite3.connect(db_file)
    cur = conn.cursor()
    cur.execute("SELECT * FROM claims WHERE id = ?", (id,))
    row = cur.fetchone()
    conn.close()

    if row == None:
        return {"error": "not found"}

    return {
        "claim_id": row[0],
        "patient": row[1],
        "provider": row[2],
        "code": row[3],
        "amount": row[4],
        "status": row[5]
    }