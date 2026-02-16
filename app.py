import os
import sys

# Oprava pre staršie Orange modely
try:
    import setuptools
    import pkg_resources
except:
    pass

import streamlit as st
import pickle

st.title("MECASYS AI - Test stability")

@st.cache_resource
def load_model():
    if os.path.exists("model.pkcls"):
        try:
            import Orange
            with open("model.pkcls", "rb") as f:
                return pickle.load(f)
        except Exception as e:
            st.error(f"Technický detail chyby: {e}")
            return None
    return None

model = load_model()

if model:
    st.success("✅ MODEL JE ÚSPEŠNE NAČÍTANÝ A PRIPRAVENÝ!")
else:
    st.warning("⏳ Čakám na správne nastavenie knižníc...")
