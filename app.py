import streamlit as st
import pandas as pd
import joblib
import os
import numpy as np
from datetime import datetime
from fpdf import FPDF

# --- 1. KONFIGURÁCIA STRÁNKY ---
st.set_page_config(page_title="MECASYS CP Kalkulátor", layout="wide")

# --- 2. NAČÍTANIE MODELU ---
@st.cache_resource
def load_model():
    try:
        return joblib.load('model_forest.pkl')
    except Exception as e:
        return None

model = load_model()

# --- 3. DATABÁZA MATERIÁLOV, AKOSTÍ A HUSTOT ---
materialy_db = {
    "FAREBNÉ KOVY": {
        "akosti": {
            "2.0371": 8500, "2.0401": 8500, "2.0402": 8500, "2.0975": 7600, 
            "2.1020": 8800, "2.1285": 8800, "2.5083": 2700, "3.1255": 2800, 
            "3.1325": 2800, "3.1355": 2800, "3.1645": 2800, "3.215": 2700, 
            "3.2315": 2700, "3.3206": 2700, "3.3207": 2700, "3.3211": 2700, 
            "3.3547": 2700, "3.4365": 2800, "3.5312": 1800, 
            "3.7035 (Titán)": 4500, "3.7165 (Titán)": 4500
        }
    },
    "NEREZ": {
        "predvolena_hustota": 8000,
        "akosti": ["1.4435", "1.4005", "1.4021", "1.4034", "1.4057", "1.4104", 
                   "1.4112", "1.4125", "1.4301", "1.4305", "1.4306", "1.4307", 
                   "1.4401", "1.4404", "1.4405", "1.4410", "1.4418", "1.4462", 
                   "1.4571", "1.5752"]
    },
    "OCEĽ": {
        "predvolena_hustota": 7900,
        "akosti": ["1.6580", "1.0037", "1.0038", "1.0039", "1.0044", "1.0045", 
                   "1.0117", "1.0308", "1.0425", "1.0460", "1.0503", "1.0570", 
                   "1.0576", "1.0577", "1.0710", "1.0715", "1.0718", "1.0762", 
                   "1.1141", "1.1191", "1.1213", "1.2343", "1.2367", "1.2379", 
                   "1.2510", "1.2738", "1.2842", "1.3243", "1.3247", "1.3343", 
                   "1.3505", "TOOLOX44"]
    },
    "PLAST": {
        "akosti": {
            "PA": 1140, "PC": 1200, "PEEK": 1320, "PE-HD": 950, "PET-G": 1270, 
            "PE-UHMW": 930, "POM": 1410, "PP": 910, "PVC": 1400
        }
    }
}

# --- 4. DATABÁZA ZÁKAZNÍKOV (Ukážka zoznamu) ---
zakaznici_db = {
    "Adient Seating Slovakia s.r.o.": {"lojalita": 0.88, "krajina": "SK"},
    "Hyundai Glovis Czech Republic s.r.o.": {"lojalita": 0.80, "krajina": "CZ"},
    "Yanfeng Namestovo": {"lojalita": 0.82, "krajina": "SK"},
    "ZKW Slovakia s.r.o.": {"lojalita": 0.44, "krajina": "SK"},
    "A2B s.r.o.": {"lojalita": 0.83, "krajina": "SK"},
    "AAH PLASTICS Slovakia s. r. o.": {"lojalita": 0.80, "krajina": "SK"}
    # Tu môžeš doplniť zvyšných zákazníkov v rovnakom formáte
}

# --- 5. POMOCNÉ FUNKCIE ---
def uloz_do_archivu(zaznam):
    file = 'archiv_naceneni.csv'
    df = pd.DataFrame([zaznam])
    df.to_csv(file, mode='a', index=False, header=not os.path.exists(file), encoding='utf-8-sig')

class CP_PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 15)
        self.cell(100, 10, 'MECASYS s.r.o.', 0, 0, 'L')
        self.set_font('Arial', '', 8)
        self.multi_cell(0, 4, 'Oravská Polhora 1117, SK-029 47\nIČO: 36433080 / IČ DPH: SK 20220377', 0, 'R')
        self.ln(10)

def generuj_pdf(id_cp, zakaznik, polozky):
    pdf = CP_PDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 10)
    pdf.cell(0, 7, f'Quotation Nbr. : {id_cp}', ln=True)
    pdf.cell(0, 7, f'Customer : {zakaznik}', ln=True)
    pdf.cell(0, 7, f'Date : {datetime.now().strftime("%d.%m.%Y")}', ln=True)
    pdf.ln(5)
    
    pdf.set_fill_color(230, 230, 230)
    pdf.cell(80, 8, ' Item', 1, 0, 'L', True)
    pdf.cell(20, 8, ' Qty', 1, 0, 'C', True)
    pdf.cell(35, 8, ' Price/Item', 1, 0, 'C', True)
    pdf.cell(35, 8, ' Total', 1, 1, 'C', True)
    
    total = 0
    pdf.set_font("Arial", "", 9)
    for p in polozky:
        pdf.cell(80, 7, f" {p['ID_komponent']}", 1)
        pdf.cell(20, 7, f" {p['n_komponent']}", 1, 0, 'C')
        pdf.cell(35, 7, f" {p['Cena_jednotkova']} €", 1, 0, 'C')
        pdf.cell(35, 7, f" {p['Cena_celkova']} €", 1, 1, 'C')
        total += p['Cena_celkova']
    
    pdf.set_font("Arial", "B", 10)
    pdf.cell(135, 8, 'Total price w/o VAT: ', 1, 0, 'R', True)
    pdf.cell(35, 8, f' {round(total, 2)} €', 1, 1, 'C', True)
    return pdf.output(dest='S').encode('latin-1')

# --- 6. UI APLIKÁCIE ---
if 'polozky_cp' not in st.session_state: st.session_state.polozky_cp = []

with st.sidebar:
    st.header("Správa a Archív")
    id_cp = st.text_input("ID Cenovej ponuky", "OP-26-0001")
    vybrany_zak = st.selectbox("Zákazník", sorted(list(zakaznici_db.keys())))
    
    if os.path.isfile('archiv_naceneni.csv'):
        with open('archiv_naceneni.csv', 'rb') as f:
            st.download_button("📩 Stiahnuť archív CP (CSV)", f, "archiv_cp.csv", "text/csv")
            
    if st.button("Resetovať celú ponuku"):
        st.session_state.polozky_cp = []
        st.rerun()

st.title("MECASYS - Inteligentné Naceňovanie")

if not model:
    st.warning("⚠️ Model 'model_forest.pkl' nebol načítaný. Aplikácia používa bezpečnostný výpočet.")

with st.container(border=True):
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        id_komp = st.text_input("ID Komponentu")
        kat_mat = st.selectbox("Kategória materiálu", list(materialy_db.keys()))
        if kat_mat in ["FAREBNÉ KOVY", "PLAST"]:
            akost = st.selectbox("Akosť", list(materialy_db[kat_mat]["akosti"].keys()))
        else:
            akost = st.selectbox("Akosť", materialy_db[kat_mat]["akosti"])
    with c2:
        d_val = st.number_input("D (mm)", min_value=0.0)
        l_val = st.number_input("L (mm)", min_value=0.0)
        n_kusov = st.number_input("Množstvo (ks)", min_value=1, value=1)
    with c3:
        c_mat_kg = st.number_input("Trhová cena mat. (€/kg)", min_value=0.0)
        c_koop = st.number_input("Kooperácia celkom (€)", min_value=0.0)
    with c4:
        narocnost = st.slider("Náročnosť výroby", 1, 5, 3)
        add_btn = st.button("PRIDAŤ POLOŽKU", use_container_width=True)

if add_btn:
    # Určenie hustoty
    if kat_mat in ["FAREBNÉ KOVY", "PLAST"]:
        hustota = materialy_db[kat_mat]["akosti"][akost]
    else:
        hustota = materialy_db[kat_mat]["predvolena_hustota"]

    # Výpočet hmotnosti (KR - Kruhová tyč)
    objem_m3 = (np.pi * (d_val / 2000)**2) * (l_val / 1000)
    hmotnost_kg = objem_m3 * hustota
    c_mat_komp = hmotnost_kg * c_mat_kg
    
    lojalita = zakaznici_db[vybrany_zak]["lojalita"]
    krajina_id = 1 if zakaznici_db[vybrany_zak]["krajina"] == "SK" else 2

    # PREDIKCIA (17 parametrov podľa Excelu)
    if model:
        try:
            vstupy = [2026, 1.0, 0, n_kusov, 0.5*narocnost, 1, narocnost, c_koop, lojalita, krajina_id, 1, 1, 1, d_val, l_val, hustota, c_mat_kg]
            cena_predikcia = model.predict([vstupy])[0]
        except:
            cena_predikcia = (c_mat_komp + (c_koop/n_kusov) + (narocnost * 15)) * (1.5 - lojalita)
    else:
        cena_predikcia = (c_mat_komp + (c_koop/n_kusov) + (narocnost * 15)) * (1.5 - lojalita)

    zaznam = {
        "ID_komponent": id_komp, "n_komponent": n_kusov, "Akost": akost,
        "Cena_jednotkova": round(float(cena_predikcia), 2),
        "Cena_celkova": round(float(cena_predikcia * n_kusov), 2),
        "Hmotnost_kg": round(hmotnost_kg, 4)
    }
    st.session_state.polozky_cp.append(zaznam)
    uloz_do_archivu({**zaznam, "Zákazník": vybrany_zak, "ID_CP": id_cp, "Timestamp": datetime.now()})
    st.rerun()

# --- ZOBRAZENIE TABUĽKY A PDF ---
if st.session_state.polozky_cp:
    df = pd.DataFrame(st.session_state.polozky_cp)
    st.table(df[["ID_komponent", "Akost", "n_komponent", "Cena_jednotkova", "Cena_celkova"]])
    
    celkova_suma = df["Cena_celkova"].sum()
    st.metric("VÝSLEDNÁ SUMA PONUKY", f"{round(celkova_suma, 2)} €")
    
    pdf_out = generuj_pdf(id_cp, vybrany_zak, st.session_state.polozky_cp)
    st.download_button("📩 STIAHNUŤ PDF PONUKU", pdf_out, f"{id_cp}.pdf", "application/pdf")

