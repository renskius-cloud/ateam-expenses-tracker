import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from streamlit_gsheets import GSheetsConnection

# 1. PAGE SETUP
st.set_page_config(
    page_title="ATeam Expenses & CC Tracker",
    page_icon="💳",
    layout="wide"
)

# 2. GOOGLE SHEETS CONNECTION
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=5)
def load_data():
    cards_df = conn.read(worksheet="Cards")
    tx_df = conn.read(worksheet="Transactions")
    inst_df = conn.read(worksheet="Installments")
    try:
        daddy_df = conn.read(worksheet="Daddy")
    except Exception:
        daddy_df = pd.DataFrame(columns=["Date", "Items", "Amount", "Notes"])
    try:
        payments_df = conn.read(worksheet="Payments")
    except Exception:
        payments_df = pd.DataFrame(columns=["Month", "Year", "Card", "Status", "Timestamp"])
    return cards_df, tx_df, inst_df, daddy_df, payments_df

try:
    cards_df, tx_df, inst_df, daddy_df, payments_df = load_data()
except Exception as e:
    st.error(f"⚠️ Error loading data from Google Sheets: {e}")
    st.stop()

# 3. HELPER FUNCTIONS FOR CLEAN NUMBERS & DATES
def clean_num(val):
    if pd.isna(val):
        return 0.0
    s = str(val).replace("₱", "").replace(",", "").strip()
    try:
        return float(s)
    except:
        return 0.0

def parse_day(val):
    if pd.isna(val):
        return 1
    nums = [int(s) for s in str(val).replace("th","").replace("st","").replace("nd","").replace("rd","").split() if s.isdigit()]
    return nums[0] if nums else 1

# 4. SIDEBAR NAVIGATION
st.sidebar.title("📌 Navigation")
page = st.sidebar.radio("Go to", ["💳 Credit Cards", "📜 Daddy List"])


# ==========================================
# PAGE 1: CREDIT CARDS
# ==========================================
if page == "💳 Credit Cards":
    st.title("💳 Credit Cards Tracker")

    # --- Billing Period Selection ---
    col_m, col_y = st.columns(2)
    months_map = {
        "January": 1, "February": 2, "March": 3, "April": 4, 
        "May": 5, "June": 6, "July": 7, "August": 8, 
        "September": 9, "October": 10, "November": 11, "December": 12
    }

    with col_m:
        sel_month_name = st.selectbox("Select Billing Period Month", list(months_map.keys()), index=7) # August
        sel_month = months_map[sel_month_name]
    with col_y:
        sel_year = st.selectbox("Select Billing Period Year", [2025, 2026, 2027], index=1)

    # --- STATEMENT WINDOW & DASHBOARD COMPUTATIONS ---
    dashboard_rows = []
    
    tot_15th_ours = 0.0
    tot_15th_others = 0.0
    
    tot_30th_ours = 0.0
    tot_30th_others = 0.0

    for _, card in cards_df.iterrows():
        card_name = card.get("Card Name", "")
        pay_period = str(card.get("Pay Period", ""))
        cutoff_day = parse_day(card.get("Billing Period", 1))

        # Determine Statement Range Dates for selected Payout Month/Year
        if "15" in pay_period:
            stmt_end_month = sel_month - 1 if sel_month > 1 else 12
            stmt_end_year = sel_year if sel_month > 1 else sel_year - 1
        else:
            stmt_end_month = sel_month
            stmt_end_year = sel_year

        stmt_end_date = datetime(stmt_end_year, stmt_end_month, cutoff_day)
        
        # Statement start date is previous month's cutoff + 1 day
        prev_m = stmt_end_month - 1 if stmt_end_month > 1 else 12
        prev_y = stmt_end_year if stmt_end_month > 1 else stmt_end_year - 1
        stmt_start_date = datetime(prev_y, prev_m, cutoff_day) + timedelta(days=1)

        stmt_range_str = f"{stmt_start_date.strftime('%b %d')} – {stmt_end_date.strftime('%b %d')}"

        # 1. Sum Installments split by Owner (Ours vs Tatay/Kuya Jaypard)
        inst_ours = 0.0
        inst_others = 0.0
        
        if not inst_df.empty and "Card" in inst_df.columns:
            card_insts = inst_df[inst_df["Card"].astype(str).str.strip() == card_name.strip()]
            for _, row in card_insts.iterrows():
                m_amt = clean_num(row.get("Monthly_Payment", 0))
                owner = str(row.get("Owner", "")).strip().lower()
                
                if owner in ["tatay", "kuya jaypard"]:
                    inst_others += m_amt
                else:
                    inst_ours += m_amt

        # 2. Sum Daily Transactions in Statement Window (All Daily Txs are Ours)
        tx_sum = 0.0
        if not tx_df.empty and "Card" in tx_df.columns:
            card_txs = tx_df[tx_df["Card"].astype(str).str.strip() == card_name.strip()].copy()
            if not card_txs.empty:
                card_txs["Parsed_Date"] = pd.to_datetime(card_txs["Date"], errors="coerce")
                in_range_tx = card_txs[
                    (card_txs["Parsed_Date"] >= stmt_start_date) & 
                    (card_txs["Parsed_Date"] <= stmt_end_date + timedelta(hours=23, minutes=59))
                ]
                tx_sum = in_range_tx["Amount"].apply(clean_num).sum()

        card_total_ours = tx_sum + inst_ours
        card_total_others = inst_others
        total_card_due = card_total_ours + card_total_others

        # Accumulate period totals
        if "15" in pay_period:
            tot_15th_ours += card_total_ours
            tot_15th_others += card_total_others
        else:
            tot_30th_ours += card_total_ours
            tot_30th_others += card_total_others

        # Check Payment Status
        status = "Unpaid"
        if not payments_df.empty:
            match_pay = payments_df[
                (payments_df["Month"].astype(str) == str(sel_month)) &
                (payments_df["Year"].astype(str) == str(sel_year)) &
                (payments_df["Card"].astype(str).str.strip() == card_name.strip())
            ]
            if not match_pay.empty:
                status = match_pay.iloc[0].get("Status", "PAID")

        if total_card_due == 0:
            status = "No Due"

        dashboard_rows.append({
            "Credit Card": card_name,
            "Pay Period": pay_period,
            "Statement / Billing Range": stmt_range_str,
            "Total Amount Due": f"₱{total_card_due:,.2f}",
            "Payment Status": status
        })

    display_dashboard_df = pd.DataFrame(dashboard_rows)

    tot_15th_grand = tot_15th_ours + tot_15th_others
    tot_30th_grand = tot_30th_ours + tot_30th_others

    # --- CLICKABLE PAYOUT DUES BUTTONS WITH SPLIT METRICS ---
    st.markdown("#### 🗓️ Payout Dues Summary *(Click to view details)*")
    
    if "selected_payout" not in st.session_state:
        st.session_state.selected_payout = None

    c1, c2, c3 = st.columns([2, 2, 1])
    
    with c1:
        if st.button(f"🗓️ Due for {sel_month_name} 15th: ₱{tot_15th_grand:,.2f}", type="primary" if st.session_state.selected_payout == "15th" else "secondary", use_container_width=True):
            st.session_state.selected_payout = "15th" if st.session_state.selected_payout != "15th" else None
            
        sub_a, sub_b = st.columns(2)
        sub_a.caption(f"🏠 **Ours:** ₱{tot_15th_ours:,.2f}")
        sub_b.caption(f"🤝 **Tatay/Kuya:** ₱{tot_15th_others:,.2f}")

    with c2:
        if st.button(f"🗓️ Due for {sel_month_name} 30th: ₱{tot_30th_grand:,.2f}", type="primary" if st.session_state.selected_payout == "30th" else "secondary", use_container_width=True):
            st.session_state.selected_payout = "30th" if st.session_state.selected_payout != "30th" else None
            
        sub_c, sub_d = st.columns(2)
        sub_c.caption(f"🏠 **Ours:** ₱{tot_30th_ours:,.2f}")
        sub_d.caption(f"🤝 **Tatay/Kuya:** ₱{tot_30th_others:,.2f}")

    with c3:
        if st.button("❌ Close View", use_container_width=True):
            st.session_state.selected_payout = None

    # --- DYNAMIC BREAKDOWN DISPLAY WHEN CLICKED ---
    if st.session_state.selected_payout:
        payout_tag = st.session_state.selected_payout
        st.info(f"📋 **Showing Breakdown for {sel_month_name} {payout_tag} Payout**")
        
        selected_cards = cards_df[cards_df["Pay Period"].astype(str).str.contains(payout_tag)]["Card Name"].dropna().tolist()
        
        d1, d2 = st.columns(2)
        
        with d1:
            st.markdown(f"##### 🧾 Daily Transactions ({payout_tag} Cards)")
            if not tx_df.empty and "Card" in tx_df.columns:
                filtered_tx = tx_df[tx_df["Card"].isin(selected_cards)]
                st.dataframe(filtered_tx, use_container_width=True, hide_index=True)
            else:
                st.write("No daily transactions found.")
                
        with d2:
            st.markdown(f"##### 🔄 Monthly Installments ({payout_tag} Cards)")
            if not inst_df.empty and "Card" in inst_df.columns:
                filtered_inst = inst_df[inst_df["Card"].isin(selected_cards)]
                st.dataframe(filtered_inst, use_container_width=True, hide_index=True)
            else:
                st.write("No installments found.")

    st.divider()

    # --- CREDIT CARDS DASHBOARD TABLE ---
    st.markdown("### 📊 Credit Card Dashboard & Status")
    st.dataframe(display_dashboard_df, use_container_width=True, hide_index=True)

    st.divider()

    # --- CC ENTRY FORMS ---
    st.markdown("### 📝 Quick Entry Forms")
    t1, t2 = st.tabs(["➕ Daily Expense", "🔄 Register Installment"])
    card_opts = cards_df["Card Name"].dropna().unique().tolist() if "Card Name" in cards_df.columns else []

    with t1:
        with st.form("form_daily", clear_on_submit=True):
            f1, f2 = st.columns(2)
            d_date = f1.date_input("Date")
            d_card = f2.selectbox("Card", card_opts)
            f3, f4 = st.columns(2)
            d_cat = f3.selectbox("Category", ["Dining & Food", "Groceries", "Utilities & Bills", "Health & Medical", "Gas & Travel", "Shopping & Clothes", "Miscellaneous"])
            d_amt = f4.number_input("Amount (PHP)", min_value=0.0, step=50.0)
            d_notes = st.text_input("Notes")

            if st.form_submit_button("Save Expense", type="primary", use_container_width=True):
                new_row = pd.DataFrame([{
                    "Date": d_date.strftime("%m/%d/%Y"),
                    "Card": d_card,
                    "Category": d_cat,
                    "Amount": f"₱{d_amt:,.2f}",
                    "Notes": d_notes
                }])
                updated = pd.concat([tx_df, new_row], ignore_index=True)
                conn.update(worksheet="Transactions", data=updated)
                st.success("Expense saved successfully!")
                st.cache_data.clear()
                st.rerun()

    with t2:
        with st.form("form_inst", clear_on_submit=True):
            f1, f2 = st.columns(2)
            i_owner = f1.selectbox("Owner", ["A-Team", "Tatay", "Kuya Jaypard", "Daddy"])
            i_card = f2.selectbox("Card", card_opts, key="inst_card_sel")
            i_item = st.text_input("Item Description")
            p1, p2, p3 = st.columns(3)
            i_prin = p1.number_input("Principal (PHP)", min_value=0.0)
            i_tenor = p2.number_input("Tenor (Months)", min_value=1, value=12)
            i_monthly = p3.number_input("Monthly Payment (PHP)", min_value=0.0)
            i_start = st.date_input("Start Date")

            if st.form_submit_button("Register Installment", type="primary", use_container_width=True):
                new_inst = pd.DataFrame([{
                    "Owner": i_owner,
                    "Item": i_item,
                    "Card": i_card,
                    "Principal": f"₱{i_prin:,.2f}",
                    "Tenor": i_tenor,
                    "Monthly_Payment": f"₱{i_monthly:,.2f}",
                    "Start_Date": i_start.strftime("%m/%d/%Y")
                }])
                updated = pd.concat([inst_df, new_inst], ignore_index=True)
                conn.update(worksheet="Installments", data=updated)
                st.success("Installment registered successfully!")
                st.cache_data.clear()
                st.rerun()


# ==========================================
# PAGE 2: DADDY LIST
# ==========================================
elif page == "📜 Daddy List":
    st.title("📜 Utang ni Daddy kay Mommy Tracker")

    if not daddy_df.empty and "Amount" in daddy_df.columns:
        total_daddy_due = daddy_df["Amount"].apply(clean_num).sum()
        st.metric("Total Outstanding Balance", f"₱{total_daddy_due:,.2f}")

    st.divider()

    st.markdown("### 📋 Expenses List")
    st.dataframe(daddy_df, use_container_width=True, hide_index=True)

    st.divider()

    st.markdown("### ➕ Add Entry for Daddy")
    with st.form("form_daddy_entry", clear_on_submit=True):
        c1, c2 = st.columns(2)
        d_date = c1.date_input("Date")
        d_amt = c2.number_input("Amount (PHP)", min_value=0.0, step=50.0)
        d_item = st.text_input("Item Description / Expense")
        d_notes = st.text_input("Notes (Optional)")

        if st.form_submit_button("Save Entry", type="primary", use_container_width=True):
            new_entry = pd.DataFrame([{
                "Date": d_date.strftime("%m/%d/%Y"),
                "Items": d_item,
                "Amount": f"₱{d_amt:,.2f}",
                "Notes": d_notes
            }])
            updated = pd.concat([daddy_df, new_entry], ignore_index=True)
            conn.update(worksheet="Daddy", data=updated)
            st.success("Entry added successfully!")
            st.cache_data.clear()
            st.rerun()
