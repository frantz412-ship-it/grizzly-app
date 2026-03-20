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
# 0. CONFIGURATION (Noms de ta liste)
# ==========================================
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

def appel_ia(prompt):
    # On utilise le modèle exact confirmé par ton diagnostic
    # Priorité : Gemini 3 Flash (ton choix) > Gemini 2.0 Flash (vitesse)
    modeles_confirmes = ["gemini-3-flash-preview", "gemini-2.0-flash", "gemini-1.5-flash"]
    
    for m_name in modeles_confirmes:
        try:
            model = genai.GenerativeModel(m_name)
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            if "404" in str(e): continue 
            return f"❌ Erreur : {e}"
    return "❌ Aucun modèle de ta liste n'a répondu."

# ==========================================
# 1. LE TRIEUR (SÉCURITÉ QUOTA)
# ==========================================
def extraire_passages_perso(texte, nom_perso, fenetre=1000):
    """
    Triage Python : Scanne 1600 pages en une seconde et 
    ne garde que la 'moelle' pour l'IA.
    """
    nom_perso = nom_perso.lower()
    # On cherche les 30 premières occurrences pour ne pas saturer le quota gratuit
    matches = [m.start() for m in re.finditer(re.escape(nom_perso), texte.lower())]
    passages = []
    for m in matches[:30]:
        start, end = max(0, m - fenetre), min(len(texte), m + fenetre)
        passages.append(texte[start:end])
    return "\n\n--- EXTRAIT DU MANUSCRIT ---\n\n".join(passages)

# ==========================================
# 2. INTERFACE ÉDITORIALE
# ==========================================
st.set_page_config(page_title="Archiviste V17.2", layout="wide")
st.title("🛡️ L'Archiviste V17.2 (Moteur Gemini 3)")

f_inputs = st.sidebar.file_uploader("Charger les 4 Tomes", type=["pdf", "docx", "odt"], accept_multiple_files=True)

if f_inputs and st.sidebar.button("⚙️ Scanner l'Intégrale"):
    with st.spinner("Conversion des manuscrits en texte brut..."):
        full_txt = ""
        for f in f_inputs:
            if f.name.endswith(".pdf"):
                with pdfplumber.open(f) as pdf:
                    full_txt += "\n".join([p.extract_text() or "" for p in pdf.pages])
            elif f.name.endswith(".docx"):
                full_txt += "\n".join([p.text for p in Document(f).paragraphs])
            elif f.name.endswith(".odt"):
                full_txt += "\n".join([extractText(p) for p in load(f).getElementsByType(P)])
        st.session_state.txt_saga = full_txt.replace("’", "'")
        st.success(f"Saga chargée ! ({len(full_txt)//1000}k caractères détectés)")

if "txt_saga" in st.session_state:
    nom = st.text_input("Nom du personnage (Zack, Jonas, Léo...)")
    if nom and st.button(f"🔍 Générer la Fiche Ultra-Détaillée"):
        with st.spinner(f"Triage et Analyse de {nom} par Gemini 3..."):
            extraits = extraire_passages_perso(st.session_state.txt_saga, nom)
            
            prompt = f"""
            Génère une fiche personnage exhaustive pour {nom} basée sur les extraits fournis.
            
            STRUCTURE REQUISE :
            1. PHYSIQUE & AURAS : Traits, cicatrices, couleurs d'auras.
            2. PSYCHOLOGIE : État mental actuel, évolution depuis le début.
            3. DIAGNOSTIC NARRATIF : Analyse de la cohérence somatique du trauma (tremblements, mutisme, etc.).
            4. LIENS & RAPPORTS : Relations (Asexuel/Sexuel), amitiés, tensions.
            5. ÉQUIPEMENT & VÊTEMENTS : Ce qu'il porte, ses armes.
            6. LIEUX ASSOCIÉS : Où on le trouve le plus souvent.
            
            TEXTE DU MANUSCRIT :
            {extraits}
            """
            resultat = appel_ia(prompt)
            st.markdown(resultat)
            st.download_button("💾 Exporter la Fiche", resultat, file_name=f"Fiche_{nom}.txt")
