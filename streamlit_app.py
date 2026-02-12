import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import time

st.set_page_config(page_title="CS Ultra Search", layout="wide")
st.title("⚡ ระบบค้นหาข้อมูล CS (Speed Version 28.0)")

@st.cache_resource
def get_config():
    try:
        conf = dict(st.secrets["gcp_service_account"])
        if "\\n" in conf["private_key"]:
            conf["private_key"] = conf["private_key"].replace("\\n", "\n")
        return conf
    except Exception as e:
        return None

config = get_config()

# ฟังก์ชันโหลดข้อมูลทุกแท็บมาเก็บไว้ (ทำครั้งเดียวแล้วจำ)
@st.cache_data(ttl=1800) # จำข้อมูลไว้ 30 นาที (1800 วินาที)
def load_all_tabs_fast(file_id, _config):
    scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    creds = Credentials.from_service_account_info(_config, scopes=scopes)
    client = gspread.authorize(creds)
    sh = client.open_by_key(file_id)
    worksheets = sh.worksheets()
    
    all_data = {}
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, ws in enumerate(worksheets):
        status_text.text(f"🚀 กำลังโหลดแท็บ: {ws.title} ({i+1}/{len(worksheets)})")
        raw = ws.get_all_values()
        if raw:
            df = pd.DataFrame(raw)
            df.columns = df.iloc[0]
            all_data[ws.title] = df[1:].reset_index(drop=True)
        progress_bar.progress((i + 1) / len(worksheets))
    
    status_text.empty()
    progress_bar.empty()
    return all_data

if config:
    try:
        scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        creds = Credentials.from_service_account_info(config, scopes=scopes)
        client = gspread.authorize(creds)
        
        all_files = client.openall()
        file_map = {f.title: f.id for f in all_files}
        
        # ส่วนควบคุมที่แถบด้านข้าง
        st.sidebar.header("⚙️ ตั้งค่า")
        selected_file_name = st.sidebar.selectbox("เลือกไฟล์:", list(file_map.keys()))
        
        if st.sidebar.button("🔄 อัปเดตข้อมูลใหม่ (Refresh)"):
            st.cache_data.clear()
            st.rerun()

        # โหลดข้อมูล (จะช้าแค่ครั้งแรก ครั้งต่อไปจะเร็วมาก)
        data = load_all_tabs_fast(file_map[selected_file_name], config)

        # ช่องค้นหา (ไฮไลท์หลัก)
        search_query = st.text_input("🔍 ใส่ ID ที่ต้องการค้นหา (ค้นหาทันทีทุกแท็บ):", placeholder="พิมพ์ ID แล้วรอผลลัพธ์...")

        if search_query:
            st.markdown(f"### 📊 ผลการค้นหาสำหรับ: `{search_query}`")
            start_time = time.time()
            found_count = 0

            for tab_name, df in data.items():
                # ค้นหาใน DataFrame ที่โหลดมาแล้ว (เร็วมาก!)
                result = df[df.apply(lambda row: row.astype(str).str.contains(search_query, case=False, na=False).any(), axis=1)]

                if not result.empty:
                    found_count += 1
                    with st.expander(f"📍 แท็บ: {tab_name}", expanded=True):
                        st.dataframe(result, use_container_width=True)
            
            end_time = time.time()
            if found_count > 0:
                st.caption(f"⚡ ค้นหาเสร็จสิ้นใน {end_time - start_time:.2f} วินาที")
            else:
                st.warning(f"❌ ไม่พบข้อมูล '{search_query}'")
        else:
            st.info("💡 ข้อมูลถูกโหลดไว้ในระบบแล้ว พิมพ์ ID เพื่อค้นหาได้ทันทีครับ")

    except Exception as e:
        st.error(f"ข้อผิดพลาด: {e}")
