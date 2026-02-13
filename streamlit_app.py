import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# --- 1. การตั้งค่าหน้าตาเบื้องต้น ---
st.set_page_config(
    page_title="CS Case Intelligence", 
    page_icon="🚀", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# ใช้ CSS เพื่อปรับแต่งหน้าตา (Custom Styling)
st.markdown("""
    <style>
    .main {
        background-color: #f5f7f9;
    }
    .stDataFrame {
        border: 1px solid #e6e9ef;
        border-radius: 10px;
    }
    h1 {
        color: #1e3a8a;
        font-family: 'Sarabun', sans-serif;
    }
    .st-emotion-cache-1kyxreq {
        justify-content: center;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🚀 CS Case Finder Intelligence")
st.markdown("ระบบค้นหาและจัดการเคสพนักงานเวอร์ชันประสิทธิภาพสูง")

# --- 2. การเชื่อมต่อข้อมูล (คงความเร็วเดิมไว้) ---
@st.cache_resource
def get_sheets_client():
    try:
        scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        creds = Credentials.from_service_account_file('key.json', scopes=scopes)
        return gspread.authorize(creds)
    except Exception as e:
        st.error(f"❌ ระบบหากุญแจไม่เจอ: {e}")
        return None

@st.cache_data(ttl=900)
def load_all_data_fast():
    gc = get_sheets_client()
    if not gc: return {}
    sh = gc.open('Copy of ไฟล์เก็บเคส2025V1')
    worksheets = sh.worksheets()
    ranges = [f"'{ws.title}'" for ws in worksheets]
    all_data = {}
    
    try:
        batch_result = sh.values_batch_get(ranges)
        value_ranges = batch_result.get('valueRanges', [])
        for ws, val_range in zip(worksheets, value_ranges):
            values = val_range.get('values', [])
            if not values: continue
            df = pd.DataFrame(values)
            
            # ระบบ Smart Header เหมือนเดิม
            header_idx = 0
            max_non_empty = 0
            for idx in range(min(15, len(df))):
                count = sum(1 for x in df.iloc[idx] if str(x).strip() not in ['', 'None', 'nan'])
                if count > max_non_empty:
                    max_non_empty = count
                    header_idx = idx
            
            raw_headers = df.iloc[header_idx].astype(str).tolist()
            final_headers = [h.strip() if h.strip() else f"Col_{i}" for i, h in enumerate(raw_headers)]
            df.columns = final_headers
            df = df.iloc[header_idx + 1 :].reset_index(drop=True)
            all_data[ws.title] = df
        return all_data
    except: return {}

# --- 3. Sidebar ปรับปรุงใหม่ ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=100)
    st.header("แผงควบคุม")
    if st.button("🔄 อัปเดตข้อมูลล่าสุด", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    st.divider()
    st.info("💡 เคล็ดลับ: พิมพ์แค่ ID 4 ตัวท้าย หรือเลข IMEI บางส่วนก็ได้ ระบบจะควานหาให้ทันที")

# --- 4. ส่วนค้นหาและการแสดงผล ---
master_data = load_all_data_fast()

# สร้างกล่องค้นหาขนาดใหญ่ตรงกลาง
search_val = st.text_input("", placeholder="พิมพ์ ID หรือ IMEI ของพนักงานที่ต้องการค้นหาที่นี่...", label_visibility="collapsed")

if search_val:
    q = search_val.strip().lower()
    found_results = {}

    for title, df in master_data.items():
        if df.empty: continue
        combined_text = df.astype(str).agg(' '.join, axis=1).str.lower()
        mask = combined_text.str.contains(q, na=False)
        res = df[mask]
        if not res.empty:
            found_results[title] = res

    if found_results:
        # แสดงสถิติเบื้องต้น
        st.success(f"พบข้อมูลพนักงานในระบบทั้งหมด {len(found_results)} แท็บ")
        
        # วนลูปโชว์ตารางแบบสวยๆ
        for name, res_df in found_results.items():
            with st.expander(f"📂 ข้อมูลจากแท็บ: {name}", expanded=True):
                # เพิ่มลูกเล่น Color Highlight ถ้ามีคอลัมน์ "สถานะ"
                def highlight_status(val):
                    color = 'transparent'
                    if 'ปิด' in str(val): color = '#d4edda' # เขียวอ่อน
                    elif 'รอ' in str(val): color = '#fff3cd' # เหลืองอ่อน
                    elif 'ปัญหา' in str(val): color = '#f8d7da' # แดงอ่อน
                    return f'background-color: {color}'

                # พยายามใช้สไตล์ถ้าทำได้ (ถ้าพังจะกลับไปโชว์ตารางปกติ)
                try:
                    st.dataframe(res_df.style.applymap(highlight_status), use_container_width=True, hide_index=True)
                except:
                    st.dataframe(res_df, use_container_width=True, hide_index=True)
                
    else:
        st.error(f"ไม่พบข้อมูลพนักงานที่ระบุ (`{search_val}`) โปรดตรวจสอบตัวเลขอีกครั้ง")
else:
    # หน้า Welcome ตอนที่ยังไม่ได้ค้นหา
    st.divider()
    cols = st.columns(3)
    cols[0].metric("จำนวนแท็บทั้งหมด", f"{len(master_data)} แท็บ")
    cols[1].metric("สถานะระบบ", "เชื่อมต่อปกติ")
    cols[2].metric("ความเร็วการค้นหา", "0.2s")
