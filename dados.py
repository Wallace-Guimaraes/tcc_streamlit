"""Leitura das versões das bases utilizadas no TCC e sorteio de registros."""
import csv
import hashlib
import io
import os
import random
import sys
import urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
PASTA_BASES = Path(os.environ.get("PASTA_BASES", str(RAIZ / "bases")))
FONTES = (
    ("GOLPEBR", "GBR", "golpebr.csv", "|", "text",
     "https://raw.githubusercontent.com/Jhonata-Tirloni/golpebr_dataset/main/golpebr_dataset.csv",
     "051ebd5bc001a7c62064dc5e8b9e455bb801b51cbef18ba8121f8c9bf716ef8b"),
    ("FRAUDWHATSAPP_BR", "FWA", "whatsapp.csv", ",", "text_content",
     "https://raw.githubusercontent.com/jmmfilho/sec-fraudimabr/desenv/data/df_rotulado_whatsapp.csv",
     "5c152e93f84afaf19cea4f392c29c4d42eff4d297e513986801bb76688a90abe"),
    ("FRAUDTELEGRAM_BR", "FTG", "telegram.csv", ",", "text_content",
     "https://raw.githubusercontent.com/jmmfilho/sec-fraudimabr/desenv/data/dataset_rotulado_telegram.csv",
     "0851a5b0a71e560b0fdd66aae956ac69be71094753281838507e3a91ff538e0b"),
)


def carregar_bases(pasta=PASTA_BASES):
    # O GolpeBR tem notícias longas, acima do limite padrão do leitor CSV.
    csv.field_size_limit(min(sys.maxsize, 2_147_483_647))
    pasta = Path(pasta)
    pasta.mkdir(parents=True, exist_ok=True)
    bases = {}
    for nome, prefixo, arquivo, separador, campo_texto, url, hash_esperado in FONTES:
        caminho = pasta / arquivo
        conteudo = caminho.read_bytes() if caminho.exists() else urllib.request.urlopen(url, timeout=60).read()
        if hashlib.sha256(conteudo).hexdigest() != hash_esperado:
            raise ValueError(f"A versão de {arquivo} difere da usada no TCC. Confira a fonte antes de substituir o arquivo.")
        if not caminho.exists():
            caminho.write_bytes(conteudo)
        leitor = csv.DictReader(io.StringIO(conteudo.decode("utf-8-sig"), newline=""), delimiter=separador)
        registros = []
        for indice, linha in enumerate(leitor):
            texto = linha[campo_texto]
            if texto.strip():
                registros.append({"id_registro": f"{prefixo}-{indice:06d}", "base_origem": nome,
                                  "texto": texto, "sha256_texto": hashlib.sha256(texto.encode("utf-8")).hexdigest()})
        bases[nome] = registros
    return bases


def sortear_registro(bases, vistos):
    disponiveis = {nome: [r for r in registros if r["id_registro"] not in vistos] for nome, registros in bases.items()}
    disponiveis = {nome: registros for nome, registros in disponiveis.items() if registros}
    if not disponiveis:
        return None
    return random.choice(disponiveis[random.choice(list(disponiveis))])

