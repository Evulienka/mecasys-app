import os
import sys

# Silová oprava pre chýbajúce súčasti
try:
    import pkg_resources
except ImportError:
    try:
        from pip._vendor import pkg_resources
        sys.modules['pkg_resources'] = pkg_resources
    except:
        pass

# Vypnutie grafického rozhrania Orangeu
os.environ['QT_QPA_PLATFORM'] = 'offscreen'

import streamlit as st
import pickle
import pandas as pd

st.set_page_config(page_title="MECASYS AI")

@st.cache_resource
def load_model():
    # Tu načítame tvoj .pkcls súbor
    model_path = "model.pkcls"
    if os.path.exists(model_path):
        try:
            # Dôležité: Orange modely často vyžadujú import Orange pred pickle.load
            import Orange
            with open(model_path, "rb") as f:
                return pickle.load(f)
        except Exception as e:
            st.error(f"Načítanie zlyhalo: {e}")
            return None
    return None

model = load_model()

st.title("⚙️ MECASYS Master AI")

if model:
    st.success("✅ Model bol načítaný cez odľahčené jadro!")
    # Tu pridáme tvoj výpočtový formulár...
else:
    st.info("Systém sa pokúša o čistú inštaláciu bez grafických chýb. Ak to trvá dlho, dajte Reboot.")
