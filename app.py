import os
import streamlit as st
import pickle
import pandas as pd

# Oprava pre Orange
os.environ['QT_QPA_PLATFORM'] = 'offscreen'

st.title("⚙️ MECASYS Master AI - Test")

@st.cache_resource
def load_model():
    if os.path.exists("model.pkcls"):
        try:
            import Orange
            with open("model.pkcls", "rb") as f:
                return pickle.load(f)
        except Exception as e:
            st.error(f"Chyba: {e}")
            return None
    return None

model = load_model()

if model:
    st.success("✅ HURÁ! Model je úspešne načítaný.")
    st.write("Teraz môžeme začať počítať ceny.")
else:
    st.info("⏳ Načítavam model alebo konfigurujem prostredie...")
