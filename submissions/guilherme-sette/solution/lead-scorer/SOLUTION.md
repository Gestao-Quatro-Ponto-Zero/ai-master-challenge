# Lead Scorer - Solucao funcional

## Objetivo

Ferramenta operacional para priorizar oportunidades abertas e orientar decisoes de vendedor e gerente.

A solucao tem duas divisoes:

- Portal do vendedor: fila de prioridades da propria carteira.
- Portal do gerente: abas de `Cenario` para risco/roteamento atual e `Aprovacoes` para decisoes pendentes.

## Como rodar

Na raiz do repositorio:

```bash
python3 -m pip install -r challenges/build-003-lead-scorer/requirements.txt

python3 challenges/build-003-lead-scorer/scripts/etl.py
python3 challenges/build-003-lead-scorer/scripts/seller_xray.py
python3 challenges/build-003-lead-scorer/scripts/seller_specialty_fit.py
python3 challenges/build-003-lead-scorer/scripts/score_pipeline.py
python3 challenges/build-003-lead-scorer/scripts/benchmark_score.py
python3 challenges/build-003-lead-scorer/scripts/validate_outputs.py
```

Depois, servir o front:

```bash
cd challenges/build-003-lead-scorer/frontend
python3 -m http.server 4173
```

Abrir:

```text
http://127.0.0.1:4173/
```

## Arquivos principais

- `scripts/score_pipeline.py`: gera score, roteamento, red-flags e dados do front.
- `data/processed/scored_open_opportunities.csv`: oportunidades abertas pontuadas.
- `data/processed/seller_portal_summary.csv`: resumo por vendedor.
- `data/processed/manager_portal_summary.csv`: resumo por gerente.
- `frontend/data/dashboard_data.json`: payload consumido pelo front.
- `frontend/index.html`: app.
- `frontend/app.js`: interacao, filtros e renderizacao.
- `frontend/styles.css`: UI.
- `reports/score_benchmark.md`: sanity check historico do score contra baselines simples.
- `reports/frontend_visual_validation.md`: screenshots e checks visuais do front.
- `reports/research_applicability.md`: comparacao da pesquisa anexada com o universo do desafio.
- `reports/research_sources/`: arquivos-fonte da pesquisa anexada.

## Logica de score

O score e uma prioridade operacional de 0 a 100, nao uma probabilidade de fechamento.

Pesos:

| Componente | Peso |
|---|---:|
| Valor economico | 20% |
| Fit vendedor-oportunidade | 25% |
| Timing / envelhecimento | 20% |
| Stage operacional | 10% |
| Qualidade da conta / ICP | 10% |
| Contexto da carteira | 10% |
| Confianca dos dados | 5% |

Sinais de roteamento:

- `manter`: vendedor atual deve agir.
- `consultar_especialista`: existe fit superior, mas governanca/capacidade pede apoio, nao transferencia.
- `remanejar`: candidato a troca de ownership com manager.
- `manager_review`: revisao gerente antes da acao.
- `corrigir_dados`: dados incompletos bloqueiam decisao boa.
- `last_chance`: ultima tentativa com SLA curto.
- `nurture`: nutricao ou retirada da fila principal.

## Fila de aprovacoes do gerente

Dois sinais entram na fila de aprovacao:

- `remanejar`: aprovar ou recusar a troca de ownership sugerida.
- `manager_review`: aprovar ou recusar a revisao gerente antes da acao comercial.

No front, o gerente pode marcar cada item como:

- `Aprovado`
- `Recusado`
- `Apoio delegado`

Essas decisoes ficam salvas no `localStorage` do navegador para a demonstracao. Elas nao sobrescrevem `current_sales_agent`, nao alteram os CSVs originais e nao simulam uma integracao real com CRM.

## Regras de remanejamento

Remanejamento exige:

- conta conhecida;
- especialista diferente do vendedor atual;
- ganho de match >= 12 pontos;
- confianca de match >= 0,65;
- preferencia por janela de 91 a 180 dias;
- respeito a cap de capacidade do especialista.

Capacidade:

- cap macio: `max(5, 15% da carteira aberta atual)`;
- cap duro: `max(8, 25% da carteira aberta atual)`.

## Cortes de idade

| Idade em `engaging` | Politica |
|---:|---|
| 0-90 dias | Normal |
| 91-180 dias | Recovery |
| 181-270 dias | Revisao gerente |
| >270 dias | Quarantine, nutricao ou ultima tentativa |

## Benchmark historico

Foi adicionado um benchmark simples para evitar uma narrativa sem evidencia.

Metodologia:

- 70% das oportunidades fechadas mais antigas por `engage_date` para construir taxas historicas;
- 30% mais recentes para testar ranking;
- comparacao entre score V1 compativel, valor puro, win rate historico do vendedor e win rate historico do produto.

Leitura:

- no top 10%, o score V1 melhora win rate contra valor puro;
- no top 20%, valor puro ainda captura mais receita ganha;
- portanto, o V1 nao deve ser vendido como modelo que maximiza receita historica pura, mas como ferramenta operacional explicavel com governanca, fit, saneamento de dados e controle de remanejamento.

## Evidencia visual

Screenshots atuais:

- `reports/frontend-current-seller.png`
- `reports/frontend-current-manager-scenario.png`
- `reports/frontend-current-manager-approvals.png`

A validacao foi feita com Chrome headless em viewport desktop 1440x1050. Os checks confirmaram portal do vendedor sem abas de gerente, portal do gerente com abas `Cenario`/`Aprovacoes`, breakdown do score visivel e ausencia de overflow horizontal no body.

## Limitacoes

- Nao ha snapshots historicos reais, entao o score nao deve ser vendido como forecast calibrado.
- 68,2% das oportunidades abertas nao tem conta conhecida; isso reduz a confianca e limita fit por setor/porte.
- Nao ha calls, emails, notas, contatos ou buying group; por isso LLM enrichment e graph ML ficam fora do V1.
- O fit vendedor-produto e associativo, nao causal.
- O front e uma aplicacao estatica para o desafio; em producao, autenticacao, permissoes e persistencia seriam obrigatorias.
