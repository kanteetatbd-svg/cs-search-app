import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# --- 1. การตั้งค่าหน้าตาให้รองรับทุกธีม ---
st.set_page_config(
    page_title="CS Case Intelligence", 
    page_icon="🚀", 
    layout="wide"
)

# ใช้ CSS เพื่อให้ตัวหนังสืออ่านออกไม่ว่าพื้นหลังจะสีอะไร
st.markdown("""
    <style>
    .stDataFrame {
        border: 1px solid #e6e9ef;
        border-radius: 10px;
    }
    /* ปรับแต่งหัวข้อให้เด่นชัด */
    h1, h3 {
        font-family: 'Sarabun', sans-serif;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🚀 CS Case Finder Intelligence")
st.caption("ระบบค้นหาเคสพนักงาน รองรับโหมดสว่าง/มืด (ปรับสีอัตโนมัติ)")

# --- 2. การเชื่อมต่อข้อมูล (คงความเร็วเทอร์โบไว้) ---
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

# --- 3. Sidebar แผงควบคุม ---
with st.sidebar:
    st.header("⚙️ แผงควบคุม")
    if st.button("🔄 ดึงข้อมูลล่าสุด", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    st.divider()
    st.markdown("**วิธีสลับโหมด:** ไปที่ปุ่ม ⋮ มุมขวาบน > Settings > Theme")

# --- 4. ส่วนค้นหาและการแสดงผล ---
master_data = load_all_data_fast()
search_val = st.text_input("🔍 กรอก ID หรือ IMEI เพื่อค้นหา:", placeholder="ระบุเลขที่ต้องการค้นหา...")

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
        st.success(f"พบข้อมูลพนักงานใน {len(found_results)} แท็บ")
        
        for name, res_df in found_results.items():
            st.markdown(f"### 📂 แท็บ: {name}")
            
            # 🎯 แก้ปัญหา "อ่านไม่ออก": ปรับสี Highlight ให้เข้มขึ้นและตัวหนังสือเป็นสีดำ
            def style_status(val):
                color = ''
                text_color = 'black' # บังคับตัวหนังสือสีดำให้อ่านง่ายเสมอ
                if 'ปิด' in str(val): color = '#90ee90' # เขียวชัดเจน
                elif 'รอ' in str(val): color = '#ffd700' # เหลืองทอง
                elif 'ปัญหา' in str(val): color = '#ffcccb' # แดงชัดเจน
                
                if color:
                    return f'background-color: {color}; color: {text_color}; font-weight: bold;'
                return ''

            # แสดงตารางแบบไม่มีสีพื้นหลังตัวตาราง (ให้ปรับตามธีม) แต่คงสี Highlight เฉพาะจุด
            try:
                st.dataframe(res_df.style.applymap(style_status), use_container_width=True, hide_index=True)
            except:
                st.dataframe(res_df, use_container_width=True, hide_index=True)
            st.divider()
                
    else:
        st.error(f"ไม่พบข้อมูลพนักงานที่ระบุ (`{search_val}`)")
