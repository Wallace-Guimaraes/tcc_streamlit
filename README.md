# Anotação de estratégias de persuasão

Aplicação do TCC de Wallace e Vinicius para anotar textos de GolpeBR, FraudWhatsApp.Br e FraudTelegram.Br. A tela usa Streamlit, a API usa FastAPI e as novas respostas ficam no PostgreSQL. Os três componentes estão no mesmo repositório.

Para publicar na nuvem, siga [NUVEM.md](NUVEM.md). O roteiro mantém a tela no Streamlit Community Cloud e apresenta Render ou Railway para hospedar API e banco.

## Executar

Com Docker e Docker Compose instalados, abra o PowerShell na pasta do projeto:

```powershell
python configurar.py
docker compose up --build -d
```

Abra `http://localhost:8501`. O PostgreSQL fica em um volume separado dos contêineres. Para encerrar sem apagar as respostas, use `docker compose down`, sem `-v`.

Para executar apenas a tela com uma API que já esteja publicada, configure `URL_API` e `CHAVE_API` nas variáveis de ambiente ou nos Secrets do Streamlit. Depois:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Abra o endereço mostrado no terminal, normalmente `http://localhost:8501`.

O formulário usa duas colunas no computador: texto à esquerda e resposta à direita. Textos longos têm rolagem dentro do próprio campo. As explicações das categorias ficam nos ícones de ajuda. Para alternar entre claro e escuro, abra o menu `⋮` no canto superior direito e escolha o tema. A interface também acompanha a preferência de tema do sistema.

Antes do formulário, a aplicação apresenta o Termo de Consentimento Livre e Esclarecido, com cópia para download. A pessoa precisa informar nome completo e e-mail e marcar a declaração de maioridade e aceite. Não é solicitada idade. O texto e sua versão estão em `consentimento.py`. Os responsáveis são Wallace Luan da Cruz Guimarães e Vinicíus Yoshimitsu Aoki Alvez, pelo contato `wallace.guimaraes@discente.ufra.edu.br`.

O termo prevê a guarda dos dados por 5 (cinco) anos após o término da pesquisa, sob responsabilidade dos pesquisadores. O código não executa descarte automático. Cabe aos pesquisadores manter os backups e realizar o descarte ao final desse prazo, conforme o termo e o protocolo da pesquisa.

Publique as alterações da API e da tela juntas. Na inicialização, a API adiciona as colunas de consentimento ao PostgreSQL sem apagar linhas existentes. Respostas antigas ficam com esses campos nulos; não recebem aceite retroativo. Novas respostas exigem aceite, versão, hash e data/hora do termo. Ao alterar o conteúdo do termo, atualize também sua versão e publique os dois serviços.

## Como funciona

Após o consentimento, o Streamlit solicita um registro à API. O sorteio considera as três bases juntas e dá prioridade ao menor número de respostas mais reservas ativas. Entre registros com a mesma ocupação, vêm primeiro os que têm menos respostas efetivamente salvas; empates são resolvidos aleatoriamente. Assim, os registros sem avaliações e sem reservas são oferecidos antes daqueles que já receberam uma vaga. Não há mais uma escolha de base com probabilidade igual.

Cada registro tem até dez respostas pela API. A distribuição e a gravação usam a mesma trava de transação PostgreSQL (`pg_advisory_xact_lock`), com isolamento READ COMMITTED: o limite é conferido dentro da transação que insere a resposta, e não somente no sorteio. Registros que já tinham dez ou mais respostas antes da atualização deixam de receber novas avaliações. As respostas antigas não são apagadas.

A API mantém uma reserva de 30 minutos por sessão. Reabrir o formulário conserva a reserva válida. Ao salvar ou pular, a sessão libera sua vaga. Quando a reserva expira, deixa de contar na ocupação e outra pessoa pode usar a vaga. Uma resposta atrasada ainda pode ser aceita se sua reserva não foi trocada e houver capacidade livre; caso contrário, o sistema informa o conflito e conserva o formulário. O backend impede a mesma sessão de responder novamente ao mesmo registro.

Todos os 7.412 registros são cadastrados na fila, inclusive os que ainda têm zero respostas. São usados todos os textos das fontes, inclusive os que não foram rotulados como fraude. O limite representa respostas por ID, não dez pessoas autenticadas nem dez famílias de textos distintas. Sessões diferentes podem pertencer à mesma pessoa, pois não há autenticação individual.

Cobertura depende de participação suficiente: uma avaliação por registro exige pelo menos 7.412 respostas salvas; a meta de dez por registro exige 74.120 no total. Pular ou abandonar textos não cria respostas artificiais. A coleta termina quando todos os registros têm pelo menos dez avaliações; falta de textos para uma sessão não é apresentada como conclusão global.

As oito estratégias são Urgência, Medo, Ameaça, Falsa autoridade, Promessa de vantagem, Escassez, Confiança e Vínculo emocional. É possível marcar várias ou escolher explicitamente `Nenhuma das categorias`. Essa opção representa ausência das oito estratégias, não dúvida. Para textos que não podem ser avaliados, use o botão de sortear outro; isso não grava um voto negativo.

O trecho é obrigatório quando houver alguma estratégia marcada e opcional ao escolher `Nenhuma das categorias`. Quando preenchido, deve ser copiado do registro apresentado. Podem ser usadas várias passagens, uma por linha, para justificar as categorias. O sistema verifica a presença dos trechos, mas a adequação das categorias depende da análise humana. A escolha e o texto permanecem na tela enquanto o formulário é preenchido. Ao salvar, é sorteado o próximo registro.

As respostas de outras pessoas e os rótulos originais de fraude não aparecem na tela. O sorteio livre não garante que dois participantes recebam os mesmos textos; para calcular concordância, use apenas registros efetivamente anotados por ambos, ou defina uma amostra compartilhada em uma próxima etapa.

## Arquivos

```text
app.py             tela da aplicação
categorias.py      categorias e validação da resposta
dados.py           leitura e conferência das fontes
distribuicao.py    fila, reservas e limite de respostas no PostgreSQL
banco.py           envio para a API e acesso ao SQLite antigo
cliente_api.py     cliente HTTP usado pelo servidor Streamlit
api.py             validação e gravação no PostgreSQL
compose.yaml       execução dos três serviços com Docker
NUVEM.md           publicação e configuração dos serviços
testes_app.py      testes da gravação e do formulário
requirements.txt   dependências
bases/             cópias locais dos CSVs de origem (fora do Git)
armazenamento/     arquivos antigos do modo SQLite (fora do Git)
```

Na primeira execução, as bases são baixadas dos endereços públicos declarados em `dados.py`. Os hashes SHA-256 conferem a versão usada no TCC. Se a fonte mudar, a aplicação interrompe o carregamento. Também é possível copiar `golpebr.csv`, `whatsapp.csv` e `telegram.csv` do projeto do TCC para `bases/`.

Neste repositório, as três bases foram copiadas para `bases/`: 557 registros do GolpeBR, 2.640 do WhatsApp e 4.215 do Telegram, totalizando 7.412. Elas são usadas localmente e não precisam ser baixadas outra vez. Como `bases/` não vai para o Git, em um novo servidor será necessário copiar esses arquivos ou permitir o download das versões conferidas.

## Respostas coletadas

Cada nova anotação registra nome completo, e-mail, IP da conexão quando disponível, data/hora em UTC, identificação da sessão, ID e base do texto, hash do texto, categorias e trecho. Nome, e-mail e IP podem identificar participantes. Não são coletados idade, senha, localização ou informações do sistema operacional. O IP vem do contexto do Streamlit, sem consultar serviços externos. Em acesso por localhost, ele pode estar ausente; atrás de intermediários, pode representar a conexão disponível ao servidor, não o IP privado do computador.

Na atualização para nome e e-mail, a API acrescenta a coluna `email` e deixa de exigir a coluna antiga `idade`. As idades das respostas anteriores são preservadas como histórico, e novas respostas não preenchem esse campo. O TCLE passa à versão `2026-10-29.2`, exigindo um novo aceite. O e-mail recebe validação de formato, sem enviar mensagens nem confirmar a titularidade do endereço.

## Job de disponibilidade

O workflow `.github/workflows/manter-api.yml` consulta `/saude` a cada cinco minutos, em um runner do GitHub Actions. Também permite execução manual. Ele não usa a chave da API nem consulta respostas dos participantes; verifica apenas se a API e a conexão do banco respondem.

Para ativar, publique o workflow na branch padrão (`main`) e confira a aba **Actions → Verificar disponibilidade da API**. Use **Run workflow** para a primeira execução manual. O agendamento não funciona apenas com o arquivo no computador. Se mudar o domínio, defina a variável de repositório `API_HEALTH_URL` com a URL completa de `/saude`.

Chamadas regulares podem reduzir a suspensão por inatividade do Render, mas não garantem disponibilidade contínua. O GitHub pode atrasar ou descartar execuções agendadas e desativar o cron de um repositório público após 60 dias sem atividade. O job também não impede manutenção, limites de plano ou expiração do PostgreSQL gratuito. Serviços sem suspensão por inatividade são a opção para disponibilidade contínua.

Referências: [agendamentos no GitHub Actions](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule) e [limites gratuitos do Render](https://render.com/docs/free).

No PostgreSQL, as novas respostas também registram `consentimento`, `consentimento_versao`, `consentimento_hash` e `consentimento_em`. O aceite é associado à sessão e enviado junto de cada anotação. Preencher a tela inicial sem enviar anotações não cria, por si só, uma linha no banco.

As novas respostas ficam na tabela `anotacoes` do PostgreSQL. O Streamlit envia os dados à API usando uma chave configurada apenas no servidor. Não há uma rota pública de consulta das respostas. O nome informado identifica a resposta, mas não é uma autenticação. Recarregar ou encerrar a sessão pode exigir nova identificação; as respostas já gravadas permanecem no banco.

Quando a API está indisponível, a aplicação informa a falha e mantém a resposta na tela. Ela não desvia silenciosamente os dados para um SQLite local. Cada relato pode receber respostas de várias sessões, e reenvios da mesma anotação não criam cópias.

## Arquivos antigos do SQLite

Se houver respostas coletadas na versão anterior, o arquivo `armazenamento/anotacoes.sqlite3` continua preservado. Para exportar esse arquivo local, em um ambiente sem `URL_API` configurada:

```powershell
.\.venv\Scripts\python.exe banco.py
```

O CSV antigo será salvo em `armazenamento/anotacoes.csv`. Ele reúne texto original, estratégias, trecho e dados do anotador. Não há migração automática desse arquivo para PostgreSQL. A administração e os backups da coleta nova ficam no servidor PostgreSQL. Banco, exportações, bases e segredos ficam fora do Git.

Cada linha corresponde a uma anotação individual. O mesmo relato pode aparecer várias vezes, com respostas de pessoas diferentes. Uma nova resposta não substitui as anteriores, e o sistema não transforma as avaliações em consenso automaticamente. A restrição de duplicidade evita apenas repetir o envio do mesmo relato na mesma sessão.

## Git e hospedagem

O repositório contém o código da tela e da gravação. Publique os arquivos do projeto, mantendo os dados coletados fora do Git.

No Community Cloud, selecione este repositório, a branch publicada e `app.py` como entrada. Após atualizar as dependências ou a configuração, reinicie a aplicação pela opção `Reboot app`. O projeto fixa Streamlit em `1.66.1` e PyArrow em `24.0.0`, alinhado ao ajuste de compatibilidade indicado nos logs da hospedagem. A vigilância de arquivos está desligada para evitar recargas de módulos durante a execução; ao editar código localmente, reinicie o servidor.

Todas as instâncias do Streamlit devem usar a mesma `URL_API`. A API deve apontar para o mesmo PostgreSQL por `DATABASE_URL`. Isso centraliza a coleta mesmo quando a tela e o banco estão hospedados em serviços diferentes.

`CHAVE_API` deve ter o mesmo valor no servidor Streamlit e na API. Senhas ficam nas configurações privadas da hospedagem. O banco PostgreSQL precisa de volume e backup. `PASTA_BASES` permite alterar o local das fontes; `BANCO_ANOTACOES` só se aplica aos arquivos antigos do SQLite.

Referências: [contexto e IP no Streamlit](https://docs.streamlit.io/develop/api-reference/caching-and-state/st.context) e [persistência de arquivos locais](https://docs.streamlit.io/develop/concepts/connections/connecting-to-data).

## Testar

```powershell
.\.venv\Scripts\python.exe -m unittest testes_app -v
```

Para testar as rotas da API e o tratamento de falhas de conexão:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements_api.txt httpx
.\.venv\Scripts\python.exe -m unittest testes_api -v
```

Os testes HTTP substituem a conexão PostgreSQL por um objeto de teste. Eles não substituem a conferência com um PostgreSQL real após subir os serviços, descrita em `NUVEM.md`.

Os testes específicos da distribuição ficam em `testes_distribuicao.py`. Para executar a integração real de concorrência, use um PostgreSQL separado e configure `TEST_DATABASE_URL` antes de rodar `python -m unittest testes_postgres -v`. Esse teste cria e remove somente um schema temporário `teste_coleta_*`, sem usar `public.anotacoes`. Ele verifica cobertura inicial, preenchimento por participantes simultâneos, limite de dez, reenvio e reaproveitamento de vagas expiradas. Não use a conexão de produção para os testes.

### Conferir o andamento no DBeaver

Depois de atualizar o backend, a consulta abaixo inclui também registros sem respostas:

```sql
SELECT r.id_registro, r.base_origem,
       COUNT(a.id) AS respostas,
       GREATEST(10 - COUNT(a.id), 0) AS faltam
FROM registros_coleta r
LEFT JOIN anotacoes a USING (id_registro)
GROUP BY r.id_registro, r.base_origem
ORDER BY respostas, r.id_registro;
```

As reservas ficam em `reservas_coleta` e não são votos. Elas contêm somente identificadores técnicos e prazo. [Referência das travas de transação PostgreSQL](https://www.postgresql.org/docs/current/functions-admin.html#FUNCTIONS-ADVISORY-LOCKS).

## Uso na pesquisa

Esta pasta contém a aplicação de coleta. A exportação preserva os votos individuais. Para preparar uma amostra final de treinamento, as respostas ainda precisam passar pela revisão e, quando houver pares, pela análise de concordância antes do consenso.
