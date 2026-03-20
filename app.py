import os
import re
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
        st.error("Clé API manquante. Ajoute GEMINI_API_KEY dans les Secrets Streamlit.")
    client = genai.Client(api_key=api_key_env)

# ==========================================
# 1. CONSTANTES CANONIQUES (SOCLE IMMUABLE)
# ==========================================

CONSTANTES_SAGA = {
    "Zack": (
        "ÂGE: 15 ans. IDENTITÉ: Zackary (officiel), Zack (amis). "
        "ORIGINE: Cité de Pierre. Victime de sa tribu. PSYCHOLOGIE: Quête du soi, protecteur. "
        "ORIENTATION: Bisexuel. COUPLE ASEXUEL avec Jade (Souveraineté). "
        "RELATIONS SEXUELLES: Léo, Jonas, Autyssé. AURA: Rouge et Noir. "
        "STIGMATE: 'Gaz' est une insulte, pas un pouvoir."
    ),
    "Jonas": (
        "ÂGE: 17 ans. ORIGINE: Grosstouff. RÔLE: Grizzly (Chasseur/Protecteur). "
        "ORIENTATION: Homosexuel (Gay). COUPLE: Officiel avec Léo. "
        "RELATIONS SEXUELLES: Léo, Zack. LIMITE: Aucun contact sexuel avec Jade. "
        "AURA: Brun / Terre."
    ),
    "Léo": (
        "ÂGE: 15 ans. ORIGINE: Cathédrale. RÔLE: Moineau (Fils de Lumière). "
        "ORIENTATION: Bisexuel. COUPLE: Officiel avec Jonas. "
        "RELATIONS SEXUELLES: Jonas, Zack, Jade. POUVOIR: Voit les fils d'auras."
    ),
    "Jade": (
        "ORIGINE: Village Soleil. ORIENTATION: Bisexuelle. "
        "COUPLE: Officiel ASEXUEL avec Zack. RELATIONS SEXUELLES: Léo, Zack."
    ),
    "Autyssé": (
        "PROFIL: Autiste (TSA). RÔLE: Fils de la Structure (Cartographe). "
        "ORIENTATION: Pansexuel. RELATION: Affection et sexe avec Zack. AURA: Bleu."
    ),
    "SAGA": "THÈMES: Reconstruction, Consentement, l'Ombre (Ligne Noire)."
}

# ==========================================
# ==========================================
# 2. MOTEUR IA (VERSION ULTRA-STABLE)
# ==========================================

def appel_ia(prompt: str, temperature: float = 0.1) -> str:
    """
    Tente d'utiliser les modèles Pro de manière séquentielle.
    Si 404 ou 429, bascule sur le suivant jusqu'au Flash.
    """
    # Liste des modèles à tester par ordre de priorité (Pro stable, puis Pro beta, puis Flash)
    modeles_a_tester = ["gemini-1.5-pro", "gemini-1.5-pro-002", "gemini-1.5-flash"]
    
    derniere_erreur = ""

    for model_id in modeles_a_tester:
        try:
            response = client.models.generate_content(
                model=model_id,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=temperature,
                    max_output_tokens=4096,
                ),
            )
            return response.text or ""
            
        except Exception as e:
            derniere_erreur = str(e)
            # Si c'est un 404 (non trouvé) ou 429 (quota), on passe au modèle suivant
            if "404" in derniere_erreur or "429" in derniere_erreur:
                continue
            else:
                # Pour les autres erreurs (clé API, etc.), on s'arrête
                return f"❌ Erreur critique Gemini : {derniere_erreur}"

    return f"❌ Échec total : Aucun modèle n'a répondu. (Dernière erreur : {derniere_erreur})"

# ==========================================
# 3. LECTURE MULTI-FORMATS
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
        return f"Erreur de lecture sur {f.name}"

def decouper_chapitres(texte: str):
    pattern = r'(?i)chapitre\s+\d+'
    segments = re.split(pattern, texte)
    titres = re.findall(pattern, texte)
    chapitres = []
    if len(segments) > 0 and len(segments[0].strip()) > 100:
        chapitres.append({"titre": "Prologue / Intro", "contenu": segments[0].strip()})
    for i, t in enumerate(titres):
        if i + 1 < len(segments):
            chapitres.append({"titre": t, "contenu": segments[i + 1].strip()})
    return chapitres

# ==========================================
# 4. INTERFACE UTILISATEUR
# ==========================================

st.set_page_config(page_title="Grizzly & Moineau V4.2.3", layout="wide")
st.title("🛡️ L'Archiviste V4.2.3 (Édition Intégrale)")

if "db" not in st.session_state:
    st.session_state.db = {"chapitres": [], "ready": False}

# Sidebar : Chargement Multi-fichiers
st.sidebar.header("📁 Bibliothèque de la Saga")
f_inputs = st.sidebar.file_uploader(
    "Charger les Tomes (PDF, DOCX, ODT)", 
    type=["pdf", "docx", "odt"], 
    accept_multiple_files=True
)

if f_inputs and not st.session_state.db["ready"]:
    if st.button("🚀 Scanner l'Intégrale"):
        texte_total = ""
        for f in f_inputs:
            with st.spinner(f"Lecture de {f.name}..."):
                texte_total += extraire_texte(f) + "\n\n"
        
        txt_clean = texte_total.replace("’", "'").replace("œ", "oe")
        st.session_state.db["chapitres"] = decouper_chapitres(txt_clean)
        st.session_state.db["ready"] = True
        st.success(f"Scan terminé : {len(st.session_state.db['chapitres'])} chapitres détectés.")
        st.rerun()

# Main Area : Analyse
if st.session_state.db["ready"]:
    nom_perso = st.sidebar.selectbox("Personnage cible", options=list(CONSTANTES_SAGA.keys()))
    
    indices = [i for i, c in enumerate(st.session_state.db["chapitres"]) if nom_perso.lower() in c['contenu'].lower()]
    selection = st.multiselect(f"Chapitres pour {nom_perso}", options=indices, format_func=lambda x: st.session_state.db["chapitres"][x]['titre'])

    if nom_perso and selection:
        col_a, col_b = st.columns(2)

        with col_a:
            if st.button("🧠 Étape 1 : Analyse Stratford"):
                texte_focus = "\n".join([st.session_state.db["chapitres"][i]['contenu'][:10000] for i in selection])
                prompt_s = f"[STRATFORD V4.2] Analyse {nom_perso} :\n1.Corps/Somatique\n2.Trauma/Non-dits\n3.Souveraineté.\nEXTRAITS:\n{texte_focus}"
                with st.spinner("Analyse Pro en cours..."):
                    rapport = appel_ia(prompt_s, temperature=0.4)
                    st.session_state[f"strat_{nom_perso}"] = rapport
                    st.text_area("Rapport Stratford", rapport, height=400)

        with col_b:
            if st.button("📖 Étape 2 : Générer Bible"):
                if f"strat_{nom_perso}" not in st.session_state:
                    st.error("Lance d'abord Stratford !")
                else:
                    texte_synthese = "\n".join([st.session_state.db["chapitres"][i]['contenu'][:10000] for i in selection])
                    prompt_b = f"""[BIBLE SAGA] PERSO: {nom_perso}
CANON: {CONSTANTES_SAGA[nom_perso]}
TEXTURE: {st.session_state[f"strat_{nom_perso}"]}
MISSION: Rédige la fiche officielle. Signale tout ÉCART AU CANON (ex: mauvaise relation ou âge).
EXTRAITS: {texte_synthese}"""
                    with st.spinner("Génération de la Bible..."):
                        bible = appel_ia(prompt_b, temperature=0.0)
                        st.markdown(bible)
                        st.download_button("💾 Sauvegarder", bible, file_name=f"Bible_{nom_perso}.txt")

if st.sidebar.button("🗑️ Nouveau Scan"):
    st.session_state.db = {"chapitres": [], "ready": False}
    st.rerun()
