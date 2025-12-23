import streamlit as st
import pandas as pd
from datetime import datetime
from oauth2client.service_account import ServiceAccountCredentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from sqlalchemy import text
import os

from database import SessionLocal
from models import Farmer, Woreda, Kebele, create_tables
from auth import check_auth

# --- INIT ---
st.set_page_config(page_title="Amhara Survey 2025", layout="wide", page_icon="🌳")
create_tables()

# Migration to ensure all tree columns exist
def run_migrations():
    db = SessionLocal()
    cols = ["gesho", "giravila", "diceres", "wanza", "papaya", "moringa", "lemon", "arzelibanos", "guava", "phone", "f_type", "registered_by", "audio_url"]
    for c in cols:
        try:
            t = "INTEGER DEFAULT 0" if c not in ["phone", "f_type", "registered_by", "audio_url"] else "TEXT"
            db.execute(text(f"ALTER TABLE farmers ADD COLUMN {c} {t}"))
            db.commit()
        except:
            db.rollback()
    db.close()

run_migrations()

# --- GOOGLE DRIVE ---
def upload_to_drive(file, farmer_name):
    try:
        creds_info = st.secrets["gcp_service_account"]
        creds = ServiceAccountCredentials.from_json(creds_info, ['https://www.googleapis.com/auth/drive'])
        service = build('drive', 'v3', credentials=creds)
        file_name = f"{farmer_name}_{datetime.now().strftime('%Y%m%d_%H%M')}.mp3"
        media = MediaIoBaseUpload(file, mimetype='audio/mpeg', resumable=True)
        g_file = service.files().create(body={'name': file_name}, media_body=media, fields='id').execute()
        fid = g_file.get('id')
        service.permissions().create(fileId=fid, body={'type': 'anyone', 'role': 'viewer'}).execute()
        return f"https://drive.google.com/uc?id={fid}"
    except Exception as e:
        st.error(f"Drive Error: {e}")
        return None

# --- UI NAVIGATION ---
def nav(p):
    st.session_state["page"] = p
    st.rerun()

# --- MAIN APP ---
def main():
    check_auth() # Check login first
    
    if "page" not in st.session_state: st.session_state["page"] = "Home"
    
    st.sidebar.title(f"Welcome, {st.session_state['user']}")
    if st.sidebar.button("Logout"):
        del st.session_state["user"]
        st.rerun()

    p = st.session_state["page"]

    if p == "Home":
        st.title("🌾 Amhara Survey Dashboard")
        c1, c2, c3 = st.columns(3)
        if c1.button("📝 NEW REGISTRATION", use_container_width=True): nav("Reg")
        if c2.button("📍 LOCATIONS", use_container_width=True): nav("Loc")
        if c3.button("📊 VIEW DATA", use_container_width=True): nav("Data")

    elif p == "Reg":
        if st.button("⬅️ Back"): nav("Home")
        st.header("Farmer Registration")
        db = SessionLocal()
        woredas = db.query(Woreda).all()
        
        with st.form("reg"):
            name = st.text_input("Farmer Name")
            phone = st.text_input("Phone")
            w_name = st.selectbox("Woreda", [w.name for w in woredas] if woredas else ["None"])
            
            kebeles = []
            if woredas and w_name != "None":
                w_obj = db.query(Woreda).filter(Woreda.name == w_name).first()
                kebeles = [k.name for k in w_obj.kebeles]
            k_name = st.selectbox("Kebele", kebeles if kebeles else ["None"])
            
            st.subheader("🌲 Seedlings Count")
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
            
            audio = st.file_uploader("🎤 Audio Record", type=['mp3', 'wav', 'm4a'])
            
            if st.form_submit_button("Save"):
                url = upload_to_drive(audio, name) if audio else None
                db.add(Farmer(name=name, phone=phone, woreda=w_name, kebele=k_name, audio_url=url,
                             gesho=gesho, wanza=wanza, lemon=lemon, giravila=giravila, papaya=papaya,
                             arzelibanos=arzelibanos, diceres=diceres, moringa=moringa, guava=guava,
                             registered_by=st.session_state['user']))
                db.commit()
                st.success("Saved!")
        db.close()

    elif p == "Loc":
        if st.button("⬅️ Back"): nav("Home")
        db = SessionLocal()
        st.header("Manage Locations")
        n_w = st.text_input("Add Woreda")
        if st.button("Save Woreda"):
            db.add(Woreda(name=n_w)); db.commit(); st.rerun()
        for w in db.query(Woreda).all():
            with st.expander(f"📍 {w.name}"):
                n_k = st.text_input(f"New Kebele for {w.name}", key=w.id)
                if st.button("Add Kebele", key=f"b{w.id}"):
                    db.add(Kebele(name=n_k, woreda_id=w.id)); db.commit(); st.rerun()
        db.close()

    elif p == "Data":
        if st.button("⬅️ Back"): nav("Home")
        db = SessionLocal()
        farmers = db.query(Farmer).all()
        if farmers:
            df = pd.DataFrame([f.__dict__ for f in farmers]).drop('_sa_instance_state', axis=1)
            st.download_button("📥 Download CSV", df.to_csv(index=False).encode('utf-8'), "data.csv")
            st.dataframe(df)
        db.close()

if __name__ == "__main__": main()
