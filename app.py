import os
import re
import streamlit as st
from docx import Document
import pdfplumber
from odf.opendocument import load
from odf.text import P
from odf.teletype import extractText

# UTILISATION EXCLUSIVE DE LA LIB STABLE
import google.generativeai as genai

# ==========================================
# 0. CONFIGURATION
# ==========================================

if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    genai.configure(api_key=os.getenv("GEMINI_API_KEY", ""))
    if not os.getenv("GEMINI_API_KEY"):
        st.error("Clé API absente (st.secrets['GEMINI_API_KEY'] ou variable d'environnement).")

# ==========================================
# 1. CONSTANTES (CANON)
# ==========================================

CONSTANTES_SAGA = {
    "Zack": "ÂGE: 15 ans. Zackary/Zack. Bisexuel. Couple Asexuel avec Jade. Aura Rouge/Noir.",
    "Jonas": "ÂGE: 17 ans. Grizzly. Gay. Couple Léo. Pas de sexe avec Jade. Aura Brun.",
    "Léo": "ÂGE: 15 ans. Moineau. Bisexuel. Couple Jonas. Voit les fils.",
    "SAGA": "Thèmes: Reconstruction, Souveraineté, l'Ombre."
}

# ==========================================
# 2. MOTEUR IA (ANTI-404)
# ==========================================

def appel_ia(prompt: str) -> str:
    """
    Essaie plusieurs modèles Gemini via google.generativeai.
    Ajoute le préfixe 'models/' pour éviter les erreurs 404 "model not found".
    """
    # Noms de modèles supportés par google.generativeai
    base_models = ["gemini-1.5-pro", "gemini-1.5-flash", "gemini-pro"]
    modeles = [f"models/{m}" for m in base_models]

    for m_name in modeles:
        try:
            model = genai.GenerativeModel(m_name)
            response = model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.1,
                    max_output_tokens=4096,
                )
            )
            return response.text or ""
        except Exception as e:
            # Si c'est clairement un 404 / not found, on tente le modèle suivant
            if "404" in str(e) or "not found" in str(e).lower():
                continue
            return f"❌ Erreur technique : {str(e)}"

    return "❌ Aucun modèle Gemini disponible (vérifie tes dépendances et ton accès API)."

# ==========================================
# 3. FONCTIONS FICHIERS
# ==========================================

def extraire_texte(f) -> str:
    """Lit PDF / DOCX / ODT et renvoie le texte brut."""
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
        return ""

def decouper_chapitres(texte: str):
    """
    Coupe le texte sur 'Chapitre X' (insensible à la casse),
    et renvoie une liste de {titre, contenu}.
    """
    pattern = r'(?i)chapitre\s+\d+'
    segments = re.split(pattern, texte)
    titres = re.findall(pattern, texte)
    chaps = []

    if len(segments) > 0 and len(segments[0].strip()) > 100:
        chaps.append({"titre": "Prologue", "contenu": segments[0].strip()})

    for i, t in enumerate(titres):
        if i + 1 < len(segments):
            chaps.append({"titre": t, "contenu": segments[i + 1].strip()})
    return chaps

# ==========================================
# 4. INTERFACE
# ==========================================

st.set_page_config(page_title="Archiviste Stable", layout="wide")
st.title("🛡️ L'Archiviste V16.5 (Roc de Pierre)")

if "db" not in st.session_state:
    st.session_state.db = {"chapitres": [], "ready": False}

f_inputs = st.sidebar.file_uploader(
    "Charger les fichiers",
    type=["pdf", "docx", "odt"],
    accept_multiple_files=True
)

if f_inputs and not st.session_state.db["ready"]:
    if st.button("🚀 Scanner la Saga"):
        full_txt = ""
        for f in f_inputs:
            full_txt += extraire_texte(f) + "\n\n"
        # normalisation de quelques caractères
        full_txt = full_txt.replace("’", "'").replace("œ", "oe")
        st.session_state.db["chapitres"] = decouper_chapitres(full_txt)
        st.session_state.db["ready"] = True
        st.rerun()

if st.session_state.db["ready"]:
    perso = st.sidebar.selectbox("Personnage", options=list(CONSTANTES_SAGA.keys()))

    indices = [
        i for i, c in enumerate(st.session_state.db["chapitres"])
        if perso.lower() in c['contenu'].lower()
    ]

    sel = st.multiselect(
        "Chapitres",
        options=indices,
        format_func=lambda x: st.session_state.db["chapitres"][x]['titre']
    )

    if sel and st.button("🧠 Analyser"):
        # on garde 10 000 caractères max par chapitre pour donner du contexte
        txt_focus = "\n".join(
            [st.session_state.db["chapitres"][i]['contenu'][:10000] for i in sel]
        )
        prompt = (
            f"Analyse le personnage {perso} dans ces extraits.\n"
            f"Canon (à respecter strictement) : {CONSTANTES_SAGA[perso]}\n\n"
            f"TEXTE :\n{txt_focus}"
        )
        with st.spinner("L'IA consulte les archives..."):
            resultat = appel_ia(prompt)
            st.markdown(resultat)

if st.sidebar.button("🗑️ Reset"):
    st.session_state.db = {"chapitres": [], "ready": False}
    st.rerun()
