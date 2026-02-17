import streamlit as st
import pandas as pd
import joblib
import numpy as np
import requests
from io import BytesIO
from datetime import datetime

# --- 1. KONFIGURÁCIA A NAČÍTANIE MODELU ---
st.set_page_config(page_title="MECASYS CP Expert", layout="wide")

# Odkazy na tvoje súbory na GitHube
MODEL_URL = "https://raw.githubusercontent.com/Evulienka/mecasys-app/main/model_ceny.pkl"
ENCODERS_URL = "https://raw.githubusercontent.com/Evulienka/mecasys-app/main/encoders.pkl"

# TVOJA URL ADRESA Z GOOGLE APPS SCRIPTU
SCRIPT_URL = "https://script.google.com/macros/s/AKfycby0sZtFiuyjj8LNlQPcDTAOTILNBYsrknRi73QWUx1shqGEfqU8u874NTZEFZBnVKCw/exec"

@st.cache_resource
def load_assets():
    try:
        m_resp = requests.get(MODEL_URL, timeout=15)
        model = joblib.load(BytesIO(m_resp.content))
        e_resp = requests.get(ENCODERS_URL, timeout=15)
        encoders = joblib.load(BytesIO(e_resp.content))
        return model, encoders
    except Exception as e:
        st.error(f"❌ Chyba pri načítaní AI modelu: {e}")
        return None, None

model, encoders = load_assets()

# --- 2. GRAFICKÉ ROZHRANIE (FORMULÁR) ---
st.title("📊 MECASYS CP Expert")
st.markdown("AI výpočet ceny s automatickou evidenciou do Google Sheets")

if model and encoders:
    # Dynamické načítanie kategórií z encoderov
    krajiny = encoders['zakaznik_krajina'].classes_
    materialy = encoders['material_nazov'].classes_
    akosti = encoders['material_AKOST'].classes_

    with st.form("expert_form"):
        c1, c2, c3 = st.columns(3)
        
        with c1:
            st.subheader("👤 Klient")
            datum_vyber = st.date_input("Dátum CP", datetime.now())
            zak_lojalita = st.number_input("Lojalita zákazníka (0.0 - 1.0)", value=0.85, step=0.01)
            zak_krajina_raw = st.selectbox("Krajina", krajiny)
            cp_uspech_raw = st.selectbox("Úspech (A/N)", ['A', 'N'])

        with c2:
            st.subheader("⚙️ Parametre výroby")
            n_komponent = st.number_input("Množstvo (ks)", min_value=1, value=100)
            v_narocnost = st.selectbox("Náročnosť výroby (1-5)", [1, 2, 3, 4, 5])
            cas_predpoklad = st.number_input("Odhadovaný čas (hod/ks)", value=0.5, step=0.1)
            ko_cena = st.number_input("Kooperácia celkom (€)", value=0.0)

        with c3:
            st.subheader("🛠️ Materiál a Rozmery")
            mat_nazov_raw = st.selectbox("Typ materiálu", materialy)
            mat_akost_raw = st.selectbox("Akosť materiálu", akosti)
            d_mm = st.number_input("Priemer D (mm)", value=20.0)
            l_mm = st.number_input("Dĺžka L (mm)", value=100.0)
            hustota = st.number_input("Hustota (kg/m3)", value=7900)
            cena_mat_kg = st.number_input("Cena materiálu (€/kg)", value=2.5)

        submit = st.form_submit_button("🚀 VYPOČÍTAŤ CENU A ULOŽIŤ DO TABUĽKY", use_container_width=True)

    if submit:
        # --- 3. VÝPOČTY PRE MODEL ---
        mesiac = datum_vyber.month
        kvartal = (datum_vyber.month - 1) // 3 + 1
        objem = (np.pi * ((d_mm/2)/1000)**2 * (l_mm/1000))
        # Výpočet hmotnosti v kg
        hmotnost = (3.14159 * (d_mm**2) * l_mm * hustota) / 4000000000

        try:
            # --- 4. PRÍPRAVA DÁT PRE AI MODEL ---
            input_dict = {
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
                'cena_material_predpoklad': float(cena_mat_kg),
                'material_AKOST': encoders['material_AKOST'].transform([mat_akost_raw])[0],
                'hmotnost': float(hmotnost)
            }
            
            vstupy_df = pd.DataFrame([input_dict])
            
            # Zoradenie stĺpcov podľa modelu
            if hasattr(model, 'feature_names_in_'):
                vstupy_df = vstupy_df[model.feature_names_in_]

            # PREDIKCIA
            predikcia = model.predict(vstupy_df)[0]
            
            # ZOBRAZENIE VÝSLEDKOV
            st.success(f"### Odhadovaná cena: {predikcia:.3f} € / ks")
            st.info(f"Celková hodnota zákazky: {predikcia * n_komponent:.2f} €")

            # --- 5. AUTOMATICKÝ ZÁPIS DO GOOGLE SHEETS ---
            payload = {
                "lojalita": zak_lojalita,
                "narocnost": v_narocnost,
                "krajina": zak_krajina_raw,
                "material": mat_nazov_raw,
                "akost": mat_akost_raw,
                "d_mm": d_mm,
                "l_mm": l_mm,
                "hmotnost": round(hmotnost, 4),
                "pocet_ks": n_komponent,
                "cena": round(predikcia, 3)
            }
            
            # Odoslanie požiadavky na tvoj Apps Script
            response = requests.post(SCRIPT_URL, json=payload, timeout=10)
            
            if response.status_code == 200:
                st.toast("Dáta boli úspešne uložené v Google Sheets!", icon="✅")
            else:
                st.warning("Cena bola vypočítaná, ale nepodarilo sa ju uložiť do tabuľky.")

        except Exception as e:
            st.error(f"Chyba pri spracovaní dát: {e}")
else:
    st.warning("Čakám na pripojenie k AI modelom na GitHub-e...")

# Päta aplikácie
st.divider()
st.caption("MECASYS Expert System v2.0 | Prepojené s Google Sheets")
