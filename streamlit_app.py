import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="CS Case Intelligence & Editor", page_icon="📝", layout="wide")

# --- 🎯 จุดตั้งค่า: อยากให้คอลัมน์ไหนเป็น Dropdown ใส่ตรงนี้เลยพี่ ---
# ตัวอย่าง: คอลัมน์ 'สถานะ' ให้เลือกจากลิสต์นี้
DROPDOWN_CONFIG = {
    'สถานะ': ['รอตรวจสอบ', 'กำลังดำเนินการ', 'ปิดเคสเรียบร้อย', 'ยกเลิก/ข้อมูลผิด'],
    'ประเภทเคส': ['ID', 'IMEI', 'เปลี่ยนเครื่อง', 'อื่นๆ']
}

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

# --- 2. โหลดข้อมูล ---
@st.cache_data(ttl=60)
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
        
        # ระบบ Smart Header หาหัวตาราง
        header_idx = 0
        max_cols = 0
        for i in range(min(15, len(df))):
            count = sum(1 for x in df.iloc[i] if str(x).strip() != "")
            if count > max_cols:
                max_cols = count
                header_idx = i
        
        headers = df.iloc[header_idx].tolist()
        df['sheet_row'] = df.index + 1 
        df.columns = headers + ['sheet_row']
        df = df.iloc[header_idx+1:].reset_index(drop=True)
        all_data[ws.title] = df
    return all_data

# --- 3. ส่วนแสดงผลหลัก ---
st.title("📝 CS Case Intelligence & Editor")
master_data = load_data_for_edit()

search_val = st.text_input("🔍 ค้นหา ID หรือ IMEI เพื่อแก้ไขข้อมูล:")

if search_val:
    q = search_val.strip().lower()
    for title, df in master_data.items():
        # ค้นหาทุกคอลัมน์
        mask = df.astype(str).apply(lambda row: row.str.lower().str.contains(q, na=False).any(), axis=1)
        res = df[mask]
        
        if not res.empty:
            st.markdown(f"### 📂 แท็บ: {title}")
            st.dataframe(res.drop(columns=['sheet_row']), use_container_width=True, hide_index=True)
            
            # --- ส่วนการแก้ไขข้อมูล ---
            with st.expander(f"🛠️ แก้ไขข้อมูลในแท็บ {title}", expanded=True):
                col1, col2, col3 = st.columns([1, 1, 0.5])
                
                # 1. เลือกคอลัมน์ที่จะแก้
                selectable_cols = [c for c in res.columns if c != 'sheet_row']
                target_col = col1.selectbox(f"เลือกหัวข้อ ({title})", selectable_cols, key=f"col_{title}")
                
                # 2. ตรวจสอบว่าคอลัมน์นี้ต้องเป็น Dropdown หรือไม่?
                if target_col in DROPDOWN_CONFIG:
                    new_val = col2.selectbox(f"เลือกค่าใหม่สำหรับ {target_col}:", DROPDOWN_CONFIG[target_col], key=f"val_{title}")
                else:
                    new_val = col2.text_input(f"พิมพ์ค่าใหม่สำหรับ {target_col}:", key=f"input_{title}")
                
                # 3. ปุ่มบันทึก
                if col3.button(f"💾 บันทึก ({title})", key=f"btn_{title}"):
                    row_in_sheet = int(res.iloc[0]['sheet_row'])
                    with st.spinner('กำลังบันทึก...'):
                        try:
                            gc = get_sheets_client()
                            sh = gc.open('Copy of ไฟล์เก็บเคส2025V1')
                            ws = sh.worksheet(title)
                            
                            # หาเลขคอลัมน์จากหัวตารางจริงใน Sheets
                            current_headers = ws.row_values(1) # ปรับเลขแถวตามจริง
                            c_idx = current_headers.index(target_col) + 1
                            
                            ws.update_cell(row_in_sheet, c_idx, new_val)
                            st.success(f"✅ แก้ไข {target_col} เป็น '{new_val}' เรียบร้อย!")
                            st.cache_data.clear() # ล้างแคชเพื่อให้โหลดข้อมูลใหม่
                            # st.rerun() # เปิดตัวนี้ถ้าอยากให้แอปรีเฟรชหน้าจอทันที
                        except Exception as e:
                            st.error(f"❌ บันทึกไม่สำเร็จ: {e}")

st.sidebar.info("💡 **วิธีตั้งค่า Dropdown:** พี่สามารถเพิ่มหัวข้อและตัวเลือกได้ในส่วน `DROPDOWN_CONFIG` ต้นโค้ดครับ")
