"""Aplicação de anotação do TCC de Wallace e Vinicius."""
import sqlite3
import os
from uuid import uuid4

import streamlit as st
from streamlit.errors import StreamlitSecretNotFoundError

from banco import salvar_anotacao
from categorias import CATEGORIAS
from dados import carregar_bases, sortear_registro

st.set_page_config(page_title="Anotação de textos — TCC", layout="wide")
try:
    for nome_configuracao in ("URL_API", "CHAVE_API"):
        if not os.environ.get(nome_configuracao) and nome_configuracao in st.secrets:
            os.environ[nome_configuracao] = str(st.secrets[nome_configuracao])
except (FileNotFoundError, StreamlitSecretNotFoundError):
    pass  # No Docker, as configurações são fornecidas pelas variáveis de ambiente.
st.markdown("""
<style>
    .stMainBlockContainer { max-width: 1180px; padding: 2.6rem 1.4rem 1rem; }
    [data-testid="stHeader"] { height: 2.5rem; background: transparent; }
    [data-testid="stVerticalBlock"] { gap: .55rem; }
    [data-testid="stMarkdownContainer"] h3 { padding: 0 0 .2rem; font-size: 1.45rem; }
    [data-testid="stForm"] { padding: .9rem 1rem; }
    [data-testid="stFormSubmitButton"] button {
        background-color: #0F766E !important;
        border-color: #0F766E !important;
        color: #FFFFFF !important;
        font-weight: 600;
    }
    [data-testid="stFormSubmitButton"] button p { color: inherit !important; }
    [data-testid="stFormSubmitButton"] button:hover:not(:disabled) {
        background-color: #115E59 !important;
        border-color: #115E59 !important;
    }
    [data-testid="stFormSubmitButton"] button:focus-visible {
        outline: 3px solid #5EEAD4 !important;
        outline-offset: 3px;
    }
    [data-testid="stFormSubmitButton"] button:disabled {
        background-color: #334155 !important;
        border-color: #64748B !important;
        color: #CBD5E1 !important;
        opacity: 1;
    }
    [data-testid="stCheckbox"] { min-height: 1.8rem; }
    [data-testid="stCheckbox"] p { font-size: .93rem; }
    [data-testid="stTextArea"] textarea { font-size: .95rem; line-height: 1.5; }
    [data-testid="stTextArea"] textarea:disabled {
        opacity: 1; color: inherit; -webkit-text-fill-color: currentColor; cursor: text;
    }
    @media (max-width: 760px) {
        .stMainBlockContainer { padding: 2.6rem .8rem 1rem; }
    }
</style>
""", unsafe_allow_html=True)
st.markdown("### Anotação de textos")


@st.cache_data(show_spinner="Carregando as três bases…")
def obter_bases():
    return carregar_bases()


if "participante" not in st.session_state:
    st.caption("TCC · Wallace e Vinicius")
    st.write("Leia o texto, marque as categorias e copie os trechos que justificam sua escolha.")
    st.caption("Registro: nome, idade, IP quando disponível, data/hora e resposta.")
    with st.form("identificacao"):
        campo_nome, campo_idade = st.columns([3, 1])
        nome = campo_nome.text_input("Nome", max_chars=150)
        idade = campo_idade.number_input("Idade", min_value=1, max_value=120, value=None, step=1, placeholder="Idade")
        iniciar = st.form_submit_button("Começar", type="primary")
    if iniciar:
        if not nome.strip() or idade is None:
            st.error("Preencha seu nome e sua idade para começar.")
        else:
            st.session_state.participante = {"nome": nome.strip(), "idade": int(idade)}
            st.session_state.sessao_id = str(uuid4())
            st.session_state.vistos = set()
            st.session_state.salvas = 0
            st.rerun()
    st.stop()

try:
    bases = obter_bases()
except (OSError, ValueError) as erro:
    st.error(f"Não foi possível carregar as bases: {erro}")
    st.stop()

participante = st.session_state.participante
st.caption(f"{participante['nome']} · {st.session_state.salvas} respostas nesta sessão")
if "mensagem" in st.session_state:
    st.toast(st.session_state.pop("mensagem"))

if "registro" not in st.session_state:
    st.session_state.registro = sortear_registro(bases, st.session_state.vistos)
    st.session_state.anotacao_id = str(uuid4())
registro = st.session_state.registro
if registro is None:
    st.info("Você já percorreu todos os textos disponíveis nesta sessão. Obrigado pela participação!")
    st.stop()

coluna_texto, coluna_resposta = st.columns([1.15, 1], gap="medium")
with coluna_texto:
    st.caption(f"{registro['base_origem']} · {registro['id_registro']}")
    st.text_area("Texto", value=registro["texto"], height=390, disabled=True,
                 label_visibility="collapsed", key=f"texto_{registro['id_registro']}")
    pular = st.button("Pular texto", help="Use quando não conseguir avaliar. Não grava uma resposta.")

with coluna_resposta:
    with st.form(f"anotacao_{st.session_state.anotacao_id}"):
        st.markdown("**Categorias**")
        colunas_categorias = st.columns(2)
        categorias = []
        for indice, (categoria, explicacao) in enumerate(CATEGORIAS.items()):
            with colunas_categorias[indice % 2]:
                if st.checkbox(categoria, help=explicacao):
                    categorias.append(categoria)
        nenhuma = st.checkbox("Nenhuma das categorias")
        trecho = st.text_area("Trecho de justificativa", height=110,
                              placeholder="Opcional para “Nenhuma das categorias”",
                              help="Obrigatório ao marcar estratégias. Copie uma passagem por linha. Se escolher nenhuma das categorias, pode deixar em branco.")
        salvar = st.form_submit_button("Salvar e próximo", type="primary", use_container_width=True)

if salvar:
    try:
        gravou = salvar_anotacao(st.session_state.anotacao_id, st.session_state.sessao_id,
                                 participante["nome"], participante["idade"], st.context.ip_address,
                                 registro, categorias, trecho, nenhuma)
    except (ValueError, sqlite3.Error, OSError) as erro:
        st.error(f"A resposta não foi salva: {erro}")
    else:
        st.session_state.salvas += int(gravou)
        st.session_state.vistos.add(registro["id_registro"])
        del st.session_state.registro
        st.session_state.mensagem = "Anotação salva." if gravou else "Esta resposta já estava salva. Nenhuma cópia foi criada."
        st.rerun()

if pular:
    st.session_state.vistos.add(registro["id_registro"])
    del st.session_state.registro
    st.rerun()

