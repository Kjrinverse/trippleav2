import streamlit as st
import pandas as pd
import requests
import openai
openai.api_key = st.secrets["OPENAI_API_KEY"]
import plotly.express as px

# --- SIMPLE PASSWORD LOGIN ---
PASSWORD = "letmein123"

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("🔐 Login Required")
    pw = st.text_input("Enter Password", type="password")
    if pw == PASSWORD:
        st.session_state.logged_in = True
        st.success("✅ Logged in successfully!")
        st.rerun()
    else:
        st.stop()


st.set_page_config(page_title="RP AI Accounting Module", layout="wide")
st.title("📊 RP AI Accounting Module")

API_BASE = "https://rp-ai-accounting.onrender.com"

section = st.sidebar.radio("Navigation", [
    "🧠 AI Journal Assistant","📄 Invoices", "💸 Expenses", "📒 Chart of Accounts",
    "📈 Income Statement", "📋 Trial Balance", "📊 Balance Sheet",
    "📘 General Ledger", "📘 Manual Journal Entry", "📉 Net Income Trend", "🧠 AI Insight Generator"
])

# 🔌 Backend Connection Test
st.sidebar.markdown("### 🔌 Backend Connection Test")
try:
    r = requests.get(f"{API_BASE}/ping")
    st.sidebar.success(f"✅ Connected: {r.json()}")
except Exception as e:
    st.sidebar.error(f"❌ Failed to connect to backend: {e}")

# Load data
try:
    accounts = requests.get(f"{API_BASE}/accounts").json()
    journals = requests.get(f"{API_BASE}/journals").json()

    if isinstance(accounts, dict):
        accounts = [accounts]  # Ensure it's a list

    df_acc = pd.DataFrame(accounts)

    # Auto-rename fallback for account keys
    df_acc.rename(columns={
        "account_code": "code",
        "account_name": "name",
        "account_type": "type"
    }, inplace=True)

except Exception as e:
    st.error("❌ Failed to load data from backend.")
    st.exception(e)
    st.stop()


    if isinstance(accounts, dict):
        accounts = [accounts]


df_acc = pd.DataFrame(accounts)
df_acc["label"] = df_acc["code"] + " - " + df_acc["name"]
if journals:
    df_journal = pd.DataFrame(journals)
else:
    df_journal = pd.DataFrame(columns=["date", "account_code", "description", "debit", "credit", "reference"])

# Rename columns if needed
expected_cols = {"account_code": "code", "account_name": "name", "account_type": "type"}
df_acc.rename(columns={k: v for k, v in expected_cols.items() if k in df_acc.columns}, inplace=True)

# Safe date handling
if "date" in df_journal.columns:
    df_journal["date"] = pd.to_datetime(df_journal["date"], errors="coerce")
else:
    st.warning("⚠ 'date' missing. Defaulting to empty.")
    df_journal["date"] = pd.to_datetime([])

# Safe min/max date
if df_journal["date"].dropna().empty:
    min_date = pd.to_datetime("2023-01-01")
    max_date = pd.to_datetime("2023-12-31")
else:
    min_date = df_journal["date"].min()
    max_date = df_journal["date"].max()

start_date = st.sidebar.date_input("Start Date", min_date)
end_date = st.sidebar.date_input("End Date", max_date)

# Merge safety
if "account_code" in df_journal.columns:
    merged = pd.merge(df_journal, df_acc, left_on="account_code", right_on="code", how="left")
else:
    st.warning("⚠ 'account_code' missing — merge skipped.")
    merged = pd.DataFrame()

# This is just the shell. Let me know if you want me to inject all the actual tab logic again.
st.info("✅ Tabs and logic will be injected here in next step.")



# ========================= 📄 INVOICES ============================
if section == "📄 Invoices":
    st.header("📄 Invoices")
    ar = df_acc[df_acc["type"] == "asset"].set_index("code")["label"].to_dict()
    rev = df_acc[df_acc["type"] == "revenue"].set_index("code")["label"].to_dict()
    with st.form("add_invoice"):
        date = st.date_input("Date")
        inv_num = st.text_input("Invoice Number")
        customer = st.text_input("Customer")
        amount = st.number_input("Amount", value=0.0)
        col1, col2 = st.columns(2)
        debit = col1.selectbox("Debit (A/R)", list(ar), format_func=lambda x: ar[x])
        credit = col2.selectbox("Credit (Revenue)", list(rev), format_func=lambda x: rev[x])
        if st.form_submit_button("Add Invoice"):
            payload = {"date": str(date), "invoice_number": inv_num, "customer": customer, "amount": amount}
            r = requests.post(f"{API_BASE}/invoices?debit_account={debit}&credit_account={credit}", json=payload)
            st.success("Invoice added!" if r.status_code == 200 else "Failed.")
    invoices = requests.get(f"{API_BASE}/invoices").json()
elif section == "📄 Invoices":
    try:
        invoices = requests.get(f"{API_BASE}/invoices").json()

        if isinstance(invoices, dict):
            invoices = [invoices]

        st.dataframe(pd.DataFrame(invoices))

    except Exception as e:
        st.error("❌ Failed to load invoices.")
        st.exception(e)

    st.dataframe(pd.DataFrame(invoices))

# ========================= 💸 EXPENSES ============================
elif section == "💸 Expenses":
    st.header("💸 Expenses")
    exp = df_acc[df_acc["type"] == "expense"].set_index("code")["label"].to_dict()
    cash = df_acc[df_acc["type"] == "asset"].set_index("code")["label"].to_dict()
    with st.form("add_expense"):
        date = st.date_input(" key='exp_date'")
        desc = st.text_input("Description")
        amt = st.number_input("Amount", value=0.0)
        col1, col2 = st.columns(2)
        debit = col1.selectbox("Debit (Expense)", list(exp), format_func=lambda x: exp[x])
        credit = col2.selectbox("Credit (Cash)", list(cash), format_func=lambda x: cash[x])
        if st.form_submit_button("Add Expense"):
            payload = {"date": str(date), "description": desc, "amount": amt}
            r = requests.post(f"{API_BASE}/expenses?debit_account={debit}&credit_account={credit}", json=payload)
            st.success("Expense added!" if r.status_code == 200 else "Failed.")
        expenses = requests.get(f"{API_BASE}/expenses").json()
        if isinstance(expenses, dict):
            expenses = [expenses]

        st.dataframe(pd.DataFrame(expenses))


# ========================= 📒 COA ============================
elif section == "📒 Chart of Accounts":
    st.header("📒 Chart of Accounts")
    action = st.radio("Action", ["Add", "Edit", "Delete"])
    if action == "Add":
        with st.form("add_account"):
            code = st.text_input("Code")
            name = st.text_input("Name")
            typ = st.selectbox("Type", ["asset", "liability", "equity", "revenue", "expense", "cogs"])
            if st.form_submit_button("Submit"):
                r = requests.post(f"{API_BASE}/accounts", json={"code": code, "name": name, "type": typ})
                st.success("Added!" if r.status_code == 200 else "Failed.")
    elif action == "Edit":
        if not df_acc.empty:
            selected = st.selectbox("Select Account", df_acc["id"], format_func=lambda x: df_acc[df_acc["id"] == x]["label"].values[0])
            acc = df_acc[df_acc["id"] == selected].iloc[0]
            with st.form("edit_account"):
                new_code = st.text_input("Code", value=acc["code"])
                new_name = st.text_input("Name", value=acc["name"])
                new_type = st.selectbox("Type", ["asset", "liability", "equity", "revenue", "expense"], index=["asset", "liability", "equity", "revenue", "expense"].index(acc["type"]))
                if st.form_submit_button("Update"):
                    r = requests.put(f"{API_BASE}/accounts/{selected}", json={"code": new_code, "name": new_name, "type": new_type})
                    st.success("Updated!" if r.status_code == 200 else "Failed.")
    elif action == "Delete":
        selected = st.selectbox("Delete Account", df_acc["id"], format_func=lambda x: df_acc[df_acc["id"] == x]["label"].values[0])
        if st.button("Delete"):
            r = requests.delete(f"{API_BASE}/accounts/{selected}")
            st.success("Deleted!" if r.status_code == 200 else "Failed.")
    st.dataframe(df_acc)

# ========================= 📈 Income Statement ============================
elif section == "📈 Income Statement":
    st.header("📈 Income Statement")

    # Merge if not done already
    df_journal["account_code"] = df_journal["account_code"].astype(str)
    df_acc["code"] = df_acc["code"].astype(str)
    merged = df_journal.merge(df_acc, how="left", left_on="account_code", right_on="code")

    # Define codes
    revenue_codes = ["4000"]
    cogs_codes = ["6000"]
    expense_codes = ["5000", "5100", "5200"]

    # Filter by code
    income = merged[merged["account_code"].isin(revenue_codes)]
    cogs = merged[merged["account_code"].isin(cogs_codes)]
    expense = merged[merged["account_code"].isin(expense_codes)]

    # Net amounts
    revenue_amt = income["credit"].sum() - income["debit"].sum()
    cogs_amt = cogs["debit"].sum() - cogs["credit"].sum()
    expense_amt = expense["debit"].sum() - expense["credit"].sum()
    gross_profit = revenue_amt - cogs_amt
    net_income = gross_profit - expense_amt

    # Display metrics
    st.metric("Revenue", f"{revenue_amt:,.2f}")
    st.metric("Cost of Goods Sold", f"{cogs_amt:,.2f}")
    st.metric("Gross Profit", f"{gross_profit:,.2f}")
    st.metric("Operating Expenses", f"{expense_amt:,.2f}")
    st.metric("Net Income", f"{net_income:,.2f}")


# ========================= 📋 Trial Balance ============================
elif section == "📋 Trial Balance":
    st.header("📋 Trial Balance")
    tb = merged.groupby(["code", "name", "type"]).agg({"debit": "sum", "credit": "sum"}).reset_index()
    st.dataframe(tb)

# ========================= 📊 Balance Sheet ============================
elif section == "📊 Balance Sheet":
    st.header("📊 Balance Sheet")
    bs = merged.groupby(["code", "name", "type"]).agg({"debit": "sum", "credit": "sum"}).reset_index()
    bs["balance"] = bs["debit"] - bs["credit"]
    for t in ["asset", "liability", "equity"]:
        st.subheader(t.capitalize())
        st.dataframe(bs[bs["type"] == t][["code", "name", "balance"]])

# ========================= 📘 General Ledger ============================
elif section == "📘 General Ledger":
    st.subheader("📘 General Ledger")

    try:
        # Fetch journal entries from backend
        journals = requests.get(f"{API_BASE}/journals").json()

        # Ensure it's a list
        if isinstance(journals, dict):
            journals = [journals]

        # Create DataFrame
        df_journal = pd.DataFrame(journals)

        # Display if there is data
        if not df_journal.empty:
            df_journal["date"] = pd.to_datetime(df_journal["date"])
            df_journal.sort_values("date", inplace=True)

            # Optional formatting
            df_journal["debit"] = df_journal["debit"].astype(float)
            df_journal["credit"] = df_journal["credit"].astype(float)

            st.dataframe(df_journal, use_container_width=True)

        else:
            st.info("No journal entries found.")

    except Exception as e:
        st.error("❌ Failed to load journal entries.")
        st.exception(e)

# ========================= 📉 Net Income Trend ============================
elif section == "📝 Manual Journal Test":
    st.header("📝 Manual Journal Entry Test Section")

    df_acc["code"] = df_acc["code"].astype(str)
    df_acc["label"] = df_acc["code"] + " - " + df_acc["name"]
    label_list = df_acc["label"].tolist()

    with st.form("manual_test_form"):
        date = st.date_input("Date")
        description = st.text_input("Description")
        amount = st.number_input("Amount", value=0.0, step=0.01)

        debit_label = st.selectbox("Debit Account", label_list)
        credit_label = st.selectbox("Credit Account", label_list)

        debit_account = df_acc[df_acc["label"] == debit_label]["code"].values[0]
        credit_account = df_acc[df_acc["label"] == credit_label]["code"].values[0]

        submit = st.form_submit_button("✅ Post Manual Entry")
        if submit:
            journals = [
                {
                    "date": str(date),
                    "account_code": debit_account,
                    "description": description,
                    "debit": amount,
                    "credit": 0,
                    "reference": "AI-MANUAL"
                },
                {
                    "date": str(date),
                    "account_code": credit_account,
                    "description": description,
                    "debit": 0,
                    "credit": amount,
                    "reference": "AI-MANUAL"
                }
            ]
            for j in journals:
                st.write("📤 Posting payload:", j)
                r = requests.post(f"{API_BASE}/journals", json=[j])
                st.write("🔍 POST response:", r.status_code, r.text)
            st.success("✅ Manual journal entry posted.")

elif section == "📉 Net Income Trend":
    st.header("📉 Net Income Trend")
    trend = merged.copy()
    trend["month"] = trend["date"].dt.to_period("M").astype(str)
    revenue = trend[trend["type"] == "revenue"].groupby("month")["credit"].sum()
    expense = trend[trend["type"] == "expense"].groupby("month")["debit"].sum()
    net = revenue.subtract(expense, fill_value=0).reset_index()
    net.columns = ["Month", "Net Income"]
    fig = px.line(net, x="Month", y="Net Income", title="Monthly Net Income")
    st.plotly_chart(fig)

# ========================= 🧠 AI Insight Tab ============================
elif section == "🧠 AI Insight Generator":
    st.header("🧠 AI Insight")
    source = st.radio("Data Source", ["📂 Upload File", "📊 Internal Report"])
    memo_type = st.selectbox("Memo Type", ["Revenue Recognition", "Audit Summary", "Custom Prompt"])
    memo_input = ""
    if source == "📂 Upload File":
        uploaded_file = st.file_uploader("Upload File", type=["csv", "xlsx", "pdf"])
        if uploaded_file:
            if uploaded_file.name.endswith(".csv"):
                df = pd.read_csv(uploaded_file)
                memo_input = df.head(20).to_csv(index=False)
            elif uploaded_file.name.endswith(".xlsx"):
                df = pd.read_excel(uploaded_file)
                memo_input = df.head(20).to_csv(index=False)
            elif uploaded_file.name.endswith(".pdf"):
                with pdfplumber.open(io.BytesIO(uploaded_file.read())) as pdf:
                    text = "\n".join(p.extract_text() for p in pdf.pages if p.extract_text())
                memo_input = text
            st.text_area("Input Data", memo_input, height=200)
    else:
        report = st.selectbox("Select Report", ["Income Statement", "Trial Balance", "Balance Sheet", "General Ledger"])
        report_map = {
            "Income Statement": merged[merged["type"].isin(["revenue", "expense"])],
            "Trial Balance": merged,
            "Balance Sheet": merged[merged["type"].isin(["asset", "liability", "equity"])],
            "General Ledger": merged
        }
        df = report_map[report]
        memo_input = df.to_csv(index=False)
    if memo_type == "Custom Prompt":
        prompt = st.text_area("Custom Prompt", height=150)
        full_prompt = f"{prompt}\n\n{memo_input}"
    elif memo_type == "Revenue Recognition":
        full_prompt = f"Generate a GAAP-compliant revenue recognition memo:\n{memo_input}"
    else:
        full_prompt = f"Summarize audit insights from this data:\n{memo_input}"
    if st.button("💡 Generate AI Memo"):
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a financial analyst."},
                {"role": "user", "content": full_prompt}
            ]
        )
        st.markdown("### 📄 AI Insight")
        st.markdown(response.choices[0].message.content)



# ========================= 📘 Manual Journal Entry ============================
elif section == "📘 Manual Journal Entry":
    st.header("📘 Manual Journal Entry")
    with st.form("manual_journal_form"):
        date = st.date_input("Date")
        description = st.text_input("Description")
        amount = st.number_input("Amount", value=0.0, step=0.01)

        debit_account = st.selectbox("Debit Account", df_acc["code"], format_func=lambda x: df_acc[df_acc["code"] == x]["label"].values[0])
        credit_account = st.selectbox("Credit Account", df_acc["code"], index=1, format_func=lambda x: df_acc[df_acc["code"] == x]["label"].values[0])

        submitted = st.form_submit_button("Submit Journal Entry")
        if submitted:
            if debit_account == credit_account:
                st.error("⚠ Debit and credit accounts must be different.")
            elif amount <= 0:
                st.error("⚠ Amount must be greater than 0.")
            else:
                # Create journal entries
                journals = [
                    {
                        "date": str(date),
                        "account_code": debit_account,
                        "description": description,
                        "debit": amount,
                        "credit": 0,
                        "reference": "Manual"
                    },
                    {
                        "date": str(date),
                        "account_code": credit_account,
                        "description": description,
                        "debit": 0,
                        "credit": amount,
                        "reference": "Manual"
                    }
                ]
                success = True
                for j in journals:
                    r = requests.post(f"{API_BASE}/journals", json=[j])
                    if r.status_code != 200:
                        success = False
                        st.error(f"❌ Failed to post journal: {r.text}")
                if success:
                    st.success("✅ Journal entry posted.")



# ========================= 🧠 AI Journal Assistant ============================
elif section == "🧠 AI Journal Assistant":
    st.header("🧠 AI Journal Assistant")
    
    if "gpt_entry" not in st.session_state:
        st.session_state["gpt_entry"] = None

    from openai import OpenAI
    import json

    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

    prompt = st.text_area("📝 Describe the transaction (e.g., 'Paid $500 for office rent in June')")

    coa_preview = df_acc[["code", "name", "type"]].to_string(index=False)

    ...
    
    if st.button("💡 Generate Journal Entry", key="generate_gpt"):
        with st.spinner("Asking GPT..."):
            try:
                response = client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": f"""YYou are a professional accountant working with a structured Chart of Accounts.

Below is the Chart of Accounts used in this accounting system:

{coa_preview}

Your task is to convert natural-language transactions into proper double-entry journal entries using only the accounts provided.

### Accounting Guidelines:

- Revenue accounts should appear on the **credit side**
- Expense and COGS accounts should appear on the **debit side**
- Asset accounts (like cash, bank) are typically debited when increased
- Liability accounts (like payables) are typically credited when increased
- Use valid account codes only from the chart above
- Always match accounts to their intended use and type

### Output Format:

Return your answer in **raw JSON only**, using this structure:
{{
  "date": "YYYY-MM-DD",
  "description": "string",
  "debit_account_code": "account_code",
  "credit_account_code": "account_code",
  "amount": float,
  "reference": "AI-GPT"
}}

Avoid any explanation — return JSON only.
"""
                        },
                        {"role": "user", "content": prompt}
                        ],
                    temperature=0.3
                        )
                suggestion = response.choices[0].message.content.strip("` \n")
                
                try:
                    parsed = json.loads(suggestion)
                    st.session_state["gpt_entry"] = parsed
                except json.JSONDecodeError as e:
                    st.error("❌ GPT response is not valid JSON")
                    st.write("🚫 Error:", e)
                    st.code(suggestion, language="json")
                    st.stop()
                
                st.subheader("📑 GPT Suggested Entry")
                st.json(parsed)

            except Exception as e:
                st.error("❌ GPT failed")
                st.exception(e)


        # Show the form only if a GPT entry exists
    if st.session_state.get("gpt_entry"):
        parsed = st.session_state["gpt_entry"]

        with st.form("post_gpt_entry_form"):
            submit_gpt = st.form_submit_button("✅ Post Suggested Entry")
            if submit_gpt:
                journals = [
                    {
                        "date": parsed["date"],
                        "account_code": str(parsed["debit_account_code"]),
                        "description": parsed["description"],
                        "debit": parsed["amount"],
                        "credit": 0,
                        "reference": parsed["reference"]
                      },
                ]
                for j in journals:
                    r = requests.post(f"{API_BASE}/journals", json=[j])
                    st.write("📤 POST:", j)
                    st.write("🔍 Response:", r.status_code, r.text)

                st.success("✅ GPT journal entry posted.")
                st.session_state["gpt_entry"] = None  # ✅ Prevent auto re-posting



    st.markdown("---")
    st.subheader("📝 Manual Journal Entry (Always Available)")

    df_acc["code"] = df_acc["code"].astype(str)
    df_acc["label"] = df_acc["code"] + " - " + df_acc["name"]
    label_list = df_acc["label"].tolist()

    with st.form("manual_form_ai_tab"):
        j_date = st.date_input("Manual Date")
        j_desc = st.text_input("Manual Description")
        j_amt = st.number_input("Manual Amount", value=0.0, step=0.01)

        debit_label = st.selectbox("Manual Debit Account", label_list)
        credit_label = st.selectbox("Manual Credit Account", label_list)

        debit_code = df_acc[df_acc["label"] == debit_label]["code"].values[0]
        credit_code = df_acc[df_acc["label"] == credit_label]["code"].values[0]

        submit_manual = st.form_submit_button("✅ Post Manual Entry")

        if submit_manual:
            journals = [
                {
                    "date": str(j_date),
                    "account_code": debit_code,
                    "description": j_desc,
                    "debit": j_amt,
                    "credit": 0,
                    "reference": "AI-MANUAL"
                },
            ]
            for j in journals:
                st.write("📤 Posting payload:", j)
                r = requests.post(f"{API_BASE}/journals", json=[j])
                st.write("🔍 POST response:", r.status_code, r.text)
            st.success("✅ Manual journal entry posted.")
