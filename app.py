import streamlit as st
import pandas as pd
from database import SessionLocal, engine
from models import BackCheck, Base

# --- CONFIGURATION ---
st.set_page_config(page_title="OAF Nursery Back Check", layout="wide", page_icon="🌳")

def init_db():
    Base.metadata.create_all(bind=engine)

init_db()

# --- NAVIGATION ---
if "page" not in st.session_state:
    st.session_state["page"] = "Form"

def nav(p):
    st.session_state["page"] = p
    st.rerun()

def main():
    page = st.session_state["page"]
    
    st.sidebar.title("OAF Nursery 🌳")
    if st.sidebar.button("📝 Registration Form", use_container_width=True): nav("Form")
    if st.sidebar.button("📊 View Records", use_container_width=True): nav("Data")

    # --- PAGE: FORM ---
    if page == "Form":
        st.title("🚜 OAF Nursery Back Check Form")
        db = SessionLocal()

        with st.form("oaf_form", clear_on_submit=True):
            st.subheader("📍 Location & Personnel")
            c1, c2, c3 = st.columns(3)
            woreda = c1.text_input("Woreda")
            kebele = c2.text_input("Kebele")
            fenced = c3.radio("Nursery Fenced?", ["Yes", "No"], horizontal=True)

            p1, p2, p3 = st.columns(3)
            fa_name = p1.text_input("Name of Back checker (FAs)")
            cbe_name = p2.text_input("Back checker (CBE)")
            phone = p3.text_input("Back checker phone #")

            st.markdown("---")

            def bed_section(species, expected):
                st.markdown(f"### 🌿 {species} (Expect {expected} sockets)")
                bc1, bc2, bc3 = st.columns(3)
                n = bc1.number_input(f"{species} beds number", min_value=0, step=1, key=f"n_{species}")
                l = bc2.number_input(f"Length of {species} beds (m)", min_value=0.0, step=0.1, key=f"l_{species}")
                s = bc3.number_input(f"Sockets in width", min_value=0, step=1, key=f"s_{species}")
                return n, l, s

            g_n, g_l, g_s = bed_section("Guava", 13)
            ge_n, ge_l, ge_s = bed_section("Gesho", 16)
            l_n, l_l, l_s = bed_section("Lemon", 13)
            gr_n, gr_l, gr_s = bed_section("Grevillea", 16)

            total_l_sockets = l_n * l_s
            st.metric("Total Lemon Sockets", total_l_sockets)

            if st.form_submit_button("Submit OAF Back Check"):
                if not woreda or not fa_name:
                    st.error("Please fill in Woreda and FAs Name!")
                else:
                    new_rec = BackCheck(
                        woreda=woreda, kebele=kebele, checker_fa_name=fa_name,
                        checker_cbe_name=cbe_name, checker_phone=phone, fenced=fenced,
                        guava_beds=g_n, guava_length=g_l, guava_sockets=g_s,
                        gesho_beds=ge_n, gesho_length=ge_l, gesho_sockets=ge_s,
                        lemon_beds=l_n, lemon_length=l_l, lemon_sockets=l_s,
                        total_lemon_sockets=total_l_sockets,
                        grevillea_beds=gr_n, grevillea_length=gr_l, grevillea_sockets=gr_s
                    )
                    db.add(new_rec); db.commit(); st.success("✅ Data saved!")
        db.close()

    # --- PAGE: DATA VIEW (ORDERED) ---
    elif page == "Data":
        st.title("📊 OAF Recorded Data")
        db = SessionLocal()
        records = db.query(BackCheck).all()
        if records:
            df = pd.DataFrame([r.__dict__ for r in records])
            
            # --- STRICT COLUMN ORDERING ---
            cols = [
                'woreda', 'kebele', 'checker_fa_name', 'checker_cbe_name',
                'guava_beds', 'guava_length', 'guava_sockets',  # Group 1
                'gesho_beds', 'gesho_length', 'gesho_sockets',  # Group 2
                'lemon_beds', 'lemon_length', 'lemon_sockets',  # Group 3
                'grevillea_beds', 'grevillea_length', 'grevillea_sockets', # Group 4
                'total_lemon_sockets', 'fenced', 'timestamp'
            ]
            df = df[[c for c in cols if c in df.columns]]
            df.columns = [c.replace('_', ' ').title() for c in df.columns]
            st.dataframe(df, use_container_width=True)
            
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Export CSV", data=csv, file_name="OAF_Nursery.csv")
        else:
            st.info("No records found.")
        db.close()

if __name__ == "__main__":
    main()
