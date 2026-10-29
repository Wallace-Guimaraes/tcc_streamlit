# Publicar a coleta na nuvem

O Streamlit mostra os textos. A FastAPI recebe as anotações e grava no PostgreSQL. O navegador não recebe a senha do banco nem a chave da API.

É possível manter a tela no Streamlit Community Cloud e publicar a API e o PostgreSQL no Render ou no Railway. O Docker também permite usar outro servidor. A hospedagem ainda não foi criada por este código.

## Alternativa: API e PostgreSQL no Render

O código atual funciona com o Render sem alterações na API:

1. Publique as alterações no GitHub e entre em [render.com](https://render.com).
2. Selecione **New → Postgres**, escolha uma região e crie o banco. Copie a **Internal Database URL** quando estiver disponível.
3. Selecione **New → Web Service**, conecte o repositório `wallace-guimaraes/tcc_streamlit` e escolha a mesma região do banco. Use o ambiente **Docker**, com `Dockerfile` na raiz. Não use a detecção Python com o `requirements.txt` da tela.
4. Nas variáveis do Web Service, adicione `DATABASE_URL` com a URL interna do banco e `CHAVE_API` com a chave gerada em `.env` por `python configurar.py`. Não use a senha do banco como chave da API.
5. Configure o caminho de verificação de saúde como `/saude`. Mantenha o comando padrão do Dockerfile: ele inicia FastAPI e utiliza a porta fornecida pela hospedagem.
6. Após a publicação, confira `https://SEU-SERVICO.onrender.com/saude`. A resposta esperada é `{"status":"ok"}`.
7. No Streamlit, em **Settings → Secrets**, configure:

```toml
URL_API = "https://SEU-SERVICO.onrender.com"
CHAVE_API = "A-MESMA-CHAVE-CONFIGURADA-NO-RENDER"
```

Salve e reinicie o Streamlit. Use somente o domínio da API em `URL_API`, sem acrescentar `/saude` ou `/anotacoes`.

O banco gratuito do Render expira após 30 dias e não oferece backups. Ele serve a testes temporários; para conservar a coleta por mais tempo, escolha um banco sem essa expiração ou um plano pago. A API gratuita suspende após 15 minutos sem tráfego e pode levar cerca de um minuto para voltar. Nesse caso, abra `/saude` e aguarde a resposta antes de iniciar a coleta. Uma falha de conexão mantém a anotação na tela para novo envio.

Documentação: [FastAPI no Render](https://render.com/docs/deploy-fastapi), [conexão interna do PostgreSQL](https://render.com/docs/postgresql-creating-connecting) e [limites gratuitos](https://render.com/docs/free).

## Opção com Railway

As etapas abaixo são para quem escolher Railway. Se utilizar Render, siga a seção anterior e depois a conferência da anotação na etapa 5.

## 1. Atualizar o GitHub

Publique os arquivos atualizados deste repositório. Não envie `.env`, `.streamlit/secrets.toml`, as respostas coletadas ou senhas. O `.gitignore` já exclui esses arquivos.

## 2. Criar o PostgreSQL no Railway

Entre em [railway.com](https://railway.com), crie um projeto e adicione um serviço de banco **PostgreSQL**. Confira se o serviço tem um volume de armazenamento associado. A conexão aparece entre as variáveis do banco como `DATABASE_URL`.

Essa URL é uma credencial: mantenha-a nas configurações do serviço. Não a publique no GitHub nem a envie aos participantes. Consulte os planos e o consumo na plataforma antes da coleta; este roteiro não pressupõe hospedagem gratuita.

## 3. Criar o serviço da API

No mesmo projeto, adicione um serviço a partir do repositório GitHub `wallace-guimaraes/tcc_streamlit`. Use a raiz do repositório. O `Dockerfile` termina na etapa da API, portanto o build padrão inicia FastAPI, não Streamlit. Ele usa Python 3.12 e instala `requirements_api.txt`.

Nas variáveis do serviço da API:

| Variável | Valor |
|---|---|
| `DATABASE_URL` | Adicione uma referência à variável `DATABASE_URL` do serviço PostgreSQL pela interface do Railway. |
| `CHAVE_API` | Uma chave aleatória que será usada somente pela API e pelo servidor Streamlit. |

Para gerar a chave no computador, execute `python configurar.py`. Esse comando cria `.env`, sem mostrar as credenciais no terminal. Copie somente o valor de `CHAVE_API` para os serviços. A senha `POSTGRES_PASSWORD` gerada nesse arquivo serve ao Docker local; o PostgreSQL criado no Railway tem suas próprias credenciais.

Nas configurações de rede da API, gere um domínio público HTTPS. O comando de inicialização lê a variável `PORT` fornecida pela hospedagem. Configure o caminho de verificação de saúde como `/saude`.

Ao abrir `https://SEU-DOMINIO-DA-API/saude`, a resposta esperada é:

```json
{"status": "ok"}
```

Esse caminho verifica a conexão com o PostgreSQL e não mostra as anotações. O envio usa `POST /anotacoes` com a chave no cabeçalho `X-API-Key`. Não há endpoint público que liste os dados dos participantes.

Na primeira anotação, a API carrega as versões das três fontes declaradas em `dados.py`. Como as bases não vão para o Git, o servidor precisa de acesso aos endereços públicos para baixá-las. A aplicação confere os hashes antes de usá-las.

## 4. Conectar o Streamlit

Na aplicação que já está no Streamlit Community Cloud, abra **Settings → Secrets** e informe, no nível principal do TOML:

```toml
URL_API = "https://SEU-DOMINIO-DA-API"
CHAVE_API = "A-MESMA-CHAVE-CONFIGURADA-NA-API"
```

Substitua os exemplos pelos valores reais. Não crie uma seção `[api]`, pois o aplicativo procura esses dois nomes no nível principal. Salve e reinicie a aplicação. A entrada do Streamlit continua sendo `app.py`, com as dependências de `requirements.txt`.

O Streamlit faz a chamada à API pelo servidor, não pelo navegador. Não é necessário liberar CORS para esse fluxo. Em produção, use o domínio HTTPS da API.

Ao publicar a versão com TCLE, inclua `consentimento.py` no Git e atualize a API e a tela. A inicialização da API adiciona as colunas de consentimento ao banco existente. Depois, reinicie o Streamlit e faça um novo aceite. As respostas antigas são mantidas sem receber aceite retroativo. A edição do termo exige atualizar os dois serviços para que versão e hash coincidam.

A versão `2026-10-29.2` substitui a coleta de idade por e-mail. Publique API e tela juntas: a API cria `email`, mantém idades antigas e aceita novas respostas com nome completo e e-mail. A maioridade permanece como declaração no termo.

O workflow `.github/workflows/manter-api.yml`, após publicado na branch padrão, faz uma verificação externa de saúde a cada cinco minutos. Acompanhe a execução na aba Actions do GitHub. Ele pode reduzir o tempo ocioso da API gratuita, mas não elimina limitações da hospedagem nem garante que o serviço nunca durma. Detalhes de ativação e limites estão no README.

Na versão com distribuição centralizada, inclua também `distribuicao.py`. Ao iniciar, a API carrega e confere as fontes, cria o catálogo completo em `registros_coleta` e a tabela `reservas_coleta`, preservando as anotações existentes. A tela solicita cada texto por `POST /sorteio`; o identificador da reserva é usado como identificador da resposta em `POST /anotacoes`. Atualize a API e a tela juntas e reinicie as sessões antigas. Formulários sorteados apenas no navegador, antes desta atualização, não possuem reserva válida para a nova API.

Se a API estiver indisponível, a resposta continua na tela e não é gravada em um SQLite alternativo. O mesmo identificador de anotação pode ser reenviado sem criar cópias.

## 5. Conferir uma anotação

Abra a tela, informe nome e idade e salve uma anotação. Na consulta ao PostgreSQL, confira a contagem:

```sql
SELECT COUNT(*) FROM anotacoes;
```

Para verificar múltiplas respostas do mesmo relato sem exibir os dados pessoais:

```sql
SELECT id_registro, COUNT(*) AS respostas
FROM anotacoes
GROUP BY id_registro
ORDER BY respostas DESC;
```

Cada linha é um voto individual. Participantes de sessões distintas podem avaliar o mesmo relato. A aplicação não calcula consenso automaticamente. Os dados antigos de um SQLite, se existirem, não são migrados automaticamente para PostgreSQL.

Configure os backups do banco pela hospedagem. Um volume conserva os dados entre reinícios, mas não substitui backup. A exportação e a administração ficam no acesso restrito ao PostgreSQL, não em uma rota aberta da aplicação.

## Executar os três serviços no computador

Com Docker e Docker Compose instalados:

```powershell
python configurar.py
docker compose up --build -d
```

Abra `http://localhost:8501`. A API usa `http://localhost:8000/saude`. O PostgreSQL não expõe uma porta pública nesse Compose. Seus dados ficam no volume `banco_postgres`.

`docker compose down` encerra os serviços sem apagar o volume. O parâmetro `-v` apaga o volume e as anotações; não o utilize para uma parada comum.

## Referências

- [PostgreSQL e variáveis de referência no Railway](https://docs.railway.com/guides/docker-compose)
- [Comandos de inicialização e variável PORT](https://docs.railway.com/deployments/start-command)
- [Secrets no Streamlit Community Cloud](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management)
