# Lead Scorer · app

A janela da planilha `sales_pipeline`. Next.js 16, App Router, Tailwind 4, sem banco: lê a planilha por uma API em Apps Script e, sem ela, roda do snapshot em `src/data/snapshot.json`.

```bash
npm install
cp .env.example .env.local   # APPS_SCRIPT_URL e API_TOKEN conectam na planilha; sem eles, modo snapshot
npm run dev                  # http://localhost:3000
```

Sem login na demo: a primeira tela escolhe o vendedor ou o manager (os e-mails do dataset não existem, então um login seria de mentira). Com a aprovação da RevOps, entra o login da empresa (SSO) e cada vendedor vê só o seu, o manager só o time.

Páginas: `/` (escolha), `/meu-dia` (KPIs + lista do dia com Feito / Ganho / Perdido, bloco Recompra sem deal com Feito, bloco Confirmar com Demanda separada), `/fila` (deals sem conta), `/manager` (time, passos, alertas), `/revops` (todos os times, filtro por manager e região), `/simulacao` (avançar um dia, mandar as mensagens, ligar o job diário, zerar; pede a senha `DEMO_ADMIN_PASSWORD`, porque mexe na planilha de todo mundo).

Onde cada coisa mora: `src/lib/data.ts` (planilha ou snapshot), `src/lib/actions.ts` (o que grava de volta), `src/lib/types.ts` (nomes das colunas, exatamente como na planilha), `src/app/*` (páginas), `src/components/*`.
