import streamlit as st
import google.generativeai as genai
import os

# Obtém a chave da API da variável de ambiente
api_key = os.getenv("GOOGLE_GEMINI_API_KEY")

if api_key:
    genai.configure(api_key=api_key)

    try:
        # Lista os modelos disponíveis
        models = genai.list_models()

        # Filtra apenas os modelos que suportam a geração de conteúdo e estão atualizados
        supported_models = [model for model in models if 'generateContent' in model.supported_generation_methods and 'gemini-1.0-pro' not in model.name]

        # Verifica se há modelos disponíveis para geração de conteúdo
        if supported_models:
            st.write("Conexão bem-sucedida! Modelos disponíveis para geração de conteúdo:")

            # Exibe apenas os modelos que suportam generateContent
            for model in supported_models:
                st.write(f"- {model.name}")

            # Usar o modelo mais recente
            mode = genai.GenerativeModel(supported_models[0].name)

            # Recebe o prompt do usuário
            prompt = st.text_input("Digite o prompt para a IA", "O que é IA Generativa?")

            if prompt:
                response = mode.generate_content(prompt)

                st.write("Resposta da IA:")
                st.write(response.text)
        else:
            st.write("Nenhum modelo disponível para geração de conteúdo.")

    except Exception as e:
        st.error(f"Erro ao conectar à API: {e}")

else:
    st.warning("Por favor, insira a chave da API em config.py para continuar.")
