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

MODEL_URL = "https://raw.githubusercontent.com/Evulienka/mecasys-app/main/model_ceny.pkl"
ENCODERS_URL = "https://raw.githubusercontent.com/Evulienka/mecasys-app/main/encoders.pkl"

# --- 2. KOMPLETNÁ DATABÁZA ZÁKAZNÍKOV (Spracované zo všetkých príloh) ---
# Doplnené o chýbajúcich zákazníkov z posledných screenshotov
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
    "BCF EUROPE s.r.o": {"krajina": "SK", "lojalita": 0.88},
    "BelFox Torautomatik GmbH": {"krajina": "DE", "lojalita": 0.25},
    "Ben Innova Systemtechnik GmbH": {"krajina": "DE", "lojalita": 0.09},
    "BIA Plastic and Plating Technology Slovakia s.r.o.": {"krajina": "SK", "lojalita": 0.33},
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
    "Eurostyle Systems Liptovský Mikuláš s.r.o.": {"krajina": "SK", "lojalita": 0.67},
    "EXAIL Robotics": {"krajina": "FR", "lojalita": 0.75},
    "EXCENT": {"krajina": "FR", "lojalita": 0.33},
    "Exerion Precision Technology Olomouc s.r.o.": {"krajina": "CZ", "lojalita": 0.33},
    "Fabryka Plastików Gliwice": {"krajina": "PL", "lojalita": 0.33},
    "FDonlinehandel": {"krajina": "DE", "lojalita": 0.33},
    "Franz Nüsing GmbH & Co. KG": {"krajina": "DE", "lojalita": 0.25},
    "Frauenthal Gnotec Slovakia s.r.o.": {"krajina": "SK", "lojalita": 0.18},
    "FREMACH TRNAVA, s.r.o.": {"krajina": "SK", "lojalita": 0.33},
    "GEDAST s. r. o.": {"krajina": "SK", "lojalita": 0.20},
    "GERGONNE SLOVENSKO s.r.o.": {"krajina": "SK", "lojalita": 0.75},
    "Gluematic GmbH & Co.KG": {"krajina": "DE", "lojalita": 0.25},
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
    "Hyundai Glovis Czech Republic s.r.o.": {"krajina": "CZ", "lojalita": 0.80},
    "Hyundai Motor Manufacturing Czech s.r.o.": {"krajina": "CZ", "lojalita": 0.67},
    "IBEX GmbH": {"krajina": "DE", "lojalita": 0.33},
    "Ideal Fertigung": {"krajina": "DE", "lojalita": 0.33},
    "iGrow Network, s.r.o.": {"krajina": "SK", "lojalita": 0.17},
    "Ing. Róbert Palider": {"krajina": "SK", "lojalita": 0.33},
    "IRTS - Headquarters": {"krajina": "FR", "lojalita": 0.33},
    "ITW Slovakia s.r.o.": {"krajina": "SK", "lojalita": 0.67},
    "IWT Industrielle Wickeltechnologie GmbH": {"krajina": "DE", "lojalita": 0.33},
    "J.P.Plast Svatobořská": {"krajina": "CZ", "lojalita": 0.33},
    "JAFFA, s.r.o.": {"krajina": "SK", "lojalita": 0.67},
    "Jiří Řebíček - Metalplast, s.r.o.": {"krajina": "CZ", "lojalita": 0.67},
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
    "KUHLA® Kühltechnik & Ladenbau GmbH": {"krajina": "DE", "lojalita": 0.33},
    "LEBEDA Tools s.r.o.": {"krajina": "CZ", "lojalita": 0.33},
    "LEPAL TECHNIK, spol. s r.o.": {"krajina": "SK", "lojalita": 0.33},
    "LETECH INDUSTRY s. r. o.": {"krajina": "SK", "lojalita": 0.33},
    "LinEx Slovakia, s. r. o.": {"krajina": "SK", "lojalita": 0.50},
    "LPH Vranov n/T, s.r.o.": {"krajina": "SK", "lojalita": 0.43},
    "Lubomír Hutlas": {"krajina": "SK", "lojalita": 0.67},
    "Lubomír Jagnešák": {"krajina": "SK", "lojalita": 0.80},
    "m conso s.r.o.": {"krajina": "SK", "lojalita": 0.33},
    "M.O.U.D. s. r. o.": {"krajina": "SK", "lojalita": 0.60},
    "MAGNA SLOVTECA, s.r.o.": {"krajina": "SK", "lojalita": 0.25},
    "MAGONTEC GmbH": {"krajina": "DE", "lojalita": 0.25},
    "MAHLE Behr Námestovo s.r.o.": {"krajina": "SK", "lojalita": 0.73},
    "MAHLE Industrial Thermal Systems Námestovo s.r.o.": {"krajina": "SK", "lojalita": 0.67},
    "MAPA-Tech GmbH & Co. KG": {"krajina": "DE", "lojalita": 0.33},
    "Mapes": {"krajina": "SK", "lojalita": 0.67},
    "Maschinenbau Dahme GmbH": {"krajina": "DE", "lojalita": 0.33},
    "Maschinenfabrik Ludwig Berger GmbH": {"krajina": "AT", "lojalita": 0.33},
    "Mäsovýroba SKURČÁK, s. r. o.": {"krajina": "SK", "lojalita": 0.33},
    "Max Blank GmbH": {"krajina": "DE", "lojalita": 0.33},
    "maxon motor Hungary Kft": {"krajina": "HU", "lojalita": 0.33},
    "MB \"SOLMETO\"": {"krajina": "LT", "lojalita": 0.33},
    "MBM MECANIQUE": {"krajina": "FR", "lojalita": 0.25},
    "MBO Postpress Solutions GmbH": {"krajina": "DE", "lojalita": 0.17},
    "MB-TecSolutions GmbH": {"krajina": "DE", "lojalita": 0.25},
    "MECASYS s.r.o.": {"krajina": "SK", "lojalita": 0.67},
    "Mergon CZ": {"krajina": "CZ", "lojalita": 0.25},
    "METAL STEEL INDUSTRY, spol. s r.o.": {"krajina": "SK", "lojalita": 0.20},
    "Micro-Epsilon Inspection, s.r.o.": {"krajina": "SK", "lojalita": 0.33},
    "MINITUB SLOVAKIA spol. s r.o.": {"krajina": "SK", "lojalita": 0.17},
    "Miroslava Bartošová": {"krajina": "SK", "lojalita": 0.33},
    "MPM steel s. r. o.": {"krajina": "SK", "lojalita": 0.22},
    "Nanogate Slovakia s. r. o.": {"krajina": "SK", "lojalita": 0.63},
    "Nela Brüder Neumeister GmbH": {"krajina": "DE", "lojalita": 0.33},
    "Nicea s. r. o.": {"krajina": "SK", "lojalita": 0.33},
    "NR Craft, s.r.o.": {"krajina": "SK", "lojalita": 0.33},
    "NTV - náradie SK s. r. o.": {"krajina": "SK", "lojalita": 0.25},
    "OCEANSCAN - Marine Systems & Technology Lda": {"krajina": "PT", "lojalita": 0.45},
    "Ondrej Sandtner US ATYP": {"krajina": "SK", "lojalita": 0.33},
    "OR - METAL, s. r. o.": {"krajina": "SK", "lojalita": 0.67},
    "ORVEX spol. s r.o.": {"krajina": "SK", "lojalita": 0.67},
    "PackSys Global AG": {"krajina": "SUI", "lojalita": 0.32},
    "Pi-Tech Industrielle Dienstleistungen": {"krajina": "DE", "lojalita": 0.25},
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
    "RUDOS RUŽOMBEROK , s.r.o.": {"krajina": "SK", "lojalita": 0.67},
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
    "Taplast, Priemyselný park Géňa": {"krajina": "SK", "lojalita": 0.67},
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
    "Yanfeng International Automotive Technology": {"krajina": "SK", "lojalita": 0.75},
    "Yanfeng Namestovo": {"krajina": "SK", "lojalita": 0.82},
    "Železiarstvo Páleník s.r.o.": {"krajina": "SK", "lojalita": 0.33},
    "ZKW Slovakia s.r.o.": {"krajina": "SK", "lojalita": 0.44}
}

# --- 3. MATERIÁLY (Bez zmeny) ---
MATERIAL_MAP = {
    "Plast": {"PA": 1200, "PC": 1500, "PEEK": 1400, "PE-HD": 1000, "PET-G": 1700, "PE-UHMW": 1000, "POM": 1500, "PP": 1000, "PVC": 1700},
    "Oceľ": {
        "1.0037": 7900, "1.0038": 7900, "1.0039": 7900, "1.0044": 7900, "1.0045": 7900, "1.0117": 7900, "1.0308": 7900, 
        "1.0425": 7900, "1.0460": 7900, "1.0503": 7900, "1.0570": 7900, "1.0576": 7900, "1.0577": 7900, "1.0710": 7900, 
        "1.0715": 7900, "1.0718": 7900, "1.0762": 7900, "1.1141": 7900, "1.1191": 7900, "1.1213": 7900, "1.2343": 7900, 
        "1.2367": 7900, "1.2379": 7900, "1.2510": 7900, "1.2738": 7900, "1.2842": 7900, "1.3243": 7900, "1.3247": 7900, 
        "1.3343": 7900, "1.3505": 7900, "1.4571": 7900, "1.5060": 7900, "1.6323": 7900, "1.6580": 7900, "1.6773": 7900, 
        "1.7131": 7900, "1.7225": 7900, "1.7227": 7900, "1.8515": 7900, "TOOLOX44": 7900
    },
    "Nerez": {
        "1.4005": 8000, "1.4021": 8000, "1.4034": 8000, "1.4057": 8000, "1.4104": 8000, "1.4112": 8000, "1.4125": 8000, 
        "1.4301": 8000, "1.4305": 8000, "1.4306": 8000, "1.4307": 8000, "1.4401": 8000, "1.4404": 8000, "1.4405": 8000, 
        "1.4410": 8000, "1.4418": 8000, "1.4435": 8000, "1.4462": 8000, "1.4571": 8000, "1.5752": 8000
    },
    "Farebné kovy": {
        "2.0371": 9000, "2.0401": 9000, "2.0402": 9000, "2.0975": 9000, "2.1020": 9000, "2.1285": 9000, "2.5083": 2900, 
        "3.1255": 2900, "3.1325": 2900, "3.1355": 2900, "3.1645": 2900, "3.215": 2900, "3.2315": 2900, "3.3206": 2900, 
        "3.3207": 2900, "3.3211": 2900, "3.3547": 2900, "3.4365": 2900, "3.5312": 2900, "Titan Gr.2": 4500, "Titan Gr.5": 4500
    }
}

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
if 'kosik' not in st.session_state: st.session_state.kosik = []

# --- 4. ROZHRANIE ---
st.title("📊 MECASYS: Inteligentná Cenotvorba")

if model and encoders:
    # Sekcia Zákazník
    with st.container(border=True):
        c1, c2, c3 = st.columns([1, 2, 1])
        with c1: cp_number = st.text_input("📝 Číslo CP", "CP-2026-001")
        with c2:
            customer_options = ["--- NOVÝ ZÁKAZNÍK ---"] + sorted(list(CUSTOMER_MAP.keys()))
            sel_customer = st.selectbox("🤝 Výber zákazníka", customer_options)
        with c3: cp_date = st.date_input("📅 Dátum", datetime.now())

    # Logika zákazníka
    if sel_customer == "--- NOVÝ ZÁKAZNÍK ---":
        final_cust_name = st.text_input("Názov novej firmy")
        final_krajina = st.selectbox("Krajina", sorted(encoders['zakaznik_krajina'].classes_))
        final_lojalita = 0.50
        st.info("💡 Lojalita pre nového zákazníka je automaticky nastavená na 0.50")
    else:
        final_cust_name = sel_customer
        final_krajina = CUSTOMER_MAP[sel_customer]["krajina"]
        final_lojalita = CUSTOMER_MAP[sel_customer]["lojalita"]
        st.success(f"✅ Overený zákazník: {final_cust_name} | Krajina: {final_krajina} | Lojalita: {final_lojalita}")

    # Sekcia Položka
    with st.form("input_form"):
        st.subheader("🛠️ Parametre komponentu")
        r1c1, r1c2, r1c3, r1c4 = st.columns(4)
        with r1c1: item_id = st.text_input("ID dielu / Pozícia")
        with r1c2: qty = st.number_input("Počet kusov", 1, 50000, 100)
        with r1c3:
            mat_cat = st.selectbox("Kategória materiálu", list(MATERIAL_MAP.keys()))
            mat_akosti = sorted(list(MATERIAL_MAP[mat_cat].keys())) + ["INÝ (zadať ručne)"]
            sel_akost = st.selectbox("Akosť", mat_akosti)
        with r1c4:
            diam = st.number_input("Priemer D (mm)", 0.0, 1000.0, 20.0)
            length = st.number_input("Dĺžka L (mm)", 0.0, 6000.0, 100.0)

        # Logika vlastného materiálu
        if sel_akost == "INÝ (zadať ručne)":
            custom_akost = st.text_input("Názov novej akosti")
            custom_hustota = st.number_input("Hustota (kg/m3)", 500, 20000, 7900)
            active_akost, active_hustota = (custom_akost if custom_akost else "Neznáma"), custom_hustota
        else:
            active_akost, active_hustota = sel_akost, MATERIAL_MAP[mat_cat][sel_akost]

        st.divider()
        r2c1, r2c2, r2c3, r2c4 = st.columns(4)
        with r2c1: mat_cost = st.number_input("Mat. náklady (€/ks)", 0.0, 5000.0, 2.5)
        with r2c2: coop_cost = st.number_input("Kooperácia (€/ks)", 0.0, 5000.0, 0.0)
        with r2c3: time_est = st.number_input("Čas (hod/ks)", 0.01, 100.0, 0.2)
        with r2c4: complexity = st.select_slider("Náročnosť", options=[1,2,3,4,5], value=3)

        if st.form_submit_button("📥 PRIDAŤ DO PONUKY"):
            weight = (np.pi * (diam**2) * length * active_hustota) / 4000000000
            st.session_state.kosik.append({
                "id": item_id, "zakaznik": final_cust_name, "krajina": final_krajina, "lojalita": final_lojalita,
                "ks": qty, "kategoria": mat_cat, "akost": active_akost, "hustota": active_hustota,
                "hmotnost": round(weight, 4), "d": diam, "l": length, "cas": time_est, 
                "mat_cena": mat_cost, "koop": coop_cost, "narocnost": complexity,
                "objem_v": (np.pi * ((diam/2)/1000)**2 * (length/1000)) * qty
            })
            st.rerun()

    # Zobrazenie výsledkov
    if st.session_state.kosik:
        st.subheader("📋 Aktuálna ponuka")
        df_out = pd.DataFrame(st.session_state.kosik)
        st.dataframe(df_out[['id', 'zakaznik', 'akost', 'ks', 'hmotnost']], use_container_width=True)

        if st.button("🚀 GENEROVAŤ CENY AI", type="primary"):
            total_vol = sum(i['objem_v'] for i in st.session_state.kosik)
            for item in st.session_state.kosik:
                # Ošetrenie neznámych hodnôt pre model
                enc_akost = item['akost'] if item['akost'] in encoders['material_AKOST'].classes_ else encoders['material_AKOST'].classes_[0]
                enc_mat = item['kategoria'] if item['kategoria'] in encoders['material_nazov'].classes_ else encoders['material_nazov'].classes_[0]
                
                row = {
                    'kvartal': float((cp_date.month-1)//3+1), 'mesiac': float(cp_date.month),
                    'CP_objem': float(total_vol), 'n_komponent': float(item['ks']),
                    'cas_v_predpoklad_komponent (hod)': float(item['cas']), 'CP_uspech': 1.0,
                    'v_narocnost': float(item['narocnost']), 'ko_cena_komponent': float(item['koop']),
                    'zakaznik_lojalita': float(item['lojalita']), 
                    'zakaznik_krajina': encoders['zakaznik_krajina'].transform([item['krajina']])[0],
                    'material_nazov': encoders['material_nazov'].transform([enc_mat])[0],
                    'tvar_polotovaru': encoders['tvar_polotovaru'].transform(['KR'])[0],
                    'D(mm)': float(item['d']), 'L(mm)': float(item['l']),
                    'material_HUSTOTA': float(item['hustota']), 'cena_material_predpoklad': float(item['mat_cena']),
                    'material_AKOST': encoders['material_AKOST'].transform([enc_akost])[0],
                    'hmotnost': float(item['hmotnost'])
                }
                pred_df = pd.DataFrame([row])[model.feature_names_in_]
                item['cena_ai'] = round(float(model.predict(pred_df)[0]), 2)
            
            st.success("Ceny vypočítané!")
            st.dataframe(pd.DataFrame(st.session_state.kosik)[['id', 'akost', 'ks', 'cena_ai']], use_container_width=True)
