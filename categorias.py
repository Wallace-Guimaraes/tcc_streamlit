"""Categorias adotadas no protocolo do TCC."""

CATEGORIAS = {
    "Urgência": "Pressão para agir logo ou dentro de um prazo. Rapidez do serviço, sozinha, não basta.",
    "Medo": "Risco ou consequência negativa explorados para induzir uma ação.",
    "Ameaça": "Dano ou punição anunciados para coagir a pessoa.",
    "Falsa autoridade": "Uso de uma suposta autoridade institucional, profissional ou hierárquica.",
    "Promessa de vantagem": "Benefício financeiro, material ou outro ganho usado para induzir uma ação.",
    "Escassez": "Limitação de vagas, quantidade ou disponibilidade para pressionar a adesão.",
    "Confiança": "Credibilidade construída com garantias, depoimentos ou supostas provas.",
    "Vínculo emocional": "Exploração de afeto, parentesco, romance, solidariedade ou pertencimento.",
}


def validar_anotacao(texto, categorias, trecho, nenhuma=False):
    if nenhuma and categorias:
        raise ValueError("Escolha as estratégias ou marque 'Nenhuma das categorias', sem combinar as duas opções.")
    if not categorias and not nenhuma:
        raise ValueError("Marque ao menos uma estratégia ou 'Nenhuma das categorias'.")
    if set(categorias) - CATEGORIAS.keys():
        raise ValueError("Há uma categoria que não pertence ao protocolo.")
    if not trecho.strip():
        if nenhuma:
            return
        raise ValueError("Preencha o trecho que justifica sua resposta.")
    # Cada linha pode ser uma passagem diferente do mesmo texto.
    texto_normalizado = " ".join(texto.casefold().split())
    for passagem in trecho.splitlines():
        if passagem.strip() and " ".join(passagem.casefold().split()) not in texto_normalizado:
            raise ValueError("Copie os trechos do texto apresentado, um por linha, sem acrescentar títulos ou comentários.")

