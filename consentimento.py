"""Texto e identificação da versão do termo apresentado antes da coleta."""
import hashlib
from datetime import datetime, timezone

VERSAO_TCLE = "2026-10-29.1"

TCLE = """# Termo de Consentimento Livre e Esclarecido

## Sobre a pesquisa

Você está sendo convidado(a) a participar do TCC de Wallace Luan da Cruz Guimarães e Vinicíus Yoshimitsu Aoki Alvez sobre estratégias de engenharia social em textos relacionados a golpes e fraudes digitais.

O objetivo desta atividade é reunir avaliações humanas para estudar como estratégias de persuasão aparecem nesses textos e apoiar as análises previstas no trabalho.

## Sua participação

Esta atividade é destinada a pessoas com 18 anos ou mais. Você informará seu nome e sua idade, lerá textos sorteados das bases GolpeBR, FraudWhatsApp.Br e FraudTelegram.Br e marcará as estratégias que identificar. Um texto pode receber mais de uma categoria. Ao marcar uma estratégia, será necessário copiar um trecho que justifique sua escolha. Se não identificar nenhuma das oito categorias, poderá selecionar essa opção sem preencher justificativa.

Não há quantidade obrigatória de textos nem duração fixa. Você poderá pular um texto ou encerrar sua participação quando quiser. Os textos vêm de bases de pesquisa e podem conter relatos, notícias e mensagens reais; não são situações fictícias criadas para a atividade. A presença de um registro na base não comprova que ele seja uma fraude.

## Dados registrados

Ao salvar uma anotação, serão registrados nome, idade, IP da conexão quando disponível, data e hora, identificadores da sessão e do texto, categorias escolhidas e justificativa. Também serão registrados a versão do termo, seu identificador de integridade e a data e hora do aceite.

As respostas são enviadas pelo servidor Streamlit à API da pesquisa e armazenadas no PostgreSQL hospedado no Render. Esta aplicação não envia suas respostas à OpenAI nem utiliza um assistente de inteligência artificial para responder por você. Não é solicitado e-mail do participante.

## Riscos e desconfortos

Os textos podem abordar ameaças, perdas financeiras, constrangimento e outras situações desagradáveis. Se algum conteúdo causar desconforto, você poderá pular o registro ou fechar a página. Não é necessário abrir links, contatar pessoas citadas ou executar ações descritas nos textos.

Por se tratar de uma atividade pela internet, existem riscos de falhas de conexão, interrupção do serviço e acesso indevido a informações. O acesso às respostas e às credenciais será restrito aos responsáveis pela pesquisa, sem promessa de ausência total de riscos.

## Participação voluntária

Sua participação é voluntária. Não haverá pagamento nem cobrança para participar. Eventuais custos de acesso à internet dependem da conexão que você utiliza. Você pode recusar o convite, pular textos ou interromper a atividade, sem precisar justificar e sem prejuízo por essa decisão.

Fechar a página interrompe a participação, mas não apaga respostas já enviadas. Para solicitar a retirada de suas respostas identificáveis ou esclarecer dúvidas, entre em contato com os pesquisadores pelo e-mail informado ao final deste termo.

## Confidencialidade

As respostas serão utilizadas nas análises do TCC. Nome, idade e IP não tornam a coleta anônima. Os resultados destinados à divulgação deverão ser apresentados sem expor os nomes, IPs ou outros identificadores diretos dos participantes. As respostas dos demais anotadores não são mostradas durante a atividade.

## Guarda do material

Os dados coletados ficarão sob a responsabilidade de Wallace Luan da Cruz Guimarães e Vinicíus Yoshimitsu Aoki Alvez pelo período de 12 meses após o término da pesquisa. Ao final desse período, caberá aos pesquisadores realizar o descarte do material identificável, inclusive das cópias sob sua guarda.

## Benefícios

Não são previstos benefícios diretos aos participantes. As avaliações poderão contribuir para a compreensão de estratégias de persuasão e para a organização dos dados utilizados no estudo de engenharia social em fraudes digitais.

## Em caso de problemas ou danos

Se ocorrer algum problema ou dano que você relacione à participação, comunique os pesquisadores pelo contato abaixo para que a situação seja avaliada. O aceite deste termo não representa renúncia aos seus direitos.

## Contato

Pesquisadores: Wallace Luan da Cruz Guimarães e Vinicíus Yoshimitsu Aoki Alvez.

E-mail para dúvidas e solicitações: wallace.guimaraes@discente.ufra.edu.br

Baixe uma cópia deste termo antes de iniciar e guarde-a para consultar os objetivos, as condições de participação e o contato dos pesquisadores.

## Consentimento

Ao marcar a declaração de aceite e clicar em “Concordo e quero participar”, você confirma ter 18 anos ou mais, ter lido as informações acima e concordar voluntariamente com a participação e o registro dos dados descritos. Caso não concorde, feche a página sem enviar o formulário.

Versão do termo: 2026-10-29.1.
"""

HASH_TCLE = hashlib.sha256(TCLE.encode("utf-8")).hexdigest()


def registrar_aceite(nome, idade, concordou):
    if not nome.strip() or len(nome.strip()) > 150:
        raise ValueError("Informe seu nome completo.")
    if not isinstance(idade, int) or isinstance(idade, bool) or not 18 <= idade <= 120:
        raise ValueError("A participação é destinada a pessoas com 18 anos ou mais.")
    if concordou is not True:
        raise ValueError("Para participar, leia o termo e marque a declaração de consentimento.")
    return {"consentimento": True, "consentimento_versao": VERSAO_TCLE,
            "consentimento_hash": HASH_TCLE, "consentimento_em": datetime.now(timezone.utc).isoformat()}
