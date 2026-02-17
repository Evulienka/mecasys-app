import streamlit as st
import pandas as pd
import joblib
import numpy as np
import requests
import math
from io import BytesIO

# --- 1. KONFIGURÁCIA A NAČÍTANIE MODELU ---
st.set_page_config(page_title="MECASYS CP Kalkulátor", layout="wide")

# !!! SEM VLOŽ SVOJ ODKAZ Z GITHUB (tlačidlo Raw) !!!
MODEL_URL = "https://raw.githubusercontent.com/tvoj-ucet/repo/main/model_ceny.pkl"

@st.cache_resource
def load_model(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        return joblib.load(BytesIO(response.content))
    except Exception as e:
        st.error(f"Chyba pri načítaní modelu: {e}")
        return None

model = load_model(MODEL_URL)

# --- 2. DATABÁZA ZÁKAZNÍKOV (Ukážka z tvojho pôvodného kódu) ---
zakaznici_db = {
    "A2B s.r.o.": {"lojalita": 0.83, "krajina": "SK"},
    "AAH PLASTICS Slovakia s. r. o.": {"lojalita": 0.80, "krajina": "SK"},
    "Adient Seating Slovakia s.r.o.": {"lojalita": 0.88, "krajina": "SK"},
    "Kia Slovakia s.r.o.": {"lojalita": 0.95, "krajina": "SK"},
    "Iný / Nový zákazník": {"lojalita": 0.70, "krajina": "EU"}
}

# --- 3. POUŽÍVATEĽSKÉ ROZHRANIE ---
st.title("📊 MECASYS - Predpoveď ceny (Gradient Boosting)")
st.markdown("---")

with st.container():
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("Klient a Množstvo")
        vybrany_zakaznik = st.selectbox("Vyberte zákazníka", list(zakaznici_db.keys()))
        pocet_kusov = st.number_input("Počet kusov (ks)", min_value=1, value=100, step=1)
        narocnost = st.slider("Náročnosť výroby (1-5)", 1, 5, 3)

    with col2:
        st.subheader("Technické parametre")
        d_val = st.number_input("Priemer D (mm)", min_value=0.1, value=20.0, format="%.2f")
        l_val = st.number_input("Dĺžka L (mm)", min_value=0.1, value=100.0, format="%.2f")
        hustota = st.selectbox("Materiál (Hustota kg/m3)", 
                              options=[7900, 8000, 2700, 7850], 
                              format_func=lambda x: f"Oceľ ({x})" if x==7900 else (f"Nerez ({x})" if x==8000 else f"Hliník ({x})"))

    with col3:
        st.subheader("Ekonomika")
        c_mat_kg = st.number_input("Cena mat. (€/kg)", min_value=0.0, value=2.50, format="%.2f")
        c_koop = st.number_input("Kooperácia celkom (€)", min_value=0.0, value=0.0, format="%.2f")

# --- 4. VÝPOČTY A PREDIKCIA ---
if st.button("🚀 VYPOČÍTAŤ CENOVÚ PONUKU", use_container_width=True):
    if model:
        # Interné výpočty podľa tvojej logiky
        lojalita = zakaznici_db[vybrany_zakaznik]["lojalita"]
        krajina_kod = 1 if zakaznici_db[vybrany_zakaznik]["krajina"] == "SK" else 0
        
        # Geometria a hmotnosť (18. parameter)
        polomer_m = (d_val / 2) / 1000
        dlzka_m = l_val / 1000
        objem_m3 = math.pi * (polomer_m**2) * dlzka_m
        hmotnost_kg = objem_m3 * hustota
        
        # Príprava 18 vstupov pre model
        vstupy = np.array([[
            2026,            # 1. Rok
            2.0,             # 2. Mesiac (Február)
            17,              # 3. Deň
            pocet_kusov,     # 4. Množstvo
            0.5 * narocnost, # 5. Práca (odhad)
            1,               # 6. Počet strojov
            narocnost,       # 7. Náročnosť
            c_koop,          # 8. Kooperácia
            lojalita,        # 9. Lojalita
            krajina_kod,     # 10. Krajina
            1, 1, 1,         # 11, 12, 13. Strediská/Typy (Fixné)
            d_val,           # 14. Rozmer D
            l_val,           # 15. Rozmer L
            hustota,         # 16. Hustota
            c_mat_kg,        # 17. Cena za kg
            hmotnost_kg      # 18. Vypočítaná hmotnosť
        ]])

        # Samotná predpoveď
        predpovedana_cena = model.predict(vstupy)[0]

        # --- 5. ZOBRAZENIE VÝSLEDKOV ---
        st.markdown("---")
        res_col1, res_col2, res_col3 = st.columns(3)
        
        with res_col1:
            st.metric("Jednotková cena", f"{predpovedana_cena:.3f} €")
        
        with res_col2:
            st.metric("Celková cena", f"{predpovedana_cena * pocet_kusov:.2f} €")
            
        with res_col3:
            st.info(f"Hmotnosť kusu: {hmotnost_kg:.4f} kg")
            
        st.success("Predpoveď bola úspešne vygenerovaná modelom Gradient Boosting.")
    else:
        st.error("Model nie je k dispozícii. Skontrolujte prepojenie s GitHubom.")
