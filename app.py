import os
import re
import json
import pandas as pd
import streamlit as st
import google.generativeai as genai
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timezone
from docx import Document
import pdfplumber
from odf.opendocument import load
from odf.text import P
from odf.teletype import extractText

# ==========================================
# 1. CONFIGURATION & CANON
# ==========================================

st.set_page_config(
    page_title="Grizzly & Moineau - Archiviste V17.5",
    layout="wide"
)

CANON_DATA = {
    "Jonas": (
        "ÂGE: 17 ans. Grizzly. Couple exclusif Léo. "
        "Aura: VERTE phosphorescente (Colère). "
        "Yeux verts, cheveux bruns, cicatrice gorge."
    ),
    "Léo": (
        "ÂGE: 15-17 ans. Moineau. Couple exclusif Jonas. "
        "Aura: BLEUE. Louve blanche de lumière (gardienne). "
        "Voit les fils d'aura."
    ),
    "Zack": (
        "ÂGE: 15 ans. Zackary/Zack (prénom choisi). "
        "Aura: ROUGE CHAUD. Ailes aux flancs, capable de voler. "
        "Talismans: Louveteau de pierre, sac fleur. "
        "Couple asexuel avec Jade."
    ),
    "Jade": (
        "Jade. Cheffe de terrain. "
        "Aura: JAUNE/DORÉE. Arme: Fronde. "
        "Souveraineté, non-sacrificielle. "
        "Couple asexuel avec Zack."
    ),
    "Autyss": (
        "Autyss. Chirurgien des colonnes. "
        "Aura: VIOLETTE. "
        "Capacité: Colonnes/Diagrammes. Poésie. "
        "Profil autiste (règles strictes)."
    ),
    "Luc": (
        "Luc. Surnom: Gremlin. "
        "Personnage secondaire. "
        "Enjeux d'appartenance. Protégé de Zack."
    ),
    "SAGA": (
        "Couple Jonas-Léo intouchable. "
        "Si flou = non. "
        "Corps passager, jamais outil. "
        "Consentement explicite obligatoire. "
        "L'Ombre = menace de corruption diffuse. "
        "Thèmes: Reconstruction, Souveraineté, Trauma, Famille choisie."
    ),
}

SHEET_ID = "189e8EDBteW2bk-6XQMqz5CbDN7g2_CC-VY238jnC98I"

# ==========================================
# 2. MÉMOIRE SESSION
# ==========================================

if "chapitres" not in st.session_state:
    st.session_state.chapitres = []
if "analyses" not in st.session_state:
    st.session_state.analyses = []

# ==========================================
# 3. FONCTIONS FICHIERS
# ==========================================

def normaliser_texte(txt: str) -> str:
    replacements = {
        "\u2019": "'",
        "\u2018": "'",
        "\u00ab": '"',
        "\u00bb": '"',
        "\u0153": "oe",
        "\u2026": "...",
        "\u2013": "-",
        "\u2014": "-",
    }
    for old, new in replacements.items():
        txt = txt.replace(old, new)
    return txt

def extraire_texte(file) -> str:
    try:
        if file.name.endswith(".pdf"):
            with pdfplumber.open(file) as pdf:
                return "\n".join([p.extract_text() or "" for p in pdf.pages])
        elif file.name.endswith(".docx"):
            doc = Document(file)
            return "\n".join([p.text for p in doc.paragraphs])
        elif file.name.endswith(".odt"):
            odt_doc = load(file)
            return "\n".join([
                extractText(p)
                for p in odt_doc.getElementsByType(P)
            ])
    except Exception as e:
        st.error(f"Erreur lecture {file.name}: {e}")
    return ""

def decouper_chapitres(texte: str):
    pattern = r"(?i)(Prologue|Epilogue|Épilogue|Chapitre\s*[\(\s]*\d+[\.\s\)]*)"
    parts = re.split(pattern, texte)
    if len(parts) <= 1:
        return [{"titre": "Manuscrit Complet", "contenu": texte}]
    chapitres = []
    for i in range(1, len(parts), 2):
        if i + 1 < len(parts):
            titre = parts[i].strip()
            contenu = parts[i + 1].strip()
            if contenu:
                chapitres.append({"titre": titre, "contenu": contenu})
    return chapitres

# ==========================================
# 4. CONNEXION IA (Gemini stable, free tier)
# ==========================================

def appel_ia_stable(prompt: str) -> str:
    api_key = st.secrets.get("GEMINI_API_KEY", "")
    if not api_key:
        return "❌ Clé GEMINI_API_KEY manquante dans les Secrets Streamlit."

    genai.configure(api_key=api_key)

    modeles = [
        "models/gemini-1.5-flash",
        "models/gemini-1.5-pro",
        "models/gemini-pro",
    ]

    last_error = ""
    for m_name in modeles:
        try:
            model = genai.GenerativeModel(m_name)
            resp = model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.2,
                    max_output_tokens=2048,
                )
            )
            return resp.text or ""
        except Exception as e:
            last_error = str(e)
            if "404" in last_error or "not found" in last_error.lower():
                continue
            return f"❌ Erreur Gemini ({m_name}) : {last_error}"

    return f"❌ Aucun modèle Gemini disponible. Dernière erreur : {last_error}"

# ==========================================
# 5. CONNEXION GOOGLE SHEETS (gspread)
# ==========================================

def get_worksheet(nom_onglet: str):
    try:
        if "GCP_JSON_BRUT" not in st.secrets:
            st.error("GCP_JSON_BRUT manquant dans les Secrets Streamlit.")
            return None

        json_info = json.loads(st.secrets["GCP_JSON_BRUT"], strict=False)
        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive",
        ]
        creds = Credentials.from_service_account_info(json_info, scopes=scope)
        client_gs = gspread.authorize(creds)
        ss = client_gs.open_by_key(SHEET_ID)

        try:
            return ss.worksheet(nom_onglet)
        except gspread.exceptions.WorksheetNotFound:
            ws = ss.add_worksheet(title=nom_onglet, rows="2000", cols="4")
            ws.append_row(["Date", "Personnage", "Type", "Texte"])
            return ws

    except Exception as e:
        st.error(f"Erreur Google Sheets : {e}")
        return None

# ==========================================
# 6. SIDEBAR
# ==========================================

with st.sidebar:
    st.image(
        "https://img.icons8.com/emoji/96/grizzly-bear-emoji.png",
        width=60
    )
    st.title("Archiviste V17.5")
    st.divider()

    st.header("📂 Bibliothèque")
    files = st.file_uploader(
        "Charger Tomes (PDF / DOCX / ODT)",
        accept_multiple_files=True,
        type=["pdf", "docx", "odt"],
    )

    if st.button("🚀 Scanner l'Intégrale", use_container_width=True):
        if files:
            with st.spinner("Triage des manuscrits en cours..."):
                all_text = ""
                for f in files:
                    contenu = extraire_texte(f)
                    all_text += f"\n\n[TOME: {f.name}]\n\n{contenu}"
                all_text = normaliser_texte(all_text)
                st.session_state.chapitres = decouper_chapitres(all_text)
            st.success(
                f"✅ {len(st.session_state.chapitres)} sections détectées."
            )
        else:
            st.warning("⚠️ Charge au moins un fichier d'abord.")

    st.divider()

    if st.button("🗑️ Tout effacer", use_container_width=True):
        st.session_state.chapitres = []
        st.session_state.analyses = []
        st.rerun()

    st.divider()
    st.caption(
        "Grizzly & Moineau © 2026\n"
        "Archiviste propulsé par Gemini API"
    )

# ==========================================
# 7. LABORATOIRE D'ANALYSE
# ==========================================

st.title("🔬 Laboratoire Grizzly & Moineau")

if not st.session_state.chapitres:
    st.info(
        "📂 Charge tes fichiers dans la barre latérale "
        "puis clique sur **Scanner l'Intégrale** pour commencer."
    )
else:
    col_sel, col_outils = st.columns([1, 2])

    with col_sel:
        st.subheader("🎯 Cible")
        perso = st.selectbox(
            "Personnage",
            list(CANON_DATA.keys()),
            label_visibility="collapsed"
        )

        filtre = [
            c for c in st.session_state.chapitres
            if perso.lower() in c["contenu"].lower() or perso == "SAGA"
        ]

        st.caption(f"{len(filtre)} chapitres contenant **{perso}**")
        selection = st.multiselect(
            "Chapitres à analyser (1–2 recommandé)",
            filtre,
            format_func=lambda x: x["titre"],
        )

        with st.expander("📖 Canon actif"):
            st.markdown(f"> {CANON_DATA[perso]}")

    with col_outils:
        st.subheader("🛠️ Outils d'Analyse")

        config = {
            "🧠 Psyché": (
                "Trauma, évolution psychologique, mécanismes de défense, "
                "émotions dominantes, souveraineté intérieure."
            ),
            "⚔️ Physique": (
                "Portrait physique précis, aura et couleur, "
                "manifestations somatiques du trauma, posture, gestes."
            ),
            "🕸️ Liens": (
                "Relations affectives, amoureuses, sexuelles. "
                "Fils d'aura, dynamiques de groupe, type d'attachement."
            ),
            "🕵️ Diagnostic": (
                "Analyse clinique/traumatique (C-PTSD, TPL, TDAH, etc.), "
                "cohérence narrative, écarts par rapport au canon."
            ),
        }

        btns = st.columns(4)
        for i, (label, focus) in enumerate(config.items()):
            if btns[i].button(label, use_container_width=True):
                if not selection:
                    st.error("⚠️ Sélectionne au moins un chapitre !")
                else:
                    choisis = selection[:2]
                    contexte = "\n\n".join([
                        f"### {c['titre']}\n{c['contenu'][:3000]}"
                        for c in choisis
                    ])
                    prompt = (
                        f"[ARCHIVISTE GRIZZLY & MOINEAU]\n\n"
                        f"CANON DE {perso} (règles absolues) :\n"
                        f"{CANON_DATA[perso]}\n\n"
                        f"FOCUS D'ANALYSE : {focus}\n\n"
                        f"CONSIGNES STRICTES :\n"
                        f"- Ne contredis jamais le canon ci-dessus.\n"
                        f"- Si une information est absente du texte, "
                        f"écris exactement : 'Non mentionné dans le manuscrit.'\n"
                        f"- Structure ta réponse avec des titres clairs.\n"
                        f"- Termine par une SYNTHÈSE en 3-4 lignes.\n\n"
                        f"EXTRAITS DU MANUSCRIT :\n{contexte}"
                    )

                    with st.spinner(f"Analyse de {perso} en cours..."):
                        txt_ia = appel_ia_stable(prompt)
                        entry = {
                            "id": str(datetime.now(timezone.utc).timestamp()),
                            "date": datetime.now().strftime("%d/%m/%Y %H:%M"),
                            "perso": perso,
                            "type": label,
                            "texte": txt_ia,
                            "chapitres": ", ".join([c["titre"] for c in choisis]),
                        }
                        st.session_state.analyses.insert(0, entry)

# ==========================================
# 8. HISTORIQUE & ARCHIVAGE GOOGLE SHEETS
# ==========================================

if st.session_state.analyses:
    st.divider()
    st.subheader("📚 Historique des analyses")

    for ana in st.session_state.analyses:
        with st.expander(
            f"📌 {ana['type']} — {ana['perso']} ({ana['date']}) "
            f"| Chapitres : {ana.get('chapitres', '?')}",
            expanded=True,
        ):
            st.markdown(ana["texte"])
            st.divider()

            col_arch, col_vide = st.columns([1, 3])
            with col_arch:
                if st.button(
                    f"💾 Archiver dans Sheets",
                    key=f"btn-{ana['id']}",
                    use_container_width=True,
                ):
                    ws = get_worksheet(ana["perso"])
                    if ws:
                        ws.append_
