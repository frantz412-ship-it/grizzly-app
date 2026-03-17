import os
import pandas as pd
from datetime import datetime, timezone
import streamlit as st
from mistralai import Mistral
from streamlit_gsheets import GSheetsConnection

# Configuration
st.set_page_config(page_title="Grizzly et Moineau", layout="wide")

# Connexions sécurisées
try:
    MISTRAL_API_KEY = st.secrets["MISTRAL_API_KEY"]
    client = Mistral(api_key=MISTRAL_API_KEY)
    conn = st.connection("gsheets", type=GSheetsConnection)
    SHEET_URL = st.secrets["connections"]["gsheets"]["spreadsheet"]
except Exception as e:
    st.error(f"Configuration manquante : {e}")
    st.stop()

# Fonctions
def load_data():
    return conn.read(spreadsheet=SHEET_URL, worksheet="Feuille 1", ttl="5m")

st.title("📚 Grizzly et Moineau : Station d'Écriture")

# Affichage des données existantes
st.subheader("Historique des analyses")
df = load_data()
st.dataframe(df, use_container_width=True)

# Zone d'écriture
st.subheader("Nouvel extrait")
txt = st.text_area("Colle ton texte ici...", height=300)

if st.button("Analyser et Sauvegarder"):
    if txt:
        with st.spinner("Analyse en cours..."):
            # Ici, l'IA Mistral fera son travail
            st.success("Prêt pour l'analyse !")
    else:
        st.warning("Texte vide.")
