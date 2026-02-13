Big Query Code
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
        st.error(f"❌ KeyError: {e}")
        return None

# --- 2. โหลดข้อมูล "ทุกแท็บ" ในคำสั่งเดียว (API Call เดียว) ---
@st.cache_data(ttl=900) # จำข้อมูลไว้ 15 นาที
def load_all_data_fast():
    gc = get_sheets_client()
    if not gc: return {}
    
    sh = gc.open('Copy of ไฟล์เก็บเคส2025V1')
    worksheets = sh.worksheets()
    
    # สร้างรายชื่อแท็บทั้งหมด เพื่อส่งไปขอ Google ทีเดียว
    ranges = [f"'{ws.title}'" for ws in worksheets]
    all_data = {}
    
    try:
        # ⚡ ไม้ตายที่ 1: ดึงข้อมูลทุกแท็บพร้อมกันใน 1 คำสั่ง (ข้ามคอขวดเน็ต)
        batch_result = sh.values_batch_get(ranges)
        value_ranges = batch_result.get('valueRanges', [])
        
        # จับคู่ชื่อแท็บกับข้อมูลที่ได้มา
        for ws, val_range in zip(worksheets, value_ranges):
            values = val_range.get('values', [])
            if values:
                all_data[ws.title] = pd.DataFrame(values)
        return all_data
    except Exception as e:
        st.error(f"เกิดข้อผิดพลาดในการดึงข้อมูล: {e}")
        return {}

# --- 3. ส่วนการทำงานหลัก ---
# ปุ่มรีเฟรช เผื่อต้องการอัปเดตข้อมูลทันที
if st.sidebar.button("🔄 อัพเดทข้อมูล"):
    st.cache_data.clear()
    st.rerun()

# โหลดข้อมูลรอไว้ในแรมเลย (รอโหลดแค่ตอนเปิดแอปครั้งแรก)
with st.spinner('⚡ กำลังดูดข้อมูลทั้งหมดมาไว้ในเครื่อง (รอแค่ครั้งแรก)...'):
    master_data = load_all_data_fast()

search_val = st.text_input("🔍 กรอก ID หรือ IMEI แล้วกด Enter")

if search_val:
    q = search_val.strip().lower()
    found_results = {}

    for title, df in master_data.items():
        if df.empty: continue
        
        # ⚡ ไม้ตายที่ 2: รวบทุกคอลัมน์เป็นข้อความเดียว แล้วค้นหารวดเดียว (เร็วกว่าเดิม 100 เท่า)
        combined_text = df.astype(str).agg(' '.join, axis=1).str.lower()
        mask = combined_text.str.contains(q, na=False)
        res = df[mask]
        
        if not res.empty:
            found_results[title] = res

    # --- แสดงผลแบบเรียงต่อกัน ---
    if found_results:
        st.success(f"✅ เจอข้อมูล `{search_val}` ใน {len(found_results)} แท็บ")
        for name, res_df in found_results.items():
            st.markdown(f"### 📂 แท็บ: {name}")
            st.dataframe(res_df, use_container_width=True, hide_index=True)
            st.divider()
    else:
        st.error(f"❌ ไม่พบข้อมูล `{search_val}`")
