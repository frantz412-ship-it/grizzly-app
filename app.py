def appel_ia_stable(prompt: str) -> str:
    api_key = st.secrets.get("GEMINI_API_KEY", "")
    if not api_key:
        return "❌ Clé GEMINI_API_KEY manquante dans les Secrets Streamlit."

    genai.configure(api_key=api_key)

    # Modèles confirmés disponibles sur ton compte (mars 2026)
    modeles = [
        "models/gemini-2.5-flash",   # meilleur choix : rapide + gratuit
        "models/gemini-2.0-flash",   # fallback stable
        "models/gemini-2.0-flash-lite",  # fallback ultra-léger
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

    return f"❌ Aucun modèle disponible. Dernière erreur : {last_error}"
