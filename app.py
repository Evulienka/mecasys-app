import os
import sys

# --- 1. OPRAVA KOMPATIBILITY (DÔLEŽITÉ) ---
# Tento blok rieši chybu: Can't get attribute '__pyx_unpickle_CyHalfSquaredError'
try:
    import sklearn.metrics._pairwise_distances_reduction._datasets_pair
    import sklearn.metrics._pairwise_distances_reduction._middle_term_computer
    # Trik pre presmerovanie chýbajúcich modulov v novších verziách sklearn
    from sklearn._loss import loss
    sys.modules['sklearn._loss._loss'] = loss
except Exception:
    pass

# Nastavenie pre Orange (vypnutie grafického rozhrania na serveri)
os.environ['QT_QPA_PLATFORM'] = 'offscreen'

import streamlit as st
import pickle
import pandas as pd
import numpy as np
from datetime import datetime

# --- 2. KONFIGURÁCIA STRÁNKY ---
st.set_page_config(page_title="MECASYS AI Kalkulátor", layout="wide", page_icon="⚙️")

# --- 3. NAČÍTANIE MODELU ---
@st.cache_resource
def load_model():
    model_path = "model.pkcls"
    if os.path.exists(model_path):
        try:
            import Orange
            with open(model_path, "rb") as f:
                # Načítanie modelu pomocou pickle
                model = pickle.load(f)
            return model
        except Exception as e:
            st.error(f"Chyba pri načítaní modelu: {e}")
            return None
    else:
        st.error(f"Súbor {model_path} nebol nájdený!")
        return None

model = load_model()

# --- 4. POMOCNÉ VÝPOČTY ---
def vypocitaj_vahu(tvar, d, l, hustota):
    try:
        if "KR" in tvar:
            return (np.pi * (float(d)**2) * float(l) * float(hustota)) / 4e9
        else:
            return (float(d) * float(d) * float(l) * float(hustota)) / 1e9
    except:
        return 0.0

# --- 5. PREDIKČNÁ FUNKCIA (Data Mapper) ---
def predpovedaj_cenu(diel, celkovy_objem, lojalita, krajina):
    # Presné mapovanie podľa tvojho screenshotu z Orange
    vstup = pd.DataFrame([{
        "CP_datum": datetime.now(),
        "CP_objem": float(celkovy_objem),
        "n_komponent": float(diel["n"]),
        "cas_v_predpoklad_komponent (hod)": float(diel["cas"]),
        "CP_uspech": "A",
        "v_narocnost": str(diel["nar"]),
        "ko_cena_komponent": float(diel["ko"]),
        "zakaznik_lojalita": float(lojalita),
        "zakaznik_krajina": str(krajina),
        "material_nazov": str(diel["mat_kat"]),
        "tvar_polotovaru": str(diel["tvar"]),
        "D(mm)": float(diel["D"]),
        "L(mm)": float(diel["L"]),
        "material_HUSTOTA": float(diel["hustota"]),
        "cena_material_predpoklad": float(diel["c_mat"]),
        "material_AKOST": str(diel["akost"])
    }])

    try:
        # Spustenie predikcie Orange modelu
        vysledok = model(vstup)
        return float(vysledok[0])
    except Exception as e:
        st.error(f"Chyba výpočtu: {e}")
        return 0.0

# --- 6. ROZHRANIE ---
if 'kosik' not in st.session_state:
    st.session_state.kosik = []

st.title("⚙️ MECASYS Master AI")

# Sidebar
with st.sidebar:
    st.header("Nastavenia")
    krajina = st.selectbox("Krajina:", ["SK", "CZ", "DE", "AT", "HU", "PL", "FR"])
    lojalita = st.slider("Lojalita zákazníka:", 0.0, 1.0, 0.5)

# Formulár
with st.expander("➕ Pridať diel do ponuky", expanded=True):
    c1, c2, c3 = st.columns(3)
    with c1:
        id_dielu = st.text_input("ID dielu", value="Diel_01")
        n_ks = st.number_input("Počet kusov", min_value=1, value=10)
        narocnost = st.selectbox("Náročnosť", ["1", "2", "3", "4", "5"], index=2)
    with c2:
        cas = st.number_input("Čas (hod/ks)", value=0.5, format="%.3f")
        mat_kat = st.selectbox("Materiál", ["OCEL", "NEREZ", "FAREBNÉ KOVY", "PLAST"])
        akost = st.text_input("Akosť", value="1.0037")
    with c3:
        tvar = st.selectbox("Tvar", ["KR", "STV", "PL"])
        d_rozmer = st.number_input("Rozmer D (mm)", value=20.0)
        l_rozmer = st.number_input("Dĺžka L (mm)", value=100.0)
        c_mat = st.number_input("Materiál (€/ks)", value=1.5)
        ko = st.number_input("Kooperácia (€/ks)", value=0.0)

    if st.button("Uložiť diel"):
        hustota = 7850 if mat_kat in ["OCEL", "NEREZ"] else 2700
        vaha = vypocitaj_vahu(tvar, d_rozmer, l_rozmer, hustota)
        st.session_state.kosik.append({
            "id": id_dielu, "n": n_ks, "nar": narocnost, "cas": cas,
            "mat_kat": mat_kat, "akost": akost, "tvar": tvar,
            "D": d_rozmer, "l": l_rozmer, "c_mat": c_mat, "ko": ko,
            "hustota": hustota, "vaha": vaha, "L": l_rozmer
        })
        st.success("Diel pridaný!")

# --- 7. VÝSLEDNÁ TABUĽKA ---
if st.session_state.kosik:
    st.divider()
    st.subheader("📋 Prehľad ponuky")
    df = pd.DataFrame(st.session_state.kosik)
    st.dataframe(df[["id", "n", "mat_kat", "vaha"]], use_container_width=True)

    if st.button("🚀 VYPOČÍTAŤ AI CENU", type="primary"):
        if model is not None:
            celkovy_objem = sum(item['n'] for item in st.session_state.kosik)
            vysledky = []
            for diel in st.session_state.kosik:
                cena = predpovedaj_cenu(diel, celkovy_objem, lojalita, krajina)
                vysledky.append({
                    "Diel": diel["id"],
                    "Kusy": diel["n"],
                    "AI Cena/ks": f"{cena:.2f} €",
                    "Spolu": f"{(cena * diel['n']):.2f} €"
                })
            st.write("### ✅ Výsledok:")
            st.table(vysledky)
        else:
            st.error("Model nie je správne načítaný. Skontroluj logy.")

    if st.button("Vymazať zoznam"):
        st.session_state.kosik = []
        st.rerun()
