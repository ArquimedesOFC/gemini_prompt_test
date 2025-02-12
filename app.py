import streamlit as st
import google.generativeai as genai
import os
import sqlite3
from datetime import datetime

st.set_page_config(page_title="Assistente Gemini", page_icon=r"C:\Users\Aluno\Downloads\gemini\assistente.png", layout="wide")

st.markdown("""
    <style>
        .title { text-align: center; font-size: 2.5rem; margin-top: 20px; }
        .container { display: flex; justify-content: center; align-items: center; text-align: center; }
        .prompt-container { width: 60%; margin-top: 20px; }
    </style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="title">Assistente Gemini</h1>', unsafe_allow_html=True)

def saudacao_hora_atual():
    hora_atual = datetime.now().hour
    if hora_atual < 12:
        return "Bom dia! Como posso ajudá-lo?"
    elif hora_atual < 18:
        return "Boa tarde! Como posso ajudá-lo?"
    else:
        return "Boa noite! Como posso ajudá-lo?"

# Configuração do banco de dados
conn = sqlite3.connect("historico.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
    CREATE TABLE IF NOT EXISTS historico (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        titulo TEXT UNIQUE,
        conversa TEXT
    )
""")
conn.commit()

# Inicializa a sessão
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'show_history' not in st.session_state:
    st.session_state.show_history = False

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
            
            # Botão para exibir histórico
            if st.sidebar.button("Histórico de Conversas"):
                st.session_state.show_history = not st.session_state.show_history
            
            if st.session_state.show_history:
                st.sidebar.subheader("Histórico de Conversas")
                cursor.execute("SELECT titulo, conversa FROM historico ORDER BY id DESC")
                historico = cursor.fetchall()
                for titulo, conversa in historico:
                    if st.sidebar.button(titulo[:50] + "..." if len(titulo) > 50 else titulo):
                        st.session_state.messages = eval(conversa)
                
                # Botão para apagar histórico
                if st.sidebar.button("Apagar Histórico"):
                    cursor.execute("DELETE FROM historico")
                    conn.commit()
                    st.sidebar.success("Histórico apagado com sucesso!")
                    st.session_state.messages = []
                    st.rerun()
            
            # Botão para iniciar novo prompt
            if st.sidebar.button("Iniciar Novo Prompt"):
                if st.session_state.messages:
                    titulo = st.session_state.messages[0]["content"] if st.session_state.messages else "Conversa Anônima"
                    conversa = str(st.session_state.messages)
                    
                    # Verificar se o título já existe no banco de dados
                    cursor.execute("SELECT COUNT(*) FROM historico WHERE titulo = ?", (titulo,))
                    if cursor.fetchone()[0] == 0:  # Se não encontrar nenhum título igual
                        cursor.execute("INSERT INTO historico (titulo, conversa) VALUES (?, ?)", (titulo, conversa))
                        conn.commit()
                    else:
                        st.sidebar.warning(f"O título '{titulo}' já existe no histórico.")
                
                st.session_state.messages = []
                st.rerun()
            
            # Exibe mensagens
            for message in st.session_state.messages:
                with st.chat_message(message["role"], avatar=r"C:\Users\Aluno\Downloads\gemini\assistente.png"):  # Usando assistente.png para ambos
                    st.markdown(message["content"])
            
            # Entrada do usuário
            user_query = st.chat_input("Digite sua mensagem...")
            
            if user_query:
                st.session_state.messages.append({"role": "user", "content": user_query})
                with st.chat_message("user", avatar=r"C:\Users\Aluno\Downloads\gemini\user.png"):  # Usando assistente.png para o usuário
                    st.markdown(user_query)
                
                with st.spinner("Gerando resposta..."):
                    response = mode.generate_content(user_query)
                    resposta_texto = response.text if hasattr(response, "text") else "Não consegui gerar uma resposta."
                
                # Exibe a resposta do assistente sem a imagem extra
                st.session_state.messages.append({"role": "assistant", "content": resposta_texto})
                with st.chat_message("assistant", avatar=r"C:\Users\Aluno\Downloads\gemini\assistente.png"):  # Usando assistente.png para o assistente
                    st.markdown(resposta_texto)
            
        else:
            st.warning("Nenhum modelo disponível para geração de conteúdo.")
    except Exception as e:
        st.error(f"Erro ao conectar à API: {str(e)}")
else:
    st.warning("Insira sua chave da API para continuar.")

conn.close()
