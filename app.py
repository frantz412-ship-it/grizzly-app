import os
import re
import streamlit as st
import google.generativeai as genai
from docx import Document
import pdfplumber
from odf.opendocument import load
from odf.text import P
from odf.teletype import extractText

# ==========================================
# 0. CONFIGURATION STABLE
# ==========================================
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.error("Clé API manquante dans les Secrets Streamlit.")

def appel_ia(prompt):
    """Moteur résilient qui teste les chemins v1 stables"""
    # On teste les noms de modèles les plus standards
    for m_name in ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-pro"]:
        try:
            model = genai.GenerativeModel(m_name)
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            if "404" in str(e): continue # On tente le modèle suivant
            return f"❌ Erreur : {e}"
    return "❌ Aucun modèle n'a répondu. Vérifie tes accès sur AI Studio."

# ==========================================
# 1. TRIAGE DES TEXTES (ÉCONOMIE DE QUOTA)
# ==========================================
def convertir_en_txt(f):
    try:
        if f.name.endswith(".pdf"):
            with pdfplumber.open(f) as pdf:
                return "\n".join([p.extract_text() or "" for p in pdf.pages])
        elif f.name.endswith(".docx"):
            return "\n".join([p.text for p in Document(f).paragraphs])
        elif f.name.endswith(".odt"):
            return "\n".join([extractText(p) for p in load(f).getElementsByType(P)])
    except: return ""

def extraire_passages_perso(texte, nom_perso, fenetre=800):
    """Trieur Python : Extrait uniquement ce qui concerne le perso"""
    nom_perso = nom_perso.lower()
    matches = [m.start() for m in re.finditer(re.escape(nom_perso), texte.lower())]
    passages = []
    for m in matches[:30]: # On limite à 30 passages pour le quota gratuit
        start, end = max(0, m - fenetre), min(len(texte), m + fenetre)
        passages.append(texte[start:end])
    return "\n\n--- EXTRAIT ---\n\n".join(passages)

# ==========================================
# 2. INTERFACE
# ==========================================
st.set_page_config(page_title="Archiviste V17.1", layout="wide")
st.title("🛡️ L'Archiviste V17.1 (Mode Stable)")

f_inputs = st.sidebar.file_uploader("Charger les Tomes", type=["pdf", "docx", "odt"], accept_multiple_files=True)

if f_inputs and st.sidebar.button("⚙️ Scanner l'Intégrale"):
    with st.spinner("Conversion des 4 tomes en texte brut..."):
        full_txt = "".join([convertir_en_txt(f) for f in f_inputs])
        st.session_state.txt_saga = full_txt.replace("’", "'")
        st.success("Saga chargée et triée !")

if "txt_saga" in st.session_state:
    nom = st.text_input("Nom du personnage (Zack, Jonas, Léo...)")
    if nom and st.button(f"🔍 Générer la Fiche Complète"):
        with st.spinner(f"Triage des passages de {nom}..."):
            extraits = extraire_passages_perso(st.session_state.txt_saga, nom)
        
        if extraits:
            prompt = f"""Génère la fiche détaillée de {nom} :
            - PHYSIQUE & AURAS
            - PSYCHOLOGIE & TRAUMAS
            - DIAGNOSTIC NARRATIF (Cohérence médicale du trauma)
            - LIENS (Amours, Sexe, Tensions)
            - ÉQUIPEMENT & LIEUX
            TEXTE : {extraits}"""
            
            with st.spinner("L'IA rédige la fiche..."):
                st.markdown(appel_ia(prompt))
