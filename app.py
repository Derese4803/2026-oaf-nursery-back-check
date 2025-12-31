import streamlit as st
import pandas as pd
from database import SessionLocal, engine
from models import BackCheck, Base

st.set_page_config(page_title="OAF Nursery Back Check", layout="wide", page_icon="🌳")

def init_db():
    Base.metadata.create_all(bind=engine)

init_db()

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

    if page == "Form":
        st.title("🚜 OAF Nursery Back Check Form")
        db = SessionLocal()
        with st.form("oaf_form", clear_on_submit=True):
            st.subheader("📍 Location & Personnel")
            c1, c2, c3, c4 = st.columns(4)
            w_val = c1.text_input("Woreda (ወረዳ)")
            cl_val = c2.text_input("Cluster (ክላስተር)")
            k_val = c3.text_input("Kebele (ቀበሌ)")
            t_val = c4.text_input("TNO Name (የTNO ስም)")

            p1, p2, p3, p4 = st.columns(4)
            f_val = p1.text_input("Name of Back checker FAs")
            cb_val = p2.text_input("Back checker CBE")
            ph_val = p3.text_input("Phone #")
            fn_val = p4.radio("Fenced?", ["Yes", "No"], horizontal=True)

            def bed_section(species, amharic):
                st.markdown(f"### 🌿 {species} ({amharic})")
                bc1, bc2, bc3 = st.columns(3)
                n = bc1.number_input(f"{species} beds #", min_value=0, step=1, key=f"n_{species}")
                l = bc2.number_input(f"{species} length (m)", min_value=0.0, step=0.1, key=f"l_{species}")
                s = bc3.number_input(f"{species} sockets width", min_value=0, step=1, key=f"s_{species}")
                return n, l, s

            g_n, g_l, g_s = bed_section("Guava", "ዘይቶን")
            ge_n, ge_l, ge_s = bed_section("Gesho", "ጌሾ")
            l_n, l_l, l_s = bed_section("Lemon", "ሎሚ")
            gr_n, gr_l, gr_s = bed_section("Grevillea", "ግራቪሊያ")

            if st.form_submit_button("Submit Data"):
                new_record = BackCheck(
                    woreda=w_val, cluster=cl_val, kebele=k_val, tno_name=t_val,
                    checker_fa_name=f_val, checker_cbe_name=cb_val, checker_phone=ph_val, fenced=fn_val,
                    guava_beds=g_n, guava_length=g_l, guava_sockets=g_s, total_guava_sockets=g_n*g_s,
                    gesho_beds=ge_n, gesho_length=ge_l, gesho_sockets=ge_s, total_gesho_sockets=ge_n*ge_s,
                    lemon_beds=l_n, lemon_length=l_l, lemon_sockets=l_s, total_lemon_sockets=l_n*l_s,
                    grevillea_beds=gr_n, grevillea_length=gr_l, grevillea_sockets=gr_s, total_grevillea_sockets=gr_n*gr_s
                )
                db.add(new_record); db.commit(); st.success("✅ Saved!")
        db.close()

    elif page == "Data":
        st.title("📊 Ordered Records")
        db = SessionLocal()
        records = db.query(BackCheck).all()
        if records:
            df = pd.DataFrame([r.__dict__ for r in records])
            
            # --- THE ORDERED COLUMN LIST ---
            ordered_cols = [
                'id', 'woreda', 'cluster', 'kebele', 'tno_name',
                'guava_beds', 'guava_length', 'guava_sockets', 'total_guava_sockets',
                'gesho_beds', 'gesho_length', 'gesho_sockets', 'total_gesho_sockets',
                'lemon_beds', 'lemon_length', 'lemon_sockets', 'total_lemon_sockets',
                'grevillea_beds', 'grevillea_length', 'grevillea_sockets', 'total_grevillea_sockets',
                'checker_fa_name', 'fenced', 'timestamp'
            ]
            
            # Filter only columns that exist in the dataframe
            final_cols = [c for c in ordered_cols if c in df.columns]
            df = df[final_cols]
            
            # Bilingual Header Mapping
            rename_map = {
                'guava_beds': 'ዘይቶን አልጋ (Guava Bed)', 'guava_length': 'ዘይቶን ርዝመት (Length)', 'guava_sockets': 'ዘይቶን ሶኬት (Socket)',
                'gesho_beds': 'ጌሾ አልጋ (Gesho Bed)', 'gesho_length': 'ጌሾ ርዝመት (Length)', 'gesho_sockets': 'ጌሾ ሶኬት (Socket)',
                'lemon_beds': 'ሎሚ አልጋ (Lemon Bed)', 'lemon_length': 'ሎሚ ርዝመት (Length)', 'lemon_sockets': 'ሎሚ ሶኬት (Socket)',
                'grevillea_beds': 'ግራቪሊያ አልጋ (Grevillea Bed)', 'grevillea_length': 'ግራቪሊያ ርዝመት (Length)', 'grevillea_sockets': 'ግራቪሊያ ሶኬት (Socket)'
            }
            
            st.dataframe(df.rename(columns=rename_map), use_container_width=True)
            st.download_button("📥 Download CSV", data=df.to_csv(index=False), file_name="ordered_nursery_data.csv")
        else:
            st.info("No records.")
        db.close()

if __name__ == "__main__":
    main()
