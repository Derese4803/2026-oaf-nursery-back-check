import streamlit as st
import pandas as pd
from datetime import datetime
from oauth2client.service_account import ServiceAccountCredentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from sqlalchemy import text
import os

# --- 1. IMPORT LOCAL MODULES ---
from database import SessionLocal
from models import Farmer, Woreda, Kebele, create_tables

# --- 2. CONFIGURATION ---
st.set_page_config(
    page_title="Amhara 2026 Distribution Register Form", 
    layout="wide", 
    page_icon="🌳"
)

# Initialize Database
create_tables()

def run_migrations():
    """Ensures database columns exist to prevent errors during updates."""
    db = SessionLocal()
    cols = [
        "gesho", "giravila", "diceres", "wanza", "papaya", 
        "moringa", "lemon", "arzelibanos", "guava", 
        "phone", "officer_name", "audio_url"
    ]
    for c in cols:
        try:
            dtype = "INTEGER DEFAULT 0" if c not in ["phone", "officer_name", "audio_url"] else "TEXT"
            db.execute(text(f"ALTER TABLE farmers ADD COLUMN {c} {dtype}"))
            db.commit()
        except Exception:
            db.rollback() 
    db.close()

run_migrations()

# --- 3. GOOGLE DRIVE UPLOAD ---
def upload_to_drive(file, farmer_name):
    try:
        creds_info = st.secrets["gcp_service_account"]
        creds = ServiceAccountCredentials.from_json(creds_info, ['https://www.googleapis.com/auth/drive'])
        service = build('drive', 'v3', credentials=creds)
        
        file_name = f"{farmer_name}_{datetime.now().strftime('%Y%m%d_%H%M')}.mp3"
        media = MediaIoBaseUpload(file, mimetype='audio/mpeg', resumable=True)
        
        g_file = service.files().create(
            body={'name': file_name}, 
            media_body=media, 
            fields='id'
        ).execute()
        
        fid = g_file.get('id')
        service.permissions().create(fileId=fid, body={'type': 'anyone', 'role': 'viewer'}).execute()
        return f"https://drive.google.com/uc?id={fid}"
    except Exception as e:
        st.error(f"Cloud Storage Error: {e}")
        return None

# --- 4. NAVIGATION ---
if "page" not in st.session_state:
    st.session_state["page"] = "Home"

def nav(p):
    st.session_state["page"] = p
    st.rerun()

# --- 5. MAIN UI ---
def main():
    st.sidebar.title("🌳 Amhara 2026")
    st.sidebar.caption("Distribution System")
    
    page = st.session_state["page"]

    # --- PAGE: HOME ---
    if page == "Home":
        st.title("🚜 Amhara 2026 Distribution Register Form")
        st.markdown("---")
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("📝 NEW REGISTRATION", use_container_width=True, type="primary"): nav("Reg")
        with c2:
            if st.button("📍 MANAGE LOCATIONS", use_container_width=True): nav("Loc")
        with c3:
            if st.button("📊 VIEW SURVEY DATA", use_container_width=True): nav("Data")

    # --- PAGE: REGISTRATION ---
    elif page == "Reg":
        if st.button("⬅️ Back"): nav("Home")
        st.header("New Farmer Registration")
        db = SessionLocal()
        woredas = db.query(Woreda).all()
        
        with st.form("reg_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("Farmer Full Name")
                phone = st.text_input("Phone Number")
                officer = st.text_input("Distribution Officer Name (TNO)")
            with col2:
                w_list = [w.name for w in woredas] if woredas else ["Add Woredas First"]
                sel_woreda = st.selectbox("Woreda", w_list)
                
                kebeles = []
                if woredas and sel_woreda != "Add Woredas First":
                    w_obj = db.query(Woreda).filter(Woreda.name == sel_woreda).first()
                    kebeles = [k.name for k in w_obj.kebeles]
                sel_kebele = st.selectbox("Kebele", kebeles if kebeles else ["No Kebeles Found"])
            
            st.markdown("---")
            st.subheader("🌲 Seedlings Distributed")
            t1, t2, t3 = st.columns(3)
            with t1:
                gesho = st.number_input("Gesho", 0)
                wanza = st.number_input("Wanza", 0)
                lemon = st.number_input("Lemon", 0)
            with t2:
                giravila = st.number_input("Giravila", 0)
                papaya = st.number_input("Papaya", 0)
                arzelibanos = st.number_input("Arzelibanos", 0)
            with t3:
                diceres = st.number_input("Diceres", 0)
                moringa = st.number_input("Moringa", 0)
                guava = st.number_input("Guava", 0)

            audio = st.file_uploader("🎤 Audio Confirmation", type=['mp3', 'wav', 'm4a'])
            
            if st.form_submit_button("Submit Distribution Record"):
                if not name or not kebeles or not officer:
                    st.error("Please fill in Name, Officer, and Location!")
                else:
                    with st.spinner("Saving data..."):
                        url = upload_to_drive(audio, name) if audio else None
                        # 'officer_name' matches 'models.py'
                        new_f = Farmer(
                            name=name, phone=phone, woreda=sel_woreda, 
                            kebele=sel_kebele, officer_name=officer,
                            audio_url=url, gesho=gesho, giravila=giravila, 
                            diceres=diceres, wanza=wanza, papaya=papaya, 
                            moringa=moringa, lemon=lemon, 
                            arzelibanos=arzelibanos, guava=guava
                        )
                        db.add(new_f)
                        db.commit()
                        st.success(f"✅ Record for {name} saved successfully!")
        db.close()

    # --- PAGE: LOCATIONS ---
    elif page == "Loc":
        if st.button("⬅️ Back"): nav("Home")
        db = SessionLocal()
        st.header("📍 Manage Areas")
        nw = st.text_input("Add Woreda Name")
        if st.button("Add Woreda"):
            if nw: db.add(Woreda(name=nw)); db.commit(); st.rerun()

        for w in db.query(Woreda).all():
            with st.expander(f"📌 {w.name}"):
                nk = st.text_input(f"Add Kebele to {w.name}", key=f"k_{w.id}")
                if st.button("Add Kebele", key=f"b_{w.id}"):
                    if nk: db.add(Kebele(name=nk, woreda_id=w.id)); db.commit(); st.rerun()
                for k in w.kebeles:
                    st.write(f"- {k.name}")
        db.close()

    # --- PAGE: DATA VIEW ---
    elif page == "Data":
        if st.button("⬅️ Back"): nav("Home")
        st.header("📊 Distribution Data")
        db = SessionLocal()
        farmers = db.query(Farmer).all()
        
        if farmers:
            data = []
            for f in farmers:
                d = f.__dict__.copy()
                d.pop('_sa_instance_state', None)
                data.append(d)
            df = pd.DataFrame(data)

            # Search Bar
            search = st.text_input("🔍 Search by Farmer Name or Phone")
            if search:
                df = df[df['name'].str.contains(search, case=False) | df['phone'].str.contains(search)]

            st.download_button(
                "📥 Download CSV", 
                df.to_csv(index=False).encode('utf-8'), 
                "Amhara_2026_Distribution.csv", 
                "text/csv"
            )
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No records recorded yet.")
        db.close()

if __name__ == "__main__":
    main()
