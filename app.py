import streamlit as st
import pandas as pd
import joblib
import numpy as np
import requests
from io import BytesIO
from datetime import datetime

# --- 1. KONFIGURÁCIA A NAČÍTANIE AKTÍV ---
st.set_page_config(page_title="MECASYS CP Expert", layout="wide")

# URL adresy na tvoje súbory na Githube
MODEL_URL = "https://raw.githubusercontent.com/Evulienka/mecasys-app/main/model_ceny.pkl"
ENCODERS_URL = "https://raw.githubusercontent.com/Evulienka/mecasys-app/main/encoders.pkl"

@st.cache_resource
def load_assets():
    try:
        # Načítanie modelu
        m_resp = requests.get(MODEL_URL, timeout=15)
        model = joblib.load(BytesIO(m_resp.content))
        
        # Načítanie encoderov
        e_resp = requests.get(ENCODERS_URL, timeout=15)
        encoders = joblib.load(BytesIO(e_resp.content))
        
        return model, encoders
    except Exception as e:
        st.error(f"❌ Chyba pri načítaní assetov: {e}")
        return None, None

model, encoders = load_assets()

st.title("📊 MECASYS CP Expert Kalkulátor")

if model and encoders:
    # --- 2. DYNAMICKÉ MOŽNOSTI (získané priamo z encoderov) ---
    # Predpokladáme, že encoders je slovník, kde kľúče sú názvy stĺpcov
    try:
        krajiny = encoders['zakaznik_krajina'].classes_
        materialy = encoders['material_nazov'].classes_
        akosti = encoders['material_AKOST'].classes_
    except:
        # Záložné riešenie, ak je štruktúra iná
        krajiny = ['SK', 'DE', 'AT', 'CZ'] 
        materialy = ['OCEĽ', 'NEREZ', 'PLAST']
        akosti = ['1.4301', 'S235']

    with st.form("expert_form"):
        c1, c2, c3 = st.columns(3)
        with c1:
            datum_vyber = st.date_input("Dátum CP", datetime.now())
            cp_uspech_raw = st.selectbox("CP_uspech", ['A', 'N'])
            zak_krajina_raw = st.selectbox("zakaznik_krajina", krajiny)
            zak_lojalita = st.number_input("zakaznik_lojalita", value=0.85)
        with c2:
            n_komponent = st.number_input("n_komponent (ks)", value=100)
            v_narocnost = st.selectbox("v_narocnost", [1, 2, 3, 4, 5])
            cas_predpoklad = st.number_input("cas_v_predpoklad (hod)", value=0.5)
            ko_cena = st.number_input("ko_cena_komponent (€)", value=0.0)
        with c3:
            mat_nazov_raw = st.selectbox("material_nazov", materialy)
            mat_akost_raw = st.selectbox("material_AKOST", akosti)
            d_mm = st.number_input("D(mm)", value=20.0)
            l_mm = st.number_input("L(mm)", value=100.0)
            hustota = st.number_input("material_HUSTOTA", value=7900)
            cena_mat_pred = st.number_input("cena_material_predpoklad", value=2.5)

        submit = st.form_submit_button("🚀 VYPOČÍTAŤ PREDIKCIU CENY", use_container_width=True)

    if submit:
        # VÝPOČTY
        mesiac = datum_vyber.month
        kvartal = (datum_vyber.month - 1) // 3 + 1
        objem = (np.pi * ((d_mm/2)/1000)**2 * (l_mm/1000))
        hmotnost = (3.14159 * (d_mm**2) * l_mm * hustota) / 4000000000

        # TRANSFORMÁCIA POMOCOU ENCODEROV
        try:
            # Každý textový vstup preženieme cez príslušný encoder
            data = {
                'kvartal': float(kvartal),
                'mesiac': float(mesiac),
                'CP_objem': float(objem),
                'n_komponent': float(n_komponent),
                'cas_v_predpoklad_komponent (hod)': float(cas_predpoklad),
                'CP_uspech': encoders['CP_uspech'].transform([cp_uspech_raw])[0],
                'v_narocnost': float(v_narocnost),
                'ko_cena_komponent': float(ko_cena),
                'zakaznik_lojalita': float(zak_lojalita),
                'zakaznik_krajina': encoders['zakaznik_krajina'].transform([zak_krajina_raw])[0],
                'material_nazov': encoders['material_nazov'].transform([mat_nazov_raw])[0],
                'tvar_polotovaru': encoders['tvar_polotovaru'].transform(['KR'])[0],
                'D(mm)': float(d_mm),
                'L(mm)': float(l_mm),
                'material_HUSTOTA': float(hustota),
                'cena_material_predpoklad': float(cena_mat_pred),
                'material_AKOST': encoders['material_AKOST'].transform([mat_akost_raw])[0],
                'hmotnost': float(hmotnost)
            }
            
            vstupy = pd.DataFrame([data])
            
            # Zoradenie stĺpcov podľa modelu
            if hasattr(model, 'feature_names_in_'):
                vstupy = vstupy[model.feature_names_in_]

            predikcia = model.predict(vstupy)[0]
            st.success(f"### Odhadovaná cena: {predikcia:.3f} €")
            
        except Exception as e:
            st.error(f"Chyba pri transformácii dát: {e}")
