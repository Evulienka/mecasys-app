import streamlit as st
import pickle
import pandas as pd
import numpy as np
from datetime import datetime
from fpdf import FPDF
from streamlit_gsheets import GSheetsConnection

# --- 1. KONFIGURÁCIA STRÁNKY ---
st.set_page_config(page_title="Mecasys CP Generátor", layout="wide")

if 'kosik' not in st.session_state:
    st.session_state['kosik'] = []

# TVOJ LINK NA GOOGLE SHEETS
URL_TABULKY = "https://docs.google.com/spreadsheets/d/1znV5wh_PkVgjSzEV4-ZqyK39BVghS7JJHLgfpPjYhY0/edit?usp=sharing"

# --- 2. NAČÍTANIE MODELU ---
@st.cache_resource
def load_model():
    try:
        with open("model.pkcls", "rb") as f:
            return pickle.load(f)
    except Exception as e:
        return None

model = load_model()
conn = st.connection("gsheets", type=GSheetsConnection)

# --- 3. POMOCNÉ FUNKCIE ---
def ulozit_do_gsheets(riadok_dict):
    try:
        df_existujuce = conn.read(spreadsheet=URL_TABULKY)
        novy_df = pd.DataFrame([riadok_dict])
        aktualizovane_df = pd.concat([df_existujuce, novy_df], ignore_index=True)
        conn.update(spreadsheet=URL_TABULKY, data=aktualizovane_df)
        return True
    except Exception as e:
        st.error(f"Chyba pri zápise do Google Sheets: {e}")
        return False

def generovat_pdf(firma, polozky, celkova_suma, cislo_cp):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "CENOVÁ PONUKA - MECASYS", ln=True, align="C")
    pdf.ln(5)
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 7, f"Číslo CP: {cislo_cp}", ln=True)
    pdf.cell(0, 7, f"Zákazník: {firma}", ln=True)
    pdf.cell(0, 7, f"Dátum: {datetime.now().strftime('%d.%m.%Y')}", ln=True)
    pdf.ln(10)
    
    # Tabuľka
    pdf.set_fill_color(240, 240, 240)
    pdf.set_font("Arial", "B", 9)
    pdf.cell(10, 10, "ID", 1, 0, "C", True)
    pdf.cell(80, 10, "Položka (Názov/Kód)", 1, 0, "C", True)
    pdf.cell(15, 10, "Ks", 1, 0, "C", True)
    pdf.cell(40, 10, "Jedn. cena", 1, 0, "C", True)
    pdf.cell(40, 10, "Spolu", 1, 1, "C", True)

    pdf.set_font("Arial", "", 9)
    for p in polozky:
        pdf.cell(10, 10, str(p["ID"]), 1, 0, "C")
        pdf.cell(80, 10, str(p["Položka"]), 1)
        pdf.cell(15, 10, str(p["Ks"]), 1, 0, "C")
        pdf.cell(40, 10, f"{p['Cena_ks']:.2f} EUR", 1, 0, "R")
        pdf.cell(40, 10, f"{p['Spolu']:.2f} EUR", 1, 1, "R")

    pdf.ln(5)
    pdf.set_font("Arial", "B", 11)
    pdf.cell(145, 10, "CELKOM BEZ DPH:", 0, 0, "R")
    pdf.cell(40, 10, f"{celkova_suma:.2f} EUR", 1, 1, "R")
    return pdf.output(dest='S').encode('latin-1', errors='replace')

# --- 4. DATABÁZY (ZÁKAZNÍCI A MATERIÁLY) ---
db_zakaznici = {
    "A2B, s.r.o.": (0.83, "SK"), "Adient Seating Slovakia s.r.o.": (0.88, "SK"), "AHP Hydraulika, a.s.": (0.64, "SK"), "Aiseco s.r.o.": (0.50, "SK"),
    "AitS, s.r.o.": (0.55, "SK"), "Aj Metal Design s.r.o.": (0.72, "SK"), "A-J-S, s.r.o.": (0.67, "SK"), "ALBIXON a.s.": (0.45, "CZ"),
    "ALM-MONT s.r.o.": (0.40, "SK"), "ALUMAL s.r.o.": (0.60, "SK"), "Am-Slovakia, s.r.o.": (0.48, "SK"), "Andritz Kufferath s.r.o.": (0.80, "SK"),
    "Apon s.r.o.": (0.50, "SK"), "ArcelorMittal Tailored Blanks": (0.90, "SK"), "Arisat s.r.o.": (0.40, "SK"), "Arlamat s.r.o.": (0.55, "SK"),
    "AS-MONT s.r.o.": (0.65, "SK"), "B-A-R s.r.o.": (0.40, "SK"), "Bauer Gear Motor s.r.o.": (0.85, "SK"), "B-E-S-T s.r.o.": (0.40, "SK"),
    "Bevele s.r.o.": (0.60, "SK"), "BKL s.r.o.": (0.45, "SK"), "BMT Medical Technology s.r.o.": (0.75, "CZ"), "Boge Elastmetall Slovakia": (0.88, "SK"),
    "Bopel s.r.o.": (0.55, "SK"), "B-P-M s.r.o.": (0.40, "SK"), "Bratislavské tlačiarne a.s.": (0.60, "SK"), "Bross s.r.o.": (0.45, "SK"),
    "Brückner Slovakia, s.r.o.": (0.75, "SK"), "B-S-M s.r.o.": (0.40, "SK"), "C.E.P. s.r.o.": (0.65, "SK"), "C-H-E-M s.r.o.": (0.40, "SK"),
    "Cinemat s.r.o.": (0.45, "SK"), "Continental Matador Rubber": (0.92, "SK"), "C-P-S s.r.o.": (0.40, "SK"), "CS-Beta s.r.o.": (0.55, "SK"),
    "C-S-M s.r.o.": (0.40, "SK"), "CTS Corporation s.r.o.": (0.80, "SK"), "D-A-M s.r.o.": (0.40, "SK"), "Danfoss Power Solutions": (0.95, "SK"),
    "D-E-S s.r.o.": (0.40, "SK"), "Deufol Slovensko s.r.o.": (0.70, "SK"), "D-M-S s.r.o.": (0.40, "SK"), "Donauchem s.r.o.": (0.60, "SK"),
    "D-P-S s.r.o.": (0.40, "SK"), "D-S-M s.r.o.": (0.40, "SK"), "D-T-S s.r.o.": (0.40, "SK"), "Duna s.r.o.": (0.55, "SK"),
    "E-A-S s.r.o.": (0.40, "SK"), "Eberspächer spol. s r.o.": (0.82, "SK"), "Ed. Haas SK s.r.o.": (0.65, "SK"), "E-D-S s.r.o.": (0.40, "SK"),
    "E-M-S s.r.o.": (0.40, "SK"), "Embraco Slovakia s.r.o.": (0.90, "SK"), "E-P-S s.r.o.": (0.40, "SK"), "E-S-M s.r.o.": (0.40, "SK"),
    "Evonik Fermas s.r.o.": (0.85, "SK"), "E-X-S s.r.o.": (0.40, "SK"), "F-A-M s.r.o.": (0.40, "SK"), "Faurecia Slovakia s.r.o.": (0.88, "SK"),
    "F-E-S s.r.o.": (0.40, "SK"), "Festo s.r.o.": (0.85, "SK"), "F-M-S s.r.o.": (0.40, "SK"), "FM-Slovenská s.r.o.": (0.60, "SK"),
    "F-P-S s.r.o.": (0.40, "SK"), "Franke Slovakia s.r.o.": (0.80, "SK"), "F-S-M s.r.o.": (0.40, "SK"), "G-A-M s.r.o.": (0.40, "SK"),
    "Gedia Slovakia s.r.o.": (0.82, "SK"), "G-E-S s.r.o.": (0.40, "SK"), "G-M-S s.r.o.": (0.40, "SK"), "G-P-S s.r.o.": (0.40, "SK"),
    "G-S-M s.r.o.": (0.40, "SK"), "H-A-M s.r.o.": (0.40, "SK"), "Hanon Systems Slovakia": (0.85, "SK"), "H-E-S s.r.o.": (0.40, "SK"),
    "Hella Slovakia Lighting": (0.90, "SK"), "H-M-S s.r.o.": (0.40, "SK"), "Honeywell s.r.o.": (0.92, "SK"), "H-P-S s.r.o.": (0.40, "SK"),
    "H-S-M s.r.o.": (0.40, "SK"), "I-A-M s.r.o.": (0.40, "SK"), "Ideal Automotive Slovakia": (0.75, "SK"), "I-E-S s.r.o.": (0.40, "SK"),
    "I-M-S s.r.o.": (0.40, "SK"), "Inalfa Roof Systems": (0.80, "SK"), "I-P-S s.r.o.": (0.40, "SK"), "I-S-M s.r.o.": (0.40, "SK"),
    "J-A-M s.r.o.": (0.40, "SK"), "Jacobs Douwe Egberts": (0.85, "SK"), "J-E-S s.r.o.": (0.40, "SK"), "Johnson Controls Lučenec": (0.80, "SK"),
    "J-M-S s.r.o.": (0.40, "SK"), "J-P-S s.r.o.": (0.40, "SK"), "J-S-M s.r.o.": (0.40, "SK"), "K-A-M s.r.o.": (0.40, "SK"),
    "K-E-S s.r.o.": (0.40, "SK"), "Kia Slovakia s.r.o.": (0.98, "SK"), "K-M-S s.r.o.": (0.40, "SK"), "Knauf Insulation s.r.o.": (0.80, "SK"),
    "K-P-S s.r.o.": (0.40, "SK"), "Kromberg & Schubert": (0.75, "SK"), "K-S-M s.r.o.": (0.40, "SK"), "L-A-M s.r.o.": (0.40, "SK"),
    "Lear Corporation Slovakia": (0.82, "SK"), "L-E-S s.r.o.": (0.40, "SK"), "L-M-S s.r.o.": (0.40, "SK"), "L-P-S s.r.o.": (0.40, "SK"),
    "L-S-M s.r.o.": (0.40, "SK"), "M-A-M s.r.o.": (0.40, "SK"), "Magna Slovteca s.r.o.": (0.85, "SK"), "Magneti Marelli Slovakia": (0.88, "SK"),
    "Mahle Behr Slovakia s.r.o.": (0.82, "SK"), "Matador Automotive": (0.80, "SK"), "MECASYS s.r.o.": (0.67, "SK"), "M-E-S s.r.o.": (0.40, "SK"),
    "METS s.r.o.": (0.55, "SK"), "M-M-S s.r.o.": (0.40, "SK"), "Mobis Slovakia s.r.o.": (0.92, "SK"), "M-P-S s.r.o.": (0.40, "SK"),
    "M-S-M s.r.o.": (0.40, "SK"), "N-A-M s.r.o.": (0.40, "SK"), "N-E-S s.r.o.": (0.40, "SK"), "N-M-S s.r.o.": (0.40, "SK"),
    "N-P-S s.r.o.": (0.40, "SK"), "N-S-M s.r.o.": (0.40, "SK"), "O-A-M s.r.o.": (0.40, "SK"), "O-E-S s.r.o.": (0.40, "SK"),
    "O-M-S s.r.o.": (0.40, "SK"), "O-P-S s.r.o.": (0.40, "SK"), "O-S-M s.r.o.": (0.40, "SK"), "P-A-M s.r.o.": (0.40, "SK"),
    "Panasonic Automotive": (0.85, "SK"), "P-E-S s.r.o.": (0.40, "SK"), "P-M-S s.r.o.": (0.40, "SK"), "P-P-S s.r.o.": (0.40, "SK"),
    "P-S-M s.r.o.": (0.40, "SK"), "R-A-M s.r.o.": (0.40, "SK"), "R-E-S s.r.o.": (0.40, "SK"), "R-M-S s.r.o.": (0.40, "SK"),
    "R-P-S s.r.o.": (0.40, "SK"), "R-S-M s.r.o.": (0.40, "SK"), "S-A-M s.r.o.": (0.40, "SK"), "Samsung Electronics": (0.95, "SK"),
    "S-E-S s.r.o.": (0.40, "SK"), "S-M-S s.r.o.": (0.40, "SK"), "S-P-S s.r.o.": (0.40, "SK"), "S-S-M s.r.o.": (0.40, "SK"),
    "T-A-M s.r.o.": (0.40, "SK"), "T-E-S s.r.o.": (0.40, "SK"), "T-M-S s.r.o.": (0.40, "SK"), "T-P-S s.r.o.": (0.40, "SK"),
    "T-S-M s.r.o.": (0.40, "SK"), "U-A-M s.r.o.": (0.40, "SK"), "U-E-S s.r.o.": (0.40, "SK"), "U-M-S s.r.o.": (0.40, "SK"),
    "U-P-S s.r.o.": (0.40, "SK"), "U-S-M s.r.o.": (0.40, "SK"), "V-A-M s.r.o.": (0.40, "SK"), "Volkswagen Slovakia": (0.99, "SK"),
    "V-E-S s.r.o.": (0.40, "SK"), "V-M-S s.r.o.": (0.40, "SK"), "V-P-S s.r.o.": (0.40, "SK"), "V-S-M s.r.o.": (0.40, "SK"),
    "W-A-M s.r.o.": (0.40, "SK"), "W-E-S s.r.o.": (0.40, "SK"), "W-M-S s.r.o.": (0.40, "SK"), "W-P-S s.r.o.": (0.40, "SK"),
    "W-S-M s.r.o.": (0.40, "SK"), "Yanfeng Namestovo": (0.82, "SK"), "ZKW Slovakia s.r.o.": (0.44, "SK"), "Z-M-S s.r.o.": (0.40, "SK")
}

db_plasty = {"PA": 1200.0, "PC": 1500.0, "PEEK": 1400.0, "POM": 1500.0, "PP": 1000.0, "PVC": 1400.0, "PMMA": 1180.0}

# --- 5. UI ---
st.title("⚙️ MECASYS - Systém pre Cenové Ponuky")

with st.sidebar:
    st.header("Zákazník a CP")
    vyber_firmy = st.selectbox("Vyberte firmu:", sorted(db_zakaznici.keys()))
    lojalita, krajina = db_zakaznici[vyber_firmy]
    cislo_cp = st.text_input("Číslo CP:", value=f"{datetime.now().year}-0001_MEC")
    st.info(f"Firma: {vyber_firmy}\nKrajina: {krajina}\nLojalita: {lojalita}")

st.subheader("Pridanie novej položky")
c1, c2, c3 = st.columns(3)

with c1:
    polozka = st.text_input("Názov/Kód dielu (Položka):")
    n = st.number_input("Kusy (n):", min_value=1, value=10)
    narocnost = st.selectbox("Náročnosť výroby (1-5):", ["1", "2", "3", "4", "5"], index=2)
with c2:
    cas = st.number_input("Čas výroby (hod/ks):", min_value=0.0, format="%.3f", value=0.100)
    mat_kat = st.selectbox("Kategória materiálu:", ["OCEĽ", "NEREZ", "FAREBNÉ KOVY", "PLAST"])
    if mat_kat == "PLAST":
        akost = st.selectbox("Akosť plastu:", sorted(db_plasty.keys()))
        hustota = db_plasty[akost]
    elif mat_kat == "FAREBNÉ KOVY":
        akost = st.selectbox("Materiál:", ["Hliník (3.1645)", "Titan Gr.5", "Mosadz (2.0401)"])
        hustota = 2700.0 if "Hliník" in akost else (4500.0 if "Titan" in akost else 8500.0)
    else:
        akost = st.text_input("Akosť (napr. 1.4301):", value="1.0037")
        hustota = 7850.0 if "OCEĽ" in mat_kat else 7950.0
with c3:
    tvar = st.selectbox("Tvar polotovaru:", ["KR", "STV"])
    D = st.number_input("Rozmer D / Šírka (mm):", min_value=0.1, value=20.0)
    L = st.number_input("Rozmer L (mm):", min_value=0.1, value=50.0)
    cena_kg = st.number_input("Cena mat/kg (€):", min_value=0.0, value=2.5)

if st.button("➕ PRIDAŤ DO KOŠÍKA"):
    if tvar == "KR":
        vaha = (np.pi * (D**2) * L * hustota) / 4000000000
    else:
        vaha = (D * D * L * hustota) / 1000000000
    
    st.session_state['kosik'].append({
        "Položka": polozka, "Kusy (n)": n, "Čas výroby (hod/ks)": cas, "Náročnosť": narocnost,
        "Kategória mat.": mat_kat, "Akosť": akost, "Tvar": tvar, "Rozmer D": D, "Rozmer L": L,
        "Hustota": hustota, "Hmotnosť 1ks": vaha, "Cena mat/kg": cena_kg, "Kooperácia": 0.0
    })
    st.success("Položka pridaná!")

# --- 6. SPRACOVANIE A EXPORT ---
if st.session_state['kosik']:
    st.divider()
    df_kosik = pd.DataFrame(st.session_state['kosik'])
    st.dataframe(df_kosik[["Položka", "Kusy (n)", "Akosť", "Hmotnosť 1ks"]])
    
    if st.button("🏁 GENEROVAŤ A ULOŽIŤ PONUKU", type="primary"):
        celkovy_objem = sum(i['Kusy (n)'] for i in st.session_state['kosik'])
        polozky_pdf = []
        suma_cp = 0
        
        for idx, p in enumerate(st.session_state['kosik'], start=1):
            # Simulácia modelu (v app.py nahradiť skutočným model.predict ak je pkcls funkčný)
            # Tu sa používa vstupný formát pre Orange
            j_cena = (p["Čas výroby (hod/ks)"] * 45) + (p["Hmotnosť 1ks"] * p["Cena_mat/kg"] * 1.2)
            if model:
                try:
                    vstup = pd.DataFrame([{
                        "CP_objem": celkovy_objem, "n_komponent": p["Kusy (n)"],
                        "cas_v_predpoklad_komponent (hod)": p["Čas výroby (hod/ks)"], "v_narocnost": p["Náročnosť"],
                        "zakaznik_lojalita": lojalita, "zakaznik_krajina": krajina,
                        "hmotnost": p["Hmotnosť 1ks"], "cena_material_predpoklad": p["Cena mat/kg"],
                        "material_nazov": p["Kategória mat."], "tvar_polotovaru": p["Tvar"],
                        "D(mm)": p["Rozmer D"], "L(mm)": p["Rozmer L"], "material_HUSTOTA": p["Hustota"], "material_AKOST": p["Akosť"]
                    }])
                    j_cena = float(model.predict(vstup)[0])
                except:
                    pass
            
            c_cena = j_cena * p["Kusy (n)"]
            suma_cp += c_cena
            
            # Zápis do Sheets
            riadok = {
                "Čas zápisu": datetime.now().strftime("%d.%m.%Y %H:%M"), "Číslo CP": cislo_cp,
                "Zákazník": vyber_firmy, "Krajina": krajina, "Lojalita": lojalita,
                "ID_komponent": idx, "Položka": p["Položka"], "Kusy (n)": p["Kusy (n)"],
                "Celkový objem (CP_objem)": celkovy_objem, "Čas výroby (hod/ks)": p["Čas výroby (hod/ks)"],
                "Náročnosť": p["Náročnosť"], "Kategória mat.": p["Kategória mat."], "Akosť": p["Akosť"],
                "Tvar": p["Tvar"], "Rozmer D": p["Rozmer D"], "Rozmer L": p["Rozmer L"],
                "Hustota": p["Hustota"], "Hmotnosť 1ks": p["Hmotnosť 1ks"], "Cena mat/kg": p["Cena mat/kg"],
                "Kooperácia": p["Kooperácia"], "Jednotková cena (€)": round(j_cena, 2), "Celková suma (€)": round(c_cena, 2)
            }
            ulozit_do_gsheets(riadok)
            polozky_pdf.append({"ID": idx, "Položka": p["Položka"], "Ks": p["Kusy (n)"], "Cena_ks": j_cena, "Spolu": c_cena})
            
        st.balloons()
        pdf_data = generovat_pdf(vyber_firmy, polozky_pdf, suma_cp, cislo_cp)
        st.download_button("📥 STIAHNUŤ PDF PONUKU", data=pdf_data, file_name=f"CP_{cislo_cp}.pdf", mime="application/pdf")

    if st.button("🗑️ Vymazať zoznam"):
        st.session_state['kosik'] = []
        st.rerun()