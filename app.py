import streamlit as st
import pandas as pd
import joblib
import numpy as np
import requests
from io import BytesIO
from datetime import datetime
from fpdf import FPDF

# --- 1. KONFIGURÁCIA A NAČÍTANIE MODELU ---
st.set_page_config(page_title="MECASYS CP Expert", layout="wide")

MODEL_URL = "https://raw.githubusercontent.com/Evulienka/mecasys-app/main/model_ceny.pkl"
ENCODERS_URL = "https://raw.githubusercontent.com/Evulienka/mecasys-app/main/encoders.pkl"
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
        st.error(f"❌ Chyba pri načítaní AI modelu: {e}")
        return None, None

model, encoders = load_assets()

# --- 2. FUNKCIA NA GENEROVANIE PDF ---
def create_pdf(data):
    pdf = FPDF()
    pdf.add_page()
    
    # Hlavička
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="CENOVA PONUKA - MECASYS", ln=True, align='C')
    pdf.set_font("Arial", size=10)
    pdf.cell(200, 10, txt=f"Datum: {datetime.now().strftime('%d.%m.%Y %H:%M')}", ln=True, align='C')
    pdf.ln(10)

    # Tabuľka údajov
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, txt="Specifikacia:", ln=True)
    pdf.set_font("Arial", size=11)
    
    fields = [
        ("Material", f"{data['material']} ({data['akost']})"),
        ("Rozmery", f"D {data['d_mm']} mm x L {data['l_mm']} mm"),
        ("Hmotnost", f"{data['hmotnost']} kg"),
        ("Mnozstvo", f"{data['pocet_ks']} ks"),
        ("Krajina urcenia", data['krajina']),
        ("Narocnost vyroby", str(data['narocnost']))
    ]
    
    for label, value in fields:
        pdf.cell(50, 8, txt=f"{label}:", border=0)
        pdf.cell(100, 8, txt=value, border=0, ln=True)
    
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 14)
    pdf.set_text_color(0, 51, 102) # Tmavomodrá
    pdf.cell(200, 10, txt=f"Predpovedana cena: {data['cena']} EUR / ks", ln=True)
    pdf.cell(200, 10, txt=f"Celkova cena zakazky: {round(data['cena'] * data['pocet_ks'], 2)} EUR", ln=True)
    
    return pdf.output(dest='S').encode('latin-1')

# --- 3. FORMULÁR ---
st.title("📊 MECASYS CP Expert")

if model and encoders:
    krajiny = encoders['zakaznik_krajina'].classes_
    materialy = encoders['material_nazov'].classes_
    akosti = encoders['material_AKOST'].classes_

    with st.form("expert_form"):
        c1, c2, c3 = st.columns(3)
        with c1:
            st.subheader("👤 Klient")
            datum_vyber = st.date_input("Dátum CP", datetime.now())
            zak_lojalita = st.number_input("Lojalita (0.0-1.0)", value=0.85)
            zak_krajina_raw = st.selectbox("Krajina", krajiny)
            cp_uspech_raw = st.selectbox("Úspech (A/N)", ['A', 'N'])
        with c2:
            st.subheader("⚙️ Výroba")
            n_komponent = st.number_input("Množstvo (ks)", min_value=1, value=100)
            v_narocnost = st.selectbox("Náročnosť (1-5)", [1, 2, 3, 4, 5])
            cas_predpoklad = st.number_input("Čas (hod/ks)", value=0.5)
            ko_cena = st.number_input("Kooperácia (€)", value=0.0)
        with c3:
            st.subheader("🛠️ Materiál")
            mat_nazov_raw = st.selectbox("Typ materiálu", materialy)
            mat_akost_raw = st.selectbox("Akosť", akosti)
            d_mm = st.number_input("Priemer D (mm)", value=20.0)
            l_mm = st.number_input("Dĺžka L (mm)", value=100.0)
            hustota = st.number_input("Hustota (kg/m3)", value=7900)
            cena_mat_kg = st.number_input("Cena materiálu (€/kg)", value=2.5)

        submit = st.form_submit_button("🚀 VYPOČÍTAŤ, ULOŽIŤ A PRIPRAVIŤ PDF", use_container_width=True)

    if submit:
        # Výpočty
        mesiac = datum_vyber.month
        kvartal = (datum_vyber.month - 1) // 3 + 1
        objem = (np.pi * ((d_mm/2)/1000)**2 * (l_mm/1000))
        hmotnost = (3.14159 * (d_mm**2) * l_mm * hustota) / 4000000000

        try:
            # Predikcia
            input_dict = {
                'kvartal': float(kvartal), 'mesiac': float(mesiac), 'CP_objem': float(objem),
                'n_komponent': float(n_komponent), 'cas_v_predpoklad_komponent (hod)': float(cas_predpoklad),
                'CP_uspech': encoders['CP_uspech'].transform([cp_uspech_raw])[0],
                'v_narocnost': float(v_narocnost), 'ko_cena_komponent': float(ko_cena),
                'zakaznik_lojalita': float(zak_lojalita),
                'zakaznik_krajina': encoders['zakaznik_krajina'].transform([zak_krajina_raw])[0],
                'material_nazov': encoders['material_nazov'].transform([mat_nazov_raw])[0],
                'tvar_polotovaru': encoders['tvar_polotovaru'].transform(['KR'])[0],
                'D(mm)': float(d_mm), 'L(mm)': float(l_mm), 'material_HUSTOTA': float(hustota),
                'cena_material_predpoklad': float(cena_mat_kg),
                'material_AKOST': encoders['material_AKOST'].transform([mat_akost_raw])[0],
                'hmotnost': float(hmotnost)
            }
            
            vstupy_df = pd.DataFrame([input_dict])
            if hasattr(model, 'feature_names_in_'):
                vstupy_df = vstupy_df[model.feature_names_in_]

            predikcia = model.predict(vstupy_df)[0]
            
            # Zobrazenie výsledku
            st.success(f"### Odhadovaná cena: {predikcia:.3f} € / ks")

            # Dáta pre uloženie a PDF
            final_data = {
                "lojalita": zak_lojalita, "narocnost": v_narocnost, "krajina": zak_krajina_raw,
                "material": mat_nazov_raw, "akost": mat_akost_raw, "d_mm": d_mm, "l_mm": l_mm,
                "hmotnost": round(hmotnost, 4), "pocet_ks": n_komponent, "cena": round(predikcia, 3)
            }

            # Zápis do Google Sheets
            requests.post(SCRIPT_URL, json=final_data, timeout=10)
            st.toast("Dáta uložené v Google Sheets!", icon="✅")

            # Generovanie PDF
            pdf_bytes = create_pdf(final_data)
            
            st.download_button(
                label="📥 STIAHNUŤ CENOVÚ PONUKU (PDF)",
                data=pdf_bytes,
                file_name=f"Cenova_ponuka_{datetime.now().strftime('%Y%m%d')}.pdf",
                mime="application/pdf",
                use_container_width=True
            )

        except Exception as e:
            st.error(f"Chyba: {e}")
