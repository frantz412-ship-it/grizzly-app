import streamlit as st
import sys
import os

st.title("🕵️‍♂️ Diagnostic Grizzly")

# 1. Vérification de l'installation
try:
    import mistralai
    st.success(f"Bibliothèque installée à : {mistralai.__file__}")
    from mistralai import Mistral
    st.success("Classe 'Mistral' importée avec succès !")
except Exception as e:
    st.error(f"Erreur d'import : {e}")

# 2. Vérification des fichiers présents sur le serveur
st.subheader("Fichiers détectés sur le serveur :")
st.write(os.listdir("."))
