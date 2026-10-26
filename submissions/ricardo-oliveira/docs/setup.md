# Setup: como rodar

Três peças. A planilha é o motor, o Apps Script é a API e o job diário, o app é a janela.

## 1. A planilha (motor)

Google Sheet `sales_pipeline`: https://docs.google.com/spreadsheets/d/1IjZSZTpzergXYVKPxf-IUJwsss5xD9P_Nch5KX3IMDc/edit (leitura). Todas as abas são fórmula, menos `Atividades` (o que o app grava) e as entradas azuis da aba `Hoje`.

| Aba | O que é |
|---|---|
| `Hoje` | O relógio (B3 = dias passados desde 31/12/2017, B4 = hoje), modo de dono (Carteiras / Como está hoje), ordem dentro do passo, cortes (57 e 138 dias, janelas de recompra), resumo do dia |
| `Lista do Dia` | 664 deals com conta: passo (1 a 4, e 5 = Confirmar), ordem por vendedor, por quê, próxima ação, último contato, demanda separada confirmada |
| `Fila Sem Conta` | 1.425 deals sem conta, prazo e escalada, colunas azuis preenchidas pelo vendedor |
| `Recompra sem deal` | Pares conta e produto na hora de recomprar, quantos deals abertos (limpos e a confirmar) existem; onde não há nenhum, abrir e ligar, com Feito |
| `Visão Manager` | Carga por vendedor nos dois modos, passos, fila, alertas; por manager a partir da linha 43 |
| `KPIs Vendedor` | Os oito números do topo do app, por vendedor, com e-mail e papel |
| `Backtest` | Data de snapshot editável: a lista daquele dia e o que aconteceu depois. Top N exato por vendedor, acaso pareado por vendedor, atropelados contra limpos, e a leitura exploratória escrita na aba |
| `Atividades` | Uma linha por ação do app: feito, ganho, perdido, separado (demanda separada confirmada), conta (identificada), recompra (deal aberto / ligação) |
| `Account x Product`, `Open Deals`, `Books`, `Rep Books`, `ICP`, `ICP x Team`, `GTK 500 KPIs` | As análises e decisões que alimentam a lista (recompra, carteiras, redistribuição, ICP) |

Pra rodar com seus próprios dados: cole os quatro CSVs nas abas `sales_pipeline`, `accounts`, `sales_teams` e `Products` e tudo recalcula.

Sem acesso à planilha: toda fórmula e toda configuração estão em [`../solution/sheet`](../solution/sheet) (`formulas.md`, uma seção por aba, célula a célula, e `config.md` com os valores da aba `Hoje`). Dá pra reconstruir a planilha do zero a partir disso e dos CSVs.

## 2. O Apps Script (API e job diário)

Código em [`../solution/apps-script`](../solution/apps-script). Vinculado à planilha, publicado em 23/10/2026 como app da web (versão 9). O app em produção já aponta pra ele. O job das 9h (America/Sao_Paulo) anda o relógio e manda as mensagens por e-mail; fica desligado durante a avaliação e liga pela página Simulação, com a senha de administração.

Pela interface: abra a planilha, Extensões > Apps Script, cole `Code.gs` e `appsscript.json` (ative "Mostrar o arquivo de manifesto" nas configurações), rode `setToken('um-token-seu')` uma vez e `installTrigger()` uma vez (agenda o job das 9h), depois Implantar > Nova implantação > App da Web, executar como você, acesso "Qualquer pessoa". Copie a URL.

Pela linha de comando (Google Workspace CLI, `gws`):

```bash
gws script projects create --json '{"title":"Lead Scorer API","parentId":"<id-da-planilha>"}'
gws script +push --params '{"scriptId":"<scriptId>"}' --dir solution/apps-script
gws script projects deployments create --params '{"scriptId":"<scriptId>"}' --json '{"description":"v1"}'
```

Endpoints: `?action=config`, `?action=users`, `?action=rep&email=...`, `?action=manager&email=...`, `?action=revops`, `?action=snapshot`. POST com `{token, action: activity|conta|advance|reset|notify|trigger}`. `activity` aceita `acao` = feito, ganho, perdido, separado ou recompra (`deal` = "Conta|Produto"). `conta` grava Status e Conta na `Fila Sem Conta` e uma linha em `Atividades`. `trigger` liga ou desliga o job diário (`on: true|false`).

## 3. O app (Next.js)

```bash
cd solution/app
npm install
cp .env.example .env.local   # APPS_SCRIPT_URL e API_TOKEN conectam na planilha; DEMO_ADMIN_PASSWORD protege a Simulação
npm run dev                  # http://localhost:3000
```

Sem `APPS_SCRIPT_URL`, o app roda em **modo snapshot**: lê `src/data/snapshot.json` (exportado da planilha em 23/10/2026), e o que o vendedor marca fica num cookie do navegador. Com a URL, cada ação vira uma linha em `Atividades` e o botão "Avançar um dia" anda o relógio.

Sem login na demo: a primeira tela escolhe o vendedor ou o manager. Os e-mails do dataset não existem, então um login seria de mentira; com a aprovação da RevOps entra o SSO da empresa e a permissão por papel.

Em produção: https://g4-lead-scorer-seven.vercel.app. Variáveis no Vercel: `APPS_SCRIPT_URL`, `API_TOKEN`, `DEMO_ADMIN_PASSWORD`.

Controles da demo (página Simulação): avançar um dia, mandar as mensagens, ligar ou desligar o job diário e zerar a demo mudam a planilha pra todo mundo que está olhando. Pedem a senha de administração, `g4-revops`. Marcar Feito, Ganho, Perdido, Demanda separada e Conta identificada não pede senha: é o uso normal do vendedor, e grava na planilha como num CRM.
