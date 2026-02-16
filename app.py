import os
import sys

# --- 1. SILNÁ OPRAVA PKG_RESOURCES (MUST BE FIRST) ---
try:
    import setuptools
    import pkg_resources
except ImportError:
    try:
        from pip._vendor import pkg_resources
        sys.modules['pkg_resources'] = pkg_resources
    except:
        pass

# Zakázanie GUI pre server (dôležité pre Orange)
os.environ['QT_QPA_PLATFORM'] = 'offscreen'

import streamlit as st
import pickle
import pandas as pd
import numpy as np
from datetime import datetime

# Nastavenie vzhľadu stránky
st.set_page_config(page_title="MECASYS Master AI", page_icon="⚙️", layout="wide")

# --- 2. NAČÍTANIE MODELU ---
@st.cache_resource
def load_model():
    model_path = "model.pkcls"
    if os.path.exists(model_path):
        try:
            import Orange
            with open(model_path, "rb") as f:
                return pickle.load(f)
        except Exception as e:
            st.error(f"Chyba pri načítaní modelu: {e}")
            return None
    return None

model = load_model()

# --- 3. VÝPOČTOVÁ FUNKCIA ---
def predpovedaj_cenu(diel, celkovy_objem, lojalita, krajina):
    # Vytvorenie tabuľky pre model presne podľa formátu Orange
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
    except Exception as e:
        st.error(f"Chyba výpočtu: {e}")
        return 0.0

# --- 4. ROZHRANIE APLIKÁCIE ---
st.title("⚙️ MECASYS Master AI")

if 'kosik' not in st.session_state:
    st.session_state.kosik = []

if model:
    st.success("✅ Model je úspešne načítaný a pripravený.")
    
    with st.sidebar:
        st.header("Nastavenia dopytu")
        krajina = st.selectbox("Krajina zákazníka:", ["SK", "CZ", "DE", "AT", "HU", "PL", "FR"])
        lojalita = st.slider("Lojalita (0=nový, 1=stály):", 0.0, 1.0, 0.5)

    with st.expander("➕ Pridať nový diel do kalkulácie", expanded=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            id_dielu = st.text_input("ID / Názov dielu", value="Diel_01")
            n_ks = st.number_input("Počet kusov (ks)", min_value=1, value=10)
            nar = st.selectbox("Náročnosť výroby", ["1", "2", "3", "4", "5"], index=2)
        with c2:
            cas = st.number_input("Čas výroby (hod/ks)", value=0.5, format="%.3f")
            mat = st.selectbox("Kategória materiálu", ["OCEL", "NEREZ", "FAREBNÉ KOVY", "PLAST"])
            akost = st.text_input("Akosť materiálu", value="1.0037")
        with c3:
            tvar = st.selectbox("Tvar polotovaru", ["KR", "STV", "PL"])
            d = st.number_input("Rozmer D / hrúbka (mm)", value=20.0)
            l = st.number_input("Dĺžka L (mm)", value=100.0)
            c_m = st.number_input("Cena materiálu (€/ks)", value=1.50)
            ko = st.number_input("Kooperácia (€/ks)", value=0.0)

        if st.button("Uložiť diel do zoznamu"):
            st.session_state.kosik.append({
                "id": id_dielu, "n": n_ks, "nar": nar, "cas": cas, "mat_kat": mat, 
                "akost": akost, "tvar": tvar, "D": d, "L": l, "c_mat": c_m, "ko": ko,
                "hustota": 7850 if mat != "PLAST" else 1200
            })
            st.toast("Diel bol pridaný!")

    # Zobrazenie zoznamu dielov
    if st.session_state.kosik:
        st.subheader("📋 Aktuálny rozpis dielov")
        df_display = pd.DataFrame(st.session_state.kosik)
        st.table(df_display[["id", "n", "mat_kat", "cas"]])
        
        if st.button("🚀 VYPOČÍTAŤ AI CENU PRE VŠETKY DIELY", type="primary"):
            celkovy_objem = sum(item['n'] for item in st.session_state.kosik)
            
            st.subheader("🎯 Výsledná kalkulácia")
            for diel in st.session_state.kosik:
                cena = predpovedaj_cenu(diel, celkovy_objem, lojalita, krajina)
                st.write(f"**{diel['id']}**: {cena:.2f} € / ks (spolu: {cena * diel['n']:.2f} €)")
            
            if st.button("Vymazať zoznam"):
                st.session_state.kosik = []
                st.rerun()
else:
    st.error("❌ Model sa nepodarilo načítať. Skontrolujte logy a urobte Reboot app.")
