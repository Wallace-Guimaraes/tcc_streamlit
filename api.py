"""API de gravação das anotações em PostgreSQL."""
import hmac
import json
import os
from contextlib import asynccontextmanager
from functools import lru_cache
from uuid import UUID

import psycopg
from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, ConfigDict, Field

from categorias import validar_anotacao
from dados import carregar_bases

cabecalho_chave = APIKeyHeader(name="X-API-Key", auto_error=False)


def autenticar(chave: str | None = Depends(cabecalho_chave)):
    esperada = os.environ.get("CHAVE_API", "")
    if not esperada:
        raise HTTPException(503, "A chave da API não foi configurada.")
    if not chave or not hmac.compare_digest(chave.encode(), esperada.encode()):
        raise HTTPException(401, "Acesso não autorizado.")


def conectar():
    endereco = os.environ.get("DATABASE_URL", "")
    if not endereco:
        raise RuntimeError("Configure DATABASE_URL para conectar ao PostgreSQL.")
    return psycopg.connect(endereco, connect_timeout=10)


@asynccontextmanager
async def iniciar(aplicacao):
    if not os.environ.get("CHAVE_API"):
        raise RuntimeError("Configure CHAVE_API antes de iniciar a API.")
    with conectar() as conexao:
        conexao.execute("""CREATE TABLE IF NOT EXISTS anotacoes (
            id TEXT PRIMARY KEY, sessao_id TEXT NOT NULL,
            nome TEXT NOT NULL, idade INTEGER NOT NULL CHECK (idade BETWEEN 1 AND 120),
            ip TEXT, data_hora_utc TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            id_registro TEXT NOT NULL, base_origem TEXT NOT NULL,
            sha256_texto TEXT NOT NULL, estrategias_identificadas JSONB NOT NULL,
            evidencia_textual TEXT NOT NULL,
            UNIQUE (sessao_id, id_registro)
        )""")
    yield


app = FastAPI(title="Anotações — TCC", lifespan=iniciar, docs_url=None, redoc_url=None, openapi_url=None)


class Anotacao(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    sessao_id: UUID
    nome: str = Field(min_length=1, max_length=150)
    idade: int = Field(ge=1, le=120, strict=True)
    ip: str | None = Field(default=None, max_length=45)
    id_registro: str = Field(pattern=r"^(GBR|FWA|FTG)-\d{6}$")
    sha256_texto: str = Field(pattern=r"^[0-9a-f]{64}$")
    categorias: list[str] = Field(max_length=8)
    trecho: str = Field(default="", max_length=100000)
    nenhuma: bool = False


@lru_cache(maxsize=1)
def registros_por_id():
    return {r["id_registro"]: r for registros in carregar_bases().values() for r in registros}


@app.get("/saude")
def saude():
    try:
        with conectar() as conexao:
            conexao.execute("SELECT 1")
    except (psycopg.Error, RuntimeError):
        raise HTTPException(503, "Banco indisponível.") from None
    return {"status": "ok"}


@app.post("/anotacoes", dependencies=[Depends(autenticar)])
def receber_anotacao(anotacao: Anotacao):
    try:
        registro = registros_por_id().get(anotacao.id_registro)
    except (OSError, ValueError):
        raise HTTPException(503, "As bases de origem não estão disponíveis.") from None
    if registro is None or registro["sha256_texto"] != anotacao.sha256_texto:
        raise HTTPException(422, "Registro ou versão do texto não reconhecidos.")
    if not anotacao.nome.strip():
        raise HTTPException(422, "Informe o nome do anotador.")
    try:
        validar_anotacao(registro["texto"], anotacao.categorias, anotacao.trecho, anotacao.nenhuma)
    except ValueError as erro:
        raise HTTPException(422, str(erro)) from None
    try:
        with conectar() as conexao:
            resultado = conexao.execute("""INSERT INTO anotacoes
                (id, sessao_id, nome, idade, ip, id_registro, base_origem,
                 sha256_texto, estrategias_identificadas, evidencia_textual)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s)
                ON CONFLICT DO NOTHING RETURNING id""",
                (str(anotacao.id), str(anotacao.sessao_id), anotacao.nome.strip(), anotacao.idade,
                 anotacao.ip, registro["id_registro"], registro["base_origem"], registro["sha256_texto"],
                 json.dumps(list(dict.fromkeys(anotacao.categorias)), ensure_ascii=False), anotacao.trecho.strip()))
            criada = resultado.fetchone() is not None
    except psycopg.Error:
        raise HTTPException(503, "Não foi possível gravar a anotação. Tente novamente.") from None
    return {"criada": criada}
