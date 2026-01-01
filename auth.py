import streamlit as st

def check_password():
    """Returns True if the user had the correct password."""
    def password_entered():
        if st.session_state["password"] == "oaf2026": # Change this to your preferred password
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.text_input("Password / የይለፍ ቃል", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.text_input("Password / የይለፍ ቃል", type="password", on_change=password_entered, key="password")
        st.error("😕 Password incorrect / የይለፍ ቃል የተሳሳተ ነው")
        return False
    else:
        return True
