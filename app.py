import streamlit as st
import pandas as pd
from datetime import datetime, timezone
import os

# --- IMPORT SECURISE DE MISTRAL ---
try:
    from mistralai import Mistral
    MISTRAL_MODERN = True
except ImportError:
    try:
        from mistralai.client import MistralClient as Mistral
        MISTRAL_MODERN = False
    except ImportError:
        st.error("❌ Erreur critique : La bibliothèque Mistral n'est pas trouvée.")
        st.stop()

from streamlit_gsheets import GSheetsConnection

# --- CONFIGURATION ---
st.set_page_config(page_title="Grizzly et Moineau", page_icon="📚", layout="wide")

try:
    api_key = st.secrets["MISTRAL_API_KEY"]
    client = Mistral(api_key=api_key)
    conn = st.connection("gsheets", type=GSheetsConnection)
    url = st.secrets["connections"]["gsheets"]["spreadsheet"]
except Exception as e:
    st.error(f"⚠️ Problème de configuration des Secrets : {e}")
    st.stop()

# --- INTERFACE ---
st.title("📚 Grizzly et Moineau : Station d'Écriture")
st.write("✅ Système connecté et prêt pour l'analyse.")

# Test de lecture des données
try:
    df = conn.read(spreadsheet=url, worksheet="Feuille 1", ttl="5m")
    st.subheader("Dernières entrées du carnet")
    st.dataframe(df.tail(5), use_container_width=True)
except:
    st.info("Le carnet est vide ou l'onglet 'Feuille 1' est introuvable.")
