# Relatório de implementação e verificação

Data: **10/11/2026**, fuso America/Sao_Paulo. Repositório: `tcc_streamlit`, revisão de partida `e951738`. Alterações realizadas no clone local; sem publicação ou alteração do banco de produção.

## Escopo e diagnóstico

A solicitação foi implementar as melhorias do plano fornecido, corrigir a anonimização e atualizar os documentos do projeto. O plano foi usado como especificação das melhorias, preservando as restrições metodológicas e os dados existentes.

Já existiam as oito categorias e seus textos de ajuda, validação de evidência, escolha explícita de nenhuma categoria, sorteio centralizado, reservas de 30 minutos, limite de dez respostas, prevenção de duplicidade e tratamento de indisponibilidade da API sem desvio para SQLite. Havia testes unitários, HTTP com conexão simulada e integração PostgreSQL opcional.

Faltavam um guia reunido com exemplos fictícios e um comando administrativo agregado. A anonimização existia, mas foram reproduzidas falhas com apresentações em caixa alta/baixa, dois-pontos depois de “meu nome é”, e e-mails cuja parte anterior ao `@` parecia um domínio. Também foram cobertas diferenças de espaços na repetição dos nomes e links curtos ou com consulta sem protocolo.

## Mudanças entregues

### Guia de anotação — P0

O expander **Como realizar a anotação** fica antes do formulário e inicia recolhido. Inclui as oito categorias, exemplos inventados, cuidados de interpretação, uso de múltiplas categorias e evidências e distinção entre **Nenhuma das categorias** e **Pular texto**. Os textos de ajuda existentes foram mantidos. O guia não recebe mensagens, rótulos de origem ou respostas anteriores, nem acrescenta registros à coleta.

### Consulta administrativa — P0

`relatorio_coleta.py` consulta `registros_coleta` e `anotacoes` por um único `SELECT`, com `LEFT JOIN` e agregação total/por base. A conexão é colocada em modo somente leitura antes da consulta. O comando não importa a API, não inicia tabelas e não executa migrações.

São apresentados registros cadastrados, faixas de 0, 1–9 e 10 ou mais respostas, registros com respostas, respostas no catálogo, total efetivamente gravado e eventual diferença de respostas sem correspondência no catálogo. Essa diferença evita ocultar respostas históricas quando houver divergência cadastral. Todos os números vêm do mesmo retrato da consulta, com data/hora UTC de geração.

O script não lê nome, e-mail, IP, sessão, texto original, categorias ou evidência. Não foi criada rota pública, painel ou exportação individual. Mensagens de erro não imprimem a conexão ou o erro detalhado do driver. O Dockerfile inclui o script no estágio da API.

Execução, com `DATABASE_URL` fornecida pelo ambiente privado do pesquisador:

```powershell
.\.venv\Scripts\python.exe relatorio_coleta.py
```

Alternativa no Compose atualizado:

```powershell
docker compose exec api python relatorio_coleta.py
```

**Não foi gerado um retrato real da coleta nesta entrega:** não havia conexão PostgreSQL configurada. Os números das fixtures dos testes não representam participantes ou resultados coletados.

### Correção da anonimização

| Falha reproduzida com dado fictício | Comportamento corrigido |
|---|---|
| `nome.com@exemplo.org` virava `[LINK]@exemplo.org` | E-mails são tratados antes dos links e recebem `[EMAIL]` integralmente. |
| `Meu nome é maria da silva` permanecia visível | Apresentações reconhecem nomes em minúsculas. |
| `ME CHAMO JOAO DA SILVA` permanecia visível | Apresentações reconhecem nomes em caixa alta. |
| `Meu nome é: Maria da Silva` permanecia visível | Dois-pontos opcionais são aceitos nas apresentações. |
| Domínios curtos como `t.me/exemplo` e `bit.ly/oferta` não recebiam máscara | As terminações foram incluídas na lista de domínios reconhecidos. |
| Consulta ou fragmento de domínio sem protocolo podia permanecer | Caminho, consulta e fragmento são incluídos na máscara do link. |
| Nome com espaços diferentes na evidência podia escapar | A substituição reconhece diferenças de espaços, tabulações e quebras de linha. |

Os testes exercitam máscaras no sorteio HTTP, nos parâmetros de gravação de novas evidências e na tela. O hash continua associado ao texto original. Nome e e-mail dos participantes não são substituídos nos campos de identificação. As fontes e as respostas antigas não são reescritas.

**Limite:** são máscaras parciais por regex, com regras heurísticas para apresentações. Nomes fora desses padrões, capitalização mista, nomes divididos em linhas, apelidos, telefones, CPF, endereços e identificação pelo contexto podem permanecer. Há possibilidade de falsos positivos e negativos. A correção não comprova anonimização integral nem autoriza divulgar dados sem revisão humana.

### Testes de regressão — P0

Foram acrescentados cenários ausentes para as falhas de máscaras, proteção no sorteio e na gravação, validação antes de abrir a conexão, guia, indisponibilidade da API com preservação do formulário, pular sem voto e relatório administrativo. Foi acrescentado um teste opcional de integração do relatório ao conjunto PostgreSQL existente.

O teste antigo do formulário foi adaptado para submeter os campos em conjunto: no AppTest instalado, executar um `run()` isolado em um campo ainda não enviado descarta aquela alteração de formulário. O contexto de IP é simulado como ausente no teste que grava em SQLite temporário, evitando tentar persistir um objeto de teste. Nenhuma regra de produção foi alterada para fazer esses testes passarem.

## Evidência da execução

Ambiente: Windows, Python **3.12.10**, ambiente virtual `.venv`, Streamlit **1.66.1**, PyArrow **24.0.0**, FastAPI **0.162.0**, psycopg **3.3.6**, httpx **0.28.1**. As dependências de produção foram instaladas a partir dos arquivos existentes; o httpx foi instalado apenas para testes. Os arquivos de requisitos não foram modificados.

Comando final executado em 10/11/2026, aproximadamente **12h09 (UTC−03:00)**:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -p "testes_*.py" -v
```

Resultado: **50 testes descobertos; 47 passaram; 3 pulados; 0 falhas e 0 erros. Código de saída 0.** Tempo reportado pelo unittest: **1,859 s**.

| Grupo | Casos | Resultado e alcance |
|---|---:|---|
| Anonimização | 10 | Passaram; regex, preservação de contexto, repetição e idempotência nos exemplos testados. |
| API e cliente | 14 | Passaram; HTTP em processo e conexão PostgreSQL simulada, sem servidor de banco real. |
| Gravação, formulário e TCLE | 8 | Passaram; SQLite temporário, exemplos fictícios e AppTest. |
| Distribuição | 7 | Passaram; decisões de capacidade e comandos com conexão simulada. |
| Relatório agregado | 5 | Passaram; respostas simuladas, totais, catálogo vazio e proteção das mensagens de erro. |
| Tela | 3 | Passaram; guia, máscaras, falha da API e pular, com API simulada. |
| PostgreSQL real | 3 | Pulados: `TEST_DATABASE_URL` não configurada. |

Saída preservada em [docs/testes_2026-11-10.txt](docs/testes_2026-11-10.txt). O unittest escreve no fluxo de erro padrão; a captura do PowerShell acrescenta `NativeCommandError` ao início do arquivo por esse motivo. O resultado efetivo da suíte é o resumo `OK (skipped=3)` ao final, com código de saída 0. Não se trata de uma falha de teste omitida.

O ambiente também emitiu aviso de depreciação do uso de httpx pelo TestClient da Starlette e avisos `missing ScriptRunContext` do AppTest. Foram mantidos no registro. Não impediram a execução. A eventual adaptação do cliente de testes pode ser tratada quando as dependências forem revisadas.

`git diff --check` foi executado sem apontar erros. A revisão do diff confirmou que `dados.py`, `categorias.py`, `api.py`, `distribuicao.py`, `consentimento.py` e os requisitos permaneceram sem alterações. Os CSVs não estavam presentes no clone e não foram baixados nem modificados durante esta implementação.

## Arquivos alterados e novos

| Arquivo | Alteração |
|---|---|
| `app.py` | Guia recolhido de anotação. |
| `anonimizacao.py` | Ordem de máscaras, padrões de nomes, links e espaços. |
| `relatorio_coleta.py` (novo) | Consulta administrativa agregada, somente leitura. |
| `Dockerfile` | Inclusão do script administrativo na imagem da API. |
| `testes_anonimizacao.py`, `testes_api.py` | Regressões de máscaras e validação. |
| `testes_app.py` | Adequação da simulação de formulário/IP e asserções de preservação. |
| `testes_distribuicao.py` | Pular libera a reserva antes do novo sorteio, sem gravar voto. |
| `testes_postgres.py` | Integração opcional da consulta de cobertura. |
| `testes_relatorio.py`, `testes_tela.py` (novos) | Consulta privada e fluxos da interface. |
| `README.md` | Guia, máscaras e limites, comandos completos, consulta agregada e correção sobre CSVs ausentes no clone. |
| `NUVEM.md` | Publicação das mudanças, homologação, nome/e-mail e carregamento das bases na inicialização. |
| `RELATORIO_MELHORIAS.md` e `docs/testes_2026-11-10.txt` (novos) | Relatório da entrega e evidência da execução. |

## Preservações, limites e pendências

Não foram modificados esquema PostgreSQL, contratos HTTP, estrutura dos votos, categorias, validação das categorias, TCLE, limite de dez, reservas de 30 minutos, sorteio, controle de sessão ou hashes de referência. Não foram adicionados IA, sugestão de categorias, consenso, votação majoritária ou cálculo de concordância.

Permanecem pendentes de ambiente apropriado:

- Executar os três testes de PostgreSQL em um banco exclusivo de testes, incluindo concorrência e SQL real do relatório. Os testes simulados não comprovam essa integração.
- Consultar o banco restrito da coleta para obter indicadores reais; nenhum valor foi estimado nesta entrega.
- Revisar visualmente computador/celular e homologar Streamlit, API e PostgreSQL juntos, usando dados fictícios. AppTest não é uma captura real em navegador.
- Publicar API e tela atualizadas e iniciar nova sessão para a conferência das máscaras. Não houve push ou deploy.
- Revisar manualmente qualquer material histórico antes de divulgação, pois as correções não tratam retroativamente evidências já gravadas.

O manifesto opcional P1 não foi criado: `dados.py` já mantém fonte e SHA-256 esperados, e o README documenta as contagens de referência. Sem os CSVs locais, não houve uma nova verificação do corpus que justificasse acrescentar uma data de conferência. Não foi alterado nenhum hash para contornar essa ausência.

## Ajustes correspondentes na redação do TCC

O texto completo do TCC não está neste repositório. Portanto, foram atualizados os documentos técnicos disponíveis e ficam as orientações abaixo para incorporar à redação acadêmica:

- **Capítulo 4 — Métodos:** mencionar o guia como apoio ao protocolo humano, os critérios de evidência e a distinção entre ausência de categorias e impossibilidade de avaliar. Descrever cobertura calculada a partir do catálogo completo, incluindo zero respostas. Identificar a proteção como mascaramento parcial por regras, sujeito a revisão humana.
- **Capítulo 5 — Desenvolvimento:** descrever o guia recolhido, a consulta administrativa privada e a correção das máscaras na saída do sorteio e nas novas justificativas. Acrescentar captura real da aplicação somente depois da homologação; nenhuma imagem ilustrativa foi apresentada como captura do sistema.
- **Capítulo 6 — Resultados:** podem ser relatados os 47 testes aprovados e os três de integração não executados, com data e ambiente. Os números de cobertura devem vir de uma execução efetiva do relatório no banco restrito. Não interpretar sessões como pessoas distintas, cobertura como concordância ou máscaras como garantia de anonimização integral.

A implementação local e a documentação foram entregues; publicação, revisão visual e integração PostgreSQL real continuam explicitamente pendentes.

## Complemento — menções com @ (10/11/2026)

Após a primeira entrega, o commit `5c2b67b` foi enviado à branch `main` do GitHub a pedido do usuário. Esse envio não comprova deploy ou homologação dos serviços. O registro de 50 testes acima corresponde àquela implementação inicial.

Foi acrescentada a regra de menções a perfis e bots: `@bottelegram`, `@BOT_123`, `@maria.silva` e `@perfil-teste` passam a receber **`[USUARIO]`**, sem exigir apresentação como nome de pessoa. São aceitos letras, números, sublinhado e pontos ou hífens internos; a pontuação ao final da frase é preservada. E-mails e URLs são mascarados antes das menções, mantendo `[EMAIL]` e `[LINK]`. Um `@` isolado permanece no texto. A regra não consulta plataformas externas nem verifica se o perfil existe.

A função compartilhada protege a saída de sorteio da API, a exibição na tela e as novas evidências, preservando o texto e o SHA-256 de origem e a identificação dos participantes. Evidências com o identificador original ou com a máscara continuam válidas; um identificador inventado é recusado. As respostas históricas não são reescritas.

Arquivos deste complemento: `anonimizacao.py`, `testes_anonimizacao.py`, `testes_api.py`, `testes_tela.py`, `README.md`, `NUVEM.md` e este relatório. Foram adicionados três testes unitários e um teste HTTP com banco simulado, e o cenário de tela existente passou a incluir uma menção fictícia. A documentação descreve o novo marcador e a necessidade de atualizar a função tanto na API quanto no Streamlit.

Validação executada em **10/11/2026, aproximadamente 12h26 (UTC−03:00)**, no mesmo ambiente descrito anteriormente:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -p "testes_*.py" -v
```

Resultado observado: **54 testes descobertos; 51 aprovados; 3 pulados; nenhuma falha ou erro; código de saída 0**, em **1,995 s**. Os três testes de integração PostgreSQL permaneceram pulados por ausência de `TEST_DATABASE_URL`; API e tela usam simulações, sem verificar gravação em PostgreSQL real. Os avisos de depreciação do TestClient e de contexto do AppTest continuam presentes. O arquivo `docs/testes_2026-11-10.txt` preserva a execução anterior, de 50 casos, e não foi sobrescrito por este complemento.

A proteção continua parcial e baseada em regex; os demais limites e a necessidade de revisão humana permanecem. Este complemento foi implementado e testado localmente, sem novo commit, push ou deploy.
