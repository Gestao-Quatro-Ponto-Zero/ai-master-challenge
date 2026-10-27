# Régua — solução do Challenge 003

App Next.js (React 19, TypeScript, Tailwind CSS v4). Documentação completa no [README da submissão](../README.md).

```bash
npm install
npm run dev      # gera dataset + análise e sobe em http://localhost:3000
npm test         # 34 testes
npm run build    # build de produção
```

| Pasta | Conteúdo |
|---|---|
| `data/raw/` | CSVs do Kaggle (CC0), sem alteração |
| `scripts/` | `build-data.ts` (CSV → dataset validado) e `analyze.ts` (achados + backtest) |
| `src/lib/data/` | Schemas Zod, normalização e montagem do dataset |
| `src/lib/scoring/` | Motor de score: histórico, Bayes empírico, curva de sobrevivência, backtest |
| `src/lib/agent/` | Radar, ferramentas e configuração do Agente Gestor |
| `src/app/` | Telas e rotas (`/api/agente`, `/api/agente/teste`) |
| `tests/` | Vitest |
