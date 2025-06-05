from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import uuid
import plotly.express as px


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory stores
invoices = []
expenses = []
accounts = []
journals = []

class Invoice(BaseModel):
    id: str = None
    date: str
    invoice_number: str
    customer: str
    amount: float

class Expense(BaseModel):
    id: str = None
    date: str
    description: str
    amount: float

class Account(BaseModel):
    id: str = None
    code: str
    name: str
    type: str

class JournalEntry(BaseModel):
    id: str = None
    date: str
    account_code: str
    description: str
    debit: float = 0
    credit: float = 0
    reference: str = ""

@app.on_event("startup")
def load_default_coa():
    global accounts
    if not accounts:
        defaults = [
            ("1000", "Cash", "asset"),
            ("1100", "Accounts Receivable", "asset"),
            ("2000", "Accounts Payable", "liability"),
            ("3000", "Equity", "equity"),
            ("4000", "Sales Revenue", "revenue"),
            ("5000", "Operating Expense", "expense"),
        ]
        for code, name, typ in defaults:
            accounts.append(Account(id=str(uuid.uuid4()), code=code, name=name, type=typ))

@app.get("/")
def root():
    return {"message": "Accounting API Running"}

@app.get("/accounts")
def get_accounts():
    return [a.dict() for a in accounts]

@app.post("/accounts", response_model=Account)
def add_account(account: Account):
    account.id = str(uuid.uuid4())
    accounts.append(account)
    return account

@app.put("/accounts/{account_id}", response_model=Account)
def update_account(account_id: str, updated: Account):
    for i, acc in enumerate(accounts):
        if acc.id == account_id:
            old_code = acc.code
            accounts[i] = Account(id=account_id, code=updated.code, name=updated.name, type=updated.type)
            for j in journals:
                if j.account_code == old_code:
                    j.account_code = updated.code
            return accounts[i]
    raise HTTPException(status_code=404, detail="Account not found")

@app.delete("/accounts/{account_id}")
def delete_account(account_id: str):
    global accounts
    accounts = [acc for acc in accounts if acc.id != account_id]
    return {"message": "Account deleted"}

@app.get("/journals")
def get_journals():
    return [j.dict() for j in journals]

def post_journal(date: str, description: str, debit: tuple, credit: tuple, ref=""):
    journals.append(JournalEntry(id=str(uuid.uuid4()), date=date, account_code=debit[0], description=description, debit=debit[1], credit=0, reference=ref))
    journals.append(JournalEntry(id=str(uuid.uuid4()), date=date, account_code=credit[0], description=description, debit=0, credit=credit[1], reference=ref))

@app.get("/invoices", response_model=List[Invoice])
def get_invoices():
    return invoices

@app.post("/invoices", response_model=Invoice)
def add_invoice(invoice: Invoice, debit_account: str = None, credit_account: str = None):
    invoice.id = str(uuid.uuid4())
    invoices.append(invoice)
    ar_code = debit_account or next((a.code for a in accounts if a.type == "asset"), "1100")
    rev_code = credit_account or next((a.code for a in accounts if a.type == "revenue"), "4000")
    post_journal(invoice.date, f"Invoice {invoice.invoice_number}", (ar_code, invoice.amount), (rev_code, invoice.amount), invoice.invoice_number)
    return invoice

@app.delete("/invoices/{invoice_id}")
def delete_invoice(invoice_id: str):
    global invoices
    invoices = [inv for inv in invoices if inv.id != invoice_id]
    return {"message": "Invoice deleted"}

@app.get("/expenses", response_model=List[Expense])
def get_expenses():
    return expenses

@app.post("/expenses", response_model=Expense)
def add_expense(expense: Expense, debit_account: str = None, credit_account: str = None):
    expense.id = str(uuid.uuid4())
    expenses.append(expense)
    exp_code = debit_account or next((a.code for a in accounts if a.type == "expense"), "5000")
    cash_code = credit_account or next((a.code for a in accounts if a.type == "asset"), "1000")
    post_journal(expense.date, expense.description, (exp_code, -expense.amount), (cash_code, -expense.amount), "EXP")
    return expense

@app.delete("/expenses/{expense_id}")
def delete_expense(expense_id: str):
    global expenses
    expenses = [exp for exp in expenses if exp.id != expense_id]
    return {"message": "Expense deleted"}

@app.get("/balancesheet")
def get_balance_sheet():
    balances = {}
    for entry in journals:
        balances.setdefault(entry.account_code, 0)
        balances[entry.account_code] += entry.debit - entry.credit
    return balances



@app.post("/journals")
def post_journal_entry(entry: JournalEntry):
    journals.append(entry)
    return entry

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)
