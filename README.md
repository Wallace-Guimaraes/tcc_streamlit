# Anotação de estratégias de persuasão

Aplicação do TCC de Wallace e Vinicius para anotar textos de GolpeBR, FraudWhatsApp.Br e FraudTelegram.Br. A tela e a gravação das respostas ficam no mesmo projeto, usando Streamlit e SQLite.

## Executar

Use Python 3.11 ou superior. No PowerShell, dentro da pasta do projeto:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Abra o endereço mostrado no terminal, normalmente `http://localhost:8501`.

## Como funciona

O participante informa nome e idade. A aplicação escolhe uma das três bases com a mesma chance e sorteia um registro ainda não apresentado naquela sessão. São usados todos os registros das versões das bases do TCC, inclusive os que a fonte não marcou como fraude. A amostragem não é uniforme sobre o total de textos: bases menores recebem proporcionalmente mais sorteios.

As oito estratégias são Urgência, Medo, Ameaça, Falsa autoridade, Promessa de vantagem, Escassez, Confiança e Vínculo emocional. É possível marcar várias ou escolher explicitamente `Nenhuma das categorias`. Essa opção representa ausência das oito estratégias, não dúvida. Para textos que não podem ser avaliados, use o botão de sortear outro; isso não grava um voto negativo.

O trecho é obrigatório e deve ser copiado do registro apresentado. Podem ser usadas várias passagens, uma por linha, para justificar as categorias. O sistema verifica a presença dos trechos, mas a adequação das categorias depende da análise humana. A escolha e o texto permanecem na tela enquanto o formulário é preenchido. Ao salvar, é sorteado o próximo registro.

As respostas de outras pessoas e os rótulos originais de fraude não aparecem na tela. O sorteio livre não garante que dois participantes recebam os mesmos textos; para calcular concordância, use apenas registros efetivamente anotados por ambos, ou defina uma amostra compartilhada em uma próxima etapa.

## Arquivos

```text
app.py             tela da aplicação
categorias.py      categorias e validação da resposta
dados.py           leitura das fontes e sorteio
banco.py           gravação e exportação
testes_app.py      testes da gravação e do formulário
requirements.txt   dependências
bases/             cópias locais dos CSVs de origem (fora do Git)
armazenamento/     banco e exportação das respostas (fora do Git)
```

Na primeira execução, as bases são baixadas dos endereços públicos declarados em `dados.py`. Os hashes SHA-256 conferem a versão usada no TCC. Se a fonte mudar, a aplicação interrompe o carregamento. Também é possível copiar `golpebr.csv`, `whatsapp.csv` e `telegram.csv` do projeto do TCC para `bases/`.

Neste repositório, as três bases foram copiadas para `bases/`: 557 registros do GolpeBR, 2.640 do WhatsApp e 4.215 do Telegram, totalizando 7.412. Elas são usadas localmente e não precisam ser baixadas outra vez. Como `bases/` não vai para o Git, em um novo servidor será necessário copiar esses arquivos ou permitir o download das versões conferidas.

## Respostas coletadas

Cada anotação registra nome, idade, IP da conexão quando disponível, data/hora em UTC, identificação da sessão, ID e base do texto, hash do texto, categorias e trecho. Nome e IP são dados que podem identificar participantes. Não são coletados e-mail, senha, localização ou informações do sistema operacional. O IP vem do contexto do Streamlit, sem consultar serviços externos. Em acesso por localhost, ele pode estar ausente; atrás de intermediários, pode representar a conexão disponível ao servidor, não o IP privado do computador.

Os dados ficam em `armazenamento/anotacoes.sqlite3`, sem uma tela pública de consulta ou download. O nome informado identifica a resposta, mas não é uma autenticação. Recarregar ou encerrar a sessão pode exigir nova identificação; as respostas já gravadas permanecem no banco.

Para exportar no computador ou servidor responsável pela coleta:

```powershell
.\.venv\Scripts\python.exe banco.py
```

O CSV será salvo em `armazenamento/anotacoes.csv`. As categorias são uma lista JSON; uma lista vazia indica a escolha explícita de nenhuma categoria. Banco, exportações, bases e segredos são ignorados pelo Git. O texto completo não é duplicado na tabela de respostas; ele pode ser recuperado pelo ID e conferido pelo hash na versão congelada da fonte.

## Git e hospedagem

O repositório contém o código da tela e da gravação. Publique os arquivos do projeto, mantendo os dados coletados fora do Git.

Esta versão usa SQLite em disco. Para coletar respostas em uma hospedagem, utilize armazenamento persistente e mantenha uma cópia do banco. No Streamlit Community Cloud, arquivos locais não têm persistência garantida; subir somente este código nessa plataforma não garante a conservação das anotações. O caminho do banco pode ser definido pela variável `BANCO_ANOTACOES`, apontando para um disco persistente. `PASTA_BASES` permite definir onde ficam as fontes.

Referências: [contexto e IP no Streamlit](https://docs.streamlit.io/develop/api-reference/caching-and-state/st.context) e [persistência de arquivos locais](https://docs.streamlit.io/develop/concepts/connections/connecting-to-data).

## Testar

```powershell
.\.venv\Scripts\python.exe -m unittest testes_app -v
```

## Experimentos do TCC

Os arquivos de integração, anotações e modelagem que já estavam nesta pasta foram mantidos. As instruções anteriores estão em `README_TCC.md`. O comando `python tcc.py testar` continua verificando os experimentos; os testes da tela ficam em `testes_app.py`. A aplicação ainda não converte automaticamente as respostas coletadas em uma amostra final de treinamento: os votos precisam passar pela revisão e, quando houver pares, pela análise de concordância antes do consenso.
