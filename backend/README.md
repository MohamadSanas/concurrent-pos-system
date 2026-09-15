# Backend

FastAPI backend for the Concurrent POS System.

## Setup

python -m venv venv
venv\Scripts\activate       # Windows
source venv/bin/activate    # Linux/macOS
pip install -r requirements.txt

## Migrations

alembic upgrade head

## Run

uvicorn app.main:app --reload

## Docs

http://localhost:8000/docs
