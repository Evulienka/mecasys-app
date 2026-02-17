import streamlit as st
import pandas as pd
import joblib
import numpy as np
import requests
from io import BytesIO
from datetime import datetime
from fpdf import FPDF

# --- 1. KONFIGURÁCIA ---
st.set_page_config(page_title="MECASYS CP Expert - Košík", layout="wide")

MODEL_URL = "https://raw.githubusercontent.com/Evulienka/mecasys-app/main/model_ceny.pkl"
ENCODERS_URL = "https://raw.githubusercontent.com/Evulienka/mecasys-app/main/encoders.pkl"
# Tvoja overená URL pre Google Apps Script
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
        st.error(f"❌ Chyba pri načítaní AI: {e}")
        return None, None

model, encoders = load_assets()

# Inicializácia košíka (pamäť pre reláciu)
if 'kosik' not in st.session_state:
    st.session_state.kosik = []

# --- 2. FUNKCIA PRE PDF (VIAC POLOŽIEK) ---
def create_multiline_pdf(cislo_cp, polozky):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt=f"CENOVA PONUKA: {cislo_cp}", ln=True, align='C')
    pdf.set_font("Arial", size=10)
    pdf.cell(200, 10, txt=f"Vygenerovane: {datetime.now().strftime('%d.%m.%Y %H:%M')}", ln=True, align='C')
    pdf.ln(10)
    
    # Hlavička tabuľky
    pdf.set_font("Arial", 'B', 10)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(40, 8, "ID Komponent", 1, 0, 'C', True)
    pdf.cell(60, 8, "Material", 1, 0, 'C', True)
    pdf.cell(25, 8, "Mnozstvo", 1, 0, 'C', True)
    pdf.cell(30, 8, "Cena/ks", 1, 0, 'C', True)
    pdf.cell(35, 8, "Spolu (EUR)", 1, 1, 'C', True)
    
    pdf.set_font("Arial", size=10)
    total_sum = 0
    for p in polozky:
        cena_ks = p['cena_ai']
        mnozstvo = p['pocet_ks']
        spolu = cena_ks * mnozstvo
        total_sum += spolu
        
        pdf.cell(40, 8, str(p['id_komponent']), 1)
        pdf.cell(60, 8, f"{p['material']} {p['akost']}", 1)
        pdf.cell(25, 8, f"{mnozstvo} ks", 1, 0, 'R')
        pdf.cell(30, 8, f"{cena_ks:.3f}", 1, 0, 'R')
        pdf.cell(35, 8, f"{spolu:.2f}", 1, 1, 'R')
        
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(190, 10, txt=f"CELKOVA HODNOTA PONUKY: {total_sum:.2f} EUR", ln=True, align='R')
    return pdf.output(dest='S').encode('latin-1')

# --- 3. GRAFICKÉ ROZHRANIE ---
st.title("🛒 MECASYS: Systém hromadnej cenovej ponuky")

if model and encoders:
    # Sekcia hlavičky ponuky
    with st.container(border=True):
        col_header1, col_header2 = st.columns([1, 2])
        with col_header1:
            cislo_cp = st.text_input("Číslo cenovej ponuky (napr. CP-2024-010)", key="cp_main")
        with col_header2:
            st.write("")
            st.info("Položky pridávajte do zoznamu. AI vypočíta cenu na základe celkového objemu všetkých položiek.")

    # Formulár pre pridanie komponentu
    st.subheader("➕ Pridať komponent")
    with st.form("form_pridanie", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            new_id = st.text_input("ID / Názov komponentu")
            new_lojalita = st.number_input("Lojalita (0.0-1.0)", 0.0, 1.0, 0.85)
            new_krajina = st.selectbox("Krajina urcenia", encoders['zakaznik_krajina'].classes_)
        with c2:
            new_pocet = st.number_input("Množstvo (ks)", min_value=1, value=100)
            new_narocnost = st.selectbox("Náročnosť výroby (1-5)", [1,2,3,4,5])
            new_akost = st.selectbox("Akosť materiálu", encoders['material_AKOST'].classes_)
        with c3:
            new_mat = st.selectbox("Typ materiálu", encoders['material_nazov'].classes_)
            new_d = st.number_input("Priemer D (mm)", value=20.0)
            new_l = st.number_input("Dĺžka L (mm)", value=100.0)
            
        submitted = st.form_submit_button("Pridať do zoznamu")
        
        if submitted:
            if not cislo_cp or not new_id:
                st.error("Chýba Číslo CP alebo ID komponentu!")
            else:
                # Výpočet objemu pre tento jeden kus (m3)
                v_ks = (np.pi * ((new_d/2)/1000)**2 * (new_l/1000))
                # Hmotnosť (kg)
                h_ks = (3.14159 * (new_d**2) * new_l * 7900) / 4000000000
                
                # Uloženie do dočasného košíka
                st.session_state.kosik.append({
                    "id_komponent": new_id,
                    "lojalita": new_lojalita,
                    "krajina": new_krajina,
                    "pocet_ks": new_pocet,
                    "narocnost": new_narocnost,
                    "material": new_mat,
                    "akost": new_akost,
                    "d_mm": new_d,
                    "l_mm": new_l,
                    "objem_total_row": v_ks * new_pocet, # Celkový objem tohto riadku
                    "hmotnost_ks": round(h_ks, 4)
                })
                st.rerun()

    # Zobrazenie košíka a výpočet
    if st.session_state.kosik:
        st.divider()
        st.subheader(f"Aktuálny zoznam položiek pre: {cislo_cp}")
        
        df_view = pd.DataFrame(st.session_state.kosik)
        st.dataframe(df_view[['id_komponent', 'material', 'akost', 'pocet_ks', 'hmotnost_ks']], use_container_width=True)
        
        col_btns1, col_btns2 = st.columns([1, 5])
        with col_btns1:
            if st.button("🗑️ Vymazať všetko"):
                st.session_state.kosik = []
                st.rerun()
        
        with col_btns2:
            if st.button("🚀 FINALIZOVAŤ: PREPOČÍTAŤ AI A ULOŽIŤ DO TABUĽKY", use_container_width=True):
                # 1. KROK: Sčítanie celkového objemu CP
                celkovy_cp_objem = sum(item['objem_total_row'] for item in st.session_state.kosik)
                
                vysledky_pre_pdf = []
                
                with st.spinner("AI prepočítava ceny na základe celkového objemu..."):
                    for item in st.session_state.kosik:
                        # Príprava dát pre AI
                        input_dict = {
                            'kvartal': 1.0, 'mesiac': float(datetime.now().month), 
                            'CP_objem': float(celkovy_cp_objem), # Toto je tá kľúčová suma!
                            'n_komponent': float(item['pocet_ks']), 
                            'cas_v_predpoklad_komponent (hod)': 0.5,
                            'CP_uspech': 1.0, 'v_narocnost': float(item['narocnost']), 
                            'ko_cena_komponent': 0.0, 'zakaznik_lojalita': float(item['lojalita']),
                            'zakaznik_krajina': encoders['zakaznik_krajina'].transform([item['krajina']])[0],
                            'material_nazov': encoders['material_nazov'].transform([item['material']])[0],
                            'tvar_polotovaru': encoders['tvar_polotovaru'].transform(['KR'])[0],
                            'D(mm)': float(item['d_mm']), 'L(mm)': float(item['l_mm']), 
                            'material_HUSTOTA': 7900.0, 'cena_material_predpoklad': 2.5,
                            'material_AKOST': encoders['material_AKOST'].transform([item['akost']])[0],
                            'hmotnost': float(item['hmotnost_ks'])
                        }
                        
                        vstupy_df = pd.DataFrame([input_dict])
                        if hasattr(model, 'feature_names_in_'):
                            vstupy_df = vstupy_df[model.feature_names_in_]
                        
                        # AI PREDPOVVEĎ
                        cena_pred = model.predict(vstupy_df)[0]
                        item['cena_ai'] = round(float(cena_pred), 3)
                        vysledky_pre_pdf.append(item)
                        
                        # 2. KROK: Zápis do Google Sheets
                        payload = {
                            "cislo_cp": cislo_cp,
                            "id_komponent": item['id_komponent'],
                            "lojalita": item['lojalita'],
                            "narocnost": item['narocnost'],
                            "krajina": item['krajina'],
                            "material": item['material'],
                            "akost": item['akost'],
                            "d_mm": item['d_mm'],
                            "l_mm": item['l_mm'],
                            "hmotnost": item['hmotnost_ks'],
                            "pocet_ks": item['pocet_ks'],
                            "cena": item['cena_ai']
                        }
                        try:
                            requests.post(SCRIPT_URL, json=payload, timeout=5)
                        except:
                            pass # Ignorujeme chyby zápisu pre plynulosť testu

                st.success(f"Hotovo! Ceny boli vypočítané s ohľadom na celkový objem {celkovy_cp_objem:.4f} m³.")
                
                # 3. KROK: Generovanie PDF
                pdf_data = create_multiline_pdf(cislo_cp, vysledky_pre_pdf)
                st.download_button(
                    label="📥 STIAHNUŤ KOMBINOVANÚ PDF PONUKU",
                    data=pdf_data,
                    file_name=f"Ponuka_{cislo_cp}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
else:
    st.error("Nepodarilo sa pripojiť k AI modelom na GitHube.")
