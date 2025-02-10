import google.generativeai as genai

GOOGLE_GEMINI_API_KEY = "AIzaSyCJpsRyUBQ1ZX2ClSi8zBE5xrBFApRBrFM"  
genai.configure(api_key=GOOGLE_GEMINI_API_KEY)

try:
    models = genai.list_models()
    print("Conexão bem-sucedida! Modelos disponíveis:")
    for model in models:
        if 'generateContent' in model.supported_generation_methods:
            print(f"- {model.name}")

    mode = genai.GenerativeModel("gemini-1.0-pro")

    prompt = "O que é IA Generativa?"
    response = mode.generate_content(prompt)

    print("\nResposta da IA:")
    print(response.text)

except Exception as e:
    print(f"Erro ao conectar à API: {e}")
