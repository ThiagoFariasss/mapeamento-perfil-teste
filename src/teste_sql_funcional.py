import os 
import streamlit as st
import pandas as pd  
import psycopg2  # Biblioteca para conexão com banco de dados PostgreSQL

from dotenv import load_dotenv

# Conecta ao banco de dados PostgreSQL

load_dotenv()

POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_HOST = os.getenv("POSTGRES_HOST")
POSTGRES_PORT = os.getenv("POSTGRES_PORT")
POSTGRES_DB = os.getenv("POSTGRES_DB")

def conectar_banco():
    return psycopg2.connect(
        host=POSTGRES_HOST or "localhost",
        database=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
        port=int(POSTGRES_PORT) if POSTGRES_PORT else 5432  # Garante que seja um número
    )


# Cria uma tabela de respostas no banco, caso ainda não exista
def inicializar_banco():
    conn = conectar_banco()  # Conecta ao banco de dados
    cursor = conn.cursor()  # Cria um cursor para executar comandos SQL
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS respostas_questionario (
            id SERIAL PRIMARY KEY,  
            nome TEXT, 
            email TEXT, 
            resposta1 TEXT,  
            resposta2 TEXT,  
            resposta3 TEXT   
        )
    """)
    conn.commit()  # Confirma as alterações no banco de dados
    conn.close()  # Fecha a conexão com o banco de dados

# Salvar respostas no banco de dados
def salvar_respostas(name, email, responses):
    conn = conectar_banco()
    cursor = conn.cursor()

    # Insere as respostas no banco
    cursor.execute("""
        INSERT INTO respostas_questionario (nome, email, resposta1, resposta2, resposta3)
        VALUES (%s, %s, %s, %s, %s)
    """, (name, email, responses.get("Resposta 1", ""), responses.get("Resposta 2", ""), responses.get("Resposta 3", "")))

    conn.commit()
    conn.close()

# Carrega todas as respostas do banco de dados
def carregar_respostas():
    """Carrega as respostas do banco de dados"""
    conn = conectar_banco()
    df = pd.read_sql("SELECT * FROM respostas_questionario", con=conn)  # Lê dados em formato de DataFrame
    conn.close()
    return df

# Inicializa o estado da sessão no Streamlit
def inicializa_estado():
    """Inicializa os valores no estado da sessão"""
    if "page" not in st.session_state:  # Define página inicial
        st.session_state["page"] = 1
    if "name" not in st.session_state:  # Inicializa o nome
        st.session_state["name"] = ""
    if "email" not in st.session_state:  # Inicializa o email
        st.session_state["email"] = ""
    if "responses" not in st.session_state:  # Inicializa respostas
        st.session_state["responses"] = {}

# Página inicial para identificar o usuário
def pagina_inicial():
    """Página inicial para identificação do usuário"""
    st.title("Questionário")
    st.subheader("Identificação do Usuário")

    name = st.text_input("Digite seu nome:", value=st.session_state["name"])
    email = st.text_input("Digite seu email:", value=st.session_state["email"])

    if st.button("Avançar"):
        if not name or not email:  # Verifica campos vazios
            st.error("Por favor, preencha todos os campos!")
        else:
            st.session_state["name"] = name
            st.session_state["email"] = email

            # Verifica se já existem respostas para o usuário
            df = carregar_respostas()
            user_data = df[(df["nome"] == name) & (df["email"] == email)]
            if not user_data.empty:
                user_data = user_data.iloc[0]
                st.session_state["responses"] = {
                    "Resposta 1": user_data["resposta1"],
                    "Resposta 2": user_data["resposta2"],
                    "Resposta 3": user_data["resposta3"]
                }
            else:
                st.session_state["responses"] = {}

            st.session_state["page"] = 2  # Avança para a próxima página

# Página para responder o questionário
def pagina_questionario():
    """Página do questionário"""
    st.title("Perguntas")
    st.subheader("Responda as perguntas abaixo:")

    # Campos para entrada de respostas
    st.session_state["responses"]["Resposta 1"] = st.text_input(
        "1. Qual é a sua ferramenta favorita para trabalho?",
        value=st.session_state["responses"].get("Resposta 1", "")
    )
    st.session_state["responses"]["Resposta 2"] = st.text_input(
        "2. Qual é o principal desafio que enfrenta no seu trabalho?",
        value=st.session_state["responses"].get("Resposta 2", "")
    )
    st.session_state["responses"]["Resposta 3"] = st.text_input(
        "3. Como você avalia a eficiência das suas ferramentas atuais?",
        value=st.session_state["responses"].get("Resposta 3", "")
    )

    if st.button("Enviar"):
        if any(not answer for answer in st.session_state["responses"].values()):  # Verifica respostas incompletas
            st.error("Por favor, responda todas as perguntas!")
        else:
            salvar_respostas(st.session_state["name"], st.session_state["email"], st.session_state["responses"])
            st.success("Respostas salvas com sucesso!")
            st.session_state["page"] = 3  # Avança para a página final

# Página final para agradecimento
def pagina_final():
    """Página final com agradecimento"""
    st.title("Obrigado!")
    st.write("Suas respostas foram salvas com sucesso.")
    if st.button("Reiniciar"):
        st.session_state["page"] = 1
        st.session_state["responses"] = {}

# Controla o fluxo da aplicação
def main():
    """Controle do fluxo de páginas"""
    inicializar_banco()  # Inicializa a tabela no banco
    inicializa_estado()  # Inicializa o estado da sessão

    # Controle de navegação entre páginas
    if st.session_state["page"] == 1:
        pagina_inicial()
    elif st.session_state["page"] == 2:
        pagina_questionario()
    elif st.session_state["page"] == 3:
        pagina_final()


if __name__ == "__main__":
    main()