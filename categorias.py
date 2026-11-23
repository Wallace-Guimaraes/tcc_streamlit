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


def validar_anotacao(texto, categorias, evidencias, nenhuma=False):
    if isinstance(evidencias, str):
        evidencias = {categorias[0]: evidencias} if len(categorias) == 1 else {}
    if not isinstance(evidencias, dict):
        raise ValueError("Associe uma evidência a cada categoria selecionada.")
    if nenhuma and categorias:
        raise ValueError("Escolha as estratégias ou marque 'Nenhuma das categorias', sem combinar as duas opções.")
    if not categorias and not nenhuma:
        raise ValueError("Marque ao menos uma estratégia ou 'Nenhuma das categorias'.")
    if set(categorias) - CATEGORIAS.keys():
        raise ValueError("Há uma categoria que não pertence ao protocolo.")
    if nenhuma:
        if evidencias:
            raise ValueError("Não informe evidências ao marcar 'Nenhuma das categorias'.")
        return
    if set(evidencias) != set(categorias):
        raise ValueError("Preencha uma evidência para cada categoria selecionada.")
    if any(not isinstance(trecho, str) or len(trecho) > 100000 for trecho in evidencias.values()):
        raise ValueError("Cada evidência deve ter até 100.000 caracteres.")
    texto_normalizado = " ".join(texto.casefold().split())
    for categoria, trecho in evidencias.items():
        if not isinstance(trecho, str) or not trecho.strip():
            raise ValueError(f"Preencha a evidência da categoria {categoria}.")
        for passagem in trecho.splitlines():
            if passagem.strip() and " ".join(passagem.casefold().split()) not in texto_normalizado:
                raise ValueError(f"Copie as evidências de {categoria} do texto apresentado, uma passagem por linha.")

