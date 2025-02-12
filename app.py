import streamlit as st
import google.generativeai as genai
import os
import sqlite3
from datetime import datetime

# Função para autenticação
def autenticar_usuario(usuario, senha):
    conn = sqlite3.connect("usuarios.db", check_same_thread=False)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT UNIQUE,
            senha TEXT
        )
    """)
    conn.commit()

    cursor.execute("SELECT * FROM usuarios WHERE usuario = ? AND senha = ?", (usuario, senha))
    user = cursor.fetchone()
    conn.close()

    return user

# Função para adicionar o primeiro usuário
def adicionar_primeiro_usuario():
    conn = sqlite3.connect("usuarios.db", check_same_thread=False)
    cursor = conn.cursor()

    # Garantir que a tabela 'usuarios' seja criada
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT UNIQUE,
            senha TEXT
        )
    """)
    conn.commit()

    cursor.execute("SELECT COUNT(*) FROM usuarios WHERE usuario = 'admin'")
    if cursor.fetchone()[0] == 0:  # Verifica se o usuário "admin" já existe
        cursor.execute("INSERT INTO usuarios (usuario, senha) VALUES ('admin', 'admin')")
        conn.commit()
    conn.close()

# Função para exibir a tela de login
def tela_login():
    st.title("Login")
    usuario = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")

    if st.button("Entrar"):
        if usuario and senha:
            if autenticar_usuario(usuario, senha):
                st.session_state.logged_in = True
                st.rerun()  # Reinicia a página para carregar o chatbot
            else:
                st.error("Usuário ou senha inválidos.")
        else:
            st.warning("Preencha ambos os campos.")

# Verifica se o usuário está autenticado
if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    adicionar_primeiro_usuario()  # Adiciona o primeiro usuário se não existir
    tela_login()
else:
    # Código do chatbot
    st.set_page_config(page_title="Assistente Gemini", page_icon=r"C:\Users\Aluno\Downloads\gemini\assistente.png", layout="wide")
    st.markdown("""
        <style>
            .title { text-align: center; font-size: 2.5rem; margin-top: 20px; }
            .container { display: flex; justify-content: center; align-items: center; text-align: center; }
            .prompt-container { width: 60%; margin-top: 20px; }
            .footer-btn { position: absolute; bottom: 20px; left: 50%; transform: translateX(-50%); }
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
                
                # Exibe mensagens do histórico
                for message in st.session_state.messages:
                    avatar_url = r"C:\Users\Aluno\Downloads\gemini\assistente.png"  # Padrão: ícone do assistente
                    
                    # Ajuste para que o avatar seja diferente conforme o tipo da mensagem
                    if message["role"] == "user":
                        avatar_url = r"C:\Users\Aluno\Downloads\gemini\user.png"  # Ícone do usuário

                    # Exibe a mensagem com o avatar correto
                    with st.chat_message(message["role"], avatar=avatar_url):
                        st.markdown(message["content"])
                
                # Entrada do usuário
                user_query = st.chat_input("Digite sua mensagem...")

                if user_query:
                    # Adiciona a mensagem do usuário ao histórico
                    st.session_state.messages.append({"role": "user", "content": user_query})
                    with st.chat_message("user", avatar=r"C:\Users\Aluno\Downloads\gemini\user.png"):
                        st.markdown(user_query)
                    
                    # Criação do contexto completo, incluindo todas as mensagens anteriores
                    context = "\n".join([msg["content"] for msg in st.session_state.messages])
                    
                    with st.spinner("Gerando resposta..."):
                        response = mode.generate_content(context)
                        resposta_texto = response.text if hasattr(response, "text") else "Não consegui gerar uma resposta."
                    
                    # Exibe a resposta do assistente
                    st.session_state.messages.append({"role": "assistant", "content": resposta_texto})
                    with st.chat_message("assistant", avatar=r"C:\Users\Aluno\Downloads\gemini\assistente.png"):
                        st.markdown(resposta_texto)
                
                # Botão "Iniciar Novo Prompt" posicionado na parte inferior da interface
                st.markdown('<div class="footer-btn">', unsafe_allow_html=True)
                if st.button("Iniciar Novo Prompt"):
                    if st.session_state.messages:
                        titulo = st.session_state.messages[0]["content"] if st.session_state.messages else "Conversa Anônima"
                        conversa = str(st.session_state.messages)
                        
                        # Verificar se o título já existe no banco de dados
                        cursor.execute("SELECT COUNT(*) FROM historico WHERE titulo = ?", (titulo,))
                        if cursor.fetchone()[0] == 0:
                            cursor.execute("INSERT INTO historico (titulo, conversa) VALUES (?, ?)", (titulo, conversa))
                            conn.commit()
                        else:
                            st.warning(f"O título '{titulo}' já existe no histórico.")
                    
                    st.session_state.messages = []
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
                
            else:
                st.warning("Nenhum modelo disponível para geração de conteúdo.")
        except Exception as e:
            st.error(f"Erro ao conectar à API: {str(e)}")
    else:
        st.warning("Insira sua chave da API para continuar.")

    conn.close()
