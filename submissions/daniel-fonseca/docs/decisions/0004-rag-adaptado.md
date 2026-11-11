# 0004 — RAG: similaridade no DS2 + base de soluções validadas alimentada pelo HITL

- **Status:** Aceita (validada pelo Daniel em 2026-11-09)
- **Data:** 2026-11-09
- **Origem:** Daniel (ideia: inserir problemas num banco vetorial e responder com base em casos parecidos com solução validada) · IA (adaptação aos dados reais)

## Contexto
A ideia original pressupõe pares *problema → solução validada*. Mas:
- DS1 tem `Resolution`, porém é texto aleatório (lorem Faker) — inútil como conhecimento.
- DS2 tem texto real (47.837 tickets), porém **sem resolução** — só a categoria.

## Proposta
Dividir o RAG em duas memórias no Supabase (pgvector):
1. **`ticket_embeddings` (DS2, ~48K):** busca dos *k* tickets mais parecidos → **categoria + confiança** por votação ponderada (kNN). Avaliado em holdout estratificado: acurácia, F1 por classe, matriz de confusão e **curva de cobertura × precisão** (quanto dá para automatizar a cada limiar de confiança). Comparar com LLM zero-shot e com um baseline barato (TF-IDF + regressão logística) — usar o melhor, não o mais "bonito".
2. **`validated_resolutions` (começa pequena e cresce):** semeada com um playbook curto por categoria (rascunhado pela IA, **revisado pelo Daniel**) e alimentada por cada resposta **aprovada no HITL**. É aqui que vive o "caso parecido com solução validada" — a IA só responde sozinha quando há precedente validado próximo.

Fluxo online no n8n: ticket → embedding → busca nas duas memórias → decisão de nível (ADR-0005) → resposta automática / rascunho para revisão / alerta humano.
A carga em lote dos 48K embeddings é feita por script (mais confiável e reproduzível que um loop no n8n); o caminho online fica no n8n.

## Decisões técnicas embutidas
- `text-embedding-3-small`, armazenado como `halfvec` (16 bits) com índice HNSW (cosseno). Custo de carga estimado em centavos.
- **Dimensão decidida por medição, não por suposição** (Daniel questionou a redução para 512): gerar os embeddings uma vez em 1536, guardar localmente e avaliar 1536 × 512 (truncar + renormalizar equivale ao parâmetro `dimensions`) no holdout. Orçamento de espaço:

| Configuração | Vetores | + índice HNSW | Cabe nos 500 MB? |
|---|---|---|---|
| 1536 `vector` (32 bits) | ~295 MB | ~590 MB | **Não** — banco excedido pode ficar somente leitura |
| 1536 `halfvec` | ~147 MB | ~300 MB (+ ~25 MB de texto/tabelas) | Sim, sobra ~170 MB |
| 512 `halfvec` | ~49 MB | ~100 MB | Sim, com folga |

Padrão: **1536 `halfvec`** se a medição mostrar ganho; 512 só se a diferença for desprezível ou faltar espaço.
- Holdout fixo: `ds2_tickets.split` (80/20 estratificado, seed 42) — todos os métodos são avaliados no mesmo conjunto de teste.

## Consequências
- O sistema **aprende com o humano** — o volume automatizável cresce com o uso, em vez de ser fixado no dia 1. Isso é um argumento de ROI e de segurança.
- Precisamos de algumas respostas validadas para a demo (seed + aprovações feitas durante o vídeo).
