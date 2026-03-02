import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# --- 1. การตั้งค่าหน้าจอและ CSS Premium (คงเดิมไว้ 100%) ---
st.set_page_config(page_title="CS Smart Intelligence", page_icon="💎", layout="wide")

st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(-45deg, #0f172a, #1e293b, #0f172a, #172554);
        background-size: 400% 400%;
        animation: gradient 15s ease infinite;
    }
    @keyframes gradient {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    [data-testid="stSidebar"] {
        background-color: rgba(15, 23, 42, 0.6) !important;
        backdrop-filter: blur(15px);
        border-right: 1px solid rgba(255, 255, 255, 0.1);
    }
    .stImage img {
        border-radius: 50% !important;
        border: 3px solid #3b82f6;
        box-shadow: 0 0 25px rgba(59, 130, 246, 0.5);
        object-fit: cover;
        width: 180px !important;
        height: 180px !important;
        margin: 0 auto;
        display: block;
    }
    .status-bar-ready {
        background: rgba(16, 185, 129, 0.15);
        color: #10b981;
        padding: 12px 20px;
        border-radius: 12px;
        border: 1px solid rgba(16, 185, 129, 0.4);
        margin-bottom: 25px;
        font-weight: bold;
        text-align: center;
    }
    .main-header {
        font-size: 3rem !important;
        font-weight: 800 !important;
        background: -webkit-linear-gradient(#eee, #3b82f6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. ระบบ Login (คงเดิม) ---
USER_DB = {
    "test123": {"password": "123456", "default_pic": "https://cdn-icons-png.flaticon.com/512/3135/3135715.png"},
    "admin": {"password": "123456", "default_pic": "https://cdn-icons-png.flaticon.com/512/3135/3135715.png"}
}

def login():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if not st.session_state.logged_in:
        st.markdown("<h1 style='text-align: center; color: white; padding-top: 100px;'>💎 CS INTELLIGENCE</h1>", unsafe_allow_html=True)
        cols = st.columns([1, 2, 1])
        with cols[1]:
            with st.form("login_form"):
                user = st.text_input("Username")
                pw = st.text_input("Password", type="password")
                if st.form_submit_button("AUTHENTICATE"):
                    if user in USER_DB and USER_DB[user]["password"] == pw:
                        st.session_state.logged_in = True
                        st.session_state.username = user
                        st.session_state.user_pic = USER_DB[user]["default_pic"]
                        st.rerun()
                    else:
                        st.error("❌ ข้อมูลไม่ถูกต้อง")
        return False
    return True

# --- 3. [CONFIG] ID ไฟล์ Google Sheets (คงเดิม) ---
FAQ_SHEET_ID = '1DkCgWps-wR4kaqMQp9eATV2S0uCf8nTe' 
CASE_SHEET_LIST = [
    '1x1VKAo6pRU7dtjgliSyR-aX3ZQaGeMW9PdFb2HosGbo', # ปี 2025
    '1TRTLSmr4Zh9t0aXpVg5IpiYxEAIIKy1PSCEHHIiqNdY'  # ปี 2026
]
REFUND_SHEET_ID = '1auT1zB7y9LLJ6EgIaJTjmOPQA2_HZaxhWk2qM-WZzrA'

@st.cache_resource
def get_sheets_client():
    creds = Credentials.from_service_account_file('key.json', scopes=['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive'])
    return gspread.authorize(creds)

@st.cache_data(ttl=3600)
def load_data_from_file(sheet_id):
    gc = get_sheets_client()
    try:
        sh = gc.open_by_key(sheet_id)
        all_tabs = {}
        for ws in sh.worksheets():
            data = ws.get_all_values()
            if not data: continue
            df = pd.DataFrame(data)
            header_idx = 0
            for i in range(min(15, len(df))):
                active_cells = sum(1 for val in df.iloc[i] if str(val).strip() != "")
                if active_cells > 5:
                    header_idx = i
                    break
            headers = df.iloc[header_idx].astype(str).tolist()
            processed_headers = []
            for idx, h in enumerate(headers):
                clean_name = h.strip()
                processed_headers.append(clean_name if clean_name and clean_name not in processed_headers else f"Col_{idx+1}")
            df['sheet_row'] = df.index + 1
            df.columns = processed_headers + ['sheet_row']
            all_tabs[ws.title] = df.iloc[header_idx+1:].reset_index(drop=True)
        return all_tabs
    except:
        return None

# --- 4. Main App Flow ---
if login():
    with st.sidebar:
        st.write("") 
        c1, c2, c3 = st.columns([1, 10, 1])
        with c2:
            st.image(st.session_state.user_pic, use_container_width=True)
        st.markdown(f"<h3 style='text-align: center; color: white;'>คุณ {st.session_state.username}</h3>", unsafe_allow_html=True)
        st.divider()
        app_mode = st.radio("เลือกฟังก์ชัน:", ["📋 FAQ", "🔍 CS Search", "💰 Refund Search"])
        if st.button("🔄 SYNC DATA", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
        if st.button("🚪 LOGOUT", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()

    # ตั้งค่าหัวข้อและไฟล์เป้าหมาย
    if app_mode == "📋 FAQ":
        target_id, header_text = FAQ_SHEET_ID, "FAQ"
    elif app_mode == "🔍 CS Search":
        target_id, header_text = CASE_SHEET_LIST, "CS INTELLIGENCE"
    else:
        target_id, header_text = REFUND_SHEET_ID, "REFUND TRACKER"

    st.markdown(f"<h1 class='main-header'>{header_text}</h1>", unsafe_allow_html=True)

    # โหลดข้อมูล
    master_data = {}
    with st.spinner('กำลังเชื่อมต่อฐานข้อมูล...'):
        ids = target_id if isinstance(target_id, list) else [target_id]
        for s_id in ids:
            file_data = load_data_from_file(s_id)
            if file_data:
                for tab, df in file_data.items():
                    display_name = f"{tab} ({s_id[-4:]})" if len(ids) > 1 else tab
                    master_data[display_name] = {"data": df, "file_id": s_id, "tab_real_name": tab}

    if master_data:
        st.markdown('<div class="status-bar-ready">✅ พร้อมใช้งาน</div>', unsafe_allow_html=True)
        
        # ช่องค้นหา (Search input)
        search_val = st.text_input("", placeholder=f"🔍 ค้นหาใน {app_mode}...", label_visibility="collapsed")

        found = False
        for disp, info in master_data.items():
            df = info["data"]
            
            # --- 💡 ปรับปรุงตรรกะหน้า FAQ ให้แสดงผลทันที ---
            if app_mode == "📋 FAQ":
                if search_val:
                    query = search_val.strip().lower()
                    mask = df.drop(columns=['sheet_row']).astype(str).apply(lambda r: r.str.lower().str.contains(query).any(), axis=1)
                    res = df[mask]
                else:
                    res = df # แสดงทั้งหมดถ้าไม่มีการพิมพ์ค้นหา
            else:
                # สำหรับหน้า Search และ Refund ต้องพิมพ์ก่อนถึงจะแสดงผล (เพื่อความเร็ว)
                if search_val:
                    query = search_val.strip().lower()
                    mask = df.drop(columns=['sheet_row']).astype(str).apply(lambda r: r.str.lower().str.contains(query).any(), axis=1)
                    res = df[mask]
                else:
                    res = pd.DataFrame()

            # แสดงตารางผลลัพธ์
            if not res.empty:
                found = True
                st.markdown(f"<div style='background: rgba(59,130,246,0.1); padding: 15px; border-radius: 12px; border-left: 6px solid #3b82f6; margin: 20px 0;'>📁 หมวดหมู่: <b>{disp}</b></div>", unsafe_allow_html=True)
                
                if app_mode != "📋 FAQ":
                    # ส่วนแก้ไขข้อมูล (Data Editor)
                    edit_cfg = {"sheet_row": None, "การแบน": st.column_config.SelectboxColumn("การแบน", options=["ปลด", "แบน", "รอตรวจสอบ"]), "สถานะ": st.column_config.SelectboxColumn("สถานะ", options=["ปกติ", "ไม่ปกติ", "รอดำเนินการ"])}
                    updated = st.data_editor(res, use_container_width=True, hide_index=True, column_config=edit_cfg, key=f"ed_{disp}_{search_val}")
                    
                    if st.button(f"💾 บันทึกใน {disp}", key=f"btn_{disp}"):
                        try:
                            gc = get_sheets_client()
                            ws = gc.open_by_key(info["file_id"]).worksheet(info["tab_real_name"])
                            for _, r in updated.iterrows():
                                ws.update(f"A{int(r['sheet_row'])}", [r.drop('sheet_row').astype(str).tolist()])
                            st.toast("✅ บันทึกสำเร็จ!")
                            st.cache_data.clear()
                        except Exception as e: 
                            st.error(f"❌ พลาด: {e}")
                else:
                    # หน้า FAQ แสดงผลอย่างเดียวแบบ Read-only
                    st.dataframe(res.drop(columns=['sheet_row']), use_container_width=True, hide_index=True)
        
        if search_val and not found:
            st.warning(f"❌ ไม่พบข้อมูลสำหรับ: {search_val}")
    else: 
        st.info("📡 ตรวจสอบ ID ไฟล์และการแชร์สิทธิ์ให้ Service Account")
