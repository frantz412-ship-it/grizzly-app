import os
import re
import json
import streamlit as st
from docx import Document
import pdfplumber
from odf.opendocument import load
from odf.text import P
from odf.teletype import extractText

# Nouveau SDK Gemini
from google import genai
from google.genai import types

# ==========================================
# 0. CONFIGURATION GEMINI (SÉCURISÉE)
# ==========================================

if "GEMINI_API_KEY" in st.secrets:
    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
else:
    api_key_env = os.getenv("GEMINI_API_KEY")
    if not api_key_env:
        st.error("Clé GEMINI_API_KEY manquante. Vérifie tes Secrets Streamlit.")
    client = genai.Client(api_key=api_key_env)

# ==========================================
# 1. CONSTANTES CANONIQUES (SOCLE IMMUABLE)
# ==========================================

CONSTANTES_SAGA = {
    "Zack": (
        "ÂGE: 15 ans. ORIGINE: Cité de Pierre. Victime de sa tribu. "
        "PSYCHOLOGIE: Zackary (officiel), Zack (amis). Quête du soi. "
        "ORIENTATION: Bisexuel. COUPLE ASEXUEL avec Jade. Relations sexuelles: Léo, Jonas, Autyssé. "
        "AURA: Rouge et Noir. L'Ombre est une ligne noire qui le grignote."
    ),
    "Jonas": (
        "ÂGE: 17 ans. ORIGINE: Grosstouff. Ancien chasseur (Grizzly). "
        "ORIENTATION: Homosexuel (Gay). "
        "COUPLES: Officiel avec Léo. Relations sexuelles: Léo, Zack. "
        "LIMITE: STRICTEMENT aucun contact physique/sexuel avec Jade. AURA: Brun/Terre."
    ),
    "Léo": (
        "ÂGE: 15 ans. ORIGINE: Cathédrale. Fils de Lumière. "
        "ORIENTATION: Bisexuel. Guide du groupe. "
        "COUPLES: Officiel avec Jonas. Relations sexuelles: Jonas, Zack, Jade. "
        "POUVOIR: Voit les 'fils' (liens d'auras) par concentration."
    ),
    "Jade": (
        "ORIGINE: Village Soleil. ORIENTATION: Bisexuelle. "
        "COUPLES: Officiel ASEXUEL avec Zack. Relations sexuelles: Léo, Zack."
    ),
    "Autyssé": (
        "ORIGINE: Grosstouff. Profil autiste (TSA). Fils de la Structure. "
        "ORIENTATION: Pansexuel. Affection amoureuse et sexuelle avec Zack. AURA: Bleu."
    ),
    "SAGA": "Focus sur l'Ombre (ligne noire), la Reconstruction et la cohérence des liens (fils)."
}

# ==========================================
# 2. MOTEUR IA AVEC SÉCURITÉ QUOTA (429)
# ==========================================

def appel_ia(prompt: str, temperature: float = 0.1, primary_model: str = "gemini-1.5-pro") -> str:
    """
    Tente d'utiliser le modèle Pro. Si quota épuisé (429), bascule sur Flash.
    """
    try:
        response = client.models.generate_content(
            model=primary_model,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=temperature,
                max_output_tokens=4096,
            ),
        )
        return response.text or ""
    except Exception as e:
        if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
            st.warning("⚠️ Quota Pro saturé. Bascule automatique sur Gemini 1.5 Flash...")
            try:
                response = client.models.generate_content(
                    model="gemini-1.5-flash",
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=temperature,
                        max_output_tokens=4096,
                    ),
                )
                return response.text or ""
            except Exception as e2:
                return f"❌ Erreur critique (même en Flash) : {str(e2)}"
        return f"❌ Erreur Gemini : {str(e)}"

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
        return ""

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

st.set_page_config(page_title="Grizzly & Moineau V4.2.2 (Pro)", layout="wide")
st.title("🛡️ L'Archiviste V4.2.2 (Mode Pro & Fallback)")

if "db" not in st.session_state:
    st.session_state.db = {"chapitres": [], "ready": False}

f_input = st.file_uploader("Charger le Manuscrit (.pdf, .docx, .odt)", type=["pdf", "docx", "odt"])

if f_input and not st.session_state.db["ready"]:
    if st.button("🚀 Scanner le Manuscrit"):
        txt = extraire_texte(f_input).replace("’", "'").replace("œ", "oe")
        st.session_state.db["chapitres"] = decouper_chapitres(txt)
        st.session_state.db["ready"] = True
        st.rerun()

if st.session_state.db["ready"]:
    st.sidebar.header("📜 Bibliothèque")
    nom_perso = st.sidebar.selectbox("Personnage cible", options=list(CONSTANTES_SAGA.keys()))

    indices = [i for i, c in enumerate(st.session_state.db["chapitres"]) if nom_perso.lower() in c['contenu'].lower()]
    selection = st.multiselect(f"Chapitres pour {nom_perso}", options=indices, format_func=lambda x: st.session_state.db["chapitres"][x]['titre'])

    if nom_perso and selection:
        col_a, col_b = st.columns(2)

        with col_a:
            if st.button("🧠 Étape 1 : Analyse Stratford"):
                texte_focus = "\n".join([st.session_state.db["chapitres"][i]['contenu'][:10000] for i in selection])
                prompt_s = f"[ANALYSEUR STRATFORD V4.2] Analyse {nom_perso} : 1.Réactions viscérales 2.Non-dits 3.Souveraineté.\nEXTRAIT :\n{texte_focus}"
                with st.spinner("Analyse Stratford en cours (Pro)..."):
                    rapport = appel_ia(prompt_s, temperature=0.4)
                    st.session_state[f"strat_{nom_perso}"] = rapport
                    st.success("Analyse terminée.")
                    st.text_area("Rapport", rapport, height=300)

        with col_b:
            if st.button("📖 Étape 2 : Générer Bible"):
                if f"strat_{nom_perso}" not in st.session_state:
                    st.error("Lance d'abord l'analyse Stratford !")
                else:
                    texte_synthese = "\n".join([st.session_state.db["chapitres"][i]['contenu'][:10000] for i in selection])
                    regles = CONSTANTES_SAGA.get(nom_perso, "")
                    prompt_b = f"""[BIBLE SAGA] PERSO: {nom_perso}
CANON: {regles}
TEXTURE: {st.session_state[f"strat_{nom_perso}"]}
CONSIGNE: Rédige la fiche officielle. Signale les ÉCARTS PAR RAPPORT AU CANON si nécessaire.
EXTRAITS: {texte_synthese}"""
                    with st.spinner("Génération de la Bible (Pro)..."):
                        bible = appel_ia(prompt_b, temperature=0.0)
                        st.markdown(bible)
                        # Export simple (logiciel tiers peut être requis pour .docx complexe)
                        st.download_button("💾 Télécharger Bible", bible, file_name=f"Bible_{nom_perso}.txt")

if st.sidebar.button("🗑️ Nouveau Scan"):
    st.session_state.db = {"chapitres": [], "ready": False}
    st.rerun()
