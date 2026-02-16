import streamlit as st
import pickle
import pandas as pd
import numpy as np
import os
from datetime import datetime

# --- 1. KONFIGURÁCIA ---
st.set_page_config(page_title="MECASYS AI Kalkulátor", layout="wide", page_icon="⚙️")

# --- 2. NAČÍTANIE MODELU ---
@st.cache_resource
def load_model():
    model_path = "model.pkcls"
    if os.path.exists(model_path):
        try:
            # Pri Orange modeloch je niekedy nutné importovať Orange vnútri funkcie
            import Orange
            with open(model_path, "rb") as f:
                return pickle.load(f)
        except Exception as e:
            st.error(f"Chyba pri načítaní modelu: {e}")
    return None

model = load_model()

# --- 3. POMOCNÉ VÝPOČTY ---
def vypocitaj_vahu(tvar, d, l, hustota):
    if "KR" in tvar:
        return (np.pi * (d**2) * l * hustota) / 4e9
    else:
        return (d * d * l * hustota) / 1e9

# --- 4. PREDIKČNÁ FUNKCIA (Data Mapper) ---
def predpovedaj_cenu(komponent, celkovy_objem, lojalita, krajina):
    # Tento slovník MUSÍ presne kopírovať poradie a názvy z tvojho screenshotu!
    vstupne_data = pd.DataFrame([{
        "CP_datum": datetime.now(),
        "CP_objem": float(celkovy_objem),
        "n_komponent": float(komponent["n"]),
        "cas_v_predpoklad_komponent (hod)": float(komponent["cas"]),
        "CP_uspech": "A",  # Predpokladáme úspešnú ponuku
        "v_narocnost": str(komponent["nar"]), # Categorical (C)
        "ko_cena_komponent": float(komponent["ko"]),
        "zakaznik_lojalita": float(lojalita),
        "zakaznik_krajina": str(krajina), # Categorical (C)
        "material_nazov": str(komponent["mat_kat"]), # Categorical (C)
        "tvar_polotovaru": str(komponent["tvar"]), # Categorical (C)
        "D(mm)": float(komponent["D"]),
        "L(mm)": float(komponent["L"]),
        "material_HUSTOTA": float(komponent["hustota"]),
        "cena_material_predpoklad": float(komponent["c_mat"]),
        "material_AKOST": str(komponent["akost"]) # Categorical (C)
    }])

    try:
        # Volanie Orange modelu
        predikcia = model(vstupne_data)
        return float(predikcia[0])
    except Exception as e:
        st.error(f"Chyba pri výpočte ceny: {e}")
        return 0.0

# --- 5. ROZHRANIE A KOŠÍK ---
if 'kosik' not in st.session_state:
    st.session_state.kosik = []

st.title("⚙️ MECASYS Master AI")

# Bočný panel pre globálne nastavenia
with st.sidebar:
    st.header("Zákazník")
    krajina = st.selectbox("Krajina:", ["SK", "CZ", "DE", "AT", "HU", "PL", "FR"])
    lojalita = st.slider("Lojalita (0.0 - 1.0):", 0.0, 1.0, 0.5)

# Formulár pre pridanie dielu
with st.expander("➕ Pridať nový diel do ponuky", expanded=True):
    c1, c2, c3 = st.columns(3)
    with c1:
        id_dielu = st.text_input("Názov/ID dielu")
        n_ks = st.number_input("Počet kusov (n_komponent)", min_value=1, value=10)
        narocnost = st.selectbox("Náročnosť (v_narocnost)", ["1", "2", "3", "4", "5"], index=2)
    with c2:
        cas = st.number_input("Čas výroby (hod/ks)", value=0.5, format="%.3f")
        mat_kat = st.selectbox("Kategória materiálu", ["OCEL", "NEREZ", "FAREBNÉ KOVY", "PLAST"])
        akost = st.text_input("Akosť materiálu", value="1.0037")
    with c3:
        tvar = st.selectbox("Tvar polotovaru", ["KR", "STV", "PL"])
        d_rozmer = st.number_input("Rozmer D / Hrúbka (mm)", value=20.0)
        l_rozmer = st.number_input("Dĺžka L (mm)", value=100.0)
        c_mat = st.number_input("Cena materiálu (€/ks)", value=1.5)
        ko = st.number_input("Kooperácia (€/ks)", value=0.0)

    if st.button("Pridať diel do košíka"):
        novy_diel = {
            "id": id_dielu, "n": n_ks, "nar": narocnost, "cas": cas,
            "mat_kat": mat_kat, "akost": akost, "tvar": tvar,
            "D": d_rozmer, "L": l_rozmer, "c_mat": c_mat, "ko": ko,
            "hustota": 7850 # Príklad pre oceľ
        }
        st.session_state.kosik.append(novy_diel)
        st.toast(f"Diel {id_dielu} pridaný!")

# --- 6. PREHĽAD A VÝPOČET AI ---
if st.session_state.kosik:
    st.divider()
    st.subheader("📋 Aktuálna ponuka")
    
    # Zobrazenie košíka v tabuľke
    df_kosik = pd.DataFrame(st.session_state.kosik)
    st.dataframe(df_kosik[["id", "n", "mat_kat", "akost", "cas"]], use_container_width=True)

    if st.button("🚀 VYPOČÍTAŤ CENY POMOCOU AI", type="primary"):
        if model is None:
            st.error("Model nie je načítaný! Skontroluj model.pkcls a requirements.txt.")
        else:
            celkovy_objem = sum(item['n'] for item in st.session_state.kosik)
            vysledky = []
            
            with st.spinner('AI model práve naceňuje...'):
                for diel in st.session_state.kosik:
                    cena_ai = predpovedaj_cenu(diel, celkovy_objem, lojalita, krajina)
                    vysledky.append({
                        "Diel": diel["id"],
                        "Kusy": diel["n"],
                        "AI Odhad Jednotkovej Ceny": f"{cena_ai:.2f} €",
                        "Spolu": f"{(cena_ai * diel['n']):.2f} €"
                    })
            
            st.table(vysledky)
            
    if st.button("Vysypať košík"):
        st.session_state.kosik = []
        st.rerun()
