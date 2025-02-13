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
        usuario TEXT,
        titulo TEXT UNIQUE,
        conversa TEXT
    )
""")
cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario TEXT UNIQUE,
        senha TEXT
    )
""")
conn.commit()

# Inicializa a sessão
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'show_history' not in st.session_state:
    st.session_state.show_history = False
if 'usuario' not in st.session_state:
    st.session_state.usuario = None
if 'current_history' not in st.session_state:
    st.session_state.current_history = None  # Adicionando variável para controlar o histórico carregado

def tela_login():
    st.subheader("Login")
    usuario = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        if usuario == "admin" and senha == "admin":
            st.session_state.usuario = "admin"
            st.rerun()  # Substituir 'experimental_rerun()' por 'rerun()'
        else:
            cursor.execute("SELECT * FROM usuarios WHERE usuario = ? AND senha = ?", (usuario, senha))
            user = cursor.fetchone()
            if user:
                st.session_state.usuario = usuario
                st.rerun()  # Substituir 'experimental_rerun()' por 'rerun()'
            else:
                st.error("Usuário ou senha incorretos")

def tela_configuracoes():
    st.subheader("Configurações - Cadastro de Novos Usuários")
    novo_usuario = st.text_input("Novo Usuário")
    nova_senha = st.text_input("Nova Senha", type="password")
    if st.button("Cadastrar Usuário"):
        if novo_usuario and nova_senha:
            cursor.execute("INSERT INTO usuarios (usuario, senha) VALUES (?, ?)", (novo_usuario, nova_senha))
            conn.commit()
            st.success(f"Usuário {novo_usuario} cadastrado com sucesso!")
        else:
            st.error("Preencha todos os campos.")

def gerenciar_usuarios():
    st.subheader("Gerenciar Usuários Ativos")
    cursor.execute("SELECT * FROM usuarios")
    usuarios = cursor.fetchall()
    
    if usuarios:
        for usuario in usuarios:
            usuario_id, nome_usuario, _ = usuario
            st.write(f"Usuário: {nome_usuario}")
            
            # Botão para editar usuário
            col1, col2 = st.columns([1, 1])
            with col1:
                if st.button(f"Alterar {nome_usuario}"):
                    novo_nome = st.text_input(f"Novo nome para {nome_usuario}", value=nome_usuario)
                    nova_senha = st.text_input(f"Nova senha para {nome_usuario}", type="password")
                    if st.button("Salvar alterações"):
                        if novo_nome and nova_senha:
                            cursor.execute("UPDATE usuarios SET usuario = ?, senha = ? WHERE id = ?", (novo_nome, nova_senha, usuario_id))
                            conn.commit()
                            st.success(f"Informações de {nome_usuario} alteradas com sucesso!")
                        else:
                            st.error("Preencha todos os campos.")
            
            # Botão para excluir usuário
            with col2:
                if st.button(f"Excluir {nome_usuario}"):
                    cursor.execute("DELETE FROM usuarios WHERE id = ?", (usuario_id,))
                    conn.commit()
                    st.success(f"Usuário {nome_usuario} excluído com sucesso!")

    else:
        st.write("Nenhum usuário cadastrado.")

if st.session_state.usuario is None:
    tela_login()
else:
    if st.session_state.usuario == "admin":
        st.sidebar.subheader("Admin: Gerenciar Sistema")
        if st.sidebar.button("Sair"):
            st.session_state.usuario = None
            st.rerun()  # Substituir 'experimental_rerun()' por 'rerun()'

        # Acessar Configurações
        if st.sidebar.button("Configurações"):
            tela_configuracoes()

        # Gerenciar Usuários
        if st.sidebar.button("Gerenciar Usuários"):
            gerenciar_usuarios()

    else:
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
                        cursor.execute("SELECT id, titulo, conversa FROM historico WHERE usuario = ? ORDER BY id DESC", (st.session_state.usuario,))
                        historico = cursor.fetchall()
                        
                        if historico:
                            for historia in historico:
                                historia_id, titulo, conversa = historia
                                # Utilizando o ID da conversa para garantir uma chave única
                                if st.sidebar.button(f"{titulo[:50]}...", key=f"historico_{historia_id}"):
                                    # Verifica se a conversa já foi carregada
                                    if not any(msg['content'] == conversa for msg in st.session_state.messages):
                                        st.session_state.messages = eval(conversa)
                                        st.session_state.current_history = historia_id  # Guardar qual histórico foi carregado
                        else:
                            st.sidebar.warning("Nenhum histórico encontrado.")
                        
                        if st.sidebar.button("Apagar Histórico"):
                            cursor.execute("DELETE FROM historico WHERE usuario = ?", (st.session_state.usuario,))
                            conn.commit()
                            st.sidebar.success("Histórico apagado com sucesso!")
                            st.session_state.messages = []

                    for message in st.session_state.messages:
                        avatar_url = r"C:\Users\Aluno\Downloads\gemini\assistente.png"
                        if message["role"] == "user":
                            avatar_url = r"C:\Users\Aluno\Downloads\gemini\user.png"
                        with st.chat_message(message["role"], avatar=avatar_url):
                            st.markdown(message["content"])
                    
                    user_query = st.chat_input("Digite sua mensagem...")
                    
                    if user_query:
                        st.session_state.messages.append({"role": "user", "content": user_query})
                        with st.chat_message("user", avatar=r"C:\Users\Aluno\Downloads\gemini\user.png"):
                            st.markdown(user_query)
                        
                        context = "\n".join([msg["content"] for msg in st.session_state.messages])
                        
                        with st.spinner("Gerando resposta..."):
                            response = mode.generate_content(context)
                            resposta_texto = response.text if hasattr(response, "text") else "Não consegui gerar uma resposta."
                        
                        st.session_state.messages.append({"role": "assistant", "content": resposta_texto})
                        with st.chat_message("assistant", avatar=r"C:\Users\Aluno\Downloads\gemini\assistente.png"):
                            st.markdown(resposta_texto)
                    
                    if st.button("Iniciar Novo Prompt"):
                        if st.session_state.messages:
                            # Salvar histórico antes de iniciar um novo prompt
                            titulo = f"Conversa de {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                            conversa = str(st.session_state.messages)
                            
                            if st.session_state.current_history:  # Verifica se há um histórico atual carregado
                                cursor.execute("UPDATE historico SET conversa = ? WHERE id = ?", (conversa, st.session_state.current_history))
                                st.session_state.current_history = None
                            else:
                                cursor.execute("INSERT INTO historico (usuario, titulo, conversa) VALUES (?, ?, ?)", 
                                               (st.session_state.usuario, titulo, conversa))
                            conn.commit()

                            # Limpar as mensagens para iniciar uma nova conversa
                            st.session_state.messages = []
                        else:
                            st.warning("Não há mensagens para iniciar um novo prompt.")
                else:
                    st.warning("Nenhum modelo disponível para geração de conteúdo.")
            except Exception as e:
                st.error(f"Erro ao conectar à API: {str(e)}")
        else:
            st.warning("Por favor, insira sua chave da API.")
