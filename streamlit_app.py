import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import concurrent.futures
import time

st.set_page_config(page_title="CS Search v32", layout="wide")
st.title("🚀 ระบบค้นหา CS (V3.0)")

@st.cache_resource
def get_config():
    try:
        conf = dict(st.secrets["gcp_service_account"])
        conf["private_key"] = conf["private_key"].replace("\\n", "\n")
        return conf
    except Exception:
        return None

def make_unique(labels):
    new_labels = []
    seen = {}
    for label in labels:
        clean_label = str(label).strip()
        if not clean_label or clean_label in ["30/12/1899 0:00:00", "12/30/1899"]:
            clean_label = "Column"
        if clean_label not in seen:
            new_labels.append(clean_label)
            seen[clean_label] = 1
        else:
            new_labels.append(f"{clean_label}.{seen[clean_label]}")
            seen[clean_label] += 1
    return new_labels

# ฟังก์ชันดึงข้อมูลแบบ "ค่อยเป็นค่อยไป"
def fetch_worksheet_safe(ws):
    try:
        # หน่วงเวลา 1.2 วินาทีต่อแท็บ เพื่อให้มั่นใจว่าไม่เกิน 60 ครั้ง/นาที แน่นอน
        time.sleep(1.2) 
        raw = ws.get_all_values()
        if len(raw) > 0:
            unique_headers = make_unique(raw[0])
            df = pd.DataFrame(raw[1:], columns=unique_headers)
            return ws.title, df
        return ws.title, pd.DataFrame()
    except Exception as e:
        if "429" in str(e):
            return "ERROR_QUOTA", ws.title
        return ws.title, pd.DataFrame()

@st.cache_data(ttl=3600)
def load_all_data_stable(file_id, _config):
    scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    creds = Credentials.from_service_account_info(_config, scopes=scopes)
    client = gspread.authorize(creds)
    sh = client.open_by_key(file_id)
    worksheets = sh.worksheets()
    
    all_data = {}
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # เปลี่ยนมาโหลดทีละแท็บแบบต่อเนื่อง แทนการโหลดขนานแบบแรงๆ
    for i, ws in enumerate(worksheets):
        status_text.text(f"⏳ กำลังโหลดแท็บ: {ws.title} ({i+1}/{len(worksheets)})")
        title, result = fetch_worksheet_safe(ws)
        
        if title == "ERROR_QUOTA":
            st.warning(f"⚠️ Google ขอให้พักเครื่องครู่หนึ่ง กำลังรอเพื่อดึงแท็บ '{result}' ใหม่...")
            time.sleep(10) # พัก 10 วินาทีถ้าติดโควตา
            title, result = fetch_worksheet_safe(ws)
            
        if not isinstance(result, str) and not result.empty:
            all_data[title] = result
        progress_bar.progress((i + 1) / len(worksheets))
    
    status_text.empty()
    progress_bar.empty()
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
        
        if st.sidebar.button("🔄 อัปเดตข้อมูล (Refresh)"):
            st.cache_data.clear()
            st.rerun()

        data = load_all_data_stable(file_map[selected_file_name], config)

        search_query = st.text_input("🔍 ใส่ ID เพื่อค้นหา:", placeholder="พิมพ์เลข ID ที่ต้องการหา...")

        if search_query:
            found_count = 0
            for tab_name, df in data.items():
                mask = df.astype(str).apply(lambda x: x.str.contains(search_query, case=False, na=False)).any(axis=1)
                result = df[mask]
                if not result.empty:
                    found_count += 1
                    with st.expander(f"✅ พบในแท็บ: {tab_name}", expanded=True):
                        st.dataframe(result, use_container_width=True)
            if found_count == 0:
                st.warning(f"❌ ไม่พบข้อมูล '{search_query}'")
    except Exception as e:
        st.error(f"เกิดข้อผิดพลาด: {e}")
