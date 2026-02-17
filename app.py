import streamlit as st
import pandas as pd
import joblib
import numpy as np
import requests
import math
from io import BytesIO

# --- 1. ZÁKLADNÉ NASTAVENIE ---
st.set_page_config(page_title="MECASYS CP Kalkulátor", layout="centered")

# UNIVERZÁLNY RAW LINK
MODEL_URL = "https://raw.githubusercontent.com/Evulienka/mecasys-app/main/model_ceny.pkl"

@st.cache_resource
def load_model(url):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        model_file = BytesIO(response.content)
        return joblib.load(model_file)
    except Exception as e:
        st.error(f"❌ Chyba pri načítaní modelu: {e}")
        return None

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
            # OPRAVENÝ RIADOK 57 (pridaná zátvorka na konci)
            c_koop = st.number_input("Kooperácia celkom (€)", min_value=0.0, value=0.0)

        submit = st.form_submit_button("🚀 Vypočítať cenovú ponuku", use_container_width=True)

    if submit:
        # --- 4. LOGIKA A VÝPOČET ---
        lojalita = zakaznici_db[zakaznik]["lojalita"]
        krajina = zakaznici_db[zakaznik]["krajina"]
        
        polomer_m = (d_val / 2) / 1000
        dlzka_m = l_val / 1000
        objem_m3 = math.pi * (polomer_m**2) * dlzka_m
        hmotnost_kg = objem_m3 * hustota
        
        vstupy = np.array([[
            2026, 2, 17, mnozstvo, 0.5 * narocnost, 1, narocnost, 
            c_koop, lojalita, krajina, 1, 1, 1, 
            d_val, l_val, hustota, c_mat_kg, hmotnost_kg
        ]])

        try:
            predikcia = model.predict(vstupy)[0]
            st.success("✅ Výpočet úspešne dokončený")
            res1, res2 = st.columns(2)
            res1.metric("Jednotková cena", f"{predikcia:.3f} €")
            res2.metric("Celková cena", f"{predikcia * mnozstvo:.2f} €")
        except Exception as e:
            st.error(f"Chyba pri predikcii: {e}")
else:
    st.warning("⌛ Čakám na načítanie modelu...")
