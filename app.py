import streamlit as st
import google.generativeai as genai
import os
import sqlite3
from datetime import datetime

st.set_page_config(page_title="Assistente Gemini", page_icon=r"C:\Users\Aluno\Downloads\gemini\assistente.png", layout="wide")
st.title("Assistente Gemini")

ia_image_path = r"C:\Users\Aluno\Downloads\gemini\assistente.png"

def saudacao_hora_atual():
    hora_atual = datetime.now().hour
    if hora_atual < 12:
        return "Bom dia! Como posso ajuda-lo?"
    elif hora_atual < 18:
        return "Boa tarde! Como posso ajuda-lo?"
    else:
        return "Boa noite! Como posso ajuda-lo?"

conn = sqlite3.connect("historico.db")
cursor = conn.cursor()

cursor.execute("""
    CREATE TABLE IF NOT EXISTS historico (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pergunta TEXT UNIQUE,
        resposta TEXT
    )
""")
conn.commit()

if 'show_history' not in st.session_state:
    st.session_state.show_history = False

if 'selected_question' not in st.session_state:
    st.session_state.selected_question = None

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
            
            if st.sidebar.button("Mostrar Histórico"):
                st.session_state.show_history = not st.session_state.show_history
            
            if st.session_state.show_history:
                cursor.execute("SELECT pergunta FROM historico ORDER BY id DESC")
                perguntas = cursor.fetchall()
                
                for idx, (pergunta,) in enumerate(perguntas):
                    resumo = pergunta[:50] + "..." if len(pergunta) > 50 else pergunta
                    if st.sidebar.button(resumo, key=f"question_{idx}", help=pergunta):
                        st.session_state.selected_question = pergunta
                        st.session_state.show_history = True
                        
            col1, col2 = st.columns([0.5, 9])
            
            with col1:
                st.markdown('<div style="margin-top: 28px;"></div>', unsafe_allow_html=True)
                st.image(ia_image_path, width=60)

            with col2:
                saudacao = saudacao_hora_atual()
                message_box = st.empty()

                with st.container():
                    st.text_area(label="", value=saudacao, height=80, max_chars=None, key="greeting", disabled=True)

                if "show_history" in st.session_state and st.session_state.show_history:
                    cursor.execute("SELECT resposta FROM historico WHERE pergunta = ?", (st.session_state.selected_question,))
                    resposta = cursor.fetchone()
                    
                    if resposta:
                        st.markdown(f"**{st.session_state.selected_question}**")
                        st.markdown(f"**{resposta[0]}**")
                    
                    if st.button("acessar o chat"):
                        st.session_state.show_history = False
                        st.session_state.selected_question = None
                        st.rerun()
                else:
                    user_query = st.text_input("Digite sua dúvida abaixo...", "")
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
            
        else:
            st.warning("Nenhum modelo disponível para geração de conteúdo.")
    except Exception as e:
        st.error(f"Erro ao conectar à API: {str(e)}")
else:
    st.warning("Insira sua chave da API para continuar.")

conn.close()
