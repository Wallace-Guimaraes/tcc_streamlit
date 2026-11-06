"""Ocultação por regex de identificadores nos textos dos registros."""
import re


EMAIL = re.compile(r"[\w.!#$%&'*+/=?^`{|}~-]+@[\w-]+(?:\.[\w-]+)+", re.UNICODE)
LINK = re.compile(
    r"(?i)(?:\b(?:https?|ftp)://|\bwww\.)[^\s<>\"'\[\]{}]+"
    r"|(?<![\w@./-])(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+"
    r"(?:com|org|net|edu|gov|io|app|online|site|xyz|br)\b"
    r"(?:/[^\s<>\"'\[\]{}]*)?"
)
PALAVRA_NOME = r"[A-ZÀ-ÖØ-Þ][a-zà-öø-ÿ]+(?:[-'][A-ZÀ-ÖØ-Þ]?[a-zà-öø-ÿ]+)*"
NOME_COM_CONTEXTO = re.compile(
    r"(?i:\b(?:meu nome [ée]|me chamo|nome completo\s*:|nome\s*:))[^\S\n]*"
    rf"(?P<nome>{PALAVRA_NOME}(?:[ \t]+(?:(?:da|de|do|das|dos|e)[ \t]+)?{PALAVRA_NOME}){{0,5}})"
)


def ocultar_link(encontro):
    link = encontro.group()
    fim = len(link.rstrip(".,;:!?)}"))
    return "[LINK]" + link[fim:]


def anonimizar_texto(texto, referencia=None):
    """Usa o registro completo como referência para ocultar nomes em trechos.

    Nomes são identificados por apresentações explícitas, como 'me chamo'.
    A regra é parcial e exige revisão humana para uma divulgação dos dados.
    """
    referencia = texto if referencia is None else referencia
    nomes = {encontro.group("nome") for encontro in NOME_COM_CONTEXTO.finditer(referencia)}
    texto = LINK.sub(ocultar_link, texto)
    texto = EMAIL.sub("[EMAIL]", texto)
    if nomes:
        alternativas = "|".join(re.escape(nome) for nome in sorted(nomes, key=len, reverse=True))
        texto = re.sub(rf"(?<!\w)(?:{alternativas})(?!\w)", "[PESSOA]", texto, flags=re.IGNORECASE)
    return texto
