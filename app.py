import os
import sys

# --- OPRAVA PRE ORANGE A PKG_RESOURCES ---
try:
    import setuptools
    import pkg_resources
except ImportError:
    pass

# Zakázanie grafického rozhrania pre serverové prostredie
os.environ['QT_QPA_PLATFORM'] = 'offscreen'

import streamlit as st
import pickle
import pandas as pd
import numpy as np
from datetime import datetime

# --- KONFIGURÁCIA STRÁNKY ---
st.set_page_config(page_title="MECASYS Master AI", layout="wide", page_icon="⚙️")

# --- NAČÍTANIE MODELU ---
@st.cache_resource
def load_model():
    model_path = "model.pkcls"
    if os.path.exists(model_path):
        try:
            import Orange
            with open(model_path, "rb") as f:
                # Načítanie modelu pomocou pickle
                return pickle.load(f)
        except Exception as e:
            st.error(f"Chyba pri otváraní modelu: {e}")
            return None
    else:
        st.error("Súbor model.pkcls nebol nájdený v repozitári!")
        return None

model = load_model()

# --- VÝPOČTOVÁ FUNKCIA ---
def predpovedaj_cenu(diel, celkovy_objem, lojalita, krajina):
    # Mapovanie vstupov presne podľa štruktúry tvojho Orange modelu
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

# --- ROZHRANIE APLIKÁCIE ---
if 'kosik' not in st.session_state:
    st.session_state.kosik = []

st.title("⚙️ MECASYS Master AI")

# Sidebar s nastaveniami
with st.sidebar:
    st.header("Nastavenia zákazníka")
    krajina = st.selectbox("Krajina (podľa modelu):", ["SK", "CZ", "DE", "AT", "HU", "PL", "FR"])
    lojalita = st.slider("Lojalita zákazníka:", 0.0, 1.0, 0.5)

# Formulár pre pridanie dielu
with st.expander("➕ Pridať nový diel do kalkulácie", expanded=True):
    c1, c2, c3 = st.columns(3)
    with c1:
        id_dielu = st.text_input("Názov / ID dielu", value="Diel_01")
        n_ks = st.number_input("Počet kusov (n_komponent)", min_value=1, value=10)
        nar = st.selectbox("Náročnosť (v_narocnost)", ["1", "2", "3", "4", "5"], index=2)
    with c2:
        cas = st.number_input("Čas výroby (hod/ks)", value=0.500, format="%.3f")
        mat = st.selectbox("Materiál", ["OCEL", "NEREZ", "FAREBNÉ KOVY", "PLAST"])
        akost = st.text_input("Akosť (material_AKOST)", value="1.0037")
    with c3:
        tvar = st.selectbox("Tvar polotovaru", ["KR", "STV", "PL"])
        d_dim = st.number_input("Rozmer D (mm)", value=20.0)
        l_dim = st.number_input("Dĺžka L (mm)", value=100.0)
        c_m = st.number_input("Materiál (€/ks)", value=1.50)
        ko = st.number_input("Kooperácia (€/ks)", value=0.00)

    if st.button("Pridať do zoznamu"):
        hustota = 7850 if mat in ["OCEL", "NEREZ"] else 2700
        st.session_state.kosik.append({
            "id": id_dielu, "n": n_ks, "nar": nar, "cas": cas, "mat_kat": mat, 
            "akost": akost, "tvar": tvar, "D": d_dim, "L": l_dim, "c_mat": c_m, 
            "ko": ko, "hustota": hustota
        })
        st.toast(f"Diel {id_dielu} pridaný!")

# Tabuľka a výpočet
if st.session_state.kosik:
    st.divider()
    st.subheader("📋 Zoznam položiek")
    temp_df = pd.DataFrame(st.session_state.kosik)
    st.dataframe(temp_df[["id", "n", "mat_kat", "akost"]], use_container_width=True)

    col_btn1, col_btn2 = st.columns([1, 4])
    with col_btn1:
        if st.button("🚀 VYPOČÍTAŤ", type="primary"):
            if model:
                celkovy_objem = sum(item['n'] for item in st.session_state.kosik)
                vysledky = []
                for d in st.session_state.kosik:
                    cena = predpovedaj_cenu(d, celkovy_objem, lojalita, krajina)
                    vysledky.append({
                        "Položka": d["id"],
                        "Množstvo": d["n"],
                        "AI Cena/ks": f"{cena:.2f} €",
                        "Celkom": f"{(cena * d['n']):.2f} €"
                    })
                st.write("### ✅ Výsledná kalkulácia:")
                st.table(vysledky)
            else:
                st.error("Model nie je načítaný. Skontrolujte logy vpravo.")
    
    with col_btn2:
        if st.button("Vymazať všetko"):
            st.session_state.kosik = []
            st.rerun()
