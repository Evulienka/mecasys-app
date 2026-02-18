import streamlit as st
import pandas as pd
import joblib
import numpy as np
import requests
from io import BytesIO
from datetime import datetime
from fpdf import FPDF

# --- 1. KONFIGURÁCIA ZDROJOV ---
st.set_page_config(page_title="MECASYS AI Expert", layout="wide")

MODEL_URL = "https://raw.githubusercontent.com/Evulienka/mecasys-app/main/model_ceny.pkl"
ENCODERS_URL = "https://raw.githubusercontent.com/Evulienka/mecasys-app/main/encoders.pkl"
# URL tvojho Google Apps Scriptu pre zápis do tabuľky
APPS_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbz_7fFmD_Y6V8P0A-L-fR_J_T-vY7h8U_E1Y-l-Y_Y/exec"

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

# --- 2. KOMPLETNÝ ČÍSELNÍK MATERIÁLOV A HUSTOTY ---
MATERIAL_DATA = {
    "PLAST": {
        "PA": 1200, "PC": 1500, "PEEK": 1400, "PE-HD": 1000, 
        "PET-G": 1700, "PE-UHMW": 1000, "POM": 1500, "PP": 1000, "PVC": 1700
    },
    "OCEĽ": {
        "1.6580": 7900, "1.0037": 7900, "1.0038": 7900, "1.0039": 7900, "1.0044": 7900,
        "1.0045": 7900, "1.0117": 7900, "1.0308": 7900, "1.0425": 7900, "1.0460": 7900,
        "1.0503": 7900, "1.0570": 7900, "1.0576": 7900, "1.0577": 7900, "1.0710": 7900,
        "1.0715": 7900, "1.0718": 7900, "1.0762": 7900, "1.1141": 7900, "1.1191": 7900,
        "1.2343": 7900, "1.2367": 7900, "1.2379": 7900, "1.2510": 7900, "1.2738": 7900,
        "1.2842": 7900, "1.3243": 7900, "1.3343": 7900, "1.7131": 7900, "1.7225": 7900, 
        "TOOLOX44": 7900
    },
    "NEREZ": {
        "1.4435": 8000, "1.4005": 8000, "1.4021": 8000, "1.4034": 8000, "1.4057": 8000,
        "1.4104": 8000, "1.4112": 8000, "1.4125": 8000, "1.4301": 8000, "1.4305": 8000,
        "1.4306": 8000, "1.4307": 8000, "1.4401": 8000, "1.4404": 8000, "1.4410": 8000,
        "1.4418": 8000, "1.4462": 8000, "1.4571": 8000, "1.5752": 8000
    },
    "FAREBNÉ KOVY": {
        "2.0371": 9000, "2.0401": 9000, "2.0402": 9000, "2.0975": 9000, "2.1020": 9000,
        "2.1285": 9000, "2.5083": 9000, "3.1255": 2900, "3.1645": 2900, "3.2315": 2900,
        "3.3206": 2900, "3.3547": 2900, "3.4365": 2900, "Titan Gr.5": 4500
    }
}

# --- 3. KOMPLETNÝ ZOZNAM ZÁKAZNÍKOV ---
CUSTOMER_MAP = {
    "A2B, s.r.o.": {"krajina": "SK", "lojalita": 0.833},
    "AAH PLASTICS Slovakia s. r. o.": {"krajina": "SK", "lojalita": 0.800},
    "Adient Innotec Metal Technologies s.r.o.": {"krajina": "SK", "lojalita": 0.312},
    "Adient Seating S.A.S.": {"krajina": "FR", "lojalita": 0.333},
    "Adient Seating Slovakia s.r.o.": {"krajina": "SK", "lojalita": 0.882},
    "BIA Plastic and Plating Technology": {"krajina": "SK", "lojalita": 0.333},
    "Brückner Slovakia, s.r.o.": {"krajina": "SK", "lojalita": 0.750},
    "CABLEX SK s.r.o.": {"krajina": "SK", "lojalita": 0.571},
    "Craemer Slovakia, s. r. o.": {"krajina": "SK", "lojalita": 0.750},
    "EBZ SysTec GmbH": {"krajina": "DE", "lojalita": 0.286},
    "ERCE CZ, s.r.o.": {"krajina": "CZ", "lojalita": 0.750},
    "Exerion Precision Technology": {"krajina": "CZ", "lojalita": 0.333},
    "Frauenthal Gnotec Slovakia": {"krajina": "SK", "lojalita": 0.182},
    "GERGONNE SLOVENSKO s.r.o.": {"krajina": "SK", "lojalita": 0.750},
    "HYDAC Electronic, s.r.o.": {"krajina": "SK", "lojalita": 0.875},
    "Hyundai Glovis Czech Republic": {"krajina": "CZ", "lojalita": 0.800},
    "MAHLE Behr Námestovo s.r.o.": {"krajina": "SK", "lojalita": 0.727},
    "MECASYS s.r.o.": {"krajina": "SK", "lojalita": 0.667},
    "Nanogate Slovakia s. r. o.": {"krajina": "SK", "lojalita": 0.625},
    "PackSys Global AG": {"krajina": "SUI", "lojalita": 0.320},
    "PWO Czech Republic a.s.": {"krajina": "CZ", "lojalita": 0.750},
    "SEC Technologies, s.r.o.": {"krajina": "SK", "lojalita": 0.800},
    "Yanfeng Namestovo": {"krajina": "SK", "lojalita": 0.820},
    "ZKW Slovakia s.r.o.": {"krajina": "SK", "lojalita": 0.444}
}

if 'kosik' not in st.session_state:
    st.session_state.kosik = []

# --- 4. FUNKCIA PDF GENERÁTORA ---
def create_pdf(data, cp_num, zakaznik):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(190, 10, f"Cenova ponuka: {cp_num}", ln=True, align='C')
    pdf.set_font("Arial", "", 12)
    pdf.cell(190, 10, f"Zakaznik: {zakaznik} | Datum: {datetime.now().strftime('%d.%m.%Y')}", ln=True, align='C')
    pdf.ln(10)
    pdf.set_fill_color(200, 220, 255)
    pdf.cell(50, 10, "ID dielu", 1, 0, 'C', True)
    pdf.cell(20, 10, "Ks", 1, 0, 'C', True)
    pdf.cell(60, 10, "Akost", 1, 0, 'C', True)
    pdf.cell(55, 10, "Cena AI (EUR/ks)", 1, 1, 'C', True)
    for item in data:
        pdf.cell(50, 10, str(item['id']), 1)
        pdf.cell(20, 10, str(item['ks']), 1)
        pdf.cell(60, 10, str(item['akost']), 1)
        pdf.cell(55, 10, f"{item.get('cena_ai', 0.0):.2f}", 1, 1)
    return pdf.output(dest='S').encode('latin-1')

# --- 5. HLAVNÁ LOGIKA A UI ---
st.title("📊 MECASYS: AI Expert (Full System)")

if model and encoders:
    with st.sidebar:
        st.header("⚙️ Nastavenia CP")
        cp_num = st.text_input("Číslo CP", f"CP-{datetime.now().year}-001")
        sel_cust = st.selectbox("Zákazník", sorted(list(CUSTOMER_MAP.keys())))
        cp_date = st.date_input("Dátum vystavenia", datetime.now())
        f_krajina = CUSTOMER_MAP[sel_cust]["krajina"]
        f_lojalita = CUSTOMER_MAP[sel_cust]["lojalita"]
        st.info(f"📍 {f_krajina} | 🤝 Lojalita: {f_lojalita}")

    st.subheader("🛠️ Parametre komponentu")
    
    # Dynamický výber materiálu (okamžitá reakcia)
    col_mat1, col_mat2 = st.columns(2)
    with col_mat1:
        m_cat = st.selectbox("Kategória materiálu", sorted(list(MATERIAL_DATA.keys())))
    with col_mat2:
        m_akost = st.selectbox(f"Akosť pre {m_cat}", sorted(list(MATERIAL_DATA[m_cat].keys())))

    with st.form("input_form", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            item_id = st.text_input("ID dielu / Číslo výkresu")
            qty = st.number_input("n_komponent (ks)", 1, 100000, 100)
        with c2:
            d_val = st.number_input("D (mm)", 0.1, 1000.0, 20.0)
            l_val = st.number_input("L (mm)", 0.1, 6000.0, 100.0)
        with c3:
            mat_c = st.number_input("cena_material_predpoklad (€/ks)", 0.0, 10000.0, 1.0)
            time_e = st.number_input("cas_v_predpoklad_komponent (hod/ks)", 0.001, 100.0, 0.2, format="%.3f")

        st.divider()
        r1, r2, r3 = st.columns(3)
        with r1:
            coop_c = st.number_input("ko_cena_komponent (€/ks)", 0.0, 10000.0, 0.0)
        with r2:
            complexity = st.selectbox("v_narocnost (1-5)", [1, 2, 3, 4, 5], index=2)
        with r3:
            tvar = st.selectbox("tvar_polotovaru", ["KR", "PL", "6H", "4H"])

        if st.form_submit_button("➕ PRIDAŤ DO ZOZNAMU"):
            hustota = MATERIAL_DATA[m_cat][m_akost]
            # 
            # Výpočet hmotnosti (D^2 * pi / 4 * L * hustota / 10^9 pre kg)
            weight = (np.pi * (d_val**2) * l_val * hustota) / 4000000000
            
            st.session_state.kosik.append({
                "id": item_id, "ks": qty, "kategoria": m_cat, "akost": m_akost,
                "hustota": hustota, "hmotnost": weight, "d": d_val, "l": l_val,
                "cas": time_e, "mat_cena": mat_c, "kooperacia": coop_c,
                "narocnost": complexity, "krajina": f_krajina, "lojalita": f_lojalita,
                "tvar": tvar
            })
            st.rerun()

    if st.session_state.kosik:
        st.divider()
        st.subheader("📋 Položky v aktuálnej ponuke")
        st.table(pd.DataFrame(st.session_state.kosik)[['id', 'ks', 'akost', 'hmotnost']])

        if st.button("🚀 GENEROVAŤ CENY AI MODELOM", type="primary"):
            total_vol = sum(i['ks'] for i in st.session_state.kosik)
            
            for item in st.session_state.kosik:
                # 
                # Logika napĺňania parametrov podľa tréningu modelu
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
                    'v_narocnost': float(item['narocnost']),
                    'CP_uspech': encoders['CP_uspech'].transform(['A'])[0],
                    'zakaznik_krajina': encoders['zakaznik_krajina'].transform([item['krajina']])[0],
                    'material_nazov': encoders['material_nazov'].transform([item['kategoria']])[0],
                    'material_AKOST': encoders['material_AKOST'].transform([item['akost']])[0],
                    'tvar_polotovaru': encoders['tvar_polotovaru'].transform([item['tvar']])[0]
                }
                
                # Predikcia bez akýchkoľvek zásahov
                input_df = pd.DataFrame([row])[model.feature_names_in_]
                item['cena_ai'] = round(float(model.predict(input_df)[0]), 2)
            
            st.success("AI Model úspešne vypočítal ceny!")
            st.dataframe(pd.DataFrame(st.session_state.kosik)[['id', 'ks', 'akost', 'cena_ai']])
            
            # PDF Export
            pdf_bytes = create_pdf(st.session_state.kosik, cp_num, sel_cust)
            st.download_button("📥 STIAHNUŤ PDF PONUKU", pdf_bytes, f"{cp_num}.pdf")
            
            # Zápis do Google tabuľky
            try:
                requests.post(APPS_SCRIPT_URL, json=st.session_state.kosik, timeout=10)
                st.toast("Dáta boli uložené do Google tabuľky.")
            except:
                st.error("Nepodarilo sa pripojiť k Google tabuľke.")

        if st.button("🗑️ VYMAZAŤ CELÝ ZOZNAM"):
            st.session_state.kosik = []
            st.rerun()
else:
    st.error("Chyba: Nepodarilo sa načítať AI model alebo Encodery z GitHubu.")
