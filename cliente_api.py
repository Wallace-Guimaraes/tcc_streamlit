"""Envio das respostas do Streamlit para a API, sem expor a chave ao navegador."""
import json
import urllib.error
import urllib.request


def enviar_anotacao(endereco, chave, identificador, sessao_id, nome, idade, ip, registro, categorias, trecho, nenhuma, consentimento=None):
    if not chave:
        raise ValueError("Configure CHAVE_API no servidor do Streamlit.")
    dados = {"id": identificador, "sessao_id": sessao_id, "nome": nome, "idade": idade, "ip": ip,
             "id_registro": registro["id_registro"], "sha256_texto": registro["sha256_texto"],
             "categorias": categorias, "trecho": trecho, "nenhuma": nenhuma}
    dados.update(consentimento or {})
    pedido = urllib.request.Request(endereco.rstrip("/") + "/anotacoes",
                                    data=json.dumps(dados, ensure_ascii=False).encode("utf-8"),
                                    headers={"Content-Type": "application/json", "X-API-Key": chave}, method="POST")
    try:
        with urllib.request.urlopen(pedido, timeout=30) as resposta:
            conteudo = json.load(resposta)
        if not isinstance(conteudo, dict) or not isinstance(conteudo.get("criada"), bool):
            raise ValueError("Resposta inesperada da API. A anotação não foi confirmada.")
        return conteudo["criada"]
    except urllib.error.HTTPError as erro:
        if erro.code in (401, 403):
            raise ValueError("A API recusou a chave de acesso. Confira a configuração do servidor.") from None
        if erro.code == 422:
            raise ValueError("A API recusou a anotação. Confira os campos e o aceite do termo; se a página estava aberta antes de uma atualização, reinicie a participação.") from None
        raise ValueError("A API não confirmou a gravação. Tente novamente; a resposta permanece na tela.") from None
    except (OSError, json.JSONDecodeError):
        raise ValueError("Não foi possível alcançar a API. Tente novamente; a resposta permanece na tela.") from None
