import streamlit as st
import pandas as pd
import joblib
import numpy as np
import requests
from io import BytesIO
from datetime import datetime
from fpdf import FPDF

# --- 1. KONFIGURÁCIA ---
st.set_page_config(page_title="MECASYS CP Expert", layout="wide")

# TVOJ LINK Z OBRÁZKA (Apps Script Web App URL)
APPS_SCRIPT_URL = "https://script.google.com/macros/s/AKfycby0sZtFiuyjj8LNlQPcDTAOTILNBYsrknRi73QWUx1shqGEfqU8u874NTZEFZBnVKCw/exec"

MODEL_URL = "https://raw.githubusercontent.com/Evulienka/mecasys-app/main/model_ceny.pkl"
ENCODERS_URL = "https://raw.githubusercontent.com/Evulienka/mecasys-app/main/encoders.pkl"

@st.cache_resource
def load_assets():
    try:
        m_resp = requests.get(MODEL_URL, timeout=10)
        model = joblib.load(BytesIO(m_resp.content))
        e_resp = requests.get(ENCODERS_URL, timeout=10)
        encoders = joblib.load(BytesIO(e_resp.content))
        return model, encoders
    except: return None, None

model, encoders = load_assets()

# --- 2. AKTUALIZOVANÁ DATABÁZA ZÁKAZNÍKOV (DOPLNENÁ O TVOJE SCREENSHOTY) ---
CUSTOMER_MAP = {
    # Z tvojho prvého screenshotu
    "RUETZ TECHNOLOGIES GmbH": {"krajina": "DE", "lojalita": 0.33},
    "RWT GmbH": {"krajina": "DE", "lojalita": 0.33},
    "SAG Innovations GmbH": {"krajina": "AT", "lojalita": 0.20},
    "SAS CONSTRUCTION INSTALLATION ELECTRIQL": {"krajina": "FR", "lojalita": 0.67},
    "Schaeffler Skalica, spol. s r.o.": {"krajina": "SK", "lojalita": 0.06},
    "Schiller Automation GmbH & Co. KG": {"krajina": "DE", "lojalita": 0.33},
    "SCHOCK GmbH": {"krajina": "DE", "lojalita": 0.33},
    "SEC Technologies, s.r.o.": {"krajina": "SK", "lojalita": 0.80},
    "seele pilsen s.r.o.": {"krajina": "CZ", "lojalita": 0.29},
    "Seolutions, s. r. o.": {"krajina": "SK", "lojalita": 0.20},
    "SEZ DK a. s.": {"krajina": "SK", "lojalita": 0.75},
    "Silkroad Truckparts": {"krajina": "LT", "lojalita": 0.33},
    "SITEC GmbH Sicherheitstechnik": {"krajina": "DE", "lojalita": 0.20},
    "SKM GmbH": {"krajina": "DE", "lojalita": 0.33},
    "SLER Plastic s.r.o.": {"krajina": "SK", "lojalita": 0.17},
    "Slovak Techno Export - Plastymat s.r.o.": {"krajina": "SK", "lojalita": 0.25},
    "SLUZBA NITRA, s.r.o.": {"krajina": "SK", "lojalita": 0.44},
    "SN Maschinenbau": {"krajina": "DE", "lojalita": 0.33},
    "Specac Ltd.": {"krajina": "GB", "lojalita": 0.33},
    "Städtler + Beck GmbH": {"krajina": "DE", "lojalita": 0.33},
    "Stahlotec GmbH": {"krajina": "DE", "lojalita": 0.25},
    "Stieber GmbH": {"krajina": "DE", "lojalita": 0.33},
    "SUG GmbH & Co. KG": {"krajina": "DE", "lojalita": 0.33},
    "SUMITOMO (SHI) CYCLO DRIVE GERMANY GmbH": {"krajina": "DE", "lojalita": 0.33},
    "Taplast": {"krajina": "SK", "lojalita": 0.67},
    "THERMOPLASTIK s.r.o.": {"krajina": "SK", "lojalita": 0.29},
    "Thomas GmbH": {"krajina": "DE", "lojalita": 0.20},
    "THYZONA s.r.o.": {"krajina": "SK", "lojalita": 0.33},
    "TOPSOLID CZECH, s.r.o.": {"krajina": "CZ", "lojalita": 0.67},
    "Tousek Ges.m.b.H": {"krajina": "AT", "lojalita": 0.25},
    "UPT, s.r.o.": {"krajina": "SK", "lojalita": 0.25},
    "Veeser Plastic Slovakia k. s.": {"krajina": "SK", "lojalita": 0.25},
    "VENIO, s.r.o.": {"krajina": "SK", "lojalita": 0.33},
    "Visteon Electronics Slovakia s. r. o.": {"krajina": "SK", "lojalita": 0.57},
    "Vladimír Tarci - PRIMASPOJ": {"krajina": "SK", "lojalita": 0.33},
    "W. Hartmann & Co (GmbH & Co KG)": {"krajina": "DE", "lojalita": 0.33},
    "WEGU SLOVAKIA s.r.o.": {"krajina": "SK", "lojalita": 0.33},
    "Wildkart Deutschland AG & Co.KG": {"krajina": "DE", "lojalita": 0.17},
    "Witzenmann Slovakia spol. s r. o.": {"krajina": "SK", "lojalita": 0.17},
    "Yanfeng International": {"krajina": "SK", "lojalita": 0.75},
    "Yanfeng Namestovo": {"krajina": "SK", "lojalita": 0.82},
    "Železiarstvo Páleník s.r.o.": {"krajina": "SK", "lojalita": 0.33},
    "ZKW Slovakia s.r.o.": {"krajina": "SK", "lojalita": 0.44},
    # Z tvojho druhého screenshotu
    "Lubomir Jagnešák": {"krajina": "SK", "lojalita": 0.80},
    "m conso s.r.o.": {"krajina": "SK", "lojalita": 0.33},
    "M.O.U.D. s. r. o.": {"krajina": "SK", "lojalita": 0.60},
    "MAGNA SLOVTECA, s.r.o.": {"krajina": "SK", "lojalita": 0.25},
    "MAGONTEC GmbH": {"krajina": "DE", "lojalita": 0.25},
    "MAHLE Behr Námestovo s.r.o.": {"krajina": "SK", "lojalita": 0.73},
    "MAHLE Industrial Thermal Systems": {"krajina": "SK", "lojalita": 0.67},
    "MAPA-Tech GmbH & Co. KG": {"krajina": "DE", "lojalita": 0.33},
    "Mapes": {"krajina": "SK", "lojalita": 0.67},
    "Maschinenbau Dahme GmbH": {"krajina": "DE", "lojalita": 0.33},
    "Maschinenfabrik Ludwig Berger GmbH": {"krajina": "AT", "lojalita": 0.33},
    "Mäsovýroba SKURČÁK, s. r. o.": {"krajina": "SK", "lojalita": 0.33},
    "Max Blank GmbH": {"krajina": "DE", "lojalita": 0.33},
    "maxon motor Hungary Kft": {"krajina": "HU", "lojalita": 0.33},
    "MB SOLMETO": {"krajina": "LT", "lojalita": 0.33},
    "MBM MECANIQUE": {"krajina": "FR", "lojalita": 0.25},
    "MBO Postpress Solutions GmbH": {"krajina": "DE", "lojalita": 0.17},
    "MB-TecSolutions GmbH": {"krajina": "DE", "lojalita": 0.25},
    "MECASYS s.r.o.": {"krajina": "SK", "lojalita": 0.67},
    "Mergon CZ": {"krajina": "CZ", "lojalita": 0.25},
    "METAL STEEL INDUSTRY": {"krajina": "SK", "lojalita": 0.20},
    "Micro-Epsilon Inspection, s.r.o.": {"krajina": "SK", "lojalita": 0.33},
    "MINITUB SLOVAKIA spol. s r.o.": {"krajina": "SK", "lojalita": 0.17},
    "Miroslava Bartošová": {"krajina": "SK", "lojalita": 0.33},
    "MPM steel s. r. o.": {"krajina": "SK", "lojalita": 0.22},
    "Nanogate Slovakia s. r. o.": {"krajina": "SK", "lojalita": 0.63},
    "Nela Brüder Neumeister GmbH": {"krajina": "DE", "lojalita": 0.33},
    "Nicea s. r. o.": {"krajina": "SK", "lojalita": 0.33},
    "NR Craft, s.r.o.": {"krajina": "SK", "lojalita": 0.33},
    "NTV - náradie SK s. r. o.": {"krajina": "SK", "lojalita": 0.25},
    "OCEANSCAN": {"krajina": "PT", "lojalita": 0.45},
    "Ondrej Sandtner US ATYP": {"krajina": "SK", "lojalita": 0.33},
    "OR - METAL, s. r. o.": {"krajina": "SK", "lojalita": 0.67},
    "ORVEX spol. s r.o.": {"krajina": "SK", "lojalita": 0.67},
    "PackSys Global AG": {"krajina": "SUI", "lojalita": 0.32},
    "Pi-Tech": {"krajina": "DE", "lojalita": 0.25},
    "Pneufit s. r. o.": {"krajina": "SK", "lojalita": 0.67},
    "PRAX": {"krajina": "FR", "lojalita": 0.75},
    "PROKS PLASTIC s.r.o.": {"krajina": "CZ", "lojalita": 0.75},
    "ProMatur": {"krajina": "DE", "lojalita": 0.33},
    "PWO Czech Republic a.s.": {"krajina": "CZ", "lojalita": 0.75},
    "Quintenz Hybridtechnik GmbH": {"krajina": "DE", "lojalita": 0.33},
    "Rapid Technic AG": {"krajina": "SUI", "lojalita": 0.33},
    "RECA plastics GmbH": {"krajina": "DE", "lojalita": 0.33},
    "Rehnen GmbH & Co KG": {"krajina": "DE", "lojalita": 0.17},
    "Rotodecor GmbH": {"krajina": "DE", "lojalita": 0.33},
    "RUDOS RUŽOMBEROK, s.r.o.": {"krajina": "SK", "lojalita": 0.67}
}

# --- 3. DATABÁZA MATERIÁLOV ---
MATERIAL_MAP = {
    "Plast": {"PA": 1200, "PC": 1500, "PEEK": 1400, "PE-HD": 1000, "POM": 1500, "PP": 1000},
    "Oceľ": {"1.0037": 7900, "1.0570": 7900, "1.0715": 7900, "1.2379": 7900, "1.7225": 7900},
    "Nerez": {
        "1.4301": 8000, "1.4305": 8000, "1.4404": 8000, "1.4571": 8000, 
        "1.4021": 8000, "1.4057": 8000, "1.4462": 8000
    },
    "Farebné kovy": {"2.0401": 9000, "3.3547": 2900, "3.4365": 2900, "Titan Gr.5": 4500}
}

# --- 4. FUNKCIE PRE GOOGLE SHEETS A PDF ---
def send_to_google_script(data_list):
    try:
        payload = []
        for item in data_list:
            payload.append({
                "datum": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "cp_cislo": item['cp_cislo'],
                "id_dielu": item['id'],
                "lojalita": item['lojalita'],
                "narocnost": item['narocnost'],
                "krajina": item['krajina'],
                "cena_ai": item['cena_ai']
            })
        response = requests.post(APPS_SCRIPT_URL, json=payload, timeout=15)
        return response.status_code == 200
    except: return False

def create_pdf(data, cp_num, cust_name):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, f"Cenová ponuka: {cp_num}", ln=True, align='C')
    pdf.set_font("Arial", size=12)
    pdf.cell(0, 10, f"Zákazník: {cust_name}", ln=True)
    pdf.ln(10)
    pdf.set_fill_color(220, 220, 220)
    pdf.cell(40, 10, "ID dielu", 1, 0, 'C', True)
    pdf.cell(40, 10, "Ks", 1, 0, 'C', True)
    pdf.cell(50, 10, "Cena AI (€/ks)", 1, 1, 'C', True)
    for item in data:
        pdf.cell(40, 10, str(item['id']), 1)
        pdf.cell(40, 10, str(item['ks']), 1)
        pdf.cell(50, 10, f"{item.get('cena_ai', 0):.2f}", 1, 1)
    return pdf.output(dest='S').encode('latin-1')

# --- 5. HLAVNÁ APLIKÁCIA ---
if 'kosik' not in st.session_state: st.session_state.kosik = []

st.title("📊 MECASYS: AI Cenotvorba")

if model and encoders:
    with st.container(border=True):
        c1, c2, c3 = st.columns([1, 2, 1])
        with c1: cp_number = st.text_input("📝 Číslo CP", "CP-2026-001")
        with c2:
            cust_list = ["--- NOVÝ ZÁKAZNÍK ---"] + sorted(list(CUSTOMER_MAP.keys()))
            sel_customer = st.selectbox("🤝 Výber zákazníka", cust_list)
        with c3: cp_date = st.date_input("📅 Dátum", datetime.now())

    if sel_customer == "--- NOVÝ ZÁKAZNÍK ---":
        f_cust, f_krajina, f_lojalita = st.text_input("Názov firmy"), st.selectbox("Krajina", sorted(encoders['zakaznik_krajina'].classes_)), st.number_input("Lojalita", 0.0, 1.0, 0.5, step=0.01)
    else:
        f_cust, f_krajina, f_lojalita = sel_customer, CUSTOMER_MAP[sel_customer]["krajina"], CUSTOMER_MAP[sel_customer]["lojalita"]
        st.info(f"✅ Lojalita: {f_lojalita:.2f} | Krajina: {f_krajina}")

    with st.form("item_form"):
        r1, r2, r3 = st.columns(3)
        with r1: 
            item_id = st.text_input("ID dielu")
            qty = st.number_input("Ks", 1, 50000, 100)
        with r2:
            m_cat = st.selectbox("Kategória", list(MATERIAL_MAP.keys()))
            m_akost = st.selectbox("Akosť", sorted(list(MATERIAL_MAP[m_cat].keys())), key=f"ak_{m_cat}")
        with r3:
            diam, length = st.number_input("D (mm)", 0.0, 1000.0, 20.0), st.number_input("L (mm)", 0.0, 6000.0, 100.0)
        
        st.divider()
        r4, r5, r6 = st.columns(3)
        with r4: mat_c = st.number_input("Mat (€/ks)", 0.0, 5000.0, 2.5)
        with r5: time_e = st.number_input("Čas (hod/ks)", 0.01, 100.0, 0.2)
        with r6: complexity = st.select_slider("Náročnosť", [1,2,3,4,5], 3)

        if st.form_submit_button("PRIDAŤ DO PONUKY"):
            weight = (np.pi * (diam**2) * length * MATERIAL_MAP[m_cat][m_akost]) / 4000000000
            st.session_state.kosik.append({
                "id": item_id, "zakaznik": f_cust, "krajina": f_krajina, "lojalita": f_lojalita,
                "ks": qty, "kategoria": m_cat, "akost": m_akost, "hustota": MATERIAL_MAP[m_cat][m_akost],
                "hmotnost": weight, "d": diam, "l": length, "cas": time_e, "mat_cena": mat_c, 
                "narocnost": complexity, "cp_cislo": cp_number, "objem_v": (np.pi * ((diam/2)/1000)**2 * (length/1000)) * qty
            })
            st.rerun()

    if st.session_state.kosik:
        st.subheader("Položky v ponuke")
        st.dataframe(pd.DataFrame(st.session_state.kosik)[['id', 'ks', 'akost']])
        
        if st.button("🚀 GENEROVAŤ CENY A ULOŽIŤ", type="primary"):
            total_vol = sum(i['objem_v'] for i in st.session_state.kosik)
            for item in st.session_state.kosik:
                row = {
                    'kvartal': float((cp_date.month-1)//3+1), 'mesiac': float(cp_date.month),
                    'CP_objem': float(total_vol), 'n_komponent': float(item['ks']),
                    'cas_v_predpoklad_komponent (hod)': float(item['cas']), 'CP_uspech': 1.0,
                    'v_narocnost': float(item['narocnost']), 'ko_cena_komponent': 0.0,
                    'zakaznik_lojalita': float(item['lojalita']), 
                    'zakaznik_krajina': encoders['zakaznik_krajina'].transform([item['krajina']])[0],
                    'material_nazov': encoders['material_nazov'].transform([item['kategoria']])[0],
                    'tvar_polotovaru': encoders['tvar_polotovaru'].transform(['KR'])[0],
                    'D(mm)': float(item['d']), 'L(mm)': float(item['l']),
                    'material_HUSTOTA': float(item['hustota']), 'cena_material_predpoklad': float(item['mat_cena']),
                    'material_AKOST': encoders['material_AKOST'].transform([item['akost']])[0],
                    'hmotnost': float(item['hmotnost'])
                }
                pred_df = pd.DataFrame([row])[model.feature_names_in_]
                item['cena_ai'] = round(float(model.predict(pred_df)[0]), 2)
            
            if send_to_google_script(st.session_state.kosik):
                st.success("✅ Ponuka bola vypočítaná a úspešne zapísaná do Google Tabuľky!")
            else:
                st.warning("⚠️ Ceny sú OK, ale zápis do tabuľky neprebehol (skontroluj pripojenie).")
            
            st.dataframe(pd.DataFrame(st.session_state.kosik)[['id', 'ks', 'cena_ai']])
            pdf_b = create_pdf(st.session_state.kosik, cp_number, f_cust)
            st.download_button("📄 Stiahnuť PDF ponuku", pdf_b, f"{cp_number}.pdf", "application/pdf")
