"""Gravação local das anotações e exportação pelo responsável pela pesquisa."""
import csv
import json
import os
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

from categorias import validar_anotacao
from consentimento import validar_email

BANCO = Path(os.environ.get("BANCO_ANOTACOES", str(Path(__file__).resolve().parent / "armazenamento/anotacoes.sqlite3")))


def conectar(caminho=None):
    caminho = Path(caminho) if caminho is not None else BANCO
    caminho.parent.mkdir(parents=True, exist_ok=True)
    conexao = sqlite3.connect(caminho, timeout=30)
    conexao.execute("""CREATE TABLE IF NOT EXISTS anotacoes (
        id TEXT PRIMARY KEY, sessao_id TEXT NOT NULL,
        nome TEXT NOT NULL, email TEXT NOT NULL, ip TEXT,
        data_hora_utc TEXT NOT NULL, id_registro TEXT NOT NULL,
        base_origem TEXT NOT NULL, sha256_texto TEXT NOT NULL,
        estrategias_identificadas TEXT NOT NULL, evidencia_textual TEXT NOT NULL,
        UNIQUE (sessao_id, id_registro)
    )""")
    return conexao


def salvar_anotacao(identificador, sessao_id, nome, email, ip, registro, categorias, trecho, nenhuma=False, caminho=None, consentimento=None):
    nome = nome.strip()
    if not nome or len(nome) > 150:
        raise ValueError("Informe seu nome, com até 150 caracteres.")
    email = validar_email(email)
    validar_anotacao(registro["texto"], categorias, trecho, nenhuma)
    endereco_api = os.environ.get("URL_API", "").strip()
    if caminho is None:
        if not endereco_api:
            raise ValueError("Configure URL_API e CHAVE_API para gravar no PostgreSQL pela API.")
        from cliente_api import enviar_anotacao

        return enviar_anotacao(endereco_api, os.environ.get("CHAVE_API", ""), identificador,
                               sessao_id, nome, email, ip, registro, categorias, trecho, nenhuma, consentimento)
    valores = (identificador, sessao_id, nome, email, ip,
               datetime.now(timezone.utc).isoformat(timespec="seconds"), registro["id_registro"],
               registro["base_origem"], registro["sha256_texto"],
               json.dumps(list(dict.fromkeys(categorias)), ensure_ascii=False), trecho.strip())
    with closing(conectar(caminho)) as conexao, conexao:
        cursor = conexao.execute("INSERT INTO anotacoes VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ON CONFLICT DO NOTHING", valores)
        return cursor.rowcount == 1


def exportar(caminho=None, saida=None, bases=None):
    from dados import carregar_bases

    if caminho is None and os.environ.get("URL_API"):
        raise ValueError("A coleta usa PostgreSQL remoto. Exporte pelo servidor do banco; este comando é apenas para o SQLite local.")

    caminho = Path(caminho) if caminho is not None else BANCO
    if not caminho.exists():
        raise ValueError("Ainda não há um banco de anotações para exportar.")
    saida = Path(saida) if saida else caminho.parent / "anotacoes.csv"
    saida.parent.mkdir(parents=True, exist_ok=True)
    with closing(conectar(caminho)) as conexao:
        cursor = conexao.execute("SELECT * FROM anotacoes ORDER BY data_hora_utc, id")
        cabecalho = [coluna[0] for coluna in cursor.description]
        registros = cursor.fetchall()
    fontes = bases if bases is not None else carregar_bases()
    textos = {r["id_registro"]: r for registros_base in fontes.values() for r in registros_base}
    linhas = []
    for valores in registros:
        linha = dict(zip(cabecalho, valores))
        registro = textos.get(linha["id_registro"])
        if registro is None or registro["sha256_texto"] != linha["sha256_texto"]:
            raise ValueError(f"Não foi possível conferir o texto de {linha['id_registro']} nas bases de origem.")
        linha["texto_original"] = registro["texto"]
        categorias = json.loads(linha["estrategias_identificadas"])
        linha["estrategias_identificadas"] = "; ".join(categorias) if categorias else "Nenhuma observável"
        linhas.append(linha)
    with saida.open("w", encoding="utf-8-sig", newline="") as arquivo:
        gravador = csv.DictWriter(arquivo, fieldnames=[*cabecalho, "texto_original"])
        gravador.writeheader()
        gravador.writerows(linhas)
    return saida


if __name__ == "__main__":
    print(exportar())

