import os
import sys

# --- FORZÍROVANÉ NAČÍTANIE PKG_RESOURCES ---
try:
    import pkg_resources
except ImportError:
    import pip._vendor.pkg_resources as pkg_resources
    sys.modules['pkg_resources'] = pkg_resources

# Zakázanie GUI
os.environ['QT_QPA_PLATFORM'] = 'offscreen'

import streamlit as st
import pickle
import pandas as pd

st.set_page_config(page_title="MECASYS Master AI", page_icon="⚙️")

# --- NAČÍTANIE MODELU ---
@st.cache_resource
def load_model():
    if os.path.exists("model.pkcls"):
        try:
            import Orange
            with open("model.pkcls", "rb") as f:
                return pickle.load(f)
        except Exception as e:
            st.error(f"Chyba pri otváraní modelu: {e}")
            return None
    return None

model = load_model()

# --- ROZHRANIE ---
st.title("⚙️ MECASYS Master AI")

if model:
    st.success("✅ Model je úspešne načítaný!")
    st.balloons() # Malá oslava, keď to naskočí
    
    # Tu bude tvoj formulár na výpočet...
    st.info("Teraz mi napíš a pridáme zvyšok výpočtovej logiky.")
else:
    st.warning("⏳ Systém sa konfiguruje. Ak vidíte červenú chybu, skúste 'Reboot app'.")
