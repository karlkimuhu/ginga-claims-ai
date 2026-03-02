import sqlite3
import uuid
from fastapi import FastAPI, HTTPException

app = FastAPI()

db_file = "claims.db"

conn = sqlite3.connect(db_file)
conn.execute("CREATE TABLE IF NOT EXISTS claims (id TEXT, pid TEXT, prov TEXT, icd TEXT, amt REAL, status TEXT)")
conn.close()

@app.post("/add")
def add_claim(patient_id: str, provider_id: str, icd: str, amount: float):
    if amount > 10000:
        s = "Needs Review"
    else:
        s = "Approved"

    my_id = "ID-" + str(uuid.uuid4())[:8]
    
    conn = sqlite3.connect(db_file)
    cur = conn.cursor()
    cur.execute("INSERT INTO claims VALUES (?, ?, ?, ?, ?, ?)", 
                (my_id, patient_id, provider_id, icd, amount, s))
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
