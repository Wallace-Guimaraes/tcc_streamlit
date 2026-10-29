"""Aplicação de anotação do TCC de Wallace e Vinicius."""
import sqlite3
import os
from uuid import uuid4

import streamlit as st
from streamlit.errors import StreamlitSecretNotFoundError

from banco import salvar_anotacao
from categorias import CATEGORIAS
from dados import carregar_bases, sortear_registro
from consentimento import HASH_TCLE, TCLE, VERSAO_TCLE, registrar_aceite

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


@st.cache_data(show_spinner="Carregando as três bases…")
def obter_bases():
    return carregar_bases()


aceite_atual = st.session_state.get("consentimento", {})
if ("participante" not in st.session_state
        or aceite_atual.get("consentimento_versao") != VERSAO_TCLE
        or aceite_atual.get("consentimento_hash") != HASH_TCLE):
    st.markdown("### Termo de Consentimento Livre e Esclarecido")
    st.caption("Pesquisa de TCC · Wallace e Vinicíus · Participação a partir de 18 anos")
    coluna_termo, coluna_aceite = st.columns([1.7, 1], gap="large")
    with coluna_termo:
        with st.container(height=420, border=True):
            st.markdown(TCLE.split("\n", 1)[1])
        st.download_button("Baixar uma cópia do termo", data=TCLE.encode("utf-8"),
                           file_name=f"termo_consentimento_{VERSAO_TCLE}.txt", mime="text/plain; charset=utf-8")
    with coluna_aceite:
        with st.form("identificacao"):
            nome = st.text_input("Nome completo", max_chars=150)
            idade = st.number_input("Idade", min_value=18, max_value=120, value=None, step=1, placeholder="Sua idade")
            concordou = st.checkbox("Declaro que tenho 18 anos ou mais, li o termo e concordo em participar desta pesquisa.")
            iniciar = st.form_submit_button("Concordo e quero participar", type="primary", use_container_width=True)
        st.caption("Se não concordar, feche a página. Nenhuma anotação será enviada antes do aceite.")
    if iniciar:
        try:
            aceite = registrar_aceite(nome, idade, concordou)
        except ValueError as erro:
            st.error(str(erro))
        else:
            st.session_state.consentimento = aceite
            st.session_state.participante = {"nome": nome.strip(), "idade": int(idade)}
            st.session_state.sessao_id = str(uuid4())
            st.session_state.vistos = set()
            st.session_state.salvas = 0
            st.rerun()
    st.stop()

st.markdown("### Anotação de textos")
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
                                 registro, categorias, trecho, nenhuma, consentimento=st.session_state.consentimento)
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

