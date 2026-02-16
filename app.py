import streamlit as st
import pickle
import os
import pandas as pd
import numpy as np

# --- 1. KONFIGURÁCIA STRÁNKY ---
st.set_page_config(page_title="MECASYS Model Diagnostika", layout="wide")

st.title("🧪 Diagnostika a Test Modelu")
st.write("Tento skript overí, či je prostredie Streamlit Cloud kompatibilné s tvojím Orange modelom.")

# --- 2. POKUS O IMPORT ORANGE ---
try:
    import Orange
    st.success(f"✅ Knižnica **Orange** úspešne načítaná (Verzia: {Orange.__version__})")
except ImportError:
    st.error("❌ Knižnica Orange nebola nájdená. Skontroluj, či sa requirements.txt správne nainštaloval.")
    st.stop()

# --- 3. NAČÍTANIE MODELU (.pkcls) ---
model_path = "model.pkcls"

if os.path.exists(model_path):
    st.info(f"Súbor `{model_path}` bol nájdený. Pokúšam sa o načítanie (unpickling)...")
    try:
        with open(model_path, "rb") as f:
            model = pickle.load(f)
        
        st.balloons()
        st.success("✅ MODEL BOL ÚSPEŠNE NAČÍTANÝ DO PAMÄTE!")
        
        # --- 4. ANALÝZA ŠTRUKTÚRY (DOMÉNY) ---
        if hasattr(model, "domain"):
            st.subheader("📊 Štruktúra modelu (ako ju vidí AI)")
            
            features = []
            for attr in model.domain.attributes:
                dtype = "Kategorický (C)" if attr.is_discrete else "Numerický (N)"
                values = ", ".join(attr.values) if attr.is_discrete else "-"
                features.append({
                    "Názov stĺpca": attr.name,
                    "Typ": dtype,
                    "Možné hodnoty": values
                })
            
            st.table(pd.DataFrame(features))
            st.write(f"🎯 **Cieľová premenná (Target):** `{model.domain.class_var.name}`")
            
            # --- 5. TESTOVACIA PREDIKCIA ---
            st.divider()
            st.subheader("🏃 Testovacia predikcia")
            
            test_data = pd.DataFrame([{
                "CP_datum": "2024-01-01",
                "CP_objem": 100.0,
                "n_komponent": 10.0,
                "cas_v_predpoklad_komponent (hod)": 0.5,
                "CP_uspech": "A",
                "v_narocnost": "3",
                "ko_cena_komponent": 0.0,
                "zakaznik_lojalita": 0.5,
                "zakaznik_krajina": "SK",
                "material_nazov": "OCEL",
                "tvar_polotovaru": "KR",
                "D(mm)": 20.0,
                "L(mm)": 50.0,
                "material_HUSTOTA": 7900.0,
                "cena_material_predpoklad": 2.0,
                "material_AKOST": "1.0037"
            }])
            
            if st.button("Spustiť testovací výpočet"):
                try:
                    vysledok = model(test_data)
                    st.metric("Výsledná cena z modelu", f"{float(vysledok[0]):.2f} €")
                    st.success("🎉 Model funguje aj výpočtovo!")
                except Exception as pred_err:
                    st.error(f"Chyba pri predikcii: {pred_err}")
        
    except Exception as e:
        st.error(f"❌ Chyba pri unpicklingu modelu: {e}")
else:
    st.error(f"❌ Súbor `{model_path}` nebol nájdený!")
