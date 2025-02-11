import streamlit as st
import google.generativeai as genai
import os
import sqlite3

# Configuração inicial da página
st.set_page_config(page_title="Assistente Virtual 🤖", page_icon="🤖", layout="wide")
st.title("Assistente Virtual")

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
api_key = os.environ.get("GOOGLE_GEMINI_API_KEY") or st.sidebar.text_input("Insira sua chave da API:", type="password")

if api_key:
    genai.configure(api_key=api_key)
    try:
        models = genai.list_models()
        supported_models = [
            model for model in models
            if 'generateContent' in getattr(model, "supported_generation_methods", []) and "gemini-1.0-pro" not in model.name
        ]
        
        if supported_models:
            mode = genai.GenerativeModel(supported_models[0].name)
            
            st.sidebar.subheader("Histórico de Conversas")
            cursor.execute("SELECT pergunta FROM historico ORDER BY id DESC")
            perguntas = cursor.fetchall()
            
            # Tornar as perguntas mais compactas no histórico
            for idx, (pergunta,) in enumerate(perguntas):
                if st.sidebar.button(pergunta, key=f"question_{idx}", help=pergunta):
                    st.session_state.selected_question = pergunta
                    st.session_state.show_history = True
            
            col1, col2 = st.columns([3, 1])
            
            with col1:
                if "show_history" in st.session_state and st.session_state.show_history:
                    cursor.execute("SELECT resposta FROM historico WHERE pergunta = ?", (st.session_state.selected_question,))
                    resposta = cursor.fetchone()
                    
                    if resposta:
                        st.markdown(f"**{st.session_state.selected_question}**")
                        st.markdown(f"**{resposta[0]}**")
                    
                    if st.button("Voltar ao chat"):
                        st.session_state.show_history = False
                        st.session_state.selected_question = None
                        st.rerun()
                else:
                    # Usar st.text_input para permitir envio com Enter
                    user_query = st.text_input("Digite sua mensagem aqui...", "")
                    if user_query:
                        cursor.execute("SELECT resposta FROM historico WHERE pergunta = ?", (user_query,))
                        resposta_existente = cursor.fetchone()
                        
                        if resposta_existente:
                            st.session_state.selected_question = user_query
                        else:
                            with st.spinner("Gerando resposta..."):
                                response = mode.generate_content(user_query)
                                if hasattr(response, "text"):
                                    cursor.execute("INSERT INTO historico (pergunta, resposta) VALUES (?, ?)", (user_query, response.text))
                                    conn.commit()
                                    st.session_state.selected_question = user_query
                        
                    if "selected_question" in st.session_state:
                        cursor.execute("SELECT resposta FROM historico WHERE pergunta = ?", (st.session_state.selected_question,))
                        resposta = cursor.fetchone()
                        if resposta:
                            st.markdown(f"**{st.session_state.selected_question}**")
                            st.markdown(f"**{resposta[0]}**")
            
            with col2:
                if st.button("Limpar Chat"):
                    st.session_state.selected_question = None
                    st.session_state.show_history = False
                    st.rerun()
        else:
            st.warning("Nenhum modelo disponível para geração de conteúdo.")
    except Exception as e:
        st.error(f"Erro ao conectar à API: {str(e)}")
else:
    st.warning("Insira sua chave da API para continuar.")

conn.close()
