import streamlit as st
import pandas as pd
import csv
from datetime import datetime

# ==========================================
# 🎨 1. MASTER PAGE SETUP
# ==========================================
st.set_page_config(page_title="Tally Automation Suite", page_icon="⚙️", layout="wide")

# Constants jo sab jagah use honge
SUSPENSE_LEDGER = "Suspense A/c"
LEDGER_CASH = "Cash"
LEDGER_CARD = "Card"       
LEDGER_NBH  = "NBH"         
LEDGER_ONLINE = "Online"
MY_BANK_LEDGER = "HDFC Bank a/c"

# ==========================================
# 🛠️ HELPER FUNCTIONS
# ==========================================
def escape_xml(text):
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def parse_amount(val):
    try:
        if val is None or val == '': return 0.0
        cleaned_val = str(val).replace(',', '').replace('"', '').strip()
        return float(cleaned_val) if cleaned_val else 0.0
    except ValueError:
        return 0.0

def get_ledger_xml(l_name, is_deb, amt):
    is_deem = "Yes" if is_deb else "No"
    t_amt = f"-{amt}" if is_deb else f"{amt}"
    return f"<ALLLEDGERENTRIES.LIST><LEDGERNAME>{l_name}</LEDGERNAME><ISDEEMEDPOSITIVE>{is_deem}</ISDEEMEDPOSITIVE><AMOUNT>{t_amt}</AMOUNT></ALLLEDGERENTRIES.LIST>"

# ==========================================
# 🔒 2. PASSWORD LOCK SYSTEM
# ==========================================
def check_password():
    def password_entered():
        if st.session_state["password"] == "23051987":
            st.session_state["password_correct"] = True
            del st.session_state["password"] 
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.markdown("<br><br><h2 style='text-align: center; color: #D84315;'>🔒 Tally Automation Suite Locked</h2>", unsafe_allow_html=True)
        st.text_input("Software Unlock karne ke liye Password daalein", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.markdown("<br><br><h2 style='text-align: center; color: #D84315;'>🔒 Tally Automation Suite Locked</h2>", unsafe_allow_html=True)
        st.text_input("Software Unlock karne ke liye Password daalein", type="password", on_change=password_entered, key="password")
        st.error("❌ Galat Password! Kripya sahi password dalein.")
        return False
    return True

# ==========================================
# 🚀 3. MAIN SOFTWARE EXECUTION
# ==========================================
if check_password():

    st.sidebar.markdown("## ⚙️ Main Menu")
    app_mode = st.sidebar.radio(
        "Kaunsa Tool Use Karna Hai?",
        ["📊 Daily Collection", "🏦 HDFC Bank Statement", "🏢 Monthly Billing Engine"]
    )
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 👨‍💻 Developed By")
    st.sidebar.info("**Yogesh Sharma**\n\nAutomation Expert\nContact: +91 8882516300")

    # =========================================================================
    # 📊 TOOL 1: DAILY COLLECTION
    # =========================================================================
    if app_mode == "📊 Daily Collection":
        st.markdown("<h1 style='text-align: center; color: #1E88E5;'>📊 Daily Collection Entry</h1>", unsafe_allow_html=True)
        st.markdown("---")
        
        col1, col2 = st.columns([1, 2])
        with col1:
            master_file = st.file_uploader("1. Master Ledgers (CSV)", type=['csv'], key="daily_master")
            data_file = st.file_uploader("2. Daily Collection (Excel/CSV)", type=['xlsx', 'xls', 'csv'], key="daily_data")
            
        with col2:
            if master_file and data_file:
                try:
                    master_df = pd.read_csv(master_file, encoding='latin1')
                    master_list = master_df.iloc[:, 0].dropna().astype(str).str.strip().tolist()
                    st.success(f"✔️ {len(master_list)} Ledgers Loaded!")
                except Exception as e:
                    st.error(f"❌ ERROR: Master file padhne mein dikkat aayi: {e}")
                    st.stop()

                def find_best_ledger_daily(search_string):
                    if not search_string: return SUSPENSE_LEDGER
                    search_upper = str(search_string).upper().strip()
                    for full_name in master_list:
                        if search_upper in full_name.upper(): return full_name 
                    return None 

                if st.button("🚀 Process Daily Collection & Generate XML", use_container_width=True):
                    with st.spinner('Data process ho raha hai...'):
                        try:
                            if data_file.name.lower().endswith('.csv'):
                                raw_df = pd.read_csv(data_file, encoding='latin1', header=None)
                            else:
                                raw_df = pd.read_excel(data_file, header=None)
                                
                            header_row_idx = None
                            for idx, row in raw_df.iterrows():
                                row_str = " ".join(row.fillna('').astype(str).str.lower())
                                if 'date' in row_str and ('flat' in row_str or 'name' in row_str):
                                    header_row_idx = idx
                                    break
                                    
                            if header_row_idx is None:
                                st.error("❌ Error: File mein headings theek se detect nahi hui.")
                                st.stop()
                                
                            df = raw_df.iloc[header_row_idx+1:].copy()
                            df.columns = raw_df.iloc[header_row_idx].fillna('').astype(str).str.strip().str.lower()
                            
                            date_col = next((c for c in df.columns if c == 'date'), None)
                            if not date_col: date_col = next((c for c in df.columns if 'date' in c and 'cheque' not in c), None)
                            flat_col = next((c for c in df.columns if 'flat' in c), None)
                            remark_col = next((c for c in df.columns if 'remark' in c), None)
                            chq_no_col = next((c for c in df.columns if 'cheque' in c and 'no' in c), None)

                            col_cash = next((c for c in df.columns if c == 'cash'), None)
                            col_card = next((c for c in df.columns if c == 'card'), None)
                            col_nbh = next((c for c in df.columns if c == 'nbh'), None)
                            col_online = next((c for c in df.columns if 'cheque' in c and 'online' in c), None)

                            df = df.dropna(subset=[date_col])

                            xml_header = """<?xml version="1.0" encoding="utf-8"?>\n<ENVELOPE>\n<HEADER><TALLYREQUEST>Import Data</TALLYREQUEST></HEADER>\n<BODY>\n<IMPORTDATA>\n<REQUESTDESC>\n<REPORTNAME>Vouchers</REPORTNAME>\n<STATICVARIABLES><SVCURRENTCOMPANY>##SVCURRENTCOMPANY</SVCURRENTCOMPANY></STATICVARIABLES>\n</REQUESTDESC>\n<REQUESTDATA>\n"""
                            xml_content = xml_header
                            success_count = 0
                            failed_names = []

                            for index, row in df.iterrows():
                                raw_date = str(row.get(date_col, '')).strip()
                                if not raw_date or raw_date.lower() == 'nan': continue
                                    
                                try: vch_date = pd.to_datetime(raw_date, dayfirst=True).strftime('%Y%m%d')
                                except: vch_date = raw_date.replace('-', '').replace('/', '')

                                flat_no = str(row.get(flat_col, '')).strip()
                                remarks = str(row.get(remark_col, '')).strip()
                                chq_no = str(row.get(chq_no_col, '')).strip()
                                if chq_no and chq_no.lower() != 'nan': remarks = f"{remarks} [Ref: {chq_no}]".strip()

                                detected_ledger = find_best_ledger_daily(flat_no)
                                if detected_ledger is None:
                                    failed_names.append(flat_no)
                                    detected_ledger = SUSPENSE_LEDGER
                                        
                                credit_ledger = escape_xml(detected_ledger)

                                payment_map = [('CASH', col_cash, LEDGER_CASH), ('CARD', col_card, LEDGER_CARD), ('NBH', col_nbh, LEDGER_NBH), ('ONLINE', col_online, LEDGER_ONLINE)]

                                for mode_name, col_name, debit_ledger_name in payment_map:
                                    if not col_name: continue
                                    try: amount = abs(float(str(row.get(col_name, '0')).replace(',', '').strip() or 0))
                                    except: amount = 0.0

                                    if amount > 0:
                                        debit_ledger = escape_xml(debit_ledger_name)
                                        narration = escape_xml(f"Collection via {mode_name} {remarks}".strip())
                                        credit_node = get_ledger_xml(credit_ledger, False, amount)
                                        debit_node = get_ledger_xml(debit_ledger, True, amount)
                                        xml_content += f"<TALLYMESSAGE xmlns:UDF=\"TallyUDF\"><VOUCHER VCHTYPE=\"Receipt\" ACTION=\"Create\"><DATE>{vch_date}</DATE><VOUCHERTYPENAME>Receipt</VOUCHERTYPENAME><NARRATION>{narration}</NARRATION>{credit_node}{debit_node}</VOUCHER></TALLYMESSAGE>"
                                        success_count += 1

                            xml_content += """</REQUESTDATA>\n</IMPORTDATA>\n</BODY>\n</ENVELOPE>"""
                            
                            st.success(f"✅ Kaam Pura Hua! Total {success_count} Receipts ban gayi hain.")
                            st.download_button("📥 Download Daily Collection XML", data=xml_content.encode('utf-8'), file_name="tally_daily_collections.xml", mime="application/xml")
                            
                            if failed_names:
                                txt_content = "⚠️ YE FLATS NAHI MILE (Suspense A/c):\n\n" + "\n".join([f"- {n}" for n in set(failed_names)])
                                st.download_button("⚠️ Download Suspense List", data=txt_content.encode('utf-8'), file_name="daily_suspense_flats.txt", mime="text/plain")

                        except Exception as e:
                            st.error(f"❌ Gadbad hui: {e}")
            else:
                st.info("👈 Kripya Master CSV aur Daily Excel upload karein.")

    # =========================================================================
    # 🏦 TOOL 2: HDFC BANK STATEMENT
    # =========================================================================
    elif app_mode == "🏦 HDFC Bank Statement":
        st.markdown("<h1 style='text-align: center; color: #1565C0;'>🏦 HDFC Bank to Tally XML</h1>", unsafe_allow_html=True)
        st.markdown("---")
        
        CARD_KEYWORDS = ["CARD", "POS"]
        NBH_KEYWORDS = ["NOBROKER", "NBH", "SETTLEMENT"]
        OTHER_SITE_KEYWORDS = ["VIVISH"]
        OTHER_SITE_LEDGER = "Other Site Settlement A/c"

        col1, col2 = st.columns([1, 2])
        with col1:
            master_file = st.file_uploader("1. Master Ledgers (CSV)", type=['csv'], key="hdfc_master")
            data_file = st.file_uploader("2. HDFC Statement", type=['xlsx', 'xls', 'csv'], key="hdfc_data")
            
        with col2:
            if master_file and data_file:
                try:
                    master_df = pd.read_csv(master_file, encoding='latin1')
                    master_list = master_df.iloc[:, 0].dropna().astype(str).str.strip().tolist()
                    st.success(f"✔️ {len(master_list)} Ledgers Loaded!")
                except Exception as e:
                    st.error(f"❌ ERROR: Master file error: {e}")
                    st.stop()

                def find_best_ledger_hdfc(narration_text):
                    if not narration_text: return SUSPENSE_LEDGER
                    text_upper = str(narration_text).upper().strip()
                    for keyword in CARD_KEYWORDS:
                        if keyword in text_upper: return LEDGER_CARD
                    for keyword in NBH_KEYWORDS:
                        if keyword in text_upper: return LEDGER_NBH
                    for keyword in OTHER_SITE_KEYWORDS:
                        if keyword in text_upper: return OTHER_SITE_LEDGER
                    for full_name in master_list:
                        if full_name.upper() in text_upper: return full_name 
                    return None 

                if st.button("🚀 Process HDFC Statement & Generate XML", use_container_width=True):
                    with st.spinner('Bank Data process ho raha hai...'):
                        try:
                            if data_file.name.lower().endswith('.csv'): raw_df = pd.read_csv(data_file, encoding='latin1', header=None)
                            else: raw_df = pd.read_excel(data_file, header=None)
                                
                            header_row_idx = None
                            for idx, row in raw_df.iterrows():
                                if 'narration' in " ".join(row.fillna('').astype(str).str.lower()) and 'date' in " ".join(row.fillna('').astype(str).str.lower()):
                                    header_row_idx = idx
                                    break
                                    
                            if header_row_idx is None:
                                st.error("❌ Error: File mein headings nahi mili.")
                                st.stop()
                                
                            df = raw_df.iloc[header_row_idx+1:].copy()
                            df.columns = raw_df.iloc[header_row_idx].fillna('').astype(str).str.strip().str.lower()
                            
                            date_col = next((c for c in df.columns if c == 'date'), None)
                            narration_col = next((c for c in df.columns if 'narration' in c), None)
                            chq_col = next((c for c in df.columns if 'chq' in c or 'ref' in c), None)
                            withdraw_col = next((c for c in df.columns if 'withdraw' in c), None)
                            deposit_col = next((c for c in df.columns if 'deposit' in c), None)

                            df = df.dropna(subset=[date_col])

                            xml_header = """<?xml version="1.0" encoding="utf-8"?>\n<ENVELOPE>\n<HEADER><TALLYREQUEST>Import Data</TALLYREQUEST></HEADER>\n<BODY>\n<IMPORTDATA>\n<REQUESTDESC>\n<REPORTNAME>Vouchers</REPORTNAME>\n<STATICVARIABLES><SVCURRENTCOMPANY>##SVCURRENTCOMPANY</SVCURRENTCOMPANY></STATICVARIABLES>\n</REQUESTDESC>\n<REQUESTDATA>\n"""
                            xml_content = xml_header
                            success_count = 0
                            card_count = 0
                            failed_names = []

                            for index, row in df.iterrows():
                                raw_date = str(row.get(date_col, '')).strip()
                                if not raw_date or raw_date.lower() == 'nan': continue
                                try: vch_date = pd.to_datetime(raw_date, dayfirst=True).strftime('%Y%m%d')
                                except: vch_date = raw_date.replace('-', '').replace('/', '')

                                base_narration = str(row.get(narration_col, '')).strip()
                                inst_no = str(row.get(chq_col, '')).strip().replace('.0', '') if chq_col else ''
                                
                                try: withdraw_amt = float(str(row.get(withdraw_col, '0')).replace(',', '').strip() or 0)
                                except: withdraw_amt = 0.0
                                try: deposit_amt = float(str(row.get(deposit_col, '0')).replace(',', '').strip() or 0)
                                except: deposit_amt = 0.0

                                if deposit_amt == 0 and withdraw_amt == 0: continue

                                detected_ledger = find_best_ledger_hdfc(base_narration)
                                if detected_ledger is None:
                                    failed_names.append(base_narration)
                                    detected_ledger = SUSPENSE_LEDGER

                                if detected_ledger in [OTHER_SITE_LEDGER, LEDGER_NBH, LEDGER_CARD]:
                                    vch_type = 'Contra'
                                    if detected_ledger == LEDGER_CARD: card_count += 1
                                else:
                                    vch_type = 'Receipt' if deposit_amt > 0 else 'Payment'

                                debit_ledger = escape_xml(MY_BANK_LEDGER if deposit_amt > 0 else detected_ledger)
                                credit_ledger = escape_xml(detected_ledger if deposit_amt > 0 else MY_BANK_LEDGER)
                                final_amount = deposit_amt if deposit_amt > 0 else withdraw_amt
                                narration_safe = escape_xml(f"[Ref: {inst_no}] {base_narration}" if inst_no and inst_no.lower() != 'nan' else base_narration)

                                debit_node = get_ledger_xml(debit_ledger, True, final_amount)
                                credit_node = get_ledger_xml(credit_ledger, False, final_amount)

                                xml_content += f"<TALLYMESSAGE xmlns:UDF=\"TallyUDF\"><VOUCHER VCHTYPE=\"{vch_type}\" ACTION=\"Create\"><DATE>{vch_date}</DATE><VOUCHERTYPENAME>{vch_type}</VOUCHERTYPENAME><NARRATION>{narration_safe}</NARRATION>{debit_node}{credit_node}</VOUCHER></TALLYMESSAGE>"
                                success_count += 1

                            xml_content += """</REQUESTDATA>\n</IMPORTDATA>\n</BODY>\n</ENVELOPE>"""
                            
                            st.success(f"✅ Total {success_count} Vouchers ban gaye hain. (Card Entries: {card_count})")
                            st.download_button("📥 Download HDFC Bank XML", data=xml_content.encode('utf-8'), file_name="tally_hdfc_vouchers.xml", mime="application/xml")
                            
                            if failed_names:
                                txt_content = "⚠️ YE NAAM NAHI MILE (Suspense A/c):\n\n" + "\n".join([f"- {n}" for n in set(failed_names)])
                                st.download_button("⚠️ Download Suspense List", data=txt_content.encode('utf-8'), file_name="hdfc_suspense_list.txt", mime="text/plain")

                        except Exception as e:
                            st.error(f"❌ Gadbad hui: {e}")
            else:
                st.info("👈 Kripya Master CSV aur HDFC Statement upload karein.")

    # =========================================================================
    # 🏢 TOOL 3: MONTHLY BILLING ENGINE
    # =========================================================================
    elif app_mode == "🏢 Monthly Billing Engine":
        st.markdown("<h1 style='text-align: center; color: #2E7D32;'>🏢 Society Monthly Billing</h1>", unsafe_allow_html=True)
        st.markdown("---")
        
        col1, col2 = st.columns([1, 2])
        with col1:
            master_file = st.file_uploader("1. Master Ledgers (CSV)", type=['csv'], key="bill_master")
            billing_file = st.file_uploader("2. Monthly Readings (CSV)", type=['csv'], key="bill_data")
            
            st.markdown("### Billing Settings")
            billing_month = st.text_input("Kis mahine ka bill hai?", "April 2026")
            entry_date = st.date_input("Tally Entry Date")
            date_val = entry_date.strftime("%Y%m%d")
            
            days_in_month = st.number_input("Is mahine mein total din?", min_value=1, max_value=31, value=30)
            d_col1, d_col2 = st.columns(2)
            with d_col1: days_old_rate = st.number_input("Purana Rate Din", min_value=0, max_value=31, value=0)
            with d_col2: days_new_rate = st.number_input("Naya Rate Din", min_value=0, max_value=31, value=30)
            
            if (days_old_rate + days_new_rate) != days_in_month:
                st.warning("⚠️ Din match nahi kar rahe!")
            
        with col2:
            if master_file and billing_file:
                try:
                    master_df = pd.read_csv(master_file, encoding='latin1')
                    master_list = master_df.iloc[:, 0].dropna().astype(str).str.strip().tolist()
                    st.success(f"✔️ {len(master_list)} Master Ledgers Loaded!")
                except Exception as e:
                    st.error(f"❌ ERROR: Master file error: {e}")
                    st.stop()

                def find_best_ledger_bill(flat_no):
                    if not flat_no: return SUSPENSE_LEDGER
                    search_upper = str(flat_no).upper().strip()
                    for full_name in master_list:
                        if search_upper in full_name.upper(): return full_name 
                    return None 

                if st.button("🚀 Generate Sales Bills XML", use_container_width=True):
                    with st.spinner('Bill calculate ho rahe hain...'):
                        try:
                            decoded_file = billing_file.getvalue().decode('utf-8-sig').splitlines()
                            reader = csv.DictReader(decoded_file)
                            
                            safe_month_name = billing_month.replace(" ", "_")
                            xml_header = '''<ENVELOPE>\n <HEADER>\n  <TALLYREQUEST>Import Data</TALLYREQUEST>\n </HEADER>\n <BODY>\n  <IMPORTDATA>\n   <REQUESTDESC>\n    <REPORTNAME>Vouchers</REPORTNAME>\n    <STATICVARIABLES>\n     <SVCURRENTCOMPANY>##SVCURRENTCOMPANY</SVCURRENTCOMPANY>\n    </STATICVARIABLES>\n   </REQUESTDESC>\n   <REQUESTDATA>\n'''
                            xml_content = xml_header
                            entry_count = 0
                            failed_names = []
                            
                            for row in reader:
                                clean_row = {k.strip().lower(): str(v).strip() for k, v in row.items() if k is not None}
                                flat_no = clean_row.get('flat no.', '')
                                if not flat_no: continue
                                    
                                party_ledger = find_best_ledger_bill(flat_no)
                                if party_ledger is None:
                                    failed_names.append(flat_no)
                                    party_ledger = SUSPENSE_LEDGER
                                party_ledger = escape_xml(party_ledger)
                                
                                area = parse_amount(clean_row.get('area', 0))
                                power_backup_kva = parse_amount(clean_row.get('power backup', 0))
                                main_load_kva = parse_amount(clean_row.get('main load', 0))
                                main_prev = parse_amount(clean_row.get('main prev', 0))
                                main_curr = parse_amount(clean_row.get('main curr', 0))
                                backup_prev = parse_amount(clean_row.get('backup prev', 0))
                                backup_curr = parse_amount(clean_row.get('backup curr', 0))
                                
                                if area <= 0: continue
                                
                                monthly_cam = round((area * 1.65 * 12 / 365) * days_in_month, 2)
                                monthly_sinking = round((area * 0.05 * 12 / 365) * days_in_month, 2)
                                monthly_elec = round((area * 0.39 * 12 / 365) * days_in_month, 2)
                                monthly_gst = round((area * 0.26 * 12 / 365) * days_in_month, 2)
                                monthly_vending = round((30.00 * 12 / 365) * days_in_month, 2)
                                monthly_power_backup_fixed = round((power_backup_kva * 100 * 12 / 365) * days_in_month, 2)
                                monthly_main_load_fixed = round(((main_load_kva * 60 * 12 / 365) * days_old_rate) + ((main_load_kva * 36.69 * 12 / 365) * days_new_rate), 2)
                                
                                main_units = max(0, main_curr - main_prev)
                                backup_units = max(0, backup_curr - backup_prev)
                                monthly_main_consumption = round(main_units * 6.93, 2)
                                monthly_backup_consumption = max(0, round((backup_units * 27.49) - 100, 2))
                                
                                total_party_charge = round(monthly_cam + monthly_sinking + monthly_elec + monthly_vending + monthly_gst + monthly_power_backup_fixed + monthly_main_load_fixed + monthly_main_consumption + monthly_backup_consumption, 2)
                                
                                if total_party_charge <= 0: continue

                                d_cam = round((area * 1.65 * 12) / 365, 2)
                                d_sink = round((area * 0.05 * 12) / 365, 2)
                                d_elec = round((area * 0.39 * 12) / 365, 2)
                                d_gst = round((area * 0.26 * 12) / 365, 2)
                                d_vend = round((30.00 * 12) / 365, 2)
                                d_backup = round((power_backup_kva * 100 * 12) / 365, 2)
                                d_main = round(monthly_main_load_fixed / days_in_month, 2) if days_in_month > 0 else 0
                                total_daily = round(d_cam + d_sink + d_elec + d_gst + d_vend + d_backup + d_main, 2)

                                n_text = f"Bill for {billing_month} ({days_in_month} Days) | Area: {area} SqFt | Per Day Fixed: Rs {total_daily}. "
                                if main_units > 0: n_text += f"| Main: {int(main_units)}U @ 6.93 "
                                if backup_units > 0: n_text += f"| DG: {int(backup_units)}U @ 27.49 (-100 Adj)"
                                safe_narration = escape_xml(n_text.strip())

                                v_xml = f'''<TALLYMESSAGE xmlns:UDF="TallyUDF"><VOUCHER VCHTYPE="Sales" ACTION="Create"><DATE>{date_val}</DATE><VOUCHERTYPENAME>Sales</VOUCHERTYPENAME><NARRATION>{safe_narration}</NARRATION><PERSISTEDVIEW>Accounting Voucher View</PERSISTEDVIEW><ALLLEDGERENTRIES.LIST><LEDGERNAME>{party_ledger}</LEDGERNAME><ISDEEMEDPOSITIVE>Yes</ISDEEMEDPOSITIVE><AMOUNT>-{total_party_charge}</AMOUNT></ALLLEDGERENTRIES.LIST>'''
                                
                                incomes = [("Common Area Maintenance", monthly_cam), ("Sinking Fund", monthly_sinking), ("Common Area Electricity Charges", monthly_elec), ("Power Backup Charges", monthly_power_backup_fixed), ("Main Load Charges", monthly_main_load_fixed), ("Main Load Consumption", monthly_main_consumption), ("Power Backup Consumption", monthly_backup_consumption), ("Vending Charges", monthly_vending), ("GST Collection A/c", monthly_gst)]
                                
                                for l_name, amt in incomes:
                                    if amt > 0: v_xml += f'''<ALLLEDGERENTRIES.LIST><LEDGERNAME>{escape_xml(l_name)}</LEDGERNAME><ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE><AMOUNT>{amt}</AMOUNT></ALLLEDGERENTRIES.LIST>'''
                                
                                v_xml += '''</VOUCHER></TALLYMESSAGE>\n'''
                                xml_content += v_xml
                                entry_count += 1
                                
                            xml_content += """</REQUESTDATA>\n</IMPORTDATA>\n</BODY>\n</ENVELOPE>"""
                            
                            st.success(f"✅ Total {entry_count} Flats ka Sales Invoice generate ho gaya hai.")
                            st.download_button("📥 Download Sales Bills XML", data=xml_content.encode('utf-8'), file_name=f"tally_sales_{safe_month_name}.xml", mime="application/xml")
                            
                            if failed_names:
                                txt_content = "⚠️ YE FLATS NAHI MILE (Suspense A/c):\n\n" + "\n".join([f"- Flat: {n}" for n in set(failed_names)])
                                st.download_button("⚠️ Download Suspense List", data=txt_content.encode('utf-8'), file_name="billing_suspense.txt", mime="text/plain")

                        except Exception as e:
                            st.error(f"❌ Gadbad hui: {e}")
            else:
                st.info("👈 Kripya Master CSV aur Monthly Readings upload karein.")