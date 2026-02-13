import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="CS Case Finder LIGHTNING", layout="wide")
st.title("ระบบค้นหาเคส CS")

# --- 1. เชื่อมต่อ Google Sheets ---
@st.cache_resource
def get_sheets_client():
    try:
        scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        creds = Credentials.from_service_account_file('key.json', scopes=scopes)
        return gspread.authorize(creds)
    except Exception as e:
        st.error(f"❌ กุญแจมีปัญหา: {e}")
        return None

# --- 2. โหลดข้อมูล + ค้นหาหัวตารางอัตโนมัติ ---
@st.cache_data(ttl=900) # จำข้อมูลไว้ 15 นาที
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
            
            # 🎯 ไม้ตาย: ระบบค้นหาหัวตารางที่แท้จริง
            # สแกน 20 แถวแรก หาแถวที่มีข้อมูลเยอะที่สุด (นั่นแหละคือหัวตารางของพี่)
            header_idx = 0
            max_non_empty = 0
            
            for idx in range(min(20, len(df))):
                # นับจำนวนช่องที่มีตัวหนังสือในแถวนั้น
                count = sum(1 for x in df.iloc[idx] if str(x).strip() not in ['', 'None', 'nan'])
                if count > max_non_empty:
                    max_non_empty = count
                    header_idx = idx
            
            # ดึงแถวนั้นมาทำเป็นชื่อคอลัมน์
            raw_headers = df.iloc[header_idx].astype(str).tolist()
            
            # จัดการชื่อคอลัมน์ซ้ำหรือว่างเปล่า ให้ระบบไม่ Error
            final_headers = []
            for col_idx, h in enumerate(raw_headers):
                clean_h = h.strip()
                if not clean_h or clean_h in ['None', 'nan']:
                    clean_h = f"คอลัมน์_{col_idx}"
                if clean_h in final_headers:
                    clean_h = f"{clean_h}_{col_idx}"
                final_headers.append(clean_h)
            
            df.columns = final_headers
            
            # ตัดข้อมูลส่วนที่เป็น Dashboard ด้านบนทิ้งไป เอาแต่เนื้อข้อมูลจริงๆ
            df = df.iloc[header_idx + 1 :].reset_index(drop=True)
            
            all_data[ws.title] = df
            
        return all_data
    except Exception as e:
        st.error(f"เกิดข้อผิดพลาดในการดึงข้อมูล: {e}")
        return {}

# --- 3. ส่วนค้นหาหลัก ---
if st.sidebar.button("🔄 ดึงข้อมูลล่าสุดจาก Sheets"):
    st.cache_data.clear()
    st.rerun()

with st.spinner('กำลังดึงข้อมูลทั้งหมด...'):
    master_data = load_all_data_fast()

search_val = st.text_input("🔍 กรอก ID หรือ IMEI แล้วกด Enter:")

if search_val:
    q = search_val.strip().lower()
    found_results = {}

    for title, df in master_data.items():
        if df.empty: continue
        
        # ค้นหาแบบกวาดรวดเดียวทั้งตาราง
        combined_text = df.astype(str).agg(' '.join, axis=1).str.lower()
        mask = combined_text.str.contains(q, na=False)
        res = df[mask]
        
        if not res.empty:
            found_results[title] = res

    # แสดงผล
    if found_results:
        st.success(f"✅ ค้นหาเสร็จสิ้น `{search_val}` ใน {len(found_results)} แท็บ")
        for name, res_df in found_results.items():
            st.markdown(f"### 📂 แท็บ: {name}")
            # แสดงตารางพร้อมหัวข้อจริงๆ แล้ว
            st.dataframe(res_df, use_container_width=True, hide_index=True)
            st.divider()
    else:
        st.error(f"❌ ไม่พบข้อมูล `{search_val}`")
