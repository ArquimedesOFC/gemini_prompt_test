import streamlit as st
import os
import subprocess

def menu():
    # Cria um menu para o usuário escolher o que fazer
    option = st.selectbox("Escolha uma opção", ["Inserir Chave de API", "Sobre", "Sair"], key="menu_selectbox")

    if option == "Inserir Chave de API":
        # Exibe um campo de entrada para a chave da API
        api_key = st.text_input("Digite sua chave de API do Google Gemini", type="password", key="api_key_input")
        
        if api_key:
            # Salva a chave de API em uma variável de ambiente para ser utilizada em app.py
            os.environ['GOOGLE_GEMINI_API_KEY'] = api_key
            st.success("Chave de API salva com sucesso!")

            # Redireciona para o app.py automaticamente
            st.write("Agora redirecionando para a aplicação principal...")
            
            # Executa o app.py
            subprocess.run(["streamlit", "run", "app.py"])
            
            # Finaliza a execução do config.py após redirecionamento
            st.stop()

    elif option == "Sobre":
        # Exibe informações sobre o projeto ou a aplicação
        st.write("Esta aplicação conecta-se à API do Google Gemini para gerar conteúdo com IA.")
        st.write("Insira sua chave de API para começar a usar.")

    elif option == "Sair":
        # Finaliza a aplicação
        st.write("Saindo da configuração...")
        st.stop()

# Chama a função do menu
menu()
