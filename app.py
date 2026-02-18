import streamlit as st
import pandas as pd
import joblib
import numpy as np
import requests
from io import BytesIO
from datetime import datetime
from fpdf import FPDF

# --- 1. NAČÍTANIE ASSETOV ---
st.set_page_config(page_title="MECASYS AI Expert", layout="wide")

MODEL_URL = "https://raw.githubusercontent.com/Evulienka/mecasys-app/main/model_ceny.pkl"
ENCODERS_URL = "https://raw.githubusercontent.com/Evulienka/mecasys-app/main/encoders.pkl"
APPS_SCRIPT_URL = "https://script.google.com/macros/s/AKfycby0sZtFiuyjj8LNlQPcDTAOTILNBYsrknRi73QWUx1shqGEfqU8u874NTZEFZBnVKCw/exec"

@st.cache_resource
def load_assets():
    try:
        m_resp = requests.get(MODEL_URL, timeout=15)
        model = joblib.load(BytesIO(m_resp.content))
        e_resp = requests.get(ENCODERS_URL, timeout=15)
        encoders = joblib.load(BytesIO(e_resp.content))
        return model, encoders
    except:
        return None, None

model, encoders = load_assets()

# --- 2. KOMPLETNÁ DATABÁZA (Materiály a Zákazníci) ---
MATERIAL_DATA = {
    "PLAST": {"PA": 1200, "PC": 1500, "PEEK": 1400, "PE-HD": 1000, "POM": 1410, "PP": 910},
    "OCEĽ": {"1.0037": 7850, "1.0570": 7850, "1.0715": 7850, "1.2379": 7850, "1.7225": 7850},
    "NEREZ": {"1.4301": 8000, "1.4305": 8000, "1.4404": 8000, "1.4571": 8000, "1.4021": 7750, "1.4057": 7750, "1.4462": 7800},
    "FAREBNÉ KOVY": {"2.0401": 8500, "3.3547": 2700, "3.4365": 2800, "Titan Gr.5": 4430}
}

CUSTOMER_MAP = {
    "A2B, s.r.o.": {"krajina": "SK", "lojalita": 0.833},
    "AAH PLASTICS Slovakia s. r. o.": {"krajina": "SK", "lojalita": 0.800},
    "Adient Seating Slovakia s.r.o.": {"krajina": "SK", "lojalita": 0.882},
    "ZKW Slovakia s.r.o.": {"krajina": "SK", "lojalita": 0.444},
    "Yanfeng Namestovo": {"krajina": "SK", "lojalita": 0.820},
    "MAHLE Behr Námestovo s.r.o.": {"krajina": "SK", "lojalita": 0.727},
    "Brückner Slovakia, s.r.o.": {"krajina": "SK", "lojalita": 0.750},
    "PWO Czech Republic a.s.": {"krajina": "CZ", "lojalita": 0.750},
    "Exerion Precision Technology": {"krajina": "CZ", "lojalita": 0.333},
    "PackSys Global AG": {"krajina": "SUI", "lojalita": 0.320},
    # Tu môžete pokračovať v dopĺňaní zvyšných mien...
}

if 'kosik' not in st.session_state:
    st.session_state.kosik = []

# --- 3. UI FORMULÁR ---
st.header("📊 AI Kalkulácia Ceny (Výhradne podľa modelu)")

if model and encoders:
    with st.sidebar:
        st.subheader("Parametre ponuky")
        cp_num = st.text_input("Číslo CP", f"CP-{datetime.now().year}-001")
        sel_cust = st.selectbox("Zákazník", sorted(list(CUSTOMER_MAP.keys())))
        cp_date = st.date_input("Dátum", datetime.now())
        
        # Automatické načítanie lojality a krajiny pre model
        f_krajina = CUSTOMER_MAP[sel_cust]["krajina"]
        f_lojalita = CUSTOMER_MAP[sel_cust]["lojalita"]

    # Vstup položky
    with st.container(border=True):
        st.subheader("Pridanie dielu do kalkulácie")
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            item_id = st.text_input("ID dielu")
            qty = st.number_input("Počet kusov (n_komponent)", 1, 100000, 100)
        with c2:
            m_cat = st.selectbox("Materiál (kategória)", sorted(list(MATERIAL_DATA.keys())))
            m_akost = st.selectbox("Akosť", sorted(list(MATERIAL_DATA[m_cat].keys())))
        with c3:
            diam = st.number_input("Priemer D (mm)", 0.1, 1000.0, 20.0)
            length = st.number_input("Dĺžka L (mm)", 0.1, 6000.0, 100.0)
        with c4:
            mat_c = st.number_input("Mat. cena (€/ks)", 0.0, 10000.0, 1.0)
            time_e = st.number_input("Čas (hod/ks)", 0.0, 100.0, 0.2)

        c5, c6, c7 = st.columns(3)
        with c5: coop_c = st.number_input("Kooperácia (€/ks)", 0.0, 10000.0, 0.0)
        with c6: complexity = st.selectbox("Vizuálna náročnosť (v_narocnost)", ["1", "2", "3", "4", "5"], index=2)
        with c7: 
            st.write("") 
            if st.button("➕ PRIDAŤ POLOŽKU", use_container_width=True):
                # DOPÁROVANIE HUSTOTY A VÝPOČET HMOTNOSTI (Feature Constructor Logic)
                hustota = MATERIAL_DATA[m_cat][m_akost]
                hmotnost = (np.pi * (diam**2) * length * hustota) / 4000000000
                
                st.session_state.kosik.append({
                    "id": item_id, "ks": qty, "kategoria": m_cat, "akost": m_akost,
                    "hustota": hustota, "hmotnost": hmotnost, "d": diam, "l": length,
                    "cas": time_e, "mat_cena": mat_c, "kooperacia": coop_c,
                    "narocnost": complexity, "krajina": f_krajina, "lojalita": f_lojalita
                })
                st.rerun()

    # --- 4. PREDIKCIA ---
    if st.session_state.kosik:
        st.subheader("Položky v aktuálnej ponuke")
        df_view = pd.DataFrame(st.session_state.kosik)
        st.dataframe(df_view[['id', 'ks', 'akost', 'mat_cena', 'cas']])

        if st.button("🚀 GENEROVAŤ CENY MODELOM", type="primary"):
            # VÝPOČET CP_objem (Súčet všetkých n_komponent v košíku)
            total_vol = sum(i['ks'] for i in st.session_state.kosik)
            
            for item in st.session_state.kosik:
                # Príprava dátového riadku pre model
                row = {
                    'CP_objem': float(total_vol),
                    'n_komponent': float(item['ks']),
                    'cas_v_predpoklad_komponent (hod)': float(item['cas']),
                    'ko_cena_komponent': float(item['kooperacia']),
                    'zakaznik_lojalita': float(item['lojalita']),
                    'D(mm)': float(item['d']),
                    'L(mm)': float(item['l']),
                    'material_HUSTOTA': float(item['hustota']),
                    'cena_material_predpoklad': float(item['mat_cena']),
                    'hmotnost': float(item['hmotnost']),
                    'kvartal': float((cp_date.month-1)//3+1),
                    'mesiac': float(cp_date.month),
                    # Transformácia kategórií cez Encodery
                    'CP_uspech': encoders['CP_uspech'].transform(['A'])[0],
                    'v_narocnost': encoders['v_narocnost'].transform([str(item['narocnost'])])[0],
                    'zakaznik_krajina': encoders['zakaznik_krajina'].transform([item['krajina']])[0],
                    'material_nazov': encoders['material_nazov'].transform([item['kategoria']])[0],
                    'material_AKOST': encoders['material_AKOST'].transform([item['akost']])[0],
                    'tvar_polotovaru': encoders['tvar_polotovaru'].transform(['KR'])[0]
                }
                
                # Zoradenie stĺpcov podľa modelu a predikcia
                input_df = pd.DataFrame([row])[model.feature_names_in_]
                item['cena_ai'] = round(float(model.predict(input_df)[0]), 2)
            
            st.success("Ceny vygenerované!")
            st.table(pd.DataFrame(st.session_state.kosik)[['id', 'ks', 'cena_ai']])
