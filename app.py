import streamlit as st
import google.generativeai as genai
import os

# Obtém a chave da API da variável de ambiente
api_key = os.getenv("GOOGLE_GEMINI_API_KEY")

if not api_key:
    st.warning("Por favor, configure a chave da API no ambiente para continuar.")
else:
    genai.configure(api_key=api_key)

    try:
        # Lista os modelos disponíveis
        models = genai.list_models()

        # Filtra modelos que suportam a geração de conteúdo
        supported_models = [
            model for model in models 
            if 'generateContent' in getattr(model, "supported_generation_methods", []) and "gemini-1.0-pro" not in model.name
        ]

        if supported_models:
            st.success("Conexão bem-sucedida!")

            # Usa o modelo mais recente
            mode = genai.GenerativeModel(supported_models[0].name)

            # Entrada do usuário
            prompt = st.text_input("Digite o prompt para a IA", "O que é IA Generativa?")

            if prompt:
                response = mode.generate_content(prompt)
                
                if hasattr(response, "text"):
                    st.write("Resposta da IA:")
                    st.write(response.text)
                else:
                    st.warning("Nenhuma resposta válida foi recebida da IA.")

        else:
            st.warning("Nenhum modelo disponível para geração de conteúdo.")

    except Exception as e:
        st.error(f"Erro ao conectar à API: {str(e)}")
