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

## Como funciona

O participante informa nome e idade. A aplicação escolhe uma das três bases com a mesma chance e sorteia um registro ainda não apresentado naquela sessão. São usados todos os registros das versões das bases do TCC, inclusive os que a fonte não marcou como fraude. A amostragem não é uniforme sobre o total de textos: bases menores recebem proporcionalmente mais sorteios.

As oito estratégias são Urgência, Medo, Ameaça, Falsa autoridade, Promessa de vantagem, Escassez, Confiança e Vínculo emocional. É possível marcar várias ou escolher explicitamente `Nenhuma das categorias`. Essa opção representa ausência das oito estratégias, não dúvida. Para textos que não podem ser avaliados, use o botão de sortear outro; isso não grava um voto negativo.

O trecho é obrigatório quando houver alguma estratégia marcada e opcional ao escolher `Nenhuma das categorias`. Quando preenchido, deve ser copiado do registro apresentado. Podem ser usadas várias passagens, uma por linha, para justificar as categorias. O sistema verifica a presença dos trechos, mas a adequação das categorias depende da análise humana. A escolha e o texto permanecem na tela enquanto o formulário é preenchido. Ao salvar, é sorteado o próximo registro.

As respostas de outras pessoas e os rótulos originais de fraude não aparecem na tela. O sorteio livre não garante que dois participantes recebam os mesmos textos; para calcular concordância, use apenas registros efetivamente anotados por ambos, ou defina uma amostra compartilhada em uma próxima etapa.

## Arquivos

```text
app.py             tela da aplicação
categorias.py      categorias e validação da resposta
dados.py           leitura das fontes e sorteio
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

Cada anotação registra nome, idade, IP da conexão quando disponível, data/hora em UTC, identificação da sessão, ID e base do texto, hash do texto, categorias e trecho. Nome e IP são dados que podem identificar participantes. Não são coletados e-mail, senha, localização ou informações do sistema operacional. O IP vem do contexto do Streamlit, sem consultar serviços externos. Em acesso por localhost, ele pode estar ausente; atrás de intermediários, pode representar a conexão disponível ao servidor, não o IP privado do computador.

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

## Uso na pesquisa

Esta pasta contém a aplicação de coleta. A exportação preserva os votos individuais. Para preparar uma amostra final de treinamento, as respostas ainda precisam passar pela revisão e, quando houver pares, pela análise de concordância antes do consenso.
