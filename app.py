import streamlit as st
import google.generativeai as genai
import os
import sqlite3

# Configuração inicial da página
st.set_page_config(page_title="Chat com IA", layout="wide")

# Conectar ao banco de dados SQLite
conn = sqlite3.connect("historico.db")
cursor = conn.cursor()

# Criar tabela se não existir
cursor.execute("""
    CREATE TABLE IF NOT EXISTS historico (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pergunta TEXT UNIQUE,
        resposta TEXT
    )
""")
conn.commit()

# Obtém a chave da API do ambiente ou permite que o usuário insira manualmente
api_key = os.environ.get("GOOGLE_GEMINI_API_KEY") or st.text_input("Insira sua chave da API:", type="password")

if api_key:
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
            # Usa o modelo mais recente
            mode = genai.GenerativeModel(supported_models[0].name)

            # Layout dividido em duas colunas
            col1, col2 = st.columns([1, 2])

            with col1:
                st.subheader("Histórico de Perguntas")

                # Recupera o histórico do banco de dados
                cursor.execute("SELECT pergunta FROM historico ORDER BY id DESC")
                perguntas = cursor.fetchall()

                # Exibe o histórico de perguntas
                for idx, (pergunta,) in enumerate(perguntas):
                    if st.button(pergunta, key=f"question_{idx}"):
                        st.session_state.selected_question = pergunta
                        st.session_state.show_history = True

            with col2:
                if "show_history" in st.session_state and st.session_state.show_history:
                    # Exibe a pergunta e a resposta selecionada
                    if "selected_question" in st.session_state:
                        cursor.execute("SELECT resposta FROM historico WHERE pergunta = ?", (st.session_state.selected_question,))
                        resposta = cursor.fetchone()

                        if resposta:
                            st.write(f"**{st.session_state.selected_question}**")
                            st.write(f"**{resposta[0]}**")

                    # Botão para sair do histórico e voltar ao prompt
                    if st.button("Voltar ao prompt"):
                        st.session_state.show_history = False
                        st.session_state.selected_question = None

                else:
                    # Entrada do usuário para nova pergunta
                    prompt = st.text_input("Digite sua pergunta:")

                    if prompt and st.button("Enviar", key="send_prompt"):
                        # Verifica se a pergunta já existe no banco
                        cursor.execute("SELECT resposta FROM historico WHERE pergunta = ?", (prompt,))
                        resposta_existente = cursor.fetchone()

                        if resposta_existente:
                            st.session_state.selected_question = prompt
                        else:
                            # Gera uma nova resposta
                            response = mode.generate_content(prompt)

                            if hasattr(response, "text"):
                                # Armazena a nova pergunta e resposta no banco
                                cursor.execute("INSERT INTO historico (pergunta, resposta) VALUES (?, ?)", (prompt, response.text))
                                conn.commit()

                                # Atualiza o estado com a nova pergunta
                                st.session_state.selected_question = prompt

                    # Exibe a resposta APENAS quando uma pergunta for feita ou selecionada
                    if "selected_question" in st.session_state:
                        cursor.execute("SELECT resposta FROM historico WHERE pergunta = ?", (st.session_state.selected_question,))
                        resposta = cursor.fetchone()
                        if resposta:
                            st.write(f"**{st.session_state.selected_question}**")
                            st.write(f"**{resposta[0]}**")

        else:
            st.warning("Nenhum modelo disponível para geração de conteúdo.")

    except Exception as e:
        st.error(f"Erro ao conectar à API: {str(e)}")

else:
    st.warning("Insira sua chave da API para continuar.")

# Fechar a conexão com o banco de dados
conn.close()
