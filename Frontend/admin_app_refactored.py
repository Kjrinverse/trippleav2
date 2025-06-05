
import streamlit as st
import pandas as pd
import requests
import openai
import plotly.express as px

# === Configuration ===
st.set_page_config(page_title="RP AI Accounting", layout="wide")

st.markdown("""
    <div style="background-color:#0d6efd;padding:15px 10px;border-radius:8px;margin-bottom:25px;">
    </div>
""", unsafe_allow_html=True)

openai.api_key = st.secrets["OPENAI_API_KEY"]
API_BASE = "https://rp-ai-accounting.onrender.com"

# === Simple Password Login ===
PASSWORD = "letmein123"
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if not st.session_state.logged_in:
    st.title("🔐 Secure Login")
    pw = st.text_input("Enter Password", type="password")
    if pw == PASSWORD:
        st.session_state.logged_in = True
        st.success("✅ Access Granted")
        st.rerun()
    else:
        st.stop()

# === Custom Header ===
st.markdown("""
    </div>
""", unsafe_allow_html=True)

# === Sidebar Navigation ===
section = st.sidebar.radio("📂 Navigation", [
    "🧾 AI Journal Assistant", "🧾 Invoices", "💳 Expenses", "📚 Chart of Accounts",
    "📊 Income Statement", "🧮 Trial Balance", "🧾 Balance Sheet",
    "📖 General Ledger", "✍️ Manual Journal Entry", "📈 Net Income Trend", "💡 AI Insight Generator"
])

# === Backend Connection ===
st.sidebar.markdown("### 🔌 Backend Status")
try:
    ping = requests.get(f"{API_BASE}/ping").json()
    st.sidebar.success(f"Connected: {ping}")
except Exception as e:
    st.sidebar.error(f"Backend error: {e}")

# === Load Data from API ===
try:
    accounts = requests.get(f"{API_BASE}/accounts").json()
    journals = requests.get(f"{API_BASE}/journals").json()
    if isinstance(accounts, dict):
        accounts = [accounts]
    df_acc = pd.DataFrame(accounts)
    df_acc.rename(columns={"account_code": "code", "account_name": "name", "account_type": "type"}, inplace=True)
except Exception as e:
    st.error("❌ Could not load data from backend.")
    st.exception(e)
    st.stop()

# === Process Journals ===
if journals:
    df_journal = pd.DataFrame(journals)
else:
    df_journal = pd.DataFrame(columns=["date", "account_code", "description", "debit", "credit", "reference"])

if "date" in df_journal.columns:
    df_journal["date"] = pd.to_datetime(df_journal["date"], errors="coerce")
else:
    st.warning("⚠ No 'date' found in journal data.")
    df_journal["date"] = pd.to_datetime([])

# === Date Filters ===
min_date = df_journal["date"].min() if not df_journal["date"].dropna().empty else pd.to_datetime("2023-01-01")
max_date = df_journal["date"].max() if not df_journal["date"].dropna().empty else pd.to_datetime("2023-12-31")
with st.sidebar:
    st.markdown("### 📅 Filter by Date")
    start_date = st.date_input("Start Date", min_date)
    end_date = st.date_input("End Date", max_date)

# === Placeholder for Dynamic Sections ===
st.markdown(f"<h4 style='color:#0d6efd;margin-top:20px;'>🧭 You are viewing: <strong>{section}</strong></h4>", unsafe_allow_html=True)

st.info("👉 This is a placeholder. Each module's layout and logic can now be refactored one by one for consistency.")

