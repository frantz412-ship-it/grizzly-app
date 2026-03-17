import streamlit as st
from google import genai
from mistralai import Mistral
import json
from docx import Document
import time

# --- 1. INITIALISATION DES CLIENTS ---
try:
    # Client Google
    client_google = genai.Client(api_key=st.secrets["GOOGLE_API_KEY"])
    # Client Mistral
    client_mistral = Mistral(api_key=st.secrets["MISTRAL_API_KEY"])
except Exception as e:
    st.error("⚠️ Erreur de configuration des clés API dans les Secrets.")
    st.stop()

# --- 2. CONFIGURATION UI ---
st.set_page_config(page_title="Grizzly et Moineau - Multi-IA", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0f172a; color: #f1f5f9; }
    .tag { 
        display: inline-block; padding: 4px 12px; border-radius: 20px; 
        background: #1e293b; border: 1px solid #38bdf8; 
        margin: 4px; color: #38bdf8; font-size: 0.85rem; 
    }
    .stRadio [data-testid="stMarkdownContainer"] { color: #38bdf8; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. FONCTIONS TECHNIQUES ---
def read_docx(file):
    doc = Document(file)
    return '\n'.join([p.text for p in doc.paragraphs])

def analyser_bloc(texte, moteur):
    prompt = f"Analyse cet extrait de 'Grizzly et Moineau'. Extraits en JSON : personnages, capacites, armes, traumas, lieux, resume. Texte : {texte}"
    
    if moteur == "Google Gemini 2.0":
        response = client_google.models.generate_content(
            model='gemini-2.0-flash',
            contents=prompt,
            config={'response_mime_type': 'application/json'}
        )
        return json.loads(response.text)
    
    else: # Mode Mistral
        response = client_mistral.chat.complete(
            model="mistral-large-latest",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)

# --- 4. INTERFACE ---
st.title("📚 Grizzly et Moineau : Hub d'Analyse")

# Barre latérale pour le choix du moteur
with st.sidebar:
    st.header("⚙️ Configuration")
    moteur_choisi = st.radio(
        "Choisir l'Intelligence Artificielle :",
        ["Google Gemini 2.0", "Mistral AI (Large)"]
    )
    st.info(f"Moteur actuel : **{moteur_choisi}**")

uploaded_file = st.file_uploader("Charger un chapitre (.docx)", type="docx")

if uploaded_file:
    full_text = read_docx(uploaded_file)
    # Découpage pour sécurité quotas
    morceaux = [full_text[i:i+5000] for i in range(0, len(full_text), 5000)]
    
    if st.button(f"🚀 ANALYSER AVEC {moteur_choisi.upper()}"):
        resultats_globaux = {"personnages": set(), "capacites": set(), "armes": set(), "traumas": set(), "lieux": set(), "resumes": []}
        
        progress = st.progress(0)
        for idx, bloc in enumerate(morceaux):
            with st.spinner(f"Analyse bloc {idx+1}/{len(morceaux)}..."):
                try:
                    data = analyser_bloc(bloc, moteur_choisi)
                    for k in ["personnages", "capacites", "armes", "traumas", "lieux"]:
                        if k in data: resultats_globaux[k].update(data[k])
                    if "resume" in data: resultats_globaux["resumes"].append(data["resume"])
                    time.sleep(1) # Sécurité tempo
                except Exception as e:
                    st.error(f"Erreur sur le bloc {idx+1} : {e}")
            progress.progress((idx + 1) / len(morceaux))

        # AFFICHAGE FINAL
        st.divider()
        st.subheader("📝 Résumé Global du Chapitre")
        st.write(" ".join(resultats_globaux["resumes"]))

        col1, col2 = st.columns(2)
        with col1:
            st.write("**👤 Personnages**")
            for p in sorted(resultats_globaux["personnages"]):
                st.markdown(f'<span class="tag">{p}</span>', unsafe_allow_html=True)
            st.write("**✨ Capacités & Objets**")
            items = sorted(list(resultats_globaux["capacites"]) + list(resultats_globaux["armes"]))
            for i in items:
                st.markdown(f'<span class="tag">{i}</span>', unsafe_allow_html=True)

        with col2:
            st.write("**🧠 Thèmes & Traumas**")
            for t in sorted(resultats_globaux["traumas"]):
                st.markdown(f'<span class="tag">{t}</span>', unsafe_allow_html=True)
            st.write("**📍 Lieux**")
            for l in sorted(resultats_globaux["lieux"]):
                st.markdown(f'<span class="tag">{l}</span>', unsafe_allow_html=True)
