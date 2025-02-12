import streamlit as st
import google.generativeai as genai
import os
import sqlite3
from datetime import datetime

st.set_page_config(page_title="Assistente Gemini", page_icon=r"C:\Users\Aluno\Downloads\gemini\assistente.png", layout="wide")

st.markdown("""
    <style>
        .title {
            text-align: center;
            font-size: 2.5rem;
            margin-top: 20px;
        }
        .container {
            display: flex;
            justify-content: center;
            align-items: center;
            text-align: center;
        }
        .prompt-container {
            width: 60%;
            margin-top: 20px;
        }
        .image-container {
            margin-top: 49px;
            text-align: right;
        }
    </style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="title">Assistente Gemini</h1>', unsafe_allow_html=True)

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

            if not st.session_state.show_history:
                with st.container():
                    col1, col2 = st.columns([1, 8])
                    
                    with col1:
                        st.markdown('<div class="image-container">', unsafe_allow_html=True)
                        st.image(ia_image_path, width=47)
                        st.markdown('</div>', unsafe_allow_html=True)
                    
                    with col2:
                        saudacao = saudacao_hora_atual()
                        st.markdown('<div class="prompt-container">', unsafe_allow_html=True)
                        st.text_area(label="", value=saudacao, height=80, max_chars=None, key="greeting", disabled=True)
                        user_query = st.text_input("Digite sua dúvida abaixo...", "")
                        st.markdown('</div>', unsafe_allow_html=True)

            if "show_history" in st.session_state and st.session_state.show_history:
                if st.button("Acessar o chat"):
                    st.session_state.show_history = False
                    st.session_state.selected_question = None
                    st.rerun()

                cursor.execute("SELECT resposta FROM historico WHERE pergunta = ?", (st.session_state.selected_question,))
                resposta = cursor.fetchone()
                
                if resposta:
                    st.text_area("Pergunta Selecionada", st.session_state.selected_question, height=100, disabled=True)
                    st.text_area("Resposta", resposta[0], height=200, disabled=True)
                
            else:
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
