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

# --- BRIGHT FROSTED WHITE GLASS CSS INJECTION ---
bg_img_url = "https://lh3.googleusercontent.com/d/1qDaExmKTO9-0ZBF5thIM2EA0eTrSd6Zd"

st.markdown(f"""
    <style>
    /* 1. Main Page Bright Background */
    .stApp {{
        background: url("{bg_img_url}");
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        background-attachment: fixed;
    }}

    /* 2. Global Text Color Override - Sharp Navy/Black */
    .stApp, .stApp p, .stApp span, .stApp label, .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5, .stApp h6, .stApp td, .stApp th {{
        color: #FFFFFF !important;
    }}

    /* 3. Frosted White Sidebar */
    [data-testid="stSidebar"] {{
        background-color: rgba(255, 255, 255, 0.55) !important;
        backdrop-filter: blur(16px) saturate(180%) !important;
        -webkit-backdrop-filter: blur(16px) saturate(180%) !important;
        border-right: 1px solid rgba(255, 255, 255, 0.4) !important;
    }}

    /* 4. Frosted White Glass Outer Containers */
    div[data-testid="stForm"], 
    .stAlert, 
    div[data-testid="stExpander"] {{
        background-color: rgba(255, 255, 255, 0.88) !important;
        backdrop-filter: blur(16px) !important;
        -webkit-backdrop-filter: blur(16px) !important;
        border-radius: 12px !important;
        border: 1px solid rgba(255, 255, 255, 0.8) !important;
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.12) !important;
        padding: 12px !important;
    }}

    /* Expander Header Light Styling (Fixes Black Header Bar) */
    div[data-testid="stExpander"] details summary {{
        background-color: rgba(255, 255, 255, 0.9) !important;
        color: #0F172A !important;
        border-radius: 8px !important;
    }}

    /* 5. Custom Light Frosted Glass HTML Table Styling */
    .glass-table {{
        width: 100%;
        border-collapse: separate;
        border-spacing: 0;
        background-color: rgba(255, 255, 255, 0.88) !important;
        backdrop-filter: blur(16px) !important;
        -webkit-backdrop-filter: blur(16px) !important;
        border-radius: 12px !important;
        border: 1px solid rgba(255, 255, 255, 0.8) !important;
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.12) !important;
        overflow: hidden;
        margin-bottom: 20px;
    }}

    .glass-table th {{
        background-color: rgba(255, 255, 255, 0.95) !important;
        color: #0F172A !important;
        font-weight: 700 !important;
        padding: 12px 16px !important;
        text-align: left !important;
        border-bottom: 2px solid rgba(203, 213, 225, 0.8) !important;
    }}

    .glass-table td {{
        padding: 10px 16px !important;
        color: #0F172A !important;
        border-bottom: 1px solid rgba(226, 232, 240, 0.6) !important;
        background: transparent !important;
    }}

    .glass-table tr:hover td {{
        background-color: rgba(255, 255, 255, 0.5) !important;
    }}

    /* 6. STREAMLIT TABS FROSTED GLASS BAR */
    div[data-baseweb="tab-list"] {{
        background-color: rgba(255, 255, 255, 0.85) !important;
        backdrop-filter: blur(12px) !important;
        -webkit-backdrop-filter: blur(12px) !important;
        border-radius: 12px !important;
        padding: 6px 10px !important;
        border: 1px solid rgba(255, 255, 255, 0.9) !important;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08) !important;
        gap: 8px !important;
        margin-bottom: 12px !important;
    }}

    button[data-baseweb="tab"] {{
        background-color: transparent !important;
        border-radius: 8px !important;
        padding: 8px 16px !important;
        border: none !important;
    }}

    button[data-baseweb="tab"] p, 
    button[data-baseweb="tab"] span {{
        color: #0F172A !important;
        font-weight: 700 !important;
        font-size: 0.98rem !important;
    }}

    /* Selected Active Tab */
    button[aria-selected="true"] {{
        background-color: #2563EB !important;
    }}

    button[aria-selected="true"] p, 
    button[aria-selected="true"] span {{
        color: #FFFFFF !important;
    }}

    /* 7. Frosted White Glass Buttons */
    button {{
        background-color: rgba(255, 255, 255, 0.85) !important;
        backdrop-filter: blur(10px) !important;
        -webkit-backdrop-filter: blur(10px) !important;
        color: #0F172A !important;
        border: 1px solid rgba(255, 255, 255, 0.9) !important;
        border-radius: 10px !important;
        font-weight: 700 !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08) !important;
    }}

    button[type="primary"], button[data-testid="baseButton-primary"] {{
        background-color: #2563EB !important;
        color: #FFFFFF !important;
        font-weight: 700 !important;
        border: none !important;
    }}

    /* 8. Sub-caption Texts under Buttons (Bold & Dark) */
    div[data-testid="stCaptionContainer"] p, 
    div[data-testid="stCaptionContainer"] span,
    .stCaption {{
        color: #FFFFFF !important;
        font-weight: 800 !important;
        font-size: 0.92rem !important;
        text-shadow: 0px 0px 6px rgba(255, 255, 255, 0.9) !important;
    }}

    /* 9. Input Fields & Dropdowns */
    input, select, textarea, div[role="combobox"] {{
        background-color: rgba(255, 255, 255, 0.95) !important;
        border-radius: 8px !important;
        border: 1px solid #CBD5E1 !important;
        color: #0F172A !important;
    }}
    </style>
""", unsafe_allow_html=True)

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

# 3. HELPER FUNCTIONS FOR CLEAN NUMBERS, DATES & STRINGS
def clean_num(val):
    if pd.isna(val):
        return 0.0
    s = str(val).replace("₱", "").replace(",", "").strip()
    try:
        return float(s)
    except:
        return 0.0

def fmt_peso(val):
    """Formats any number into ₱1,234.56 string format."""
    num = clean_num(val)
    return f"₱{num:,.2f}"

def clean_int_str(val):
    """Normalizes '8.0', '8', 8, or ' 8 ' into clean string '8'."""
    if pd.isna(val):
        return ""
    try:
        return str(int(float(val)))
    except:
        return str(val).strip()

def render_glass_table(df):
    """Renders a pandas DataFrame as a pure HTML white frosted glass table."""
    if df.empty:
        st.write("No data available.")
        return
    html = df.to_html(classes="glass-table", index=False, escape=False)
    st.markdown(html, unsafe_allow_html=True)

def parse_day(val):
    if pd.isna(val):
        return 1
    nums = [int(s) for s in str(val).replace("th","").replace("st","").replace("nd","").replace("rd","").split() if s.isdigit()]
    return nums[0] if nums else 1

def calculate_tenor_progress(start_date_str, tenor_total, sel_month, sel_year):
    if pd.isna(start_date_str) or not start_date_str:
        return True, f"1/{tenor_total}"
    try:
        dt = pd.to_datetime(start_date_str, format="mixed", dayfirst=False, errors="coerce")
        if pd.isna(dt):
            return True, f"1/{tenor_total}"
        
        start_m = dt.month
        start_y = dt.year
        
        elapsed_months = (sel_year - start_y) * 12 + (sel_month - start_m) + 1
        
        if elapsed_months < 1:
            return False, f"0/{tenor_total}"
        elif elapsed_months > tenor_total:
            return False, f"Completed ({tenor_total}/{tenor_total})"
        else:
            return True, f"{elapsed_months}/{tenor_total}"
    except:
        return True, f"1/{tenor_total}"

# 4. SIDEBAR NAVIGATION
st.sidebar.title("📌 Navigation")
page = st.sidebar.radio("Go to", ["💳 Credit Cards", "📜 Daddy List"])


# ==========================================
# PAGE 1: CREDIT CARDS
# ==========================================
if page == "💳 Credit Cards":
    st.title("💳 A-Team CC Tracker")

    # --- Billing Period Selection ---
    col_m, col_y = st.columns(2)
    months_map = {
        "January": 1, "February": 2, "March": 3, "April": 4, 
        "May": 5, "June": 6, "July": 7, "August": 8, 
        "September": 9, "October": 10, "November": 11, "December": 12
    }

    with col_m:
        sel_month_name = st.selectbox("Select Billing Period Month", list(months_map.keys()), index=7) # August default
        sel_month = months_map[sel_month_name]
    with col_y:
        sel_year = st.selectbox("Select Billing Period Year", [2025, 2026, 2027], index=1)

    # --- STATEMENT WINDOW & DASHBOARD COMPUTATIONS ---
    dashboard_rows = []
    card_windows = {}
    
    tot_15th_tx = 0.0
    tot_15th_inst_ours = 0.0
    tot_15th_inst_others = 0.0
    
    tot_30th_tx = 0.0
    tot_30th_inst_ours = 0.0
    tot_30th_inst_others = 0.0

    for _, card in cards_df.iterrows():
        card_name = str(card.get("Card Name", "")).strip()
        pay_period = str(card.get("Pay Period", ""))
        cutoff_day = parse_day(card.get("Billing Period", 1))

        if "15" in pay_period:
            stmt_end_month = sel_month - 1 if sel_month > 1 else 12
            stmt_end_year = sel_year if sel_month > 1 else sel_year - 1
        else:
            stmt_end_month = sel_month
            stmt_end_year = sel_year

        stmt_end_date = datetime(stmt_end_year, stmt_end_month, cutoff_day)
        
        prev_m = stmt_end_month - 1 if stmt_end_month > 1 else 12
        prev_y = stmt_end_year if stmt_end_month > 1 else stmt_end_year - 1
        stmt_start_date = datetime(prev_y, prev_m, cutoff_day) + timedelta(days=1)

        card_windows[card_name] = (stmt_start_date, stmt_end_date)
        stmt_range_str = f"{stmt_start_date.strftime('%b %d')} – {stmt_end_date.strftime('%b %d')}"

        # 1. Sum ACTIVE Installments split by Owner
        inst_ours = 0.0
        inst_others = 0.0
        
        if not inst_df.empty and "Card" in inst_df.columns:
            card_insts = inst_df[inst_df["Card"].astype(str).str.strip() == card_name]
            for _, row in card_insts.iterrows():
                m_amt = clean_num(row.get("Monthly_Payment", 0))
                owner = str(row.get("Owner", "")).strip().lower()
                start_d = row.get("Start_Date", "")
                t_total = clean_num(row.get("Tenor", 1))
                
                is_active, _ = calculate_tenor_progress(start_d, int(t_total), sel_month, sel_year)
                
                if is_active:
                    if owner in ["tatay", "kuya jaypard"]:
                        inst_others += m_amt
                    else:
                        inst_ours += m_amt

        # 2. Sum Daily Transactions inside statement window
        tx_sum = 0.0
        if not tx_df.empty and "Card" in tx_df.columns:
            card_txs = tx_df[tx_df["Card"].astype(str).str.strip() == card_name].copy()
            if not card_txs.empty:
                card_txs["Parsed_Date"] = pd.to_datetime(card_txs["Date"], format="mixed", dayfirst=False, errors="coerce")
                in_range_tx = card_txs[
                    (card_txs["Parsed_Date"] >= stmt_start_date) & 
                    (card_txs["Parsed_Date"] <= stmt_end_date + timedelta(hours=23, minutes=59))
                ]
                tx_sum = in_range_tx["Amount"].apply(clean_num).sum()

        total_card_due = tx_sum + inst_ours + inst_others

        if "15" in pay_period:
            tot_15th_tx += tx_sum
            tot_15th_inst_ours += inst_ours
            tot_15th_inst_others += inst_others
        else:
            tot_30th_tx += tx_sum
            tot_30th_inst_ours += inst_ours
            tot_30th_inst_others += inst_others

        # Check Payment Status (With Clean Normalized Integers)
        status = "Unpaid"
        if not payments_df.empty and "Card" in payments_df.columns:
            pay_copy = payments_df.copy()
            pay_copy["Card_Clean"] = pay_copy["Card"].astype(str).str.strip()
            pay_copy["Month_Clean"] = pay_copy["Month"].apply(clean_int_str)
            pay_copy["Year_Clean"] = pay_copy["Year"].apply(clean_int_str)

            target_m = clean_int_str(sel_month)
            target_y = clean_int_str(sel_year)

            match_pay = pay_copy[
                (pay_copy["Month_Clean"] == target_m) &
                (pay_copy["Year_Clean"] == target_y) &
                (pay_copy["Card_Clean"] == card_name)
            ]
            if not match_pay.empty:
                status = str(match_pay.iloc[-1].get("Status", "PAID")).strip()

        if total_card_due == 0:
            status = "No Due"

        dashboard_rows.append({
            "Credit Card": card_name,
            "Pay Period": pay_period,
            "Statement / Billing Range": stmt_range_str,
            "Total Amount Due": fmt_peso(total_card_due),
            "Payment Status": status
        })

    display_dashboard_df = pd.DataFrame(dashboard_rows)

    tot_15th_grand = tot_15th_tx + tot_15th_inst_ours + tot_15th_inst_others
    tot_30th_grand = tot_30th_tx + tot_30th_inst_ours + tot_30th_inst_others

    # --- CLICKABLE PAYOUT DUES BUTTONS WITH CLEAN SUB-BREAKDOWNS ---
    st.markdown("#### 🗓️ Payout Dues Summary *(Click to view tables)*")
    
    if "selected_payout" not in st.session_state:
        st.session_state.selected_payout = None

    c1, c2, c3 = st.columns([2, 2, 1])
    
    with c1:
        if st.button(f"🗓️ Due for {sel_month_name} 15th: {fmt_peso(tot_15th_grand)}", type="primary" if st.session_state.selected_payout == "15th" else "secondary", use_container_width=True):
            st.session_state.selected_payout = "15th" if st.session_state.selected_payout != "15th" else None
            
        sub_a, sub_b, sub_c = st.columns(3)
        sub_a.caption(f"🧾 **Daily:** {fmt_peso(tot_15th_tx)}")
        sub_b.caption(f"🏠 **A-Team Inst:** {fmt_peso(tot_15th_inst_ours)}")
        sub_c.caption(f"🤝 **Tatay/Kuya:** {fmt_peso(tot_15th_inst_others)}")

    with c2:
        if st.button(f"🗓️ Due for {sel_month_name} 30th: {fmt_peso(tot_30th_grand)}", type="primary" if st.session_state.selected_payout == "30th" else "secondary", use_container_width=True):
            st.session_state.selected_payout = "30th" if st.session_state.selected_payout != "30th" else None
            
        sub_d, sub_e, sub_f = st.columns(3)
        sub_d.caption(f"🧾 **Daily:** {fmt_peso(tot_30th_tx)}")
        sub_e.caption(f"🏠 **A-Team Inst:** {fmt_peso(tot_30th_inst_ours)}")
        sub_f.caption(f"🤝 **Tatay/Kuya:** {fmt_peso(tot_30th_inst_others)}")

    with c3:
        if st.button("❌ Close View", use_container_width=True):
            st.session_state.selected_payout = None

    # --- DYNAMIC BREAKDOWN DISPLAY WHEN CLICKED (TABLES ONLY) ---
    if st.session_state.selected_payout:
        payout_tag = st.session_state.selected_payout
        st.info(f"📋 **Showing Transaction & Installment Breakdown for {sel_month_name} {payout_tag} Payout**")
        
        payout_cards = cards_df[cards_df["Pay Period"].astype(str).str.contains(payout_tag)]["Card Name"].dropna().str.strip().tolist()
        
        # Filter Daily Txs
        filtered_tx = pd.DataFrame()
        if not tx_df.empty and "Card" in tx_df.columns:
            tx_copy = tx_df.copy()
            tx_copy["Card"] = tx_copy["Card"].astype(str).str.strip()
            tx_copy["Parsed_Date"] = pd.to_datetime(tx_copy["Date"], format="mixed", dayfirst=False, errors="coerce")
            
            in_period_txs = []
            for cname in payout_cards:
                if cname in card_windows:
                    s_start, s_end = card_windows[cname]
                    match_tx = tx_copy[
                        (tx_copy["Card"] == cname) &
                        (tx_copy["Parsed_Date"] >= s_start) &
                        (tx_copy["Parsed_Date"] <= s_end + timedelta(hours=23, minutes=59))
                    ]
                    in_period_txs.append(match_tx)
            filtered_tx = pd.concat(in_period_txs, ignore_index=True) if in_period_txs else pd.DataFrame()

        # Filter & Annotate Installments with Progress
        filtered_inst = pd.DataFrame()
        if not inst_df.empty and "Card" in inst_df.columns:
            inst_copy = inst_df[inst_df["Card"].astype(str).str.strip().isin(payout_cards)].copy()
            if not inst_copy.empty:
                progress_list = []
                is_active_list = []
                for _, row in inst_copy.iterrows():
                    s_d = row.get("Start_Date", "")
                    t_tot = int(clean_num(row.get("Tenor", 1)))
                    is_act, prog_str = calculate_tenor_progress(s_d, t_tot, sel_month, sel_year)
                    progress_list.append(prog_str)
                    is_active_list.append(is_act)
                    
                inst_copy["Tenor_Progress"] = progress_list
                inst_copy["Is_Active"] = is_active_list
                
                # Filter to only show active installments
                filtered_inst = inst_copy[inst_copy["Is_Active"] == True]

        d1, d2 = st.columns(2)
        
        with d1:
            st.markdown(f"##### 🧾 Daily Purchases ({payout_tag} Cards)")
            if not filtered_tx.empty:
                display_cols = [c for c in ["Date", "Card", "Category", "Amount", "Notes"] if c in filtered_tx.columns]
                disp_tx = filtered_tx[display_cols].copy()
                if "Amount" in disp_tx.columns:
                    disp_tx["Amount"] = disp_tx["Amount"].apply(fmt_peso)
                render_glass_table(disp_tx)
            else:
                st.write("No daily transactions in this statement period.")
                
        with d2:
            st.markdown(f"##### 🔄 Monthly Installments ({payout_tag} Cards)")
            if not filtered_inst.empty:
                display_inst_cols = [c for c in ["Owner", "Item", "Card", "Monthly_Payment", "Tenor_Progress", "Start_Date"] if c in filtered_inst.columns]
                disp_inst = filtered_inst[display_inst_cols].copy()
                if "Monthly_Payment" in disp_inst.columns:
                    disp_inst["Monthly_Payment"] = disp_inst["Monthly_Payment"].apply(fmt_peso)
                render_glass_table(disp_inst)
            else:
                st.write("No active installments found for this period.")

    st.divider()

    # --- CREDIT CARDS DASHBOARD TABLE ---
    st.markdown("### 📊 Credit Card Dashboard & Status")
    render_glass_table(display_dashboard_df)

    # --- MARK AS PAID / UNPAID SECTION ---
    with st.expander("✅ Update Card Payment Status"):
        p_col1, p_col2, p_col3 = st.columns([2, 1, 1])
        card_to_pay = p_col1.selectbox("Select Card", cards_df["Card Name"].dropna().tolist())
        
        if p_col2.button("Mark as PAID", type="primary", use_container_width=True):
            new_payment = pd.DataFrame([{
                "Month": clean_int_str(sel_month),
                "Year": clean_int_str(sel_year),
                "Card": str(card_to_pay).strip(),
                "Status": "PAID",
                "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }])
            updated_payments = pd.concat([payments_df, new_payment], ignore_index=True)
            conn.update(worksheet="Payments", data=updated_payments)
            st.success(f"Marked {card_to_pay} as PAID for {sel_month_name} {sel_year}!")
            st.cache_data.clear()
            st.rerun()

        if p_col3.button("Mark as UNPAID", use_container_width=True):
            new_payment = pd.DataFrame([{
                "Month": clean_int_str(sel_month),
                "Year": clean_int_str(sel_year),
                "Card": str(card_to_pay).strip(),
                "Status": "Unpaid",
                "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }])
            updated_payments = pd.concat([payments_df, new_payment], ignore_index=True)
            conn.update(worksheet="Payments", data=updated_payments)
            st.success(f"Marked {card_to_pay} as UNPAID for {sel_month_name} {sel_year}!")
            st.cache_data.clear()
            st.rerun()

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
                    "Amount": fmt_peso(d_amt),
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
                    "Principal": fmt_peso(i_prin),
                    "Tenor": i_tenor,
                    "Monthly_Payment": fmt_peso(i_monthly),
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
        st.metric("Total Outstanding Balance", fmt_peso(total_daddy_due))

    st.divider()

    st.markdown("### 📋 Expenses List")
    if not daddy_df.empty:
        disp_daddy = daddy_df.copy()
        if "Amount" in disp_daddy.columns:
            disp_daddy["Amount"] = disp_daddy["Amount"].apply(fmt_peso)
        render_glass_table(disp_daddy)
    else:
        st.info("No entries found in Daddy list.")

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
                "Amount": fmt_peso(d_amt),
                "Notes": d_notes
            }])
            updated = pd.concat([daddy_df, new_entry], ignore_index=True)
            conn.update(worksheet="Daddy", data=updated)
            st.success("Entry added successfully!")
            st.cache_data.clear()
            st.rerun()
