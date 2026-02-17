import streamlit as st
import pandas as pd
import joblib
import numpy as np
import requests
from io import BytesIO
from datetime import datetime

# --- 1. NASTAVENIE STRÁNKY ---
st.set_page_config(page_title="MECASYS CP Expert", layout="wide")

# Link na tvoj model (Raw verzia)
MODEL_URL = "https://raw.githubusercontent.com/Evulienka/mecasys-app/main/model_ceny.pkl"

@st.cache_resource
def load_model(url):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return joblib.load(BytesIO(response.content))
    except Exception as e:
        st.error(f"❌ Chyba pri načítaní modelu: {e}")
        return None

model = load_model(MODEL_URL)

# --- 2. KONŠTANTY Z TVOJHO ORANGE DATASETU ---
krajiny = ['AT', 'CZ', 'DE', 'FR', 'GB', 'HU', 'LT', 'NL', 'PT', 'RO', 'SK', 'SUI', 'SWE']
materialy = ['FAREBNÉ KOVY', 'NEREZ', 'OCEĽ', 'PLAST']
akosti = ['1.4301', 'S235', 'S355', 'AW 6082', 'POM-C', '1.4404', '1.7131'] # Doplň podľa potreby

st.title("📊 MECASYS CP Expert Kalkulátor")
st.markdown("Predikcia ceny na základe modelu z Orange Data Mining (17 parametrov)")

if model:
    with st.form("expert_form"):
        c1, c2, c3 = st.columns(3)
        
        with c1:
            st.subheader("📅 Dokumentácia")
            cp_datum = st.date_input("CP_datum", datetime.now())
            cp_uspech = st.selectbox("CP_uspech", ['A', 'N'])
            zak_krajina = st.selectbox("zakaznik_krajina", krajiny, index=10) # SK default
            zak_lojalita = st.number_input("zakaznik_lojalita", value=0.85, step=0.01)

        with c2:
            st.subheader("⚙️ Výrobné parametre")
            n_komponent = st.number_input("n_komponent (množstvo ks)", value=100, step=1)
            v_narocnost = st.selectbox("v_narocnost", [1, 2, 3, 4, 5], index=0)
            cas_predpoklad = st.number_input("cas_v_predpoklad (hod)", value=0.5, step=0.1)
            ko_cena = st.number_input("ko_cena_komponent (€)", value=0.0, step=1.0)

        with c3:
            st.subheader("🛠️ Materiál a Rozmery")
            mat_nazov = st.selectbox("material_nazov", materialy)
            mat_akost = st.selectbox("material_AKOST", akosti)
            d_mm = st.number_input("D (mm)", value=20.0, step=0.1)
            l_mm = st.number_input("L (mm)", value=100.0, step=1.0)
            hustota = st.number_input("material_HUSTOTA (kg/m3)", value=7900)
            cena_mat_pred = st.number_input("cena_material_predpoklad (€/kg)", value=2.5, step=0.1)

        submit = st.form_submit_button("🚀 VYPOČÍTAŤ PREDIKCIU CENY", use_container_width=True)

    if submit:
        # --- VÝPOČTY (Feature Constructor z Orangeu) ---
        # 1. CP_objem (pôvodný parameter)
        objem = (np.pi * ((d_mm/2)/1000)**2 * (l_mm/1000))
        
        # 2. hmotnost (Nový parameter podľa tvojho vzorca: (3.14159 * D**2 * L * Hustota) / 4 000 000 000)
        # Tento vzorec v Orangei predpokladá D a L v mm a výsledok pravdepodobne v kg
        hmotnost = (3.14159 * (d_mm**2) * l_mm * hustota) / 4000000000

        # --- PRÍPRAVA DÁT PRE MODEL ---
        # Dôležité: Poradie stĺpcov musí byť IDENTICKÉ ako v Orangei
        vstupy = pd.DataFrame([{
            'CP_datum': cp_datum,
            'CP_objem': objem,
            'n_komponent': n_komponent,
            'cas_v_predpoklad_komponent (hod)': cas_predpoklad,
            'CP_uspech': cp_uspech,
            'v_narocnost': v_narocnost,
            'ko_cena_komponent': ko_cena,
            'zakaznik_lojalita': zak_lojalita,
            'zakaznik_krajina': zak_krajina,
            'material_nazov': mat_nazov,
            'tvar_polotovaru': 'KR', # Fixná hodnota podľa screenshotu
            'D(mm)': d_mm,
            'L(mm)': l_mm,
            'material_HUSTOTA': hustota,
            'cena_material_predpoklad': cena_mat_pred,
            'material_AKOST': mat_akost,
            'hmotnost': hmotnost   # 17. parameter pridaný na koniec
        }])

        try:
            # Predikcia
            predikcia = model.predict(vstupy)[0]
            
            # Zobrazenie výsledkov
            st.divider()
            r1, r2, r3 = st.columns(3)
            r1.metric("Predpokladaná cena / ks", f"{predikcia:.3f} €")
            r2.metric("Celková cena zákazky", f"{predikcia * n_komponent:.2f} €")
            r3.metric("Vypočítaná hmotnosť", f"{hmotnost:.4f} kg")
            
            st.toast("Výpočet prebehol úspešne!", icon="✅")
            
        except Exception as e:
            st.error(f"Chyba predikcie: {e}")
            st.info("Tip: Skontroluj, či sú v modeli zahrnuté všetky kategórie krajín a materiálov.")

else:
    st.warning("⌛ Čakám na načítanie modelu z tvojho GitHubu...")
