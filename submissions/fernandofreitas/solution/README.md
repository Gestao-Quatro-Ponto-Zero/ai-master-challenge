# Solution - Challenge 002

Esta pasta contem a solucao para o Challenge 002: um Support Copilot com assistente para defletir tickets, abertura inteligente, painel admin e loop de aprendizado com resolucoes humanas.

## Entregaveis

- `flask_app.py`: app principal com front customizado, autenticacao, assistente IA/RAG, botao de abrir ticket, painel admin e base de conhecimento.
- `docs/operational-diagnosis.md`: analise dos gargalos, satisfacao, backlog e desperdicio recuperavel.
- `docs/automation-blueprint.md`: desenho do fluxo de automacao, regras de decisao e limites.
- `requirements.txt`: dependencias para rodar localmente.

## Como rodar

Instale as dependencias:

```powershell
pip install -r submissions\fernandofreitas\solution\requirements.txt
```

Inicie o app:

```powershell
python submissions\fernandofreitas\solution\flask_app.py
```

Ou:

```powershell
submissions\fernandofreitas\solution\run_flask.ps1
```

O app Flask abrira em `http://localhost:5000`.

## Autenticacao

O app usa autenticacao simples por senha para acelerar o deploy.

Configure variaveis de ambiente ou secrets:

```text
CLIENT_PASSWORD=troque-esta-senha
ADMIN_PASSWORD=troque-esta-senha
OPENAI_API_KEY=sua-chave-openai
OPENAI_MODEL=gpt-4.1-mini
SUPPORT_DATA_DIR=C:\Users\Jufer\Downloads\datasets g4
```

Sem configuracao, os apps usam senhas demo:

```text
Cliente: cliente123
Admin: admin123
```

Troque essas senhas antes de subir publicamente.

## Como subir no Render

Opcao recomendada para publicar rapido.

1. Suba este repositorio para o GitHub.
2. Acesse `https://render.com`.
3. Crie um novo **Web Service**.
4. Conecte o repositorio do GitHub.
5. Configure:

```text
Root Directory: submissions/fernandofreitas/solution
Build Command: pip install -r requirements.txt
Start Command: gunicorn flask_app:app
```

6. Em **Environment Variables**, configure:

```text
FLASK_SECRET_KEY=gere-uma-string-grande-aleatoria
CLIENT_PASSWORD=senha-para-cliente
ADMIN_PASSWORD=senha-para-admin
OPENAI_API_KEY=sua-chave-openai
OPENAI_MODEL=gpt-4.1-mini
```

7. Clique em **Deploy**.

Arquivos ja preparados para deploy:

- `Procfile`
- `render.yaml`
- `requirements.txt`
- `flask_app.py`

Observacao: o SQLite local (`support_copilot.db`) e criado automaticamente em runtime. Para demo, isso basta. Em producao, eu trocaria por Postgres/Supabase para persistir dados entre deploys.

## Arquivos que nao precisam subir

Nao inclua no commit:

- `__pycache__/`
- `support_copilot.db`
- qualquer arquivo com chave/token

## Dados

O prototipo baixa os datasets publicos via `kagglehub`:

- `suraj520/customer-support-ticket-dataset`
- `adisongoh/it-service-ticket-classification-dataset`

Os dados ficam no cache local do KaggleHub e nao sao versionados no repositorio.

Tambem e possivel usar os CSVs locais configurando:

```text
SUPPORT_DATA_DIR=C:\Users\Jufer\Downloads\datasets g4
```

## Guardrails de custo e seguranca

Para evitar abuso de token e reduzir risco de prompt injection, o app implementa:

- limite de caracteres por input;
- limite de chamadas de IA por sessao;
- limite de tokens de resposta na chamada da OpenAI;
- bloqueio simples de padroes suspeitos, como tentativa de revelar prompt, token ou instrucoes;
- resposta baseada somente em FAQ/casos similares;
- fallback local quando nao ha chave OpenAI;
- escalacao humana para casos criticos, refund, cancelamento, perda de dados, baixa confianca ou ambiguidade.

## Logica de scoring e automacao

O classificador usa TF-IDF + regressao logistica treinada no Dataset 2. Em validacao holdout de 20%, o modelo obteve:

- Accuracy: 86,5%
- Macro F1: 86,6%

As regras operacionais sao:

- Ticket `Critical`: escalar para humano.
- Confianca >= 80% e tipo Product/Billing/Technical: auto-rotear com resposta sugerida.
- Confianca >= 60%: revisao rapida do agente.
- Confianca < 60%: triagem humana.

## Loop de aprendizado

Quando um ticket novo e resolvido pelo admin no prototipo, a resolucao e salva em uma base SQLite local (`support_copilot.db`) e passa a ser recuperada pelo assistente em perguntas futuras.

Isso demonstra uma base de conhecimento retroalimentada por resolucoes humanas. Em producao, esse fluxo exigiria revisao, avaliacao de qualidade e retreinamento controlado.

## Limitacoes

- O Dataset 1 baixado tem 8.469 tickets, abaixo dos ~30.000 citados no briefing.
- Parte dos timestamps de resolucao vem antes da primeira resposta. Para analise, deltas negativos foram tratados como virada de dia.
- O modelo usa categorias do Dataset 2, que nao sao a taxonomia real da empresa do Dataset 1. Em producao, seria necessario retreinar com rotulos proprios.
