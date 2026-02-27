# Ginja AI - Backend Engineer Case Study (Claims Validation)

## Overview
This is a high-performance REST API built with **FastAPI** to automate the validation of health insurance claims. The system ensures that members are active, claims fall within benefit limits, and potential fraud is flagged.

## Core Features
- **POST /claims**: Validates incoming claims and stores them in a relational database.
- **GET /claims/{id}**: Retrieves the status of a previously submitted claim.
- **Validation Engine**:
    - **Eligibility**: Verifies if the member is currently active.
    - **Benefit Limit**: Automatically flags claims exceeding 40,000 as "Partial."
    - **Fraud Detection**: Compares claim amounts against average procedure costs (flags amounts > 2x the average).

## Tech Stack
- **Framework**: FastAPI (Asynchronous, high performance).
- **Database**: SQLite (Relational storage for structured claim data).
- **Validation**: Pydantic (Strong type-checking for incoming JSON).

## Production Awareness & Future Improvements
To move this from a case study to a production environment, I would implement:
1. **Security**: Add OAuth2/JWT authentication to ensure only authorized providers can submit claims.
2. **Scalability**: Migrate the SQLite database to **PostgreSQL** for better concurrent write handling.
3. **Robust Fraud Detection**: Integrate a machine learning model or a more complex historical analysis of claims.
4. **Monitoring**: Add logging (using ELK stack) and performance tracking to monitor API response times.

## How to Run
1. Activate the virtual environment: `source venv/bin/activate` (or `venv\Scripts\activate` on Windows).
2. Install dependencies: `pip install -r requirements.txt`.
3. Run the server: `uvicorn main:app --reload`.
4. Visit `http://127.0.0.1:8000/docs` for the interactive API documentation.