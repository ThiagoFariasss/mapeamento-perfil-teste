import os
import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os


# Carrega variáveis de ambiente
load_dotenv()  

import os
import streamlit as st

# Obtém a porta a partir da variável de ambiente PORT
port = int(os.environ.get("PORT",8501))

# Inicia o Streamlit na porta especificada
st.run(port=port, address="0.0.0.0")

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://mapeamento_perfil_user:MR5z22vyzWnew7MKysSpHdBuPFIYtwVs@dpg-cuj3qk2j1k6c73e1ik40-a.oregon-postgres.render.com:5432/mapeamento_perfil")

print(f"Valor de DATABASE_URL: {DATABASE_URL}")  # Depuração

if not DATABASE_URL:
    raise ValueError("DATABASE_URL não foi carregado corretamente.")


engine = create_engine(DATABASE_URL)

def inicializar_banco():
    """Cria a tabela se não existir"""
    with engine.begin() as conn:  # Usa `begin()` para permitir transações
        conn.execute(text('''
            CREATE TABLE IF NOT EXISTS respostas_questionario (
                id SERIAL PRIMARY KEY,
                nome TEXT,
                email TEXT,
                resposta1 TEXT,
                resposta2 TEXT,
                resposta3 TEXT
            )
        '''))

def salvar_respostas(name, email, responses):
    """Salva as respostas no banco de dados"""
    with engine.begin() as conn:  # Usa `begin()` para garantir `commit`
        conn.execute(text('''
            INSERT INTO respostas_questionario (nome, email, resposta1, resposta2, resposta3)
            VALUES (:name, :email, :r1, :r2, :r3)
        ''').bindparams(
            name=name,
            email=email,
            r1=responses.get("Resposta 1", ""),
            r2=responses.get("Resposta 2", ""),
            r3=responses.get("Resposta 3", "")
        ))

def carregar_respostas():
    """Carrega todas as respostas do banco"""
    with engine.connect() as conn:
        return pd.read_sql("SELECT * FROM respostas_questionario", con=conn)

def inicializa_estado():
    """Inicializa variáveis no estado da sessão"""
    for key in ["page", "name", "email", "responses"]:
        if key not in st.session_state:
            st.session_state[key] = "" if key in ["name", "email"] else (1 if key == "page" else {})

def pagina_inicial():
    """Página inicial para identificar o usuário"""
    st.title("Questionário")
    st.subheader("Identificação do Usuário")
    
    name = st.text_input("Nome:", value=st.session_state["name"])
    email = st.text_input("Email:", value=st.session_state["email"])
    
    if st.button("Avançar"):
        if not name or not email:
            st.error("Preencha todos os campos!")
        else:
            st.session_state.update({"name": name, "email": email})
            df = carregar_respostas()
            
            if not df.empty:
                user_data = df.query("nome == @name and email == @email")
                if not user_data.empty:
                    st.session_state["responses"] = user_data.iloc[0][["resposta1", "resposta2", "resposta3"]].to_dict()
                else:
                    st.session_state["responses"] = {}

            st.session_state["page"] = 2

def pagina_questionario():
    """Página do questionário"""
    st.title("Perguntas")
    
    perguntas = [
        "1. Qual é a sua ferramenta favorita para trabalho?",
        "2. Qual é o principal desafio que enfrenta no seu trabalho?",
        "3. Como você avalia a eficiência das suas ferramentas atuais?"
    ]
    
    respostas = st.session_state.get("responses", {})
    
    for i, pergunta in enumerate(perguntas, 1):
        chave = f"Resposta {i}"
        respostas[chave] = st.text_input(pergunta, value=respostas.get(chave, ""))
    
    st.session_state["responses"] = respostas

    if st.button("Enviar"):
        if any(not v for v in respostas.values()):
            st.error("Responda todas as perguntas!")
        else:
            salvar_respostas(st.session_state["name"], st.session_state["email"], respostas)
            st.success("Respostas salvas!")
            st.session_state["page"] = 3

def pagina_final():
    """Página final de agradecimento"""
    st.title("Obrigado!")
    st.write("Suas respostas foram salvas com sucesso.")
    if st.button("Reiniciar"):
        st.session_state.update({"page": 1, "responses": {}})

def main():
    """Controle do fluxo de páginas"""
    inicializar_banco()
    inicializa_estado()
    
    paginas = {1: pagina_inicial, 2: pagina_questionario, 3: pagina_final}
    paginas[st.session_state["page"]]()

if __name__ == "__main__":
    main()
