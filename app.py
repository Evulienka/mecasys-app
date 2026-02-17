import streamlit as st
import pandas as pd
import joblib
import numpy as np
import requests
import math
from io import BytesIO

# --- 1. ZÁKLADNÉ NASTAVENIE ---
st.set_page_config(page_title="MECASYS CP Kalkulátor", layout="centered")

# UNIVERZÁLNY RAW LINK (vždy na najnovšiu verziu v main branch)
MODEL_URL = "https://raw.githubusercontent.com/Evulienka/mecasys-app/main/model_ceny.pkl"

@st.cache_resource
def load_model(url):
    try:
        # Streamlit si model stiahne priamo do pamäte
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        model_file = BytesIO(response.content)
        return joblib.load(model_file)
    except Exception as e:
        st.error(f"❌ Chyba pri načítaní modelu: {e}")
        return None

# Pokus o načítanie modelu
model = load_model(MODEL_URL)

# --- 2. DATABÁZA ZÁKAZNÍKOV ---
zakaznici_db = {
    "A2B s.r.o.": {"lojalita": 0.83, "krajina": 1},
    "AAH PLASTICS Slovakia s. r. o.": {"lojalita": 0.80, "krajina": 1},
    "Adient Seating Slovakia s.r.o.": {"lojalita": 0.88, "krajina": 1},
    "Kia Slovakia s.r.o.": {"lojalita": 0.95, "krajina": 1},
    "Iný / Nový zákazník": {"lojalita": 0.70, "krajina": 0}
}

# --- 3. POUŽÍVATEĽSKÉ ROZHRANIE ---
st.title("📊 MECASYS Kalkulátor")
st.info("Gradient Boosting model pre predpoveď cien")

if model:
    with st.form("kalkulacka_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            zakaznik = st.selectbox("Zákazník", list(zakaznici_db.keys()))
            mnozstvo = st.number_input("Množstvo (ks)", min_value=1, value=100)
            narocnost = st.slider("Náročnosť výroby (1-5)", 1, 5, 3)
            c_mat_kg = st.number_input("Cena materiálu (€/kg)", min_value=0.0, value=2.50)

        with col2:
            d_val = st.number_input("Priemer D (mm)", min_value=0.1, value=20.0)
            l_val = st.number_input("Dĺžka L (mm)", min_value=0.1, value=100.0)
            hustota = st.number_input("Hustota (kg/m3)", value=7900)
            c_koop = st.number_input("Kooperácia celkom (€)", min_value=0.0, value
