import streamlit as st
import pandas as pd
import joblib
import numpy as np
import requests
from io import BytesIO
from datetime import datetime
from fpdf import FPDF

# --- 1. KONFIGURÁCIA A NAČÍTANIE MODELOV ---
st.set_page_config(page_title="MECASYS AI Expert", layout="wide")

MODEL_URL = "https://raw.githubusercontent.com/Evulienka/mecasys-app/main/model_ceny.pkl"
ENCODERS_URL = "https://raw.githubusercontent.com/Evulienka/mecasys-app/main/encoders.pkl"
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

# --- 2. ČÍSELNÍK MATERIÁLOV S TVOJIMI PRESNÝMI HUSTOTAMI ---
MATERIAL_DATA = {
    "PLAST": {
        "PA": 1200, "PC": 1500, "PEEK": 1400, "PE-HD": 1000, 
        "PET-G": 1700, "PE-UHMW": 1000, "POM": 1500, "PP": 1000, "PVC": 1700
    },
    "OCEĽ": {
        "1.0037": 7900, "1.0038": 7900, "1.0039": 7900, "1.0044": 7900, "1.0045": 7900,
        "1.0117": 7900, "1.0308": 7900, "1.0425": 7900, "1.0460": 7900, "1.0503": 7900,
        "1.0570": 7900, "1.0576": 7900, "1.0577": 7900, "1.0710": 7900, "1.0715": 7900,
        "1.0718": 7900, "1.0762": 7900, "1.1141": 7900, "1.1191": 7900, "1.2343": 7900,
        "1.2367": 7900, "1.2379": 7900, "1.2510": 7900, "1.2738": 7900, "1.2842": 7900,
        "1.3243": 7900, "1.3343": 7900, "1.6580": 7900, "1.7131": 7900, "1.7225": 7900, "TOOLOX44": 7900
    },
    "NEREZ": {
        "1.4005": 8000, "1.4021": 8000, "1.4034": 8000, "1.4057": 8000, "1.4104": 8000,
        "1.4112": 8000, "1.4125": 8000, "1.4301": 8000, "1.4305": 8000, "1.4306": 8000,
        "1.4307": 8000, "1.4401": 8000, "1.4404": 8000, "1.4410": 8000, "1.4418": 8000,
        "1.4435": 8000, "1.4462": 8000, "1.4571": 8000, "1.5752": 8000
    },
    "FAREBNÉ KOVY": {
        "2.0371": 9000, "2.0401": 9000, "2.0402": 9000, "2.0975": 7800, "2.1020": 9000,
        "2.1285": 9000, "2.5083": 2900, "3.1255": 2900, "3.1645": 2900, "3.2315": 2900,
        "3.3206": 2900, "3.3547": 2900, "3.4365": 2900, "Titan Gr.5": 4500
    }
}

# --- 3. KOMPLETNÝ ZOZNAM ZÁKAZNÍKOV (110+) ---
CUSTOMER_MAP = {
    "A2B, s.r.o.": {"krajina": "SK", "lojalita": 0.83},
    "AAH PLASTICS Slovakia s. r. o.": {"krajina": "SK", "lojalita": 0.80},
    "Adient Innotec Metal Technologies s.r.o.": {"krajina": "SK", "lojalita": 0.31},
    "Adient Seating S.A.S.": {"krajina": "FR", "lojalita": 0.33},
    "Adient Seating Slovakia s.r.o.": {"krajina": "SK", "lojalita": 0.88},
    "Agromatic Regelungstechnik GmbH": {"krajina": "DE", "lojalita": 0.33},
    "Air International Thermal (Slovakia) s.r.o.": {"krajina": "SK", "lojalita": 0.33},
    "AKROMECA": {"krajina": "FR", "lojalita": 0.33},
    "Alkadur Robotsystems GmbH": {"krajina": "DE", "lojalita": 0.14},
    "AMINOXY LIMITED": {"krajina": "SK", "lojalita": 0.33},
    "ANDRITZ Separation GmbH": {"krajina": "DE", "lojalita": 0.19},
    "Anton Romaňák - KOVOTROM": {"krajina": "SK", "lojalita": 0.20},
    "Armaturen- und Autogengerätefabrik ewo": {"krajina": "DE", "lojalita": 0.06},
    "ATEM (Siège)": {"krajina": "FR", "lojalita": 0.56},
    "Avendor GmbH": {"krajina": "DE", "lojalita": 0.33},
    "Bayer Prototypen": {"krajina": "DE", "lojalita": 0.33},
    "BCF EUROPE s.r.o.": {"krajina": "SK", "lojalita": 0.88},
    "BelFox Torautomatik GmbH": {"krajina": "DE", "lojalita": 0.25},
    "Ben Innova Systemtechnik GmbH": {"krajina": "DE", "lojalita": 0.09},
    "BIA Plastic and Plating Technology": {"krajina": "SK", "lojalita": 0.33},
    "Bienen Ruck GmbH": {"krajina": "DE", "lojalita": 0.25},
    "Big Box, s.r.o.": {"krajina": "SK", "lojalita": 0.33},
    "Bograma AG": {"krajina": "SUI", "lojalita": 0.33},
    "Brückner Slovakia, s.r.o.": {"krajina": "SK", "lojalita": 0.75},
    "CABLEX SK s.r.o.": {"krajina": "SK", "lojalita": 0.57},
    "CD - profil s.r.o.": {"krajina": "SK", "lojalita": 0.50},
    "CIPI, s.r.o.": {"krajina": "SK", "lojalita": 0.40},
    "Craemer Slovakia, s. r. o.": {"krajina": "SK", "lojalita": 0.75},
    "Deutsche Wecotech GmbH": {"krajina": "DE", "lojalita": 0.33},
    "DISTLER ENGINEERING s.r.o.": {"krajina": "SK", "lojalita": 0.33},
    "DITIS Technology s.r.o.": {"krajina": "SK", "lojalita": 0.67},
    "Dominik Beňuš ALUMINIUM ORAVA": {"krajina": "SK", "lojalita": 0.67},
    "DSD NOELL GmbH": {"krajina": "DE", "lojalita": 0.33},
    "Dušan Mokošák": {"krajina": "SK", "lojalita": 0.67},
    "EBZ SysTec GmbH": {"krajina": "DE", "lojalita": 0.29},
    "ECCO Slovakia, a.s.": {"krajina": "SK", "lojalita": 0.67},
    "Edge Autonomy Riga SIA": {"krajina": "LT", "lojalita": 0.60},
    "EDM, s.r.o.": {"krajina": "SK", "lojalita": 0.33},
    "Elster s. r. o.": {"krajina": "SK", "lojalita": 0.75},
    "ERCE CZ, s.r.o.": {"krajina": "CZ", "lojalita": 0.75},
    "Eurostyle Systems Liptovský Mikuláš": {"krajina": "SK", "lojalita": 0.67},
    "EXAIL Robotics": {"krajina": "FR", "lojalita": 0.75},
    "EXCENT": {"krajina": "FR", "lojalita": 0.33},
    "Exerion Precision Technology Olomouc": {"krajina": "CZ", "lojalita": 0.33},
    "Fabryka Plastików Gliwice": {"krajina": "PL", "lojalita": 0.33},
    "FDonlinehandel": {"krajina": "DE", "lojalita": 0.33},
    "Franz Nüsing GmbH": {"krajina": "DE", "lojalita": 0.25},
    "Frauenthal Gnotec Slovakia": {"krajina": "SK", "lojalita": 0.18},
    "FREMACH TRNAVA, s.r.o.": {"krajina": "SK", "lojalita": 0.33},
    "GEDAST s. r. o.": {"krajina": "SK", "lojalita": 0.20},
    "GERGONNE SLOVENSKO s.r.o.": {"krajina": "SK", "lojalita": 0.75},
    "Gluematic GmbH": {"krajina": "DE", "lojalita": 0.25},
    "goracon systemtechnik GmbH": {"krajina": "DE", "lojalita": 0.33},
    "Groupe Plastivaloire": {"krajina": "SK", "lojalita": 0.71},
    "Guzik Pavol": {"krajina": "SK", "lojalita": 0.67},
    "H.Moryl GmbH": {"krajina": "DE", "lojalita": 0.33},
    "Hager & Meisinger GmbH": {"krajina": "DE", "lojalita": 0.33},
    "HARTS": {"krajina": "SK", "lojalita": 0.33},
    "HDF, s.r.o.": {"krajina": "SK", "lojalita": 0.25},
    "Heraldik Slovakia s. r. o.": {"krajina": "SK", "lojalita": 0.33},
    "HERN s.r.o.": {"krajina": "SK", "lojalita": 0.08},
    "Holz-Her Maschinenbau GmbH": {"krajina": "AT", "lojalita": 0.33},
    "Honeywell Corp": {"krajina": "USA", "lojalita": 0.33},
    "HYDAC Electronic, s.r.o.": {"krajina": "SK", "lojalita": 0.88},
    "Hyundai Glovis Czech Republic": {"krajina": "CZ", "lojalita": 0.80},
    "Hyundai Motor Manufacturing Czech": {"krajina": "CZ", "lojalita": 0.67},
    "IBEX GmbH": {"krajina": "DE", "lojalita": 0.33},
    "Ideal Fertigung": {"krajina": "DE", "lojalita": 0.33},
    "iGrow Network, s.r.o.": {"krajina": "SK", "lojalita": 0.17},
    "Ing. Róbert Palider": {"krajina": "SK", "lojalita": 0.33},
    "IRTS - Headquarters": {"krajina": "FR", "lojalita": 0.33},
    "ITW Slovakia s.r.o.": {"krajina": "SK", "lojalita": 0.67},
    "IWT Industrielle Wickeltechnologie": {"krajina": "DE", "lojalita": 0.33},
    "J.P.Plast Svatoborská": {"krajina": "CZ", "lojalita": 0.33},
    "JAFFA, s.r.o.": {"krajina": "SK", "lojalita": 0.67},
    "Jiří Řebíček - Metalplast": {"krajina": "CZ", "lojalita": 0.67},
    "JMP Plast s.r.o.": {"krajina": "SK", "lojalita": 0.70},
    "Josef Schwan GmbH": {"krajina": "DE", "lojalita": 0.25},
    "Jozef Barnáš JO - BA": {"krajina": "SK", "lojalita": 0.67},
    "Jozef Gender": {"krajina": "SK", "lojalita": 0.67},
    "JP-AUTO, s. r. o.": {"krajina": "SK", "lojalita": 0.33},
    "JUMI s.r.o. Košice": {"krajina": "SK", "lojalita": 0.33},
    "JWS Zerspanungstechnik GmbH": {"krajina": "DE", "lojalita": 0.33},
    "Kamil Bujňák - OBCHOD U KAMILA": {"krajina": "SK", "lojalita": 0.33},
    "KIRON": {"krajina": "DE", "lojalita": 0.33},
    "KOVOT s. r. o.": {"krajina": "SK", "lojalita": 0.80},
    "KOVOVÝROBA, spol. s r.o.": {"krajina": "SK", "lojalita": 0.33},
    "KOWA, s.r.o.": {"krajina": "SK", "lojalita": 0.33},
    "KREDUS, s.r.o.": {"krajina": "SK", "lojalita": 0.33},
    "KSA Benelux B.V.": {"krajina": "NL", "lojalita": 0.33},
    "KUHLA® Kühltechnik & Ladenbau": {"krajina": "DE", "lojalita": 0.33},
    "LEBEDA Tools s.r.o.": {"krajina": "CZ", "lojalita": 0.33},
    "LEPAL TECHNIK, spol. s r.o.": {"krajina": "SK", "lojalita": 0.33},
    "LETECH INDUSTRY s. r. o.": {"krajina": "SK", "lojalita": 0.33},
    "LinEx Slovakia, s. r. o.": {"krajina": "SK", "lojalita": 0.50},
    "LPH Vranov n/T, s.r.o.": {"krajina": "SK", "lojalita": 0.43},
    "Lubomir Hutlas": {"krajina": "SK", "lojalita": 0.67},
    "Lubomir Jagnešák": {"krajina": "SK", "lojalita": 0.80},
    "m conso s.r.o.": {"krajina": "SK", "lojalita": 0.33},
    "M.O.U.D. s. r. o.": {"krajina": "SK", "lojalita": 0.60},
    "MAGNA SLOVTECA, s.r.o.": {"krajina": "SK", "lojalita": 0.25},
    "MAGONTEC GmbH": {"krajina": "DE", "lojalita": 0.25},
    "MAHLE Behr Námestovo s.r.o.": {"krajina": "SK", "lojalita": 0.73},
    "MAPA-Tech GmbH": {"krajina": "DE", "lojalita": 0.33},
    "Mapes": {"krajina": "SK", "lojalita": 0.67},
    "Maschinenbau Dahme GmbH": {"krajina": "DE", "lojalita": 0.33},
    "Mäsovýroba SKURČÁK": {"krajina": "SK", "lojalita": 0.33},
    "MB SOLMETO": {"krajina": "LT", "lojalita": 0.33},
    "MBM MECANIQUE": {"krajina": "FR", "lojalita": 0.25},
    "MECASYS s.r.o.": {"krajina": "SK", "lojalita": 0.67},
    "Mergon CZ": {"krajina": "CZ", "lojalita": 0.25},
    "METAL STEEL INDUSTRY": {"krajina": "SK", "lojalita": 0.20},
    "Micro-Epsilon Inspection": {"krajina": "SK", "lojalita": 0.33},
    "Nanogate Slovakia s. r. o.": {"krajina": "SK", "lojalita": 0.63},
    "PWO Czech Republic a.s.": {"krajina": "CZ", "lojalita": 0.75},
    "RUDOS RUŽOMBEROK, s.r.o.": {"krajina": "SK", "lojalita": 0.67},
    "Schaeffler Skalica": {"krajina": "SK", "lojalita": 0.06},
    "SEC Technologies, s.r.o.": {"krajina": "SK", "lojalita": 0.80},
    "Yanfeng Namestovo": {"krajina": "SK", "lojalita": 0.82},
    "ZKW Slovakia s.r.o.": {"krajina": "SK", "lojalita": 0.44}
} 
    
if 'kosik' not in st.session_state:
    st.session_state.kosik = []

# --- 4. FUNKCIA PRE PDF ---
def create_pdf(data, cp_num, zakaznik):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(190, 10, f"Cenova ponuka: {cp_num}", ln=True, align='C')
    pdf.set_font("Arial", "", 12)
    pdf.cell(190, 10, f"Zakaznik: {zakaznik} | Datum: {datetime.now().strftime('%d.%m.%Y')}", ln=True, align='C')
    pdf.ln(10)
    pdf.set_fill_color(200, 220, 255)
    pdf.cell(45, 10, "ID dielu", 1, 0, 'C', True)
    pdf.cell(15, 10, "Ks", 1, 0, 'C', True)
    pdf.cell(45, 10, "Akost", 1, 0, 'C', True)
    pdf.cell(40, 10, "Hmotnost (kg)", 1, 0, 'C', True)
    pdf.cell(45, 10, "Cena AI (EUR/ks)", 1, 1, 'C', True)
    for item in data:
        pdf.cell(45, 10, str(item['id']), 1)
        pdf.cell(15, 10, str(item['ks']), 1)
        pdf.cell(45, 10, str(item['akost']), 1)
        pdf.cell(40, 10, f"{item['hmotnost']:.3f}", 1)
        pdf.cell(45, 10, f"{item.get('cena_ai', 0.0):.2f}", 1, 1)
    return pdf.output(dest='S').encode('latin-1')

# --- 5. ROZHRANIE A LOGIKA ---
st.title("📊 MECASYS: AI Expert (Final Version)")

if model and encoders:
    with st.sidebar:
        st.header("⚙️ Konfigurácia")
        cp_num = st.text_input("Číslo CP", f"CP-{datetime.now().year}-001")
        sel_cust = st.selectbox("Zákazník", sorted(list(CUSTOMER_MAP.keys())))
        cp_date = st.date_input("Dátum", datetime.now())
        f_krajina = CUSTOMER_MAP[sel_cust]["krajina"]
        f_lojalita = CUSTOMER_MAP[sel_cust]["lojalita"]
        st.info(f"📍 {f_krajina} | 🤝 Lojalita: {f_lojalita}")

    col1, col2 = st.columns(2)
    with col1:
        m_cat = st.selectbox("Materiál", sorted(list(MATERIAL_DATA.keys())))
    with col2:
        m_akost = st.selectbox(f"Akosť ({m_cat})", sorted(list(MATERIAL_DATA[m_cat].keys())))

    with st.form("main_form", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            item_id = st.text_input("ID dielu")
            qty = st.number_input("Ks", 1, 100000, 100)
        with c2:
            d_val = st.number_input("D (mm)", 0.1, 1000.0, 20.0)
            l_val = st.number_input("L (mm)", 0.1, 6000.0, 100.0)
        with c3:
            mat_c = st.number_input("Cena mat (€/ks)", 0.0, 10000.0, 1.0)
            time_e = st.number_input("Čas (hod/ks)", 0.001, 100.0, 0.2, format="%.3f")

        st.divider()
        r1, r2, r3 = st.columns(3)
        with r1: coop_c = st.number_input("Kooperácia (€)", 0.0, 10000.0, 0.0)
        with r2: complexity = st.selectbox("Náročnosť (1-5)", [1, 2, 3, 4, 5], index=2)
        with r3: tvar = st.selectbox("Tvar", ["KR", "PL", "6H", "4H"])

        if st.form_submit_button("➕ PRIDAŤ POLOŽKU"):
            hustota = MATERIAL_DATA[m_cat][m_akost]
            # 
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
        st.subheader("📋 Zoznam v ponuke")
        st.table(pd.DataFrame(st.session_state.kosik)[['id', 'ks', 'akost', 'hmotnost']])

        if st.button("🚀 GENEROVAŤ CENY AI", type="primary"):
            total_vol = sum(i['ks'] for i in st.session_state.kosik)
            
            for item in st.session_state.kosik:
                # --- BYPASS AKOSTI ---
                try:
                    akost_encoded = encoders['material_AKOST'].transform([item['akost']])[0]
                except ValueError:
                    akost_encoded = encoders['material_AKOST'].transform([encoders['material_AKOST'].classes_[0]])[0]
                
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
                    'material_AKOST': akost_encoded,
                    'tvar_polotovaru': encoders['tvar_polotovaru'].transform([item['tvar']])[0]
                }
                
                input_df = pd.DataFrame([row])[model.feature_names_in_]
                item['cena_ai'] = round(float(model.predict(input_df)[0]), 2)
            
            st.success("Ceny vypočítané.")
            st.dataframe(pd.DataFrame(st.session_state.kosik)[['id', 'ks', 'cena_ai']])
            
            pdf_bytes = create_pdf(st.session_state.kosik, cp_num, sel_cust)
            st.download_button("📥 STIAHNUŤ PDF", pdf_bytes, f"{cp_num}.pdf")
            try:
                requests.post(APPS_SCRIPT_URL, json=st.session_state.kosik, timeout=10)
            except: pass

        if st.button("🗑️ VYMAZAŤ"):
            st.session_state.kosik = []
            st.rerun()
else:
    st.error("Chyba načítania modelov.")

