import streamlit as st
import pandas as pd
import joblib
import numpy as np
import requests
from io import BytesIO
from datetime import datetime
from fpdf import FPDF

# --- 1. KONFIGURÁCIA A NAČÍTANIE ---
st.set_page_config(page_title="MECASYS CP Expert", layout="wide")

MODEL_URL = "https://raw.githubusercontent.com/Evulienka/mecasys-app/main/model_ceny.pkl"
ENCODERS_URL = "https://raw.githubusercontent.com/Evulienka/mecasys-app/main/encoders.pkl"
# Uisti sa, že toto SCRIPT_URL je tvoje aktuálne z Google Apps Script (Deploy URL)
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

# Inicializácia košíka (session state)
if 'kosik' not in st.session_state:
    st.session_state.kosik = []

# --- 2. FUNKCIA PRE PDF ---
def create_multiline_pdf(cislo_cp, polozky):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt=f"CENOVA PONUKA: {cislo_cp}", ln=True, align='C')
    pdf.set_font("Arial", size=10)
    pdf.cell(200, 10, txt=f"Datum: {datetime.now().strftime('%d.%m.%Y')}", ln=True, align='C')
    pdf.ln(10)
    
    # Hlavička tabuľky v PDF
    pdf.set_font("Arial", 'B', 10)
    pdf.set_fill_color(230, 230, 230)
    pdf.cell(45, 8, "ID Komponent", 1, 0, 'C', True)
    pdf.cell(55, 8, "Material / Akost", 1, 0, 'C', True)
    pdf.cell(25, 8, "Mnozstvo", 1, 0, 'C', True)
    pdf.cell(30, 8, "Cena/ks", 1, 0, 'C', True)
    pdf.cell(35, 8, "Spolu (EUR)", 1, 1, 'C', True)
    
    pdf.set_font("Arial", size=10)
    total_val = 0
    for p in polozky:
        line_total = p['cena_ai'] * p['pocet_ks']
        total_val += line_total
        pdf.cell(45, 8, str(p['id_komponent']), 1)
        pdf.cell(55, 8, f"{p['material']} {p['akost']}", 1)
        pdf.cell(25, 8, f"{p['pocet_ks']} ks", 1, 0, 'R')
        pdf.cell(30, 8, f"{p['cena_ai']:.3f}", 1, 0, 'R')
        pdf.cell(35, 8, f"{line_total:.2f}", 1, 1, 'R')
        
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(190, 10, txt=f"CELKOVA HODNOTA: {total_val:.2f} EUR", ln=True, align='R')
    return pdf.output(dest='S').encode('latin-1')

# --- 3. UŽÍVATEĽSKÉ ROZHRANIE ---
st.title("📊 MECASYS: Expertný systém nacenenia")

if model and encoders:
    # Hlavná sekcia ponuky
    with st.container(border=True):
        c_main1, c_main2 = st.columns(2)
        with c_main1:
            cislo_cp = st.text_input("Číslo cenovej ponuky", placeholder="Napr. CP-2026-001")
        with c_main2:
            datum_cp = st.date_input("Dátum (určuje kvartál a mesiac pre AI)", datetime.now())

    # Formulár pre pridanie komponentu
    st.subheader("➕ Pridať komponent do zoznamu")
    with st.form("input_form", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.write("**Obchodné dáta**")
            new_id = st.text_input("ID / Názov komponentu")
            new_lojalita = st.number_input("Lojalita zákazníka (0-1)", 0.0, 1.0, 0.85)
            new_krajina = st.selectbox("Krajina určenia", encoders['zakaznik_krajina'].classes_)
            new_uspech = st.selectbox("Predpoklad úspechu", ["A", "N"])

        with col2:
            st.write("**Náklady na 1 kus**")
            new_pocet = st.number_input("Počet kusov (ks)", min_value=1, value=100)
            new_cena_mat = st.number_input("Priama cena materiálu na 1ks (€)", min_value=0.0, value=5.0)
            new_cena_koop = st.number_input("Cena kooperácie na 1ks (€)", min_value=0.0, value=0.0)
            new_cas = st.number_input("Odhadovaný čas výroby (hod/ks)", min_value=0.01, value=0.5)

        with col3:
            st.write("**Technické parametre**")
            new_mat = st.selectbox("Materiál", encoders['material_nazov'].classes_)
            new_akost = st.selectbox("Akosť", encoders['material_AKOST'].classes_)
            new_d = st.number_input("Priemer D (mm)", value=20.0)
            new_l = st.number_input("Dĺžka L (mm)", value=100.0)
            new_narocnost = st.selectbox("Náročnosť (1-5)", [1,2,3,4,5])
            
        add_item = st.form_submit_button("PRIDAŤ DO ZOZNAMU")
        
        if add_item:
            if not cislo_cp or not new_id:
                st.warning("⚠️ Prosím, zadajte Číslo CP a ID komponentu!")
            else:
                # Výpočet objemu pre jeden kus (m3) a hmotnosti (kg)
                v_ks = (np.pi * ((new_d/2)/1000)**2 * (new_l/1000))
                h_ks = (3.14159 * (new_d**2) * new_l * 7900) / 4000000000
                
                # Zápis do košíka (tu sú kľúče zjednotené)
                st.session_state.kosik.append({
                    "id_komponent": new_id, 
                    "lojalita": new_lojalita, 
                    "krajina": new_krajina,
                    "pocet_ks": new_pocet, 
                    "narocnost": new_narocnost, 
                    "cas": new_cas,
                    "kooperacia": new_cena_koop, 
                    "material": new_mat, 
                    "akost": new_akost, 
                    "d_mm": new_d, 
                    "l_mm": new_l, 
                    "cena_mat_ks": new_cena_mat,
                    "uspech": new_uspech, 
                    "objem_total_row": v_ks * new_pocet, 
                    "hmotnost": round(h_ks, 4)
                })
                st.rerun()

    # Zobrazenie košíka
    if st.session_state.kosik:
        st.divider()
        st.subheader(f"Položky v ponuke: {cislo_cp}")
        df_view = pd.DataFrame(st.session_state.kosik)
        
        # Zobrazenie tabuľky komponentov
        st.dataframe(df_view[['id_komponent', 'pocet_ks', 'material', 'akost', 'cena_mat_ks']], use_container_width=True)

        if st.button("🚀 VYPOČÍTAŤ CENY AI A ULOŽIŤ PONUKU", use_container_width=True):
            # Extrakcia dátumu (logika z pozadia)
            mesiac_val = float(datum_cp.month)
            kvartal_val = float((datum_cp.month - 1) // 3 + 1)
            
            # Celkový objem celej ponuky pre AI
            celkovy_objem_cp = sum(item['objem_total_row'] for item in st.session_state.kosik)
            
            final_vysledky = []
            
            for item in st.session_state.kosik:
                # Príprava dát pre AI model
                input_data = {
                    'kvartal': kvartal_val, 
                    'mesiac': mesiac_val, 
                    'CP_objem': float(celkovy_objem_cp),
                    'n_komponent': float(item['pocet_ks']), 
                    'cas_v_predpoklad_komponent (hod)': float(item['cas']),
                    'CP_uspech': encoders['CP_uspech'].transform([item['uspech']])[0], 
                    'v_narocnost': float(item['narocnost']), 
                    'ko_cena_komponent': float(item['kooperacia']), 
                    'zakaznik_lojalita': float(item['lojalita']),
                    'zakaznik_krajina': encoders['zakaznik_krajina'].transform([item['krajina']])[0],
                    'material_nazov': encoders['material_nazov'].transform([item['material']])[0],
                    'tvar_polotovaru': encoders['tvar_polotovaru'].transform(['KR'])[0],
                    'D(mm)': float(item['d_mm']), 'L(mm)': float(item['l_mm']), 
                    'material_HUSTOTA': 7900.0, 
                    'cena_material_predpoklad': float(item['cena_mat_ks']),
                    'material_AKOST': encoders['material_AKOST'].transform([item['akost']])[0],
                    'hmotnost': float(item['hmotnost'])
                }
                
                vstupy_df = pd.DataFrame([input_data])
                if hasattr(model, 'feature_names_in_'):
                    vstupy_df = vstupy_df[model.feature_names_in_]
                
                # Predikcia AI
                predikcia = model.predict(vstupy_df)[0]
                item['cena_ai'] = round(float(predikcia), 3)
                final_vysledky.append(item)
                
                # Zápis do Google Sheets
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
                    "hmotnost": item['hmotnost'], 
                    "pocet_ks": item['pocet_ks'], 
                    "cena": item['cena_ai']
                }
                try:
                    requests.post(SCRIPT_URL, json=payload, timeout=5)
                except:
                    pass

            st.success("✅ Ceny vypočítané a ponuka uložená do databázy.")
            
            # PDF Generovanie
            pdf_b = create_multiline_pdf(cislo_cp, final_vysledky)
            st.download_button(
                label="📥 STIAHNUŤ KOMPLETNÚ PDF PONUKU",
                data=pdf_b,
                file_name=f"Ponuka_{cislo_cp}.pdf",
                mime="application/pdf",
                use_container_width=True
            )

        if st.button("🗑️ Vymazať zoznam (Nová ponuka)"):
            st.session_state.kosik = []
            st.rerun()
else:
    st.error("Nepodarilo sa načítať AI model.")
