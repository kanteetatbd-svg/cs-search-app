import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import concurrent.futures
import time

st.set_page_config(page_title="CS Ultra Search v30", layout="wide")
st.title("🚀 ระบบค้นหา CS (V3.0)")

@st.cache_resource
def get_config():
    try:
        conf = dict(st.secrets["gcp_service_account"])
        conf["private_key"] = conf["private_key"].replace("\\n", "\n")
        return conf
    except Exception as e:
        return None

# ฟังก์ชันจัดการชื่อคอลัมน์ที่ซ้ำกัน
def make_unique(labels):
    new_labels = []
    seen = {}
    for label in labels:
        # ถ้าชื่อว่างหรือเป็นวันที่พื้นฐาน ให้ตั้งชื่อว่า Unnamed
        clean_label = str(label).strip()
        if not clean_label or clean_label == "30/12/1899 0:00:00" or clean_label == "12/30/1899":
            clean_label = "Column"
        
        if clean_label not in seen:
            new_labels.append(clean_label)
            seen[clean_label] = 1
        else:
            new_labels.append(f"{clean_label}.{seen[clean_label]}")
            seen[clean_label] += 1
    return new_labels

def fetch_worksheet(ws):
    try:
        raw = ws.get_all_values()
        if len(raw) > 1:
            # จัดการชื่อคอลัมน์ให้ไม่ซ้ำกันก่อนสร้าง DataFrame
            unique_headers = make_unique(raw[0])
            df = pd.DataFrame(raw[1:], columns=unique_headers)
            return ws.title, df
        return ws.title, pd.DataFrame()
    except Exception:
        return ws.title, pd.DataFrame()

@st.cache_data(ttl=1800)
def load_all_data_parallel(file_id, _config):
    scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    creds = Credentials.from_service_account_info(_config, scopes=scopes)
    client = gspread.authorize(creds)
    sh = client.open_by_key(file_id)
    worksheets = sh.worksheets()
    
    all_data = {}
    with st.spinner(f"🚀 กำลังรีดประสิทธิภาพจาก {len(worksheets)} แท็บ..."):
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            results = list(executor.map(fetch_worksheet, worksheets))
            for title, df in results:
                if not df.empty:
                    all_data[title] = df
    return all_data

config = get_config()

if config:
    try:
        scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        creds = Credentials.from_service_account_info(config, scopes=scopes)
        client = gspread.authorize(creds)
        
        all_files = client.openall()
        file_map = {f.title: f.id for f in all_files}
        
        st.sidebar.header("⚙️ เมนูควบคุม")
        selected_file_name = st.sidebar.selectbox("เลือกไฟล์:", list(file_map.keys()))
        
        if st.sidebar.button("🔄 อัปเดตข้อมูลใหม่"):
            st.cache_data.clear()
            st.rerun()

        data = load_all_data_parallel(file_map[selected_file_name], config)

        search_query = st.text_input("🔍 ใส่ ID เพื่อค้นหา (ค้นหาทุกแท็บ):", placeholder="เช่น 11213671")

        if search_query:
            st.markdown(f"### 📊 ผลการค้นหาสำหรับ: `{search_query}`")
            found_count = 0
            
            for tab_name, df in data.items():
                # ค้นหาในทุกคอลัมน์แบบ Case-insensitive
                mask = df.astype(str).apply(lambda x: x.str.contains(search_query, case=False, na=False)).any(axis=1)
                result = df[mask]

                if not result.empty:
                    found_count += 1
                    with st.expander(f"✅ พบในแท็บ: {tab_name}", expanded=True):
                        st.dataframe(result, use_container_width=True)
            
            if found_count == 0:
                st.warning(f"❌ ไม่พบข้อมูล '{search_query}'")
        else:
            st.info("💡 พร้อมใช้งาน! พิมพ์ ID ด้านบนเพื่อค้นหาได้เลยครับ")

    except Exception as e:
        st.error(f"เกิดข้อผิดพลาด: {e}")
