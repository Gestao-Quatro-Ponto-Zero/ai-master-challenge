## Submissão — Renan Garcia Oliveira — Challenge 003 (Lead Scorer)

**Régua**: um sistema que o vendedor abre na segunda-feira e sabe onde focar, por quê e o que largar.

- **App:** https://regua-lead-scorer.vercel.app
- **README da submissão:** [`submissions/renan/README.md`](https://github.com/salesDevRenan/ai-master-challenge/blob/submission/renan/submissions/renan/README.md)
- **Process log:** [`submissions/renan/process-log/PROCESS_LOG.md`](https://github.com/salesDevRenan/ai-master-challenge/blob/submission/renan/submissions/renan/process-log/PROCESS_LOG.md) + histórico de commits desta branch

### Em uma frase

Antes de pontuar, testei os dados. Neste CRM ninguém prevê ganho vs. perda (AUC ≈ 0,5; produto, setor e vendedor são ruído). O que dá para saber é o valor de cada deal e quais estão mortos: nenhum deal fechou depois de 138 dias, e 81% dos deals em Engaging já passaram disso (64% do valor aberto). A Régua prioriza por valor esperado, tira os parados da pauta e explica cada score com um "recibo" que fecha a conta.

### O que tem

- Telas Hoje, Pipeline, Parados, Deal, Time (sem ranking de vendedores), Agente Gestor, Metodologia e Configurações.
- Score com pesos aprendidos (Bayes empírico), curva de sobrevivência e backtest em 3 datas.
- Agente Gestor (Claude): Radar de alertas sem IA, mais perguntas aos dados restritas ao pipeline. Cada usuário usa a própria chave da API.
- 34 testes; todo número dos docs é reproduzível por `npm run analyze`.

### Como rodar

```bash
cd submissions/renan/solution && npm install && npm run dev
```

### Checklist

- [x] Li o README completo do challenge
- [x] Solução em `submissions/renan/`
- [x] Process log com evidências de uso de IA
- [x] README segue o template
- [x] Instruções de setup
- [x] Nenhum arquivo fora da minha pasta foi modificado

Tempo: cerca de 8h30 (acima da meta; justificado no README).

🤖 Generated with [Claude Code](https://claude.com/claude-code)
