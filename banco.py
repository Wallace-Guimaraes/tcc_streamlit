"""Gravação local das anotações e exportação pelo responsável pela pesquisa."""
import csv
import json
import os
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

from categorias import validar_anotacao

BANCO = Path(os.environ.get("BANCO_ANOTACOES", str(Path(__file__).resolve().parent / "armazenamento/anotacoes.sqlite3")))


def conectar(caminho=None):
    caminho = Path(caminho) if caminho is not None else BANCO
    caminho.parent.mkdir(parents=True, exist_ok=True)
    conexao = sqlite3.connect(caminho, timeout=30)
    conexao.execute("""CREATE TABLE IF NOT EXISTS anotacoes (
        id TEXT PRIMARY KEY, sessao_id TEXT NOT NULL,
        nome TEXT NOT NULL, idade INTEGER NOT NULL, ip TEXT,
        data_hora_utc TEXT NOT NULL, id_registro TEXT NOT NULL,
        base_origem TEXT NOT NULL, sha256_texto TEXT NOT NULL,
        estrategias_identificadas TEXT NOT NULL, evidencia_textual TEXT NOT NULL,
        UNIQUE (sessao_id, id_registro)
    )""")
    return conexao


def salvar_anotacao(identificador, sessao_id, nome, idade, ip, registro, categorias, trecho, nenhuma=False, caminho=None):
    nome = nome.strip()
    if not nome or len(nome) > 150:
        raise ValueError("Informe seu nome, com até 150 caracteres.")
    if not isinstance(idade, int) or isinstance(idade, bool) or not 1 <= idade <= 120:
        raise ValueError("Informe uma idade entre 1 e 120 anos.")
    validar_anotacao(registro["texto"], categorias, trecho, nenhuma)
    valores = (identificador, sessao_id, nome, idade, ip,
               datetime.now(timezone.utc).isoformat(timespec="seconds"), registro["id_registro"],
               registro["base_origem"], registro["sha256_texto"],
               json.dumps(list(dict.fromkeys(categorias)), ensure_ascii=False), trecho.strip())
    with closing(conectar(caminho)) as conexao, conexao:
        cursor = conexao.execute("INSERT INTO anotacoes VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ON CONFLICT DO NOTHING", valores)
        return cursor.rowcount == 1


def exportar(caminho=None, saida=None):
    caminho = Path(caminho) if caminho is not None else BANCO
    if not caminho.exists():
        raise ValueError("Ainda não há um banco de anotações para exportar.")
    saida = Path(saida) if saida else caminho.parent / "anotacoes.csv"
    saida.parent.mkdir(parents=True, exist_ok=True)
    with closing(conectar(caminho)) as conexao:
        cursor = conexao.execute("SELECT * FROM anotacoes ORDER BY data_hora_utc, id")
        cabecalho = [coluna[0] for coluna in cursor.description]
        registros = cursor.fetchall()
    with saida.open("w", encoding="utf-8-sig", newline="") as arquivo:
        gravador = csv.writer(arquivo)
        gravador.writerow(cabecalho)
        gravador.writerows(registros)
    return saida


if __name__ == "__main__":
    print(exportar())

