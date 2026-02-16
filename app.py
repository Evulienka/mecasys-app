import os
# Tento riadok musí byť ÚPLNE PRVÝ - hovorí Orangeu, aby nepoužíval grafické okná
os.environ['QT_QPA_PLATFORM'] = 'offscreen'

import streamlit as st
import pickle
import pandas as pd
import numpy as np
from datetime import datetime

# --- 1. KONFIGURÁCIA STRÁNKY ---
st.set_page_config(page_title="MECASYS AI Kalkulátor", layout="wide", page_icon="⚙️")

# --- 2. NAČÍTANIE MODELU (Orange vyžaduje špecifický prístup) ---
@st.cache_resource
def load_model():
    model_path = "model.pkcls"
    if os.path.exists(model_path):
        try:
            import Orange  # Importujeme až tu, aby sme nezdržali štart aplikácie
            with open(model_path, "rb") as f:
                model = pickle.load(f)
            return model
        except Exception as e:
            st.error(f"Chyba pri načítaní modelu: {e}")
            return None
    else:
        st.error(f"Súbor {model_path} nebol nájdený v repozitári!")
        return None

model = load_model()

# --- 3. POMOCNÉ VÝPOČTY (Hmotnosť) ---
def vypocitaj_vahu(tvar, d, l, hustota):
    try:
        if "KR" in tvar:
            return (np.pi * (float(d)**2) * float(l) * float(hustota)) / 4e9
        else:
            return (float(d) * float(d) * float(l) * float(hustota)) / 1e9
    except:
        return 0.0

# --- 4. PREDIKČNÁ FUNKCIA (Data Mapper podľa screenshotu) ---
def predpovedaj_cenu(diel, celkovy_objem, lojalita, krajina):
    # Tento DataFrame musí mať PRESNE rovnaké názvy a poradie ako tvoj screenshot
    vstup = pd.DataFrame([{
        "CP_datum": datetime.now(),
        "CP_objem": float(celkovy_objem),
        "n_komponent": float(diel["n"]),
        "cas_v_predpoklad_komponent (hod)": float(diel["cas"]),
        "CP_uspech": "A",  # Hodnota A alebo N zo screenshotu
        "v_narocnost": str(diel["nar"]), # Musí byť string (Categorical)
        "ko_cena_komponent": float(diel["ko"]),
        "zakaznik_lojalita": float(lojalita),
        "zakaznik_krajina": str(krajina), # Categorical
        "material_nazov": str(diel["mat_kat"]), # Categorical
        "tvar_polotovaru": str(diel["tvar"]), # Categorical
        "D(mm)": float(diel["D"]),
        "L(mm)": float(diel["L"]),
        "material_HUSTOTA": float(diel["hustota"]),
        "cena_material_predpoklad": float(diel["c_mat"]),
        "material_AKOST": str(diel["akost"]) # Categorical
    }])

    try:
        # Volanie Orange modelu (pkcls súbor funguje ako funkcia)
        vysledok = model(vstup)
        return float(vysledok[0])
    except Exception as e:
        st.error(f"Model hlási chybu: {e}")
        return 0.0

# --- 5. ROZHRANIE A KOŠÍK ---
if 'kosik' not in st.session_state:
    st.session_state.kosik = []

st.title("⚙️ MECASYS Master AI")

# Sidebar
with st.sidebar:
    st.header("Nastavenia zákazníka")
    krajina = st.selectbox("Krajina (podľa modelu):", ["SK", "CZ", "DE", "AT", "HU", "PL", "GB", "FR"])
    lojalita = st.slider("Lojalita zákazníka:", 0.0, 1.0, 0.5)

# Formulár pre diely
with st.expander("➕ Pridať nový diel do kalkulácie", expanded=True):
    c1, c2, c3 = st.columns(3)
    with c1:
        id_dielu = st.text_input("Názov / ID dielu", value="Diel_01")
        n_ks = st.number_input("Počet kusov (n_komponent)", min_value=1, value=10)
        narocnost = st.selectbox("Náročnosť (v_narocnost)", ["1", "2", "3", "4", "5"], index=2)
    with c2:
        cas = st.number_input("Čas výroby (hod/ks)", value=0.5, format="%.3f")
        mat_kat = st.selectbox("Materiál", ["OCEL", "NEREZ", "FAREBNÉ KOVY", "PLAST"])
        akost = st.text_input("Akosť (material_AKOST)", value="1.0037")
    with c3:
        tvar = st.selectbox("Tvar polotovaru", ["KR", "STV", "PL"])
        d_rozmer = st.number_input("Rozmer D (mm)", value=20.0)
        l_rozmer = st.number_input("Dĺžka L (mm)", value=100.0)
        c_mat = st.number_input("Materiál (€/ks)", value=1.5)
        ko = st.number_input("Kooperácia (€/ks)", value=0.0)

    if st.button("Pridať do zoznamu"):
        hustota = 7850 if mat_kat in ["OCEL", "NEREZ"] else 2700
        vaha = vypocitaj_vahu(tvar, d_rozmer, l_rozmer, hustota)
        
        st.session_state.kosik.append({
            "id": id_dielu, "n": n_ks, "nar": narocnost, "cas": cas,
            "mat_kat": mat_kat, "akost": akost, "tvar": tvar,
            "D": d_rozmer, "L": l_rozmer, "c_mat": c_mat, "ko": ko,
            "hustota": hustota, "vaha": vaha
        })
        st.success(f"Diel {id_dielu} bol pridaný.")

# --- 6. VÝPOČET ---
if st.session_state.kosik:
    st.divider()
    st.subheader("📋 Zoznam dielov na nacenenie")
    st.table(pd.DataFrame(st.session_state.kosik)[["id", "n", "mat_kat", "akost", "vaha"]])

    if st.button("🚀 VYPOČÍTAŤ CENY AI MODELOM", type="primary"):
        if model is None:
            st.error("Model nie je pripravený.")
        else:
            celkovy_objem = sum(item['n'] for item in st.session_state.kosik)
            finalne_vysledky = []
            
            with st.spinner('Počkajte, AI model analyzuje dáta...'):
                for diel in st.session_state.kosik:
                    cena_ai = predpovedaj_cenu(diel, celkovy_objem, lojalita, krajina)
                    finalne_vysledky.append({
                        "Diel": diel["id"],
                        "Kusy": diel["n"],
                        "AI Cena/ks": f"{cena_ai:.2f} €",
                        "Spolu": f"{(cena_ai * diel['n']):.2f} €"
                    })
            
            st.write("### ✅ Výsledné nacenenie:")
            st.table(finalne_vysledky)

    if st.button("Vymazať všetko"):
        st.session_state.kosik = []
        st.rerun()
