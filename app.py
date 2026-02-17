import streamlit as st
import pandas as pd
import joblib
import numpy as np
import requests
from io import BytesIO
from datetime import datetime

# --- 1. KONFIGURÁCIA A NAČÍTANIE MODELU ---
st.set_page_config(page_title="MECASYS CP Expert", layout="wide")

# Raw link na tvoj uložený model z Orangeu
MODEL_URL = "https://raw.githubusercontent.com/Evulienka/mecasys-app/main/model_ceny.pkl"

@st.cache_resource
def load_model(url):
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        return joblib.load(BytesIO(response.content))
    except Exception as e:
        st.error(f"❌ Nepodarilo sa načítať model: {e}")
        return None

model = load_model(MODEL_URL)

# --- 2. MOŽNOSTI PRE VÝBER (PODĽA TVOJHO DATASETU) ---
krajiny = ['AT', 'CZ', 'DE', 'FR', 'GB', 'HU', 'LT', 'NL', 'PT', 'RO', 'SK', 'SUI', 'SWE']
materialy = ['FAREBNÉ KOVY', 'NEREZ', 'OCEĽ', 'PLAST']
akosti = ['1.4301', 'S235', 'S355', 'AW 6082', 'POM-C', '1.4404', '1.7131', '1.2379', 'ETG100']

# --- 3. GRAFICKÉ ROZHRANIE ---
st.title("📊 MECASYS CP Expert Kalkulátor")
st.markdown("Aplikácia predpovedá cenu pomocou AI modelu natrénovaného v Orange Data Mining.")

if model:
    with st.form("expert_form"):
        c1, c2, c3 = st.columns(3)
        
        with c1:
            st.subheader("📅 Dokumentácia a Klient")
            datum_vyber = st.date_input("Dátum CP", datetime.now())
            cp_uspech = st.selectbox("CP_uspech (A/N)", ['A', 'N'])
            zak_krajina = st.selectbox("Krajina zákazníka", krajiny, index=10) # Default SK
            zak_lojalita = st.number_input("Lojalita (0.0 - 1.0)", value=0.85, step=0.01)

        with c2:
            st.subheader("⚙️ Výroba")
            n_komponent = st.number_input("Množstvo (ks)", min_value=1, value=100)
            v_narocnost = st.selectbox("Náročnosť výroby (1-5)", [1, 2, 3, 4, 5], index=0)
            cas_predpoklad = st.number_input("Odhadovaný čas (hod/ks)", value=0.5, step=0.1)
            ko_cena = st.number_input("Kooperácia celkom (€)", value=0.0, step=1.0)

        with c3:
            st.subheader("🛠️ Materiál a Rozmery")
            mat_nazov = st.selectbox("Typ materiálu", materialy)
            mat_akost = st.selectbox("Akosť materiálu", akosti)
            d_mm = st.number_input("Priemer D (mm)", value=20.0, step=0.1)
            l_mm = st.number_input("Dĺžka L (mm)", value=100.0, step=1.0)
            hustota = st.number_input("Hustota (kg/m3)", value=7900)
            cena_mat_kg = st.number_input("Cena materiálu (€/kg)", value=2.5, step=0.1)

        st.markdown("---")
        submit = st.form_submit_button("🚀 VYPOČÍTAŤ PREDIKCIU CENY", use_container_width=True)

    if submit:
        # --- 4. AUTOMATICKÉ VÝPOČTY (FEATURE ENGINEERING) ---
        # Rozklad dátumu na kvartál a mesiac (pretože model nevidí CP_datum)
        mesiac = datum_vyber.month
        kvartal = (datum_vyber.month - 1) // 3 + 1
        
        # Automatický výpočet objemu (m3)
        objem = (np.pi * ((d_mm/2)/1000)**2 * (l_mm/1000))
        
        # Automatický výpočet hmotnosti (podľa tvojho vzorca z Feature Constructor)
        hmotnost = (3.14159 * (d_mm**2) * l_mm * hustota) / 4000000000

        # --- 5. PRÍPRAVA DÁT PRE MODEL (IDENTICKÉ PORADIE AKO V ORANGE) ---
        vstupy = pd.DataFrame([{
            'kvartal': kvartal,
            'mesiac': mesiac,
            'CP_objem': objem,
            'n_komponent': n_komponent,
            'cas_v_predpoklad_komponent (hod)': cas_predpoklad,
            'CP_uspech': cp_uspech,
            'v_narocnost': v_narocnost,
            'ko_cena_komponent': ko_cena,
            'zakaznik_lojalita': zak_lojalita,
            'zakaznik_krajina': zak_krajina,
            'material_nazov': mat_nazov,
            'tvar_polotovaru': 'KR', # Fixná hodnota 'KR' (Kruh)
            'D(mm)': d_mm,
            'L(mm)': l_mm,
            'material_HUSTOTA': hustota,
            'cena_material_predpoklad': cena_mat_kg,
            'material_AKOST': mat_akost,
            'hmotnost': hmotnost
        }])

        try:
            # PREDPOVEĎ CENY MODELOM
            predikcia = model.predict(vstupy)[0]
            
            # --- 6. ZOBRAZENIE VÝSLEDKOV ---
            st.success("✅ Predikcia bola úspešne vygenerovaná")
            
            res1, res2, res3 = st.columns(3)
            res1.metric("Odhadovaná cena / ks", f"{predikcia:.3f} €")
            res2.metric("Celková hodnota zákazky", f"{predikcia * n_komponent:.2f} €")
            res3.metric("Vypočítaná hmotnosť kusu", f"{hmotnost:.4f} kg")
            
            with st.expander("Zobraziť technické detaily výpočtu"):
                st.write(f"Vypočítaný kvartál: {kvartal}")
                st.write(f"Vypočítaný objem: {objem:.8f} m3")
                st.dataframe(vstupy) # Ukáže tabuľku, ktorú dostal model
                
        except Exception as e:
            st.error(f"Chyba pri výpočte: {e}")
            st.info("Tento problém zvyčajne znamená, že model očakáva iné názvy stĺpcov alebo kategórie.")

else:
    st.info("⌛ Načítavam AI model z GitHubu, prosím čakajte...")
