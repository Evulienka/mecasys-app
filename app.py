import streamlit as st
import pickle
import pandas as pd
import numpy as np
from datetime import datetime
from fpdf import FPDF
from streamlit_gsheets import GSheetsConnection

# --- 1. KONFIGURÁCIA APLIKÁCIE ---
st.set_page_config(page_title="Mecasys CP Generátor", layout="wide")

if 'kosik' not in st.session_state:
    st.session_state['kosik'] = []

# URL tvojej Google tabuľky pre ukladanie histórie
URL_TABULKY = "https://docs.google.com/spreadsheets/d/1znV5wh_PkVgjSzEV4-ZqyK39BVghS7JJHLgfpPjYhY0/edit?usp=sharing"

# --- 2. NAČÍTANIE MODELU A PRIPOJENIE ---
@st.cache_resource
def load_model():
    try:
        with open("model.pkcls", "rb") as f:
            return pickle.load(f)
    except:
        return None

model = load_model()
conn = st.connection("gsheets", type=GSheetsConnection)

# --- 3. KOMPLETNÁ DATABÁZA ZÁKAZNÍKOV (ZO VŠETKÝCH SCREENSHOTOV) ---
db_zakaznici = {
    "A2B, s.r.o.": (0.83, "SK"), "AAH PLASTICS Slovakia s. r. o.": (0.80, "SK"),
    "Adient Innotec Metal Technologies s.r.o.": (0.31, "SK"), "Adient Seating S.A.S.": (0.33, "FR"),
    "Adient Seating Slovakia s.r.o.": (0.88, "SK"), "Agromatic Regelungstechnik GmbH": (0.33, "DE"),
    "Air International Thermal (Slovakia) s.r.o.": (0.33, "SK"), "AKROMECA": (0.33, "FR"),
    "Alkadur Robotsystems GmbH": (0.14, "DE"), "AMINOXY LIMITED": (0.33, "SK"),
    "ANDRITZ Separation GmbH": (0.19, "DE"), "Anton Romaňák - KOVOTROM": (0.20, "SK"),
    "Armaturen- und Autogengerätefabrik ewo": (0.06, "DE"), "ATEM (Siège)": (0.56, "FR"),
    "Avendor GmbH": (0.33, "DE"), "Bayer Prototypen": (0.33, "DE"),
    "BCF EUROPE s.r.o": (0.88, "SK"), "BelFox Torautomatik GmbH": (0.25, "DE"),
    "Ben Innova Systemtechnik GmbH": (0.09, "DE"), "BIA Plastic and Plating Technology Slovakia s.r.o.": (0.33, "SK"),
    "Bienen Ruck GmbH": (0.25, "DE"), "Big Box, s.r.o.": (0.33, "SK"),
    "Bograma AG": (0.33, "SUI"), "Brückner Slovakia, s.r.o.": (0.75, "SK"),
    "CABLEX SK s.r.o.": (0.57, "SK"), "CD - profil s.r.o.": (0.50, "SK"),
    "CIPI, s.r.o.": (0.40, "SK"), "Craemer Slovakia, s. r. o.": (0.75, "SK"),
    "Deutsche Wecotech GmbH": (0.33, "DE"), "DISTLER ENGINEERING s.r.o.": (0.33, "SK"),
    "DITIS Technology s.r.o.": (0.67, "SK"), "Dominik Beňuš ALUMINIUM ORAVA": (0.67, "SK"),
    "DSD NOELL GmbH": (0.33, "DE"), "Dušan Mokošák": (0.67, "SK"),
    "EBZ SysTec GmbH": (0.29, "DE"), "ECCO Slovakia, a.s.": (0.67, "SK"),
    "Edge Autonomy Riga SIA": (0.60, "LT"), "EDM, s.r.o.": (0.33, "SK"),
    "Elster s. r. o.": (0.75, "SK"), "ERCE CZ, s.r.o.": (0.75, "CZ"),
    "Eurostyle Systems Liptovský Mikuláš s.r.o.": (0.67, "SK"), "EXAIL Robotics": (0.75, "FR"),
    "EXCENT": (0.33, "FR"), "Exerion Precision Technology Olomouc s.r.o.": (0.33, "CZ"),
    "Fabryka Plastików Gliwice": (0.33, "PL"), "FDonlinehandel": (0.33, "DE"),
    "Franz Nüsing GmbH & Co. KG": (0.25, "DE"), "Frauenthal Gnotec Slovakia s.r.o.": (0.18, "SK"),
    "FREMACH TRNAVA, s.r.o.": (0.33, "SK"), "GEDAST s. r. o.": (0.20, "SK"),
    "GERGONNE SLOVENSKO s.r.o.": (0.75, "SK"), "Gluematic GmbH & Co.KG": (0.25, "DE"),
    "goracon systemtechnik GmbH": (0.33, "DE"), "Groupe Plastivaloire": (0.71, "SK"),
    "Guzik Pavol": (0.67, "SK"), "H.Moryl GmbH": (0.33, "DE"),
    "Hager & Meisinger GmbH": (0.33, "DE"), "HARTS": (0.33, "SK"),
    "HDF, s.r.o.": (0.25, "SK"), "Heraldik Slovakia s. r. o.": (0.33, "SK"),
    "HERN s.r.o.": (0.08, "SK"), "Holz-Her Maschinenbau GmbH": (0.33, "AT"),
    "Honeywell Corp": (0.33, "USA"), "HYDAC Electronic, s.r.o.": (0.88, "SK"),
    "Hyundai Glovis Czech Republic s.r.o.": (0.80, "CZ"), "Hyundai Motor Manufacturing Czech s.r.o.": (0.67, "CZ"),
    "IBEX GmbH": (0.33, "DE"), "Ideal Fertigung": (0.33, "DE"),
    "iGrow Network, s.r.o.": (0.17, "SK"), "Ing. Róbert Palider": (0.33, "SK"),
    "IRTS - Headquarters": (0.33, "FR"), "ITW Slovakia s.r.o.": (0.67, "SK"),
    "IWT Industrielle Wickeltechnologie GmbH": (0.33, "DE"), "J.P.Plast Svatoborská": (0.33, "CZ"),
    "JAFFA, s.r.o.": (0.67, "SK"), "Jiří Řebíček - Metalplast, s.r.o.": (0.67, "CZ"),
    "JMP Plast s.r.o.": (0.70, "SK"), "Josef Schwan GmbH": (0.25, "DE"),
    "Jozef Barnáš JO - BA": (0.67, "SK"), "Jozef Gender": (0.67, "SK"),
    "JP-AUTO, s. r. o.": (0.33, "SK"), "JUMI s.r.o. Košice": (0.33, "SK"),
    "JWS Zerspanungstechnik GmbH": (0.33, "DE"), "Kamil Bujňák - OBCHOD U KAMILA": (0.33, "SK"),
    "KIRON": (0.33, "DE"), "KOVOT s. r. o.": (0.80, "SK"),
    "KOVOVÝROBA, spol. s r.o.": (0.33, "SK"), "KOWA, s.r.o.": (0.33, "SK"),
    "KREDUS, s.r.o.": (0.33, "SK"), "KSA Benelux B.V.": (0.33, "NL"),
    "KUHLA® Kühltechnik & Ladenbau GmbH": (0.33, "DE"), "LEBEDA Tools s.r.o.": (0.33, "CZ"),
    "LEPAL TECHNIK, spol. s r.o.": (0.33, "SK"), "LETECH INDUSTRY s. r. o.": (0.33, "SK"),
    "LinEx Slovakia, s. r. o.": (0.50, "SK"), "LPH Vranov n/T, s.r.o.": (0.43, "SK"),
    "Lubomir Hutlas": (0.67, "SK"), "Lubomir Jagnesak": (0.80, "SK"),
    "m conso s.r.o.": (0.33, "SK"), "M.O.U.D. s. r. o.": (0.60, "SK"),
    "MAGNA SLOVTECA, s.r.o.": (0.25, "SK"), "MAGONTEC GmbH": (0.25, "DE"),
    "MAHLE Behr Námestovo s.r.o.": (0.73, "SK"), "MAHLE Industrial Thermal Systems Námestovo s.r.o.": (0.67, "SK"),
    "MAPA-Tech GmbH & Co. KG": (0.33, "DE"), "Mapes": (0.67, "SK"),
    "Maschinenbau Dahme GmbH": (0.33, "DE"), "Maschinenfabrik Ludwig Berger GmbH": (0.33, "AT"),
    "Mäsovýroba SKURČÁK, s. r. o.": (0.33, "SK"), "Max Blank GmbH": (0.33, "DE"),
    "maxon motor Hungary Kft": (0.33, "HU"), "MB 'SOLMETO'": (0.33, "LT"),
    "MBM MECANIQUE": (0.25, "FR"), "MBO Postpress Solutions GmbH": (0.17, "DE"),
    "MB-TecSolutions GmbH": (0.25, "DE"), "MECASYS s.r.o.": (0.67, "SK"),
    "Mergon CZ": (0.25, "CZ"), "METAL STEEL INDUSTRY, spol. s r.o.": (0.20, "SK"),
    "Micro-Epsilon Inspection, s.r.o.": (0.33, "SK"), "MINITUB SLOVAKIA spol. s r.o.": (0.17, "SK"),
    "Miroslava Bartošová": (0.33, "SK"), "MPM steel s. r. o.": (0.22, "SK"),
    "Nanogate Slovakia s. r. o.": (0.63, "SK"), "Nela Brüder Neumeister GmbH": (0.33, "DE"),
    "Nicea s. r. o.": (0.33, "SK"), "NR Craft, s.r.o.": (0.33, "SK"),
    "NTV - náradie SK s. r. o.": (0.25, "SK"), "OCEANSCAN - Marine Systems & Technology Lda": (0.45, "PT"),
    "Ondrej Sandtner US ATYP": (0.33, "SK"), "OR - METAL, s. r. o.": (0.67, "SK"),
    "ORVEX spol. s r.o.": (0.67, "SK"), "PackSys Global AG": (0.32, "SUI"),
    "Pi-Tech Industrielle Dienstleistungen": (0.25, "DE"), "Pneufit s. r. o.": (0.67, "SK"),
    "PRAX": (0.75, "FR"), "PROKS PLASTIC s.r.o.": (0.75, "CZ"), "ProMatur": (0.33, "DE"),
    "PWO Czech Republic a.s.": (0.75, "CZ"), "Quintenz Hybridtechnik GmbH": (0.33, "DE"),
    "Rapid Technic AG": (0.33, "SUI"), "RECA plastics GmbH": (0.33, "DE"),
    "Rehnen GmbH & Co KG": (0.17, "DE"), "Rotodecor GmbH": (0.33, "DE"),
    "RUDOS RUŽOMBEROK, s.r.o.": (0.67, "SK"), "RUETZ TECHNOLOGIES GmbH": (0.33, "DE"),
    "RWT GmbH": (0.33, "DE"), "SAG Innovations GmbH": (0.20, "AT"),
    "SAS CONSTRUCTION INSTALLATION ELECTRIQL": (0.67, "FR"), "Schaeffler Skalica, spol. s r.o.": (0.06, "SK"),
    "Schiller Automation GmbH & Co. KG": (0.33, "DE"), "SCHOCK GmbH": (0.33, "DE"),
    "SEC Technologies, s.r.o.": (0.80, "SK"), "seele pilsen s.r.o.": (0.29, "CZ"),
    "Seolutions, s. r. o.": (0.20, "SK"), "SEZ DK a. s.": (0.75, "SK"),
    "Silkroad Truckparts": (0.33, "LT"), "SITEC GmbH Sicherheitstechnik": (0.20, "DE"),
    "SKM GmbH": (0.33, "DE"), "SLER Plastic s.r.o.": (0.17, "SK"),
    "Slovak Techno Export - Plastymat s.r.o.": (0.25, "SK"), "SLUŽBA NITRA, s.r.o.": (0.44, "SK"),
    "SN Maschinenbau": (0.33, "DE"), "Specac Ltd.": (0.33, "GB"), "Städtler + Beck GmbH": (0.33, "DE"),
    "Stahlotec GmbH": (0.25, "DE"), "Stieber GmbH": (0.33, "DE"), "SUG GmbH & Co. KG": (0.33, "DE"),
    "SUMITOMO (SHI) CYCLO DRIVE GERMANY GmbH": (0.33, "DE"), "Taplast, s.r.o.": (0.67, "SK"),
    "THERMOPLASTIK s.r.o.": (0.29, "SK"), "Thomas GmbH": (0.20, "DE"), "THYZONA s.r.o.": (0.33, "SK"),
    "TOPSOLID CZECH, s.r.o.": (0.67, "CZ"), "Tousek Ges.m.b.H": (0.25, "AT"),
    "UPT, s.r.o.": (0.25, "SK"), "Veeser Plastic Slovakia k. s.": (0.25, "SK"),
    "VENIO, s.r.o.": (0.33, "SK"), "Visteon Electronics Slovakia s. r. o.": (0.57, "SK"),
    "Vladimír Tarci - PRIMASPOJ": (0.33, "SK"), "W. Hartmann & Co (GmbH & Co KG)": (0.33, "DE"),
    "WEGU SLOVAKIA s.r.o.": (0.33, "SK"), "Wildkart Deutschland AG & Co.KG": (0.17, "DE"),
    "Witzenmann Slovakia spol. s r. o.": (0.17, "SK"), "Yanfeng International Automotive Technology Slovakia s.r.o.": (0.75, "SK"),
    "Yanfeng Namestovo": (0.82, "SK"), "Železiarstvo Páleník s.r.o.": (0.33, "SK"), "ZKW Slovakia s.r.o.": (0.44, "SK")
}

# --- 4. KOMPLETNÁ DATABÁZA MATERIÁLOV (AKOSTI A HUSTOTY) ---
db_materialy = {
    "OCEĽ": {
        "1.6580": 7900.0, "1.0037": 7900.0, "1.0038": 7900.0, "1.0039": 7900.0, "1.0044": 7900.0,
        "1.0045": 7900.0, "1.0117": 7900.0, "1.0308": 7900.0, "1.0425": 7900.0, "1.0460": 7900.0,
        "1.0503": 7900.0, "1.0570": 7900.0, "1.0576": 7900.0, "1.0577": 7900.0, "1.0710": 7900.0,
        "1.0715": 7900.0, "1.0718": 7900.0, "1.0762": 7900.0, "1.1141": 7900.0, "1.1191": 7900.0,
        "1.1213": 7900.0, "1.2343": 7900.0, "1.2367": 7900.0, "1.2379": 7900.0, "1.2510": 7900.0,
        "1.2738": 7900.0, "1.2842": 7900.0, "1.3243": 7900.0, "1.3247": 7900.0, "1.3343": 7900.0,
        "1.3505": 7900.0, "1.4571": 7900.0, "1.5060": 7900.0, "1.6323": 7900.0, "1.6773": 7900.0,
        "1.7131": 7900.0, "1.7225": 7900.0, "1.7227": 7900.0, "1.8515": 7900.0, "TOOLOX44": 7900.0
    },
    "NEREZ": {
        "1.4435": 8000.0, "1.4005": 8000.0, "1.4021": 8000.0, "1.4034": 8000.0, "1.4057": 8000.0,
        "1.4104": 8000.0, "1.4112": 8000.0, "1.4125": 8000.0, "1.4301": 8000.0, "1.4305": 8000.0,
        "1.4306": 8000.0, "1.4307": 8000.0, "1.4401": 8000.0, "1.4404": 8000.0, "1.4405": 8000.0,
        "1.4410": 8000.0, "1.4418": 8000.0, "1.4462": 8000.0, "1.4571": 8000.0, "1.5752": 8000.0
    },
    "PLAST": {
        "PA": 1200.0, "PC": 1500.0, "PEEK": 1400.0, "PE-HD": 1000.0, "PET-G": 1700.0,
        "PE-UHMW": 1000.0, "POM": 1500.0, "PP": 1000.0, "PVC": 1700.0
    },
    "FAREBNÉ KOVY": {
        "2.0371": 9000.0, "2.0401": 9000.0, "2.0402": 9000.0, "2.0975": 9000.0, 
        "2.1020": 9000.0, "2.1285": 9000.0, "2.5083": 2900.0, "3.1255": 2900.0, 
        "3.1325": 2900.0, "3.1355": 2900.0, "3.1645": 2900.0, "3.215": 2900.0, 
        "3.2315": 2900.0, "3.3206": 2900.0, "3.3207": 2900.0, "3.3211": 2900.0, 
        "3.3547": 2900.0, "3.4365": 2900.0, "3.5312": 4500.0
    }
}

# --- 5. POMOCNÉ FUNKCIE ---
def ulozit_do_gsheets(riadok_dict):
    try:
        df_existujuce = conn.read(spreadsheet=URL_TABULKY)
        novy_df = pd.DataFrame([riadok_dict])
        aktualizovane_df = pd.concat([df_existujuce, novy_df], ignore_index=True)
        conn.update(spreadsheet=URL_TABULKY, data=aktualizovane_df)
    except Exception as e:
        st.error(f"Nepodarilo sa uložiť dáta do Google Tabuľky: {e}")

def generovat_pdf(firma, polozky, celkova_suma, cislo_cp):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "CENOVÁ PONUKA - MECASYS", ln=True, align="C")
    pdf.ln(10)
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 7, f"Zákazník: {firma}", ln=True)
    pdf.cell(0, 7, f"Číslo CP: {cislo_cp}", ln=True)
    pdf.ln(10)
    for p in polozky:
        pdf.cell(0, 8, f"{p['Položka']} | {p['Ks']} ks | {p['Cena_ks']:.2f} EUR/ks | Spolu: {p['Spolu']:.2f} EUR", ln=True)
    pdf.ln(10)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, f"CELKOM BEZ DPH: {celkova_suma:.2f} EUR", ln=True, align="R")
    return pdf.output(dest='S').encode('latin-1', errors='replace')

# --- 6. UI APLIKÁCIE ---
st.title("⚙️ MECASYS - Master CP Generátor")

with st.sidebar:
    st.header("Zákazník a CP")
    # Dynamicky zoradený zoznam firiem
    zoznam_firiem = ["--- NOVÝ ZÁKAZNÍK ---"] + sorted(db_zakaznici.keys())
    vyber_firmy = st.selectbox("Vyberte firmu:", zoznam_firiem)
    
    if vyber_firmy == "--- NOVÝ ZÁKAZNÍK ---":
        finalny_zakaznik = st.text_input("Názov novej firmy:")
        krajina, lojalita = "SK", 0.50
    else:
        finalny_zakaznik = vyber_firmy
        lojalita, krajina = db_zakaznici[vyber_firmy]
        st.info(f"Firma: {finalny_zakaznik}\nKrajina: {krajina}\nLojalita: {lojalita}")
    
    cislo_cp = st.text_input("Číslo CP:", value=f"{datetime.now().year}-0001_MEC")

st.subheader("Parametre komponentu")
c1, c2, c3 = st.columns(3)
with c1:
    polozka = st.text_input("Názov / Kód dielu:")
    n = st.number_input("Počet kusov (n):", min_value=1, value=1)
    narocnost = st.selectbox("Náročnosť (1-5):", ["1", "2", "3", "4", "5"], index=2)
with c2:
    cas = st.number_input("Čas výroby (hod/ks):", min_value=0.001, format="%.3f", value=0.100)
    mat_kat = st.selectbox("Kategória materiálu:", list(db_materialy.keys()))
    akost = st.selectbox("Akosť materiálu:", list(db_materialy[mat_kat].keys()))
    hustota = db_materialy[mat_kat][akost]
    st.caption(f"Hustota: {hustota} kg/m³")
with c3:
    tvar = st.selectbox("Tvar polotovaru:", ["KR (Kruh)", "STV (Štvorec)"])
    D = st.number_input("Rozmer D (mm):", value=20.0)
    L = st.number_input("Dĺžka L (mm):", value=50.0)
    cena_komp = st.number_input("Cena materiálu na komponent (€):", value=5.00)
    ko_cena_ks = st.number_input("Kooperácia (€/ks):", value=0.00)

if st.button("➕ PRIDAŤ DO KOŠÍKA"):
    # Výpočet teoretickej hmotnosti
    if "KR" in tvar:
        vaha = (np.pi * (D**2) * L * hustota) / 4000000000
    else:
        vaha = (D * D * L * hustota) / 1000000000
        
    st.session_state['kosik'].append({
        "Položka": polozka, "Kusy (n)": n, "Čas výroby (hod/ks)": cas, "Náročnosť": narocnost,
        "Kategória mat.": mat_kat, "Akosť": akost, "Tvar": "KR" if "KR" in tvar else "STV", 
        "Rozmer D": D, "Rozmer L": L, "Hustota": hustota, "Hmotnosť 1ks": vaha, 
        "Cena_material_predpoklad": cena_komp, "ko_cena_ks": ko_cena_ks
    })
    st.success(f"Diel {polozka} bol pridaný.")

# --- 7. KOŠÍK A FINÁLNY VÝPOČET ---
if st.session_state['kosik']:
    st.divider()
    df_prehlad = pd.DataFrame(st.session_state['kosik'])
    st.write("### Aktuálny košík")
    st.dataframe(df_prehlad[["Položka", "Kusy (n)", "Akosť", "Hmotnosť 1ks", "Cena_material_predpoklad"]])

    if st.button("🏁 GENEROVAŤ A ULOŽIŤ PONUKU", type="primary"):
        celkovy_objem = sum(i['Kusy (n)'] for i in st.session_state['kosik'])
        polozky_pdf, suma_cp = [], 0
        
        for p in st.session_state['kosik']:
            if model:
                try:
                    vstup = pd.DataFrame([{
                        "CP_objem": celkovy_objem, "n_komponent": p["Kusy (n)"],
                        "cas_v_predpoklad_komponent (hod)": p["Čas výroby (hod/ks)"],
                        "v_narocnost": p["Náročnosť"], "zakaznik_lojalita": lojalita, "zakaznik_krajina": krajina,
                        "hmotnost": p["Hmotnosť 1ks"], "cena_material_predpoklad": p["Cena_material_predpoklad"], 
                        "ko_cena_ks": p["ko_cena_ks"], "material_nazov": p["Kategória mat."],
                        "tvar_polotovaru": p["Tvar"], "D(mm)": p["Rozmer D"], "L(mm)": p["Rozmer L"],
                        "material_HUSTOTA": p["Hustota"], "material_AKOST": p["Akosť"]
                    }])
                    j_cena = float(model.predict(vstup)[0])
                except:
                    # Záložný výpočet ak model zlyhá
                    j_cena = (p["Čas výroby (hod/ks)"] * 45) + p["Cena_material_predpoklad"] + p["ko_cena_ks"]
            else:
                j_cena = (p["Čas výroby (hod/ks)"] * 45) + p["Cena_material_predpoklad"] + p["ko_cena_ks"]
            
            c_cena = j_cena * p["Kusy (n)"]
            suma_cp += c_cena
            polozky_pdf.append({"Položka": p["Položka"], "Ks": p["Kusy (n)"], "Cena_ks": j_cena, "Spolu": c_cena})
            
            # Zápis do cloudu
            ulozit_do_gsheets({
                "Dátum": datetime.now().strftime("%d.%m.%Y %H:%M"), "Číslo CP": cislo_cp,
                "Zákazník": finalny_zakaznik, "Položka": p["Položka"], "Ks": p["Kusy (n)"],
                "Jednotková cena": round(j_cena, 2), "Spolu": round(c_cena, 2)
            })

        st.balloons()
        pdf_raw = generovat_pdf(finalny_zakaznik, polozky_pdf, suma_cp, cislo_cp)
        st.download_button("📥 STIAHNUŤ PDF PONUKU", data=pdf_raw, file_name=f"CP_{cislo_cp}.pdf", mime="application/pdf")

    if st.button("🗑️ VYMAZAŤ KOŠÍK"):
        st.session_state['kosik'] = []
        st.rerun()
