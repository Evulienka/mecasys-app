import streamlit as st
import pandas as pd
import joblib
import numpy as np
import requests
from io import BytesIO
from datetime import datetime

# --- 1. NAČÍTANIE MODELU ---
st.set_page_config(page_title="MECASYS CP Expert", layout="wide")

MODEL_URL = "https://raw.githubusercontent.com/Evulienka/mecasys-app/main/model_ceny.pkl"

@st.cache_resource
def load_model(url):
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        return joblib.load(BytesIO(response.content))
    except Exception as e:
        st.error(f"❌ Nepodarilo sa načítať model: {e}")
        return None

model = load_model(MODEL_URL)

# --- 2. MOŽNOSTI VÝBERU ---
krajiny = ['AT', 'CZ', 'DE', 'FR', 'GB', 'HU', 'LT', 'NL', 'PT', 'RO', 'SK', 'SUI', 'SWE']
materialy = ['FAREBNÉ KOVY', 'NEREZ', 'OCEĽ', 'PLAST']
akosti = ['1.4301', 'S235', 'S355', 'AW 6082', 'POM-C', '1.4404', '1.7131', '1.2379', 'ETG100']

st.title("📊 MECASYS CP Expert Kalkulátor")

if model:
    with st.form("expert_form"):
        c1, c2, c3 = st.columns(3)
        
        with c1:
            st.subheader("📅 Čas a Klient")
            datum_vyber = st.date_input("Dátum CP", datetime.now())
            cp_uspech = st.selectbox("CP_uspech", ['A', 'N'])
            zak_krajina = st.selectbox("zakaznik_krajina", krajiny, index=10)
            zak_lojalita = st.number_input("zakaznik_lojalita", value=0.85)

        with c2:
            st.subheader("⚙️ Výroba")
            n_komponent = st.number_input("n_komponent (ks)", value=100)
            v_narocnost = st.selectbox("v_narocnost", [1, 2, 3, 4, 5], index=0)
            cas_predpoklad = st.number_input("cas_v_predpoklad_komponent (hod)", value=0.5)
            ko_cena = st.number_input("ko_cena_komponent (€)", value=0.0)

        with c3:
            st.subheader("🛠️ Rozmery a Materiál")
            mat_nazov = st.selectbox("material_nazov", materialy)
            mat_akost = st.selectbox("material_AKOST", akosti)
            d_mm = st.number_input("D(mm)", value=20.0)
            l_mm = st.number_input("L(mm)", value=100.0)
            hustota = st.number_input("material_HUSTOTA", value=7900)
            cena_mat_pred = st.number_input("cena_material_predpoklad", value=2.5)

        submit = st.form_submit_button("🚀 VYPOČÍTAŤ PREDIKCIU CENY", use_container_width=True)

    if submit:
        # --- AUTOMATICKÉ VÝPOČTY ---
        mesiac = datum_vyber.month
        kvartal = (datum_vyber.month - 1) // 3 + 1
        objem = (np.pi * ((d_mm/2)/1000)**2 * (l_mm/1000))
        hmotnost = (3.14159 * (d_mm**2) * l_mm * hustota) / 4000000000

        # --- ZOSTAVENIE DATAFRAME V PRESNOM PORADÍ ---
        # Poradie stĺpcov musí byť identické s Orange trénovacím datasetom
        vstupy = pd.DataFrame([{
            'kvartal': kvartal,
            'mesiac': mesiac,
            'CP_objem': objem,
            'n_komponent': n_komponent,
            'cas_v_predpoklad_komponent (hod)': cas_predpoklad,
            'CP_uspech': cp_uspech,
            'v_narocnost': v_narocnost,
            'ko_cena_komponent': ko_cena,
            'zakaznik_lojalita': zak_lojalita,
            'zakaznik_krajina': zak_krajina,
            'material_nazov': mat_nazov,
            'tvar_polotovaru': 'KR',
            'D(mm)': d_mm,
            'L(mm)': l_mm,
            'material_HUSTOTA': hustota,
            'cena_material_predpoklad': cena_mat_pred,
            'material_AKOST': mat_akost,
            'hmotnost': hmotnost
        }])

        try:
            # Reindexácia zabezpečí, že poradie stĺpcov je VŽDY presne takéto
            stlpce_poradie = [
                'kvartal', 'mesiac', 'CP_objem', 'n_komponent', 
                'cas_v_predpoklad_komponent (hod)', 'CP_uspech', 'v_narocnost', 
                'ko_cena_komponent', 'zakaznik_lojalita', 'zakaznik_krajina', 
                'material_nazov', 'tvar_polotovaru', 'D(mm)', 'L(mm)', 
                'material_HUSTOTA', 'cena_material_predpoklad', 'material_AKOST', 'hmotnost'
            ]
            vstupy = vstupy[stlpce_poradie]

            predikcia = model.predict(vstupy)[0]
            
            st.success(f"### Odhadovaná cena: {predikcia:.3f} €")
            st.info(f"Vypočítaná hmotnosť: {hmotnost:.4f} kg | Objem: {objem:.6f} m3")
            
        except Exception as e:
            st.error(f"Chyba pri výpočte: {e}")
            st.write("Skontrolujte, či poradie stĺpcov v modeli zodpovedá tabuľke.")
