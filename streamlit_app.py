import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import concurrent.futures # ตัวช่วยโหลดพร้อมกัน
import time

st.set_page_config(page_title="CS Turbo Search", layout="wide")
st.title("🚀 ระบบค้นหา (V 2.0)")

@st.cache_resource
def get_config():
    try:
        conf = dict(st.secrets["gcp_service_account"])
        conf["private_key"] = conf["private_key"].replace("\\n", "\n")
        return conf
    except Exception as e:
        return None

config = get_config()

# ฟังก์ชันดึงข้อมูล 1 แท็บ (แบบเดี่ยว)
def fetch_worksheet(ws):
    raw = ws.get_all_values()
    if raw:
        df = pd.DataFrame(raw)
        df.columns = df.iloc[0]
        return ws.title, df[1:].reset_index(drop=True)
    return ws.title, pd.DataFrame()

# ฟังก์ชันโหลดทุกแท็บพร้อมกัน (Parallel)
@st.cache_data(ttl=1800)
def load_all_data_parallel(file_id, _config):
    scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    creds = Credentials.from_service_account_info(_config, scopes=scopes)
    client = gspread.authorize(creds)
    sh = client.open_by_key(file_id)
    worksheets = sh.worksheets()
    
    all_data = {}
    with st.spinner(f"🚀 กำลังเร่งสปีดดึงข้อมูลจาก {len(worksheets)} แท็บพร้อมกัน..."):
        # ใช้ ThreadPoolExecutor เพื่อโหลดข้อมูลแบบขนาน
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            results = list(executor.map(fetch_worksheet, worksheets))
            for title, df in results:
                all_data[title] = df
    return all_data

if config:
    try:
        scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        creds = Credentials.from_service_account_info(config, scopes=scopes)
        client = gspread.authorize(creds)
        
        all_files = client.openall()
        file_map = {f.title: f.id for f in all_files}
        
        st.sidebar.header("⚙️ เมนูควบคุม")
        selected_file_name = st.sidebar.selectbox("เลือกไฟล์:", list(file_map.keys()))
        
        if st.sidebar.button("🔄 ล้างค่าแล้วโหลดใหม่"):
            st.cache_data.clear()
            st.rerun()

        # เริ่มโหลดข้อมูลแบบขนาน
        data = load_all_data_parallel(file_map[selected_file_name], config)

        search_query = st.text_input("🔍 ใส่ ID เพื่อค้นหาทันที:", placeholder="เช่น 14833323")

        if search_query:
            st.markdown(f"🔍 ผลการค้นหาสำหรับ: `{search_query}`")
            found_count = 0
            
            # ค้นหาในหน่วยความจำ (เร็วมาก)
            for tab_name, df in data.items():
                if df.empty: continue
                # ค้นหาแบบ Vectorized (เร็วกว่าวนลูปธรรมดา)
                mask = df.astype(str).apply(lambda x: x.str.contains(search_query, case=False, na=False)).any(axis=1)
                result = df[mask]

                if not result.empty:
                    found_count += 1
                    with st.expander(f"✅ พบในแท็บ: {tab_name}", expanded=True):
                        st.dataframe(result, use_container_width=True)
            
            if found_count == 0:
                st.warning(f"❌ ไม่พบข้อมูล '{search_query}'")
        else:
            st.info(f"💡 โหลดข้อมูล {len(data)} แท็บเรียบร้อย! พิมพ์ ID ด้านบนเพื่อค้นหาได้เลยครับ")

    except Exception as e:
        st.error(f"เกิดข้อผิดพลาด: {e}")
