import streamlit as st
import pickle
import pandas as pd
import os

st.set_page_config(page_title="MECASYS Master AI", page_icon="⚙️")

# --- NAČÍTANIE MODELU (ČISTÝ PICKLE) ---
@st.cache_resource
def load_model():
    # Používame premenovaný súbor model.pkl
    model_path = "model.pkl" 
    if os.path.exists(model_path):
        try:
            with open(model_path, "rb") as f:
                # Načítame čistý model bez potreby knižnice Orange
                return pickle.load(f)
        except Exception as e:
            st.error(f"Chyba: {e}. Uistite sa, že súbor je na GitHub-e.")
    return None

model = load_model()

st.title("⚙️ MECASYS Master AI")

if model:
    st.success("✅ Systém je pripravený! Orange už nepotrebujeme.")
    
    # Príklad vstupu (uprav si podľa svojich stĺpcov v Orange)
    with st.form("kalkulacia"):
        col1, col2 = st.columns(2)
        with col1:
            cas = st.number_input("Čas (hod)", value=1.0)
            hmotnost = st.number_input("Hmotnosť (kg)", value=0.5)
        with col2:
            material = st.selectbox("Materiál", [1, 2, 3]) # Číselné kódovanie
            objem = st.number_input("Objem výroby", value=100)
            
        submit = st.form_submit_button("Vypočítať cenu")
        
        if submit:
            # Vytvoríme dáta pre model
            vstup = pd.DataFrame([[cas, hmotnost, material, objem]])
            predpoved = model.predict(vstup)
            st.metric("Odhadovaná cena", f"{predpoved[0]:.2f} €")
else:
    st.warning("⚠️ Nahrajte súbor model.pkl na GitHub a urobte Reboot app.")
