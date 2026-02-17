import streamlit as st
import pandas as pd
import joblib
import numpy as np
import requests
import math
from io import BytesIO

# --- 1. KONFIGURÁCIA STRÁNKY ---
st.set_page_config(page_title="MECASYS Kalkulátor", layout="centered")

# --- 2. TVOJ RAW LINK NA MODEL ---
MODEL_URL = "https://raw.githubusercontent.com/Evulienka/mecasys-app/main/model_ceny.pkl"

@st.cache_resource
def load_model(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        return joblib.load(BytesIO(response.content))
    except Exception as e:
        st.error(f"Chyba pri načítaní modelu z GitHubu: {e}")
        return None

model = load_model(MODEL_URL)

# --- 3. DATABÁZA ZÁKAZNÍKOV (z tvojho pôvodného kódu) ---
zakaznici_db = {
    "A2B s.r.o.": {"lojalita": 0.83, "krajina": "SK"},
    "AAH PLASTICS Slovakia s. r. o.": {"lojalita": 0.80, "krajina": "SK"},
    "Adient Seating Slovakia s.r.o.": {"lojalita": 0.88, "krajina": "SK"},
    "Iný / Nový zákazník": {"lojalita": 0.70, "krajina": "EU"}
}

# --- 4. GRAFICKÉ ROZHRANIE ---
st.title("📊 MECASYS CP Kalkulátor")
st.write("Zadajte parametre pre predpoveď ceny modelu Gradient Boosting.")

with st.expander("📝 Vstupné údaje", expanded=True):
    col1, col2 = st.columns(2)
    
    with col1:
        zakaznik = st.selectbox("Zákazník", list(zakaznici_db.keys()))
        mnozstvo = st.number_input("Množstvo (ks)", min_value=1, value=100)
        narocnost = st.slider("Náročnosť výroby (1-5)", 1, 5, 3)
        c_mat_kg = st.number_input("Cena materiálu (€/kg)", min_value=0.0, value=2.5)

    with col2:
        d_val = st.number_input("Priemer D (mm)", min_value=0.1, value=20.0)
        l_val = st.number_input("Dĺžka L (mm)", min_value=0.1, value=100.0)
        hustota = st.number_input("Hustota mat. (kg/m3)", value=7900)
        c_koop = st.number_
