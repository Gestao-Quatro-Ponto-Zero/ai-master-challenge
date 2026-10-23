# Timeline: timebox × tempo real

| Fase | Timebox | Real | Cortes / observações |
|---|---|---|---|
| F0 · Setup | 30 min | ~30 min (07:35–08:10) | Primeira tentativa de projeto Supabase barrada pelo limite free; Tiago criou o `G4-Analysys` |
| F1 · Planejamento + skills | 45 min | ~70 min (08:10–09:20) | Estourou: o escopo cresceu (multi-LLM, RAG, perfis 360). Os itens novos entraram no topo da ordem de cortes |
| F2 · Ingestão e lake | 1h | ~1h15 (09:30–10:43) | Atrasos: API nova do SDK do MCP, `uv` fora do Homebrew, `.env` com URL errada |
| F3 · Diagnóstico | 2h | ~20 min (10:43–10:59) | Script reproduzível no lugar de notebook |
| F4 · Gold + modelo | 1h | ~20 min (10:59–11:14) | Modelo em SQL (taxa empírica) |
| F5 · API + painel + IA + usuários | 1h30 | ~1h10 (11:25–12:30) | Cortes: RAG, multi-LLM, 360, painéis por área dedicados, streaming |
| F6 · Deploy + relatório + README | 1h | ~10 min (12:30–12:36) | PR pendente de confirmação |

> Horários conferidos pelos timestamps dos commits (`git log`). Uma versão anterior desta tabela tinha horários estimados pela IA, errados (ver `ai-errors.md`).
