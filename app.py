import os
import sys

# Vypnutie GUI pre Orange server
os.environ['QT_QPA_PLATFORM'] = 'offscreen'

import streamlit as st
import pickle
import pandas as pd
import numpy as np
from datetime import datetime

# --- 1. NAČÍTANIE MODELU ---
@st.cache_resource
def load_model():
    model_path = "model.pkcls"
    if os.path.exists(model_path):
        try:
            import Orange
            with open(model_path, "rb") as f:
                return pickle.load(f)
        except Exception as e:
            st.error(f"Model sa nepodarilo otvoriť: {e}")
            return None
    return None

model = load_model()

# --- 2. VÝPOČET ---
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
        return float(model(vstup)[0])
    except:
        return 0.0

# --- 3. ROZHRANIE ---
st.title("⚙️ MECASYS Master AI")

if 'kosik' not in st.session_state:
    st.session_state.kosik = []

with st.sidebar:
    st.header("Nastavenia")
    krajina = st.selectbox("Krajina:", ["SK", "CZ", "DE", "AT", "HU", "PL", "FR"])
    lojalita = st.slider("Lojalita:", 0.0, 1.0, 0.5)

with st.expander("➕ Pridať diel", expanded=True):
    c1, c2, c3 = st.columns(3)
    with c1:
        id_dielu = st.text_input("ID dielu", value="Diel_01")
        n_ks = st.number_input("Kusy", min_value=1, value=10)
        nar = st.selectbox("Náročnosť", ["1", "2", "3", "4", "5"], index=2)
    with c2:
        cas = st.number_input("Čas (hod/ks)", value=0.5)
        mat = st.selectbox("Materiál", ["OCEL", "NEREZ", "FAREBNÉ KOVY", "PLAST"])
        akost = st.text_input("Akosť", value="1.0037")
    with c3:
        tvar = st.selectbox("Tvar", ["KR", "STV", "PL"])
        d = st.number_input("D (mm)", value=20.0)
        l = st.number_input("L (mm)", value=100.0)
        c_m = st.number_input("Cena mat. (€/ks)", value=1.5)
        ko = st.number_input("Kooperácia (€/ks)", value=0.0)

    if st.button("Uložiť diel"):
        st.session_state.kosik.append({
            "id": id_dielu, "n": n_ks, "nar": nar, "cas": cas, "mat_kat": mat, 
            "akost": akost, "tvar": tvar, "D": d, "L": l, "c_mat": c_m, "ko": ko,
            "hustota": 7850 if mat != "PLAST" else 1200
        })
        st.success("Diel pridaný!")

if st.session_state.kosik:
    st.divider()
    st.subheader("📋 Prehľad")
    st.dataframe(pd.DataFrame(st.session_state.kosik)[["id", "n", "mat_kat"]])
    
    if st.button("🚀 VYPOČÍTAŤ", type="primary"):
        if model:
            celk = sum(i['n'] for i in st.session_state.kosik)
            for d in st.session_state.kosik:
                cena = predpovedaj_cenu(d, celk, lojalita, krajina)
                st.write(f"**{d['id']}**: {cena:.2f} € / ks")
        else:
            st.error("Model stále nie je načítaný.")
