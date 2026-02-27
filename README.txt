# Ginja AI - Backend Engineer Case Study (Claims Validation)

## Overview
This is a high-performance REST API built with **FastAPI** to automate the validation of health insurance claims. The system ensures that members are active, claims fall within benefit limits, and potential fraud is flagged.

## Architecture Decisions
- **FastAPI**: Chosen for its native support for asynchronous programming and automatic OpenAPI (Swagger) documentation.
- **SQLite**: Used for persistence to meet the "Relational Database" requirement without requiring the reviewer to set up a complex database server.
- **Pydantic**: Used for strict data validation and type safety for incoming JSON payloads.
- **Logging**: Integrated Python's standard `logging` library to track claim processing and errors in real-time (Bonus Point).

## How to Run Locally
1. **Activate the environment**: 
   - Windows: `venv\Scripts\activate`
   - Mac/Linux: `source venv/bin/activate`
2. **Install dependencies**: `pip install -r requirements.txt`
3. **Start the server**: `uvicorn main:app --reload`
4. **Interactive Docs**: Open your browser to `http://127.0.0.1:8000/docs`

## Sample API Requests (curl)
You can test the API using the following commands in your terminal:

**Submit a Claim (POST):**
```bash
curl -X 'POST' \
  '[http://127.0.0.1:8000/claims](http://127.0.0.1:8000/claims)' \
  -H 'Content-Type: application/json' \
  -d '{
  "member_id": "M123",
  "provider_id": "H456",
  "diagnosis_code": "D001",
  "procedure_code": "P001",
  "claim_amount": 5000
}'
# --- GET CLAIM STATUS ---
@app.get("/claims/{claim_id}")
async def get_claim(claim_id: str):
    # 1. Connect to our SQLite database
    conn = sqlite3.connect("claims.db")
    cursor = conn.cursor()
    
    # 2. Search for the specific claim_id
    cursor.execute("SELECT claim_id, status FROM claims WHERE claim_id = ?", (claim_id,))
    row = cursor.fetchone()
    conn.close()

    # 3. If the ID doesn't exist in the database, send a 404 error
    if not row:
        logger.warning(f"Claim lookup failed: {claim_id} not found")
        raise HTTPException(status_code=404, detail="Claim not found")
    
    # 4. Return the data found
    return {"claim_id": row[0], "status": row[1]}
