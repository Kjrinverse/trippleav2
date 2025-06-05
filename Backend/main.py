import openai
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import datetime

app = FastAPI()

@app.get("/openai-version")
def get_version():
    return {"openai_version": openai.__version__}
    
# Enable CORS for frontend (e.g., Streamlit)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check route
@app.get("/")
def read_root():
    return {"message": "Backend is working"}

# Ping test
@app.get("/ping")
def ping():
    return {"response": "pong"}

# ========== Journal POST Route ==========

# Sample account data (for GET /accounts)
accounts = [
    {"code": "1000", "name": "Cash", "type": "asset"},
    {"code": "2000", "name": "Accounts Payable", "type": "liability"},
    {"code": "3000", "name": "Equity", "type": "equity"},
    {"code": "4000", "name": "Revenue", "type": "revenue"},
    {"code": "5000", "name": "Operating Expense", "type": "expense"},
    {"code": "6000", "name": "Cost of Goods Sold", "type": "cogs"},
]

journal_store = []

class JournalEntry(BaseModel):
    date: datetime.date
    account_code: str
    description: str
    debit: float
    credit: float
    reference: str

@app.get("/accounts")
def get_accounts():
    return accounts

@app.get("/journals")
def get_journals():
    return journal_store

@app.post("/journals")
def post_journals(entries: List[JournalEntry]):
    journal_store.extend([e.dict() for e in entries])
    return {"status": "success", "received": len(entries), "entries": entries}
