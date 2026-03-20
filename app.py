import os
import re
import streamlit as st
from docx import Document
import pdfplumber
from odf.opendocument import load
from odf.text import P
from odf.teletype import extractText

# Bibliothèque STABLE de Google
import google.generativeai as genai

# ==========================================
# 0. CONFIGURATION GEMINI STABLE
# ==========================================

if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    api_key_env = os.getenv("GEMINI_API_KEY")
    if api_key_env:
        genai.configure(api_key=api_key_env)
    else:
        st.error("Clé API manquante dans les Secrets Streamlit.")

# ==========================================
# 1. CONSTANTES CANONIQUES (SOCLE IMMUABLE)
# ==========================================

CONSTANTES_SAGA = {
    "Zack": (
        "ÂGE: 15 ans. IDENTITÉ: Zackary (officiel), Zack (amis). "
        "ORIENTATION: Bisexuel. COUPLE ASEXUEL avec Jade. "
        "AURA: Rouge et Noir. L'Ombre est une ligne noire."
    ),
    "Jonas": (
        "ÂGE: 17 ans. RÔLE: Grizzly. ORIENTATION: Gay. "
        "COUPLE: Léo. LIMITE: Aucun contact sexuel avec Jade. AURA: Brun."
    ),
    "Léo": (
        "ÂGE: 15 ans. RÔLE: Moineau. ORIENTATION: Bisexuel. "
        "COUPLE: Jonas. POUVOIR: Voit les fils d'auras."
    ),
    "Jade": "COUPLE ASEXUEL avec Zack. RELATIONS SEXUELLES: Léo, Zack.",
    "Autyssé": "PROFIL: TSA. ORIENTATION: Pansexuel. RELATION: Zack. AURA: Bleu.",
    "SAGA": "THÈMES: Reconstruction, Consentement, l'Ombre."
}

# ==========================================
# 2. MOTEUR IA (VERSION ANTI-CRASH)
# ==========================================

def appel_ia(prompt: str, temperature: float = 0.1) -> str:
    """
    Tente d'utiliser 1.5 Pro, puis 1.5 Flash en cas d'erreur.
    """
    # On teste d'abord le modèle le plus intelligent (Pro)
    try:
        model = genai.GenerativeModel('gemini-1.5-pro')
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=temperature,
                max_output_tokens=4096,
            )
        )
        return response.text
    except Exception as e:
        # En cas d'erreur (Quota, 404, etc.), on bascule sur Flash (increvable)
        try:
            st.warning("🔄 Bascule sur le modèle de secours (Flash)...")
            model = genai.GenerativeModel('gemini-1.5-flash')
            response = model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=temperature,
                    max_output_tokens=4096,
                )
            )
            return response.text
        except Exception as e2:
            return f"❌ Échec critique de l'IA : {str(e2)}"

# ==========================================
# 3. GESTION DES FICHIERS
# ==========================================

def extraire_texte(f) -> str:
    try:
        if f.name.endswith(".pdf"):
            with pdfplumber.open(f) as pdf:
                return "\n".join([p.extract_text() or "" for p in pdf.pages])
        elif f.name.endswith(".docx"):
            doc = Document(f)
            return "\n".join([p.text for p in doc.paragraphs])
        elif f.name.endswith(".odt"):
            odt_doc = load(f)
            return "\n".join([extractText(p) for p in odt_doc.getElementsByType(P)])
        return ""
    except Exception:
        return f"Erreur sur {f.name}"

def decouper_chapitres(texte: str):
    pattern = r'(?i)chapitre\s+\d+'
    segments = re.split(pattern, texte)
    titres = re.findall(pattern, texte)
    chapitres = []
    if len(segments) > 0 and len(segments[0].strip()) > 100:
        chapitres.append({"titre": "Prologue", "contenu": segments[0].strip()})
    for i, t in enumerate(titres):
        if i + 1 < len(segments):
            chapitres.append({"titre": t, "contenu": segments[i + 1].strip()})
    return chapitres

# ==========================================
# 4. INTERFACE STREAMLIT
# ==========================================

st.set_page_config(page_title="L'Archiviste V16.4 (Stable)", layout="wide")
st.title("🛡️ L'Archiviste : Mode Haute Disponibilité")

if "db" not in st.session_state:
    st.session_state.db = {"chapitres": [], "ready": False}

f_inputs = st.sidebar.file_uploader("Charger les Tomes", type=["pdf", "docx", "odt"], accept_multiple_files=True)

if f_inputs and not st.session_state.db["ready"]:
    if st.button("🚀 Scanner l'Intégrale"):
        texte_total = ""
        for f in f_inputs:
            texte_total += extraire_texte(f) + "\n\n"
        txt_clean = texte_total.replace("’", "'").replace("œ", "oe")
        st.session_state.db["chapitres"] = decouper_chapitres(txt_clean)
        st.session_state.db["ready"] = True
        st.rerun()

if st.session_state.db["ready"]:
    nom_perso = st.sidebar.selectbox("Cible", options=list(CONSTANTES_SAGA.keys()))
    indices = [i for i, c in enumerate(st.session_state.db["chapitres"]) if nom_perso.lower() in c['contenu'].lower()]
    selection = st.multiselect("Sélectionner chapitres", options=indices, format_func=lambda x: st.session_state.db["chapitres"][x]['titre'])

    if selection:
        if st.button(f"🧠 Analyser {nom_perso}"):
            texte_focus = "\n".join([st.session_state.db["chapitres"][i]['contenu'][:10000] for i in selection])
            prompt = f"Analyse {nom_perso}. Canon: {CONSTANTES_SAGA[nom_perso]}. Texte: {texte_focus}"
            with st.spinner("Analyse en cours..."):
                resultat = appel_ia(prompt)
                st.markdown(resultat)

if st.sidebar.button("🗑️ Nouveau Scan"):
    st.session_state.db = {"chapitres": [], "ready": False}
    st.rerun()
