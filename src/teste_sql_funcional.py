import os
import streamlit as st
import pandas as pd  
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker, declarative_base

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_HOST = os.getenv("POSTGRES_HOST")
POSTGRES_PORT = os.getenv("POSTGRES_PORT")
POSTGRES_DB = os.getenv("POSTGRES_DB")

DATABASE_URL = (
    f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}"
    f"@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
)

# Criar o engine e a sessão
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
Base = declarative_base()

# Definir a tabela usando SQLAlchemy
class RespostaQuestionario(Base):
    __tablename__ = "respostas_questionario"
    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String, nullable=False)
    email = Column(String, nullable=False)
    resposta1 = Column(String, nullable=True)
    resposta2 = Column(String, nullable=True)
    resposta3 = Column(String, nullable=True)

# Criar a tabela no banco de dados
Base.metadata.create_all(engine)

def salvar_respostas(name, email, responses):
    session = Session()
    resposta = RespostaQuestionario(
        nome=name,
        email=email,
        resposta1=responses.get("Resposta 1", ""),
        resposta2=responses.get("Resposta 2", ""),
        resposta3=responses.get("Resposta 3", "")
    )
    session.add(resposta)
    session.commit()
    session.close()

def carregar_respostas():
    session = Session()
    query = session.query(RespostaQuestionario).all()
    df = pd.DataFrame([r.__dict__ for r in query])
    df.drop(columns=['_sa_instance_state'], inplace=True)
    session.close()
    return df

def inicializa_estado():
    if "page" not in st.session_state:
        st.session_state["page"] = 1
    if "name" not in st.session_state:
        st.session_state["name"] = ""
    if "email" not in st.session_state:
        st.session_state["email"] = ""
    if "responses" not in st.session_state:
        st.session_state["responses"] = {}

def pagina_inicial():
    st.title("Questionário")
    st.subheader("Identificação do Usuário")

    name = st.text_input("Digite seu nome:", value=st.session_state["name"])
    email = st.text_input("Digite seu email:", value=st.session_state["email"])

    if st.button("Avançar"):
        if not name or not email:
            st.error("Por favor, preencha todos os campos!")
        else:
            st.session_state["name"] = name
            st.session_state["email"] = email

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

            st.session_state["page"] = 2

def pagina_questionario():
    st.title("Perguntas")
    st.subheader("Responda as perguntas abaixo:")

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
        if any(not answer for answer in st.session_state["responses"].values()):
            st.error("Por favor, responda todas as perguntas!")
        else:
            salvar_respostas(st.session_state["name"], st.session_state["email"], st.session_state["responses"])
            st.success("Respostas salvas com sucesso!")
            st.session_state["page"] = 3

def pagina_final():
    st.title("Obrigado!")
    st.write("Suas respostas foram salvas com sucesso.")
    if st.button("Reiniciar"):
        st.session_state["page"] = 1
        st.session_state["responses"] = {}

def main():
    inicializa_estado()

    if st.session_state["page"] == 1:
        pagina_inicial()
    elif st.session_state["page"] == 2:
        pagina_questionario()
    elif st.session_state["page"] == 3:
        pagina_final()

if __name__ == "__main__":
    main()
