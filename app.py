import os
import sys

# --- DEFINTÍVNA OPRAVA PRE PKG_RESOURCES ---
# Tento blok musí byť úplne na začiatku pred importom Orange
try:
    import setuptools
    import pkg_resources
except ImportError:
    # Ak by to zlyhalo, skúsime to importovať alternatívne
    try:
        from pip._vendor import pkg_resources
        sys.modules['pkg_resources'] = pkg_resources
    except ImportError:
        pass

# Zakázanie grafického prostredia pre server
os.environ['QT_QPA_PLATFORM'] = 'offscreen'

import streamlit as st
import pickle
import pandas as pd
import numpy as np
from datetime import datetime

# --- KONFIGURÁCIA STRÁNKY ---
st.set_page_config(page_title="MECASYS Master AI", layout="wide", page_icon="⚙️")

# --- FUNKCIA NA NAČÍTANIE MODELU ---
@st.cache_resource
def load_model():
    model_path = "model.pkcls"
    if os.path.exists(model_path):
        try:
            import Orange
            with open(model_path, "rb") as f:
                # Načítanie modelu
                return pickle.load(f)
        except Exception as e:
            st.error(f"Chyba pri otváraní modelu: {e}")
            return None
    else:
        st.error("Súbor model.pkcls nebol nájdený!")
        return None

model = load_model()

# --- PREDIKČNÁ FUNKCIA ---
def predpovedaj_cenu(diel, celkovy_objem, lojalita, krajina):
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
        predikcia = model(vstup)
        return float(predikcia[0])
    except Exception:
        return 0.0

# --- ROZHRANIE ---
if 'kosik' not in st.session_state:
    st.session_state.kosik = []

st.title("⚙️ MECASYS Master AI")

with st.sidebar:
    st.header("Nastavenia")
    krajina = st.selectbox("Krajina:", ["SK", "CZ", "DE", "AT", "HU", "PL", "FR"])
    lojalita = st.slider("Lojalita zákazníka:", 0.0, 1.0, 0.5)

with st.expander("➕ Pridať nový diel", expanded=True):
    c1, c2, c3 = st.columns(3)
    with c1:
        id_dielu = st.text_input("ID dielu", value="Diel_01")
        n_ks = st.number_input("Počet kusov", min_value=1, value=10)
        nar = st.selectbox("Náročnosť", ["1", "2", "3", "4", "5"], index=2)
    with c2:
        cas = st.number_input("Čas (hod/ks)", value=0.5, format="%.3f")
        mat = st.selectbox("Materiál", ["OCEL", "NEREZ", "FAREBNÉ KOVY", "PLAST"])
        akost = st.text_input("Akosť", value="1.0037")
    with c3:
        tvar = st.selectbox("Tvar polotovaru", ["KR", "STV", "PL"])
        d = st.number_input("Rozmer D (mm)", value=20.0)
        l = st.number_input("Dĺžka L (mm)", value=100.0)
        c_m = st.number_input("Cena mat. (€/ks)", value=1.5)
        ko = st.number_input("Kooperácia (€/ks)", value=0.0)

    if st.button("Uložiť do zoznamu"):
        hustota = 7850 if mat != "PLAST" else 1200
        st.session_state.kosik.append({
            "id": id_dielu, "n": n_ks, "nar": nar, "cas": cas, "mat_kat": mat, 
            "akost": akost, "tvar": tvar, "D": d, "L": l, "c_mat": c_m, "ko": ko,
            "hustota": hustota
        })
        st.success(f"Diel {id_dielu} pridaný.")

if st.session_state.kosik:
    st.divider()
    st.subheader("📋 Aktuálna ponuka")
    st.dataframe(pd.DataFrame(st.session_state.kosik)[["id", "n", "mat_kat"]], use_container_width=True)

    if st.button("🚀 VYPOČÍTAŤ AI CENU", type="primary"):
        if model:
            celkovy_objem = sum(i['n'] for i in st.session_state.kosik)
            vysledky = []
            for d in st.session_state.kosik:
                cena = predpovedaj_cenu(d, celkovy_objem, lojalita, krajina)
                vysledky.append({
                    "Diel": d["id"],
                    "Kusy": d["n"],
                    "Cena/ks": f"{cena:.2f} €",
                    "Spolu": f"{(cena * d['n']):.2f} €"
                })
            st.table(vysledky)
        else:
            st.error("Model stále nie je načítaný.")

    if st.button("Vymazať zoznam"):
        st.session_state.kosik = []
        st.rerun()
