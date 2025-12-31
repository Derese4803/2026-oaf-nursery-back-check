import streamlit as st
import pandas as pd
from datetime import datetime
from oauth2client.service_account import ServiceAccountCredentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from sqlalchemy import text

from database import SessionLocal, engine
from models import Farmer, Woreda, Kebele, BackCheck, Base

# --- CONFIG ---
st.set_page_config(page_title="Amhara 2026 Register", layout="wide", page_icon="🌳")

def init_db():
    Base.metadata.create_all(bind=engine)

init_db()

# --- GOOGLE DRIVE UPLOAD ---
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
        st.error(f"Cloud Storage Error: {e}")
        return None

# --- NAV ---
if "page" not in st.session_state: st.session_state["page"] = "Home"
def nav(p):
    st.session_state["page"] = p
    st.rerun()

# --- UI ---
def main():
    page = st.session_state["page"]
    st.sidebar.title("🌳 Amhara 2026")

    if page == "Home":
        st.title("🚜 Amhara 2026 Management System")
        st.markdown("---")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("📝 NEW REGISTRATION", use_container_width=True, type="primary"): nav("Reg")
            if st.button("📍 MANAGE LOCATIONS", use_container_width=True): nav("Loc")
        with c2:
            if st.button("🔍 NURSERY BACK CHECK", use_container_width=True): nav("BackCheck")
            if st.button("📊 VIEW DATA", use_container_width=True): nav("Data")

    elif page == "Reg":
        if st.button("⬅️ Back"): nav("Home")
        st.header("Farmer Registration")
        db = SessionLocal()
        woredas = db.query(Woreda).all()
        with st.form("reg"):
            c1, c2 = st.columns(2)
            name = c1.text_input("Farmer Full Name")
            phone = c1.text_input("Phone")
            officer = c1.text_input("Officer (TNO)")
            w_list = [w.name for w in woredas] if woredas else ["Add Woredas First"]
            sel_woreda = c2.selectbox("Woreda", w_list)
            
            w_obj = db.query(Woreda).filter(Woreda.name == sel_woreda).first()
            keb_list = [k.name for k in w_obj.kebeles] if w_obj else []
            sel_kebele = c2.selectbox("Kebele", keb_list if keb_list else ["None"])
            
            sc1, sc2, sc3 = st.columns(3)
            gesho = sc1.number_input("Gesho", 0); lemon = sc2.number_input("Lemon", 0); guava = sc3.number_input("Guava", 0)
            
            audio = st.file_uploader("Audio Confirmation", type=['mp3','wav','m4a'])
            if st.form_submit_button("Submit"):
                url = upload_to_drive(audio, name) if audio else None
                db.add(Farmer(name=name, phone=phone, woreda=sel_woreda, kebele=sel_kebele, 
                              officer_name=officer, audio_url=url, gesho=gesho, lemon=lemon, guava=guava))
                db.commit(); st.success("Saved!")
        db.close()

    elif page == "BackCheck":
        if st.button("⬅️ Back"): nav("Home")
        st.header("🔍 Nursery Back Check")
        db = SessionLocal()

        with st.form("bc_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                checker = st.text_input("Back Checker Name")
                # MANUAL TYPE INPUT
                sel_woreda = st.text_input("Woreda Name (Type here)")
            with col2:
                fenced = st.radio("Is Nursery Fenced?", ["Yes", "No"])
                # MANUAL TYPE INPUT
                sel_kebele = st.text_input("Kebele Name (Type here)")

            st.markdown("---")

            def bed_row(species, expected):
                st.markdown(f"**{species}** (Expect {expected} sockets)")
                bc1, bc2, bc3 = st.columns(3)
                n = bc1.number_input(f"Beds #", 0, key=f"n_{species}")
                l = bc2.number_input(f"Length (m)", 0.0, step=0.1, key=f"l_{species}")
                s = bc3.number_input(f"Socket Width", 0, key=f"s_{species}")
                return n, l, s

            g_n, g_l, g_s = bed_row("Guava", 13)
            l_n, l_l, l_s = bed_row("Lemon", 13)
            ge_n, ge_l, ge_s = bed_row("Gesho", 16)
            gr_n, gr_l, gr_s = bed_row("Grevillea", 16)

            # AUTO CALCULATION
            total_l_sockets = l_n * l_s
            st.info(f"💡 Calculated Total Lemon Sockets: {total_l_sockets}")

            if st.form_submit_button("Submit Back Check"):
                if not checker or not sel_woreda: st.error("Checker and Woreda required!")
                else:
                    new_bc = BackCheck(checker_name=checker, woreda=sel_woreda, kebele=sel_kebele, 
                                      fenced=fenced, guava_beds=g_n, guava_length=g_l, guava_sockets=g_s,
                                      lemon_beds=l_n, lemon_length=l_l, lemon_sockets=l_s, 
                                      total_lemon_sockets=total_l_sockets,
                                      gesho_beds=ge_n, gesho_length=ge_l, gesho_sockets=ge_s,
                                      grevillea_beds=gr_n, grevillea_length=gr_l, grevillea_sockets=gr_s)
                    db.add(new_bc); db.commit(); st.success("Data Recorded!")
        db.close()

    elif page == "Data":
        if st.button("⬅️ Back"): nav("Home")
        db = SessionLocal()
        t1, t2 = st.tabs(["Farmer Records", "Back Check Records"])
        with t1:
            df1 = pd.DataFrame([f.__dict__ for f in db.query(Farmer).all()]).drop('_sa_instance_state', axis=1, errors='ignore')
            st.dataframe(df1)
        with t2:
            df2 = pd.DataFrame([b.__dict__ for b in db.query(BackCheck).all()]).drop('_sa_instance_state', axis=1, errors='ignore')
            st.dataframe(df2)
        db.close()

    elif page == "Loc":
        if st.button("⬅️ Back"): nav("Home")
        db = SessionLocal()
        nw = st.text_input("New Woreda")
        if st.button("Add"): 
            if nw: db.add(Woreda(name=nw)); db.commit(); st.rerun()
        for w in db.query(Woreda).all():
            with st.expander(w.name):
                nk = st.text_input("New Kebele", key=w.id)
                if st.button("Add Kebele", key=f"b{w.id}"): 
                    if nk: db.add(Kebele(name=nk, woreda_id=w.id)); db.commit(); st.rerun()
        db.close()

if __name__ == "__main__": main()
