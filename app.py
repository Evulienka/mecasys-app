import streamlit as st
import os
import sys

st.title("🕵️ Diagnostika MECASYS")

# 1. KROK: Kontrola súborov
st.write("### 1. Kontrola súborov v repozitári")
files = os.listdir(".")
if "model.pkcls" in files:
    st.success("✅ model.pkcls nájdený")
else:
    st.error("❌ model.pkcls chýba!")

if "requirements.txt" in files:
    st.success("✅ requirements.txt nájdený")

# 2. KROK: Kontrola nainštalovaných knižníc
st.write("### 2. Kontrola knižníc")
st.write(f"Verzia Pythonu: {sys.version}")

try:
    import pandas as pd
    st.write(f"Pandas: {pd.__version__}")
    import Orange
    st.success(f"✅ Orange úspešne nainštalovaný! Verzia: {Orange.__version__}")
except Exception as e:
    st.error(f"❌ Chyba pri načítaní Orange: {e}")
    st.info("Ak je tu chyba, Streamlit Cloud pravdepodobne ešte stále inštaluje Orange3 (trvá to cca 2-5 minút).")

st.write("---")
st.write("Ak vidíš tento text, Streamlit funguje. Ak aplikácia padá do 'Oh no', skús v menu Streamlitu vybrať **'Clear Cache'** a potom **'Reboot App'**.")
