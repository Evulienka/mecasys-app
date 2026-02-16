import streamlit as st
import pickle
import pandas as pd
import numpy as np
import requests
import os
from datetime import datetime

# --- 1. PODPORA PRE ORANGE MODEL ---
try:
    import Orange
except ImportError:
    st.error("Inštalujem knižnice (Orange3)... Ak to trvá dlho, urobte Reboot app.")

# --- 2. KONFIGURÁCIA STRÁNKY ---
st.set_page_config(page_title="Mecasys CP Generátor", layout="wide", page_icon="⚙️")

# Inicializácia košíka v pamäti prehliadača
if 'kosik' not in st.session_state:
    st.session_state['kosik'] = []

# --- 3. FUNKCIA PRE ZÁPIS DO GOOGLE FORM ---
def ulozit_do_google_form(data):
    url = "https://docs.google.com/forms/d/e/1FAIpQLSf92s3nBMz6Oviq6WgNLyid9GmcNgAtQOAuWUVBPt9mcrotzw/formResponse"
    payload = {
        "entry.2036980587": data.get('cas_zapisu'),
        "entry.1706175647": data.get('cp_cislo'),
        "entry.1989679198": data.get('zakaznik'),
        "entry.539823438": data.get('krajina'),
        "entry.134015096": data.get('lojalita'),
        "entry.316867622": data.get('id_komponent'),
        "entry.1979044815": data.get('polozka'),
        "entry.1770267755": data.get('kusy'),
        "entry.1448057262": data.get('cp_objem'),
        "entry.1718042457": data.get('cas_vyroby'),
        "entry.1442116035": data.get('narocnost'),
        "entry.1202860155": data.get('kat_mat'),
        "entry.1802901358": data.get('akost'),
        "entry.515277717": data.get('tvar'),
        "entry.1691456947": data.get('rozmer_d'),
        "entry.1504975591": data.get('rozmer_l'),
        "entry.2120406855": data.get('hustota'),
        "entry.1834947990": data.get('vaha'),
        "entry.2064161749": data.get('cena_mat_kg'),
        "entry.1030739986": data.get('kooperacia'),
        "entry.1221544185": data.get('jednotkova_cena'),
        "entry.2096773216": data.get('celkova_suma')
    }
    try:
        requests.post(url, data=payload, timeout=5)
    except:
        pass

# --- 4. KOMPLETNÁ DATABÁZA ZÁKAZNÍKOV (156 FIRIEM) ---
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

# --- 5. KOMPLETNÁ DATABÁZA MATERIÁLOV ---
db_materialy = {
    "OCEĽ": {
        "1.6580": 7900.0, "1.0037": 7900.0, "1.0038": 7900.0, "1.1191": 7900.0,
        "1.2379": 7900.0, "1.7225": 7900.0, "1.7131": 7900.0, "TOOLOX44": 7900.0
    },
    "NEREZ": {
        "1.4301": 8000.0, "1.4305": 8000.0, "1.4404": 8000.0, "1.4571": 8000.0, "1.4021": 8000.0
    },
    "PLAST": {
        "PA": 1200.0, "POM": 1500.0, "PE-HD": 1000.0, "PVC": 1700.0, "PEEK": 1400.0, "TEFLON": 2200.0
    },
    "FAREBNÉ KOVY": {
        "3.4365": 2800.0, "2.0401": 8500.0, "2.5083": 2660.0, "BRONZ": 8800.0
    }
}

# --- 6. NAČÍTANIE MODELU ---
@st.cache_resource
def load_model():
    path = "model.pkcls"
    if os.path.exists(path):
        try:
            with open(path, "rb") as f:
                return pickle.load(f)
        except Exception as e:
            st.error(f"Chyba pri čítaní modelu: {e}. Skúste Reboot app.")
    return None

model = load_model()

# --- 7. HLAVNÉ ROZHRANIE ---
st.title("⚙️ MECASYS - Master CP Generátor")

if model is None:
    st.warning("Čakám na model... Uistite sa, že súbor 'model.pkcls' je v tom istom priečinku ako tento kód.")
    st.stop()

# --- SIDEBAR (ZÁKAZNÍK) ---
with st.sidebar:
    st.header("Zákazník a Projekt")
    cp_datum = st.date_input("Dátum ponuky:", datetime.now())
    vyber_firmy = st.selectbox("Vyberte firmu:", sorted(db_zakaznici.keys()))
    lojalita, krajina = db_zakaznici[vyber_firmy]
    st.info(f"📍 {krajina} | ⭐ Lojalita: {lojalita}")
    cislo_cp = st.text_input("Číslo CP:", value=f"{cp_datum.year}-0001_MEC")

# --- FORMULÁR PRE KOMPONENT ---
st.subheader("Nový komponent")
c1, c2, c3 = st.columns(3)

with c1:
    polozka = st.text_input("ID / Názov komponentu:")
    n_ks = st.number_input("Počet kusov (n):", min_value=1, value=1)
    narocnost = st.slider("Technická náročnosť (1-5):", 1, 5, 3)

with c2:
    cas = st.number_input("Čas výroby (hod/ks):", min_value=0.001, value=0.1, format="%.3f")
    mat_kat = st.selectbox("Kategória materiálu:", list(db_materialy.keys()))
    akost = st.selectbox("Akosť materiálu:", list(db_materialy[mat_kat].keys()))
    hustota = db_materialy[mat_kat][akost]

with c3:
    tvar = st.selectbox("Tvar polotovaru:", ["KR (Kruh)", "STV (Štvorec)"])
    D = st.number_input("Rozmer D / Šírka (mm):", value=20.0)
    L = st.number_input("Dĺžka L (mm):", value=50.0)
    c_mat = st.number_input("Odhad materiálu (€/ks):", value=2.0)
    ko_cena = st.number_input("Kooperácia / Iné (€/ks):", value=0.0)

if st.button("➕ PRIDAŤ DO KOŠÍKA"):
    # Výpočet hmotnosti
    vaha = (np.pi*(D**2)*L*hustota)/4e9 if "KR" in tvar else (D*D*L*hustota)/1e9
    st.session_state.kosik.append({
        "ID": polozka, "n": n_ks, "cas": cas, "nar": narocnost, "kat": mat_kat, "akost": akost,
        "tvar": "KR" if "KR" in tvar else "STV", "D": D, "L": L, "vaha": vaha, 
        "c_mat": c_mat, "ko": ko_cena, "hustota": hustota
    })
    st.success(f"Komponent '{polozka}' bol pridaný.")

# --- 8. KOŠÍK A VÝPOČET ---
if st.session_state.kosik:
    st.divider()
    st.write("### 🛒 Aktuálne položky v ponuke")
    df_preview = pd.DataFrame(st.session_state.kosik)
    st.dataframe(df_preview[["ID", "n", "akost", "vaha", "c_mat"]])

    if st.button("🏁 NACENIŤ AI MODELOM A ODOSLAŤ", type="primary"):
        celkovy_objem = sum(i['n'] for i in st.session_state.kosik)
        finalne_tabulka = []

        for p in st.session_state.kosik:
            # Príprava dát pre Orange model (vstupný DataFrame)
            vstup = pd.DataFrame([{
                "CP_datum": cp_datum.strftime("%Y-%m-%d"),
                "CP_objem": celkovy_objem,
                "n_komponent": p["n"],
                "cas_v_predpoklad_komponent (hod)": p["cas"],
                "v_narocnost": p["nar"],
                "zakaznik_lojalita": lojalita,
                "zakaznik_krajina": krajina,
                "hmotnost": p["vaha"],
                "cena_material_predpoklad": p["c_mat"],
                "ko_cena_ks": p["ko"],
                "material_nazov": p["kat"],
                "tvar_polotovaru": p["tvar"],
                "D(mm)": p["D"],
                "L(mm)": p["L"],
                "material_HUSTOTA": p["hustota"],
                "material_AKOST": p["akost"]
            }])
            
            # PREDPOVEĎ CENY
            try:
                # Orange modely niekedy vyžadujú volanie cez .predict() alebo priamo ()
                if hasattr(model, 'predict'):
                    predikcia = model.predict(vstup)
                else:
                    predikcia = model(vstup)
                
                j_cena = float(predikcia[0])
            except Exception as e:
                st.error(f"Chyba výpočtu pri diely {p['ID']}: {e}")
                j_cena = 0.0
            
            c_spolu = j_cena * p["n"]
            finalne_tabulka.append({"Diel": p["ID"], "Ks": p["n"], "Jedn. cena": f"{j_cena:.2f} €", "Celkom": f"{c_spolu:.2f} €"})

            # Logovanie do Google Form
            ulozit_do_google_form({
                "cas_zapisu": datetime.now().strftime("%d.%m.%Y %H:%M:%S"),
                "cp_cislo": cislo_cp, "zakaznik": vyber_firmy, "krajina": krajina,
                "lojalita": str(lojalita), "id_komponent": p["ID"], "polozka": p["ID"],
                "kusy": str(p["n"]), "cp_objem": str(celkovy_objem),
                "cas_vyroby": str(p["cas"]), "narocnost": str(p["nar"]),
                "kat_mat": p["kat"], "akost": p["akost"], "tvar": p["tvar"],
                "rozmer_d": str(p["D"]), "rozmer_l": str(p["L"]), "hustota": str(p["hustota"]),
                "vaha": f"{p['vaha']:.4f}", "cena_mat_kg": f"{p['c_mat']:.2f}",
                "kooperacia": f"{p['ko']:.2f}", "jednotkova_cena": f"{j_cena:.2f}",
                "celkova_suma": f"{c_spolu:.2f}"
            })

        st.divider()
        st.subheader("📊 Výsledná kalkulácia")
        st.table(pd.DataFrame(finalne_tabulka))
        st.balloons()

    if st.button("🗑️ VYMAZAŤ KOŠÍK"):
        st.session_state.kosik = []
        st.rerun()
