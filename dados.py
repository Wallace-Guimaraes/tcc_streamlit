"""Leitura das versões das bases utilizadas no TCC e conferência dos textos."""
import csv
import hashlib
import io
import os
import re
import sys
import urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
PASTA_BASES = Path(os.environ.get("PASTA_BASES", str(RAIZ / "bases")))
FONTES = (
    ("GOLPEBR", "GBR", "golpebr.csv", "|", "text", "cibercrime", "S",
     "https://raw.githubusercontent.com/Jhonata-Tirloni/golpebr_dataset/main/golpebr_dataset.csv",
     "051ebd5bc001a7c62064dc5e8b9e455bb801b51cbef18ba8121f8c9bf716ef8b"),
    ("FRAUDWHATSAPP_BR", "FWA", "whatsapp.csv", ",", "text_content", "Golpe", "1",
     "https://raw.githubusercontent.com/jmmfilho/sec-fraudimabr/desenv/data/df_rotulado_whatsapp.csv",
     "5c152e93f84afaf19cea4f392c29c4d42eff4d297e513986801bb76688a90abe"),
    ("FRAUDTELEGRAM_BR", "FTG", "telegram.csv", ",", "text_content", "Golpe", "1",
     "https://raw.githubusercontent.com/jmmfilho/sec-fraudimabr/desenv/data/dataset_rotulado_telegram.csv",
     "0851a5b0a71e560b0fdd66aae956ac69be71094753281838507e3a91ff538e0b"),
)
PADRAO_ID_REGISTRO = re.compile(r"^(GBR|FWA|FTG)-\d{6}$")


def validar_registro_canonico(id_registro, sha256_texto, registros):
    """Retorna o registro somente quando ID e hash identificam o mesmo texto."""
    if not isinstance(id_registro, str) or not PADRAO_ID_REGISTRO.fullmatch(id_registro):
        return None
    if not isinstance(sha256_texto, str) or not re.fullmatch(r"[0-9a-f]{64}", sha256_texto):
        return None
    registro = registros.get(id_registro)
    if registro is None:
        return None
    if registro["id_registro"] != id_registro or registro["sha256_texto"] != sha256_texto:
        return None
    prefixo_fonte = {"GOLPEBR": "GBR", "FRAUDWHATSAPP_BR": "FWA", "FRAUDTELEGRAM_BR": "FTG"}
    if prefixo_fonte.get(registro["base_origem"]) != id_registro[:3]:
        return None
    return registro


def carregar_bases(pasta=PASTA_BASES):
    # O GolpeBR tem notícias longas, acima do limite padrão do leitor CSV.
    csv.field_size_limit(min(sys.maxsize, 2_147_483_647))
    pasta = Path(pasta)
    pasta.mkdir(parents=True, exist_ok=True)
    bases = {}
    for nome, prefixo, arquivo, separador, campo_texto, campo_rotulo, rotulo_fraude, url, hash_esperado in FONTES:
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
            if texto.strip() and linha.get(campo_rotulo, "").strip().upper() == rotulo_fraude:
                registros.append({"id_registro": f"{prefixo}-{indice:06d}", "base_origem": nome,
                                  "texto": texto, "sha256_texto": hashlib.sha256(texto.encode("utf-8")).hexdigest()})
        bases[nome] = registros
    return bases
