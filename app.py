"""Aplicação de anotação do TCC de Wallace e Vinicius."""
import sqlite3
from uuid import uuid4

import streamlit as st

from banco import salvar_anotacao
from categorias import CATEGORIAS
from dados import carregar_bases, sortear_registro

st.set_page_config(page_title="Anotação de textos — TCC", layout="centered")
st.title("Anotação de estratégias de persuasão")
st.caption("Pesquisa de TCC — Wallace e Vinicius")


@st.cache_data(show_spinner="Carregando as três bases…")
def obter_bases():
    return carregar_bases()


if "participante" not in st.session_state:
    st.write("Leia os textos e marque as estratégias de persuasão que encontrar. Um mesmo texto pode ter mais de uma estratégia.")
    st.caption("Cada resposta será registrada com seu nome, idade, IP da conexão quando disponível, data e hora. As respostas dos demais participantes não são mostradas.")
    with st.form("identificacao"):
        nome = st.text_input("Nome", max_chars=150)
        idade = st.number_input("Idade", min_value=1, max_value=120, value=None, step=1, placeholder="Sua idade")
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
st.caption(f"Participante: {participante['nome']} · Anotações salvas nesta sessão: {st.session_state.salvas}")
if "mensagem" in st.session_state:
    st.success(st.session_state.pop("mensagem"))

if "registro" not in st.session_state:
    st.session_state.registro = sortear_registro(bases, st.session_state.vistos)
    st.session_state.anotacao_id = str(uuid4())
registro = st.session_state.registro
if registro is None:
    st.info("Você já percorreu todos os textos disponíveis nesta sessão. Obrigado pela participação!")
    st.stop()

st.subheader("Texto sorteado")
st.caption(f"Base: {registro['base_origem']} · Registro: {registro['id_registro']}")
st.text_area("Leia o texto", value=registro["texto"], height=320, disabled=True, key=f"texto_{registro['id_registro']}")

with st.expander("Consultar as oito categorias"):
    for categoria, explicacao in CATEGORIAS.items():
        st.markdown(f"**{categoria}:** {explicacao}")

with st.form(f"anotacao_{st.session_state.anotacao_id}"):
    st.write("Quais estratégias aparecem no texto?")
    categorias = [categoria for categoria in CATEGORIAS if st.checkbox(categoria)]
    nenhuma = st.checkbox("Nenhuma das categorias")
    trecho = st.text_area("Trecho que justifica a resposta (obrigatório)",
                          help="Copie uma ou mais passagens do texto, uma por linha. Inclua evidências para cada estratégia marcada. Se marcou nenhuma, copie a passagem que fundamenta sua avaliação.")
    salvar = st.form_submit_button("Salvar e sortear próximo", type="primary")

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

if st.button("Não consigo avaliar este texto: sortear outro"):
    st.session_state.vistos.add(registro["id_registro"])
    del st.session_state.registro
    st.rerun()

