"""Ocultação por regex de identificadores nos textos dos registros."""
import re


EMAIL = re.compile(r"[\w.!#$%&'*+/=?^`{|}~-]+@[\w-]+(?:\.[\w-]+)+", re.UNICODE)
LINK = re.compile(
    r"(?i)(?:\b(?:https?|ftp)://|\bwww\.)[^\s<>\"'\[\]{}]+"
    r"|(?<![\w@./-])(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+"
    r"(?:com|org|net|edu|gov|io|app|online|site|xyz|br|me|ly|info|biz|co|gg|tv|dev|tech|digital|store|pro|vip|top|click)\b"
    r"(?:[/?#][^\s<>\"'\[\]{}]*)?"
)
# Apresentações explícitas também aparecem em caixa alta/baixa. Palavras de
# continuação comuns evitam engolir a instrução persuasiva após o nome.
# Esta lista é uma heurística: não constitui reconhecimento geral de pessoas.
FIM_NOME = r"(?:da|de|do|das|dos|e|sou|estou|tenho|preciso|quero|peço|pede|usa|use|envie|acesse|confirme|pague|receba|trabalho|trabalha|moro|mora|meu|minha|seu|sua|voce|você|para|com|por|que|hoje|agora|urgente|aqui|obrigado|obrigada)\b"
PALAVRAS_NOME = (
    r"[A-ZÀ-ÖØ-Þ][a-zà-öø-ÿ]+(?:[-'’][A-ZÀ-ÖØ-Þ]?[a-zà-öø-ÿ]+)*",
    r"[A-ZÀ-ÖØ-Þ]+(?:[-'’][A-ZÀ-ÖØ-Þ]+)*",
    r"[a-zà-öø-ÿ]+(?:[-'’][a-zà-öø-ÿ]+)*",
)
# Mantém a capitalização coerente dentro de um nome: em texto com iniciais
# maiúsculas, uma continuação em minúsculas não passa a ser parte da pessoa.
PADROES_NOME = []
for palavra in PALAVRAS_NOME:
    palavra = rf"(?!(?i:{FIM_NOME})){palavra}"
    PADROES_NOME.append(rf"{palavra}(?:[ \t]+(?:(?i:da|de|do|das|dos|e)[ \t]+)?{palavra}){{0,5}}")
NOME_COM_CONTEXTO = re.compile(
    r"(?i:\b(?:meu[ \t]+nome[ \t]+[ée]\b[ \t]*:?|me[ \t]+chamo\b[ \t]*:?|nome(?:[ \t]+completo)?[ \t]*:))\s*"
    r"(?P<nome>" + "|".join(PADROES_NOME) + r")(?![\w'’\-])"
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
    # Primeiro o e-mail inteiro: a parte antes do @ pode parecer um domínio.
    texto = EMAIL.sub("[EMAIL]", texto)
    texto = LINK.sub(ocultar_link, texto)
    if nomes:
        # A validação do trecho permite diferenças de espaço/quebra de linha.
        # A máscara precisa reconhecer as mesmas variantes aceitas pelo formulário.
        alternativas = "|".join(r"\s+".join(re.escape(parte) for parte in nome.split())
                                for nome in sorted(nomes, key=len, reverse=True))
        texto = re.sub(rf"(?<!\w)(?:{alternativas})(?!\w)", "[PESSOA]", texto, flags=re.IGNORECASE)
    return texto
