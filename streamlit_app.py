import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="CS Case Intelligence v2", page_icon="📝", layout="wide")

# --- 1. เชื่อมต่อ Google Sheets ---
@st.cache_resource
def get_sheets_client():
    try:
        scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        creds = Credentials.from_service_account_file('key.json', scopes=scopes)
        return gspread.authorize(creds)
    except Exception as e:
        st.error(f"❌ ระบบหากุญแจไม่เจอ: {e}")
        return None

# --- 2. โหลดข้อมูล (เพิ่มการเก็บเลขแถวไว้แก้ไข) ---
@st.cache_data(ttl=60) # ตั้งแคชสั้นลงเพื่อให้เห็นข้อมูลที่แก้เร็วขึ้น
def load_data_for_edit():
    gc = get_sheets_client()
    if not gc: return {}
    sh = gc.open('Copy of ไฟล์เก็บเคส2025V1')
    worksheets = sh.worksheets()
    all_data = {}
    
    for ws in worksheets:
        data = ws.get_all_values()
        if not data: continue
        df = pd.DataFrame(data)
        
        # ค้นหาหัวตารางเหมือนเดิม
        header_idx = 0
        max_cols = 0
        for i in range(min(15, len(df))):
            count = sum(1 for x in df.iloc[i] if str(x).strip() != "")
            if count > max_cols:
                max_cols = count
                header_idx = i
        
        headers = df.iloc[header_idx].tolist()
        # เก็บเลขแถวจริงใน Sheets ไว้ (สำคัญมากตอนจะแก้)
        df['sheet_row'] = df.index + 1 
        df.columns = headers + ['sheet_row']
        
        # ตัดส่วน Dashboard และเก็บเนื้อข้อมูล
        df = df.iloc[header_idx+1:].reset_index(drop=True)
        all_data[ws.title] = df
    return all_data

# --- 3. ฟังก์ชันอัปเดตข้อมูลกลับไปที่ Sheets ---
def update_sheet(ws_title, row_index, col_name, new_value):
    try:
        gc = get_sheets_client()
        sh = gc.open('Copy of ไฟล์เก็บเคส2025V1')
        ws = sh.worksheet(ws_title)
        
        # หาว่าคอลัมน์ที่ต้องการแก้อยู่ลำดับที่เท่าไหร่
        headers = ws.row_values(ws.find(ws_title).row if not ws.row_values(1) else 1) # หาหัวตาราง
        # เพื่อความชัวร์ เราจะขอหัวตารางล่าสุด
        all_headers = ws.row_values(1) # สมมติหัวตารางอยู่แถว 1 (หรือตามระบบ Smart Header)
        # แก้ไขแบบระบุพิกัด [แถว, คอลัมน์]
        col_idx = all_headers.index(col_name) + 1
        ws.update_cell(row_index, col_idx, new_value)
        return True
    except:
        return False

# --- 4. ส่วนแสดงผลหลัก ---
st.title("📝 CS Case Intelligence & Editor")
master_data = load_data_for_edit()

search_val = st.text_input("🔍 ค้นหา ID หรือ IMEI เพื่อดูข้อมูลและแก้ไข:")

if search_val:
    q = search_val.strip().lower()
    for title, df in master_data.items():
        # ค้นหา
        mask = df.astype(str).apply(lambda row: row.str.lower().str.contains(q, na=False).any(), axis=1)
        res = df[mask]
        
        if not res.empty:
            st.subheader(f"📂 แท็บ: {title}")
            # แสดงข้อมูลที่ค้นหาเจอ
            st.dataframe(res.drop(columns=['sheet_row']), use_container_width=True)
            
            # สร้างฟอร์มแก้ไขข้อมูลสำหรับแถวที่เจอ
            with st.expander("🛠️ แก้ไขข้อมูลในแถวนี้"):
                col1, col2, col3 = st.columns(3)
                # เลือกคอลัมน์ที่ต้องการแก้ (ดึงจากหัวตารางพี่เลย)
                target_col = col1.selectbox(f"เลือกหัวข้อที่จะแก้ ({title})", res.columns.drop('sheet_row'))
                new_val = col2.text_input(f"ค่าใหม่ที่จะใส่ใน {target_col}:")
                row_in_sheet = res.iloc[0]['sheet_row'] # เอาเลขแถวจาก Sheets
                
                if col3.button(f"💾 บันทึกการแก้ไข ({title})"):
                    # สั่งอัปเดตไปที่ Sheets
                    gc = get_sheets_client()
                    sh = gc.open('Copy of ไฟล์เก็บเคส2025V1')
                    ws = sh.worksheet(title)
                    
                    # หาพิกัดคอลัมน์
                    current_headers = ws.row_values(1) # หรือแถวที่ระบุเป็นหัวตาราง
                    try:
                        c_idx = current_headers.index(target_col) + 1
                        ws.update_cell(row_in_sheet, c_idx, new_val)
                        st.success(f"อัปเดตข้อมูลในแท็บ {title} เรียบร้อย!")
                        st.cache_data.clear() # ล้างแคชเพื่อให้โหลดข้อมูลใหม่ที่แก้แล้ว
                    except Exception as e:
                        st.error(f"หาหัวข้อไม่เจอ หรือเกิดข้อผิดพลาด: {e}")

st.sidebar.warning("⚠️ การแก้ไขข้อมูลจะส่งผลกับไฟล์ Google Sheets ต้นฉบับทันที โปรดตรวจสอบความถูกต้องก่อนกดบันทึก")
