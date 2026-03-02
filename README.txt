Markdown
# Ginga Claims Validation API

Hi! This is my submission for the Backend Engineer Case Study. I built a REST API that helps automate how insurance claims are checked and stored.

## How it Works
When a claim is submitted, the code checks three main things:
1. **Member Status**: Is the person actually covered? (Checks a list of active members).
2. **Amount Limit**: Is the claim over $40,000? If so, it gets flagged as "Partial."
3. **Fraud Check**: Is the price way higher than normal? (Checks if the amount is more than 2x the average for that procedure).

## Tech I Used
- **Python & FastAPI**: For building the web server and the endpoints.
- **SQLite**: I used a SQL database to make sure the claims are saved properly in a table.
- **UUID**: To give every claim a unique ID number.

## How to Run it on Your Computer

1. **Activate the environment**:
   - On Windows: `venv\Scripts\activate`
   - On Mac/Linux: `source venv/bin/activate`

2. **Install what's needed**:
   ```bash
   pip install -r requirements.txt
Start the server:

Bash
uvicorn main:app --reload
How to Test
The easiest way to test is using the built-in documentation page at:
http://127.0.0.1:8000/docs

Use POST /submit_claim to add a new claim.

Use GET /get_claim/{id} to look up a claim by its ID.

Use GET /check just to see if the server is running.
