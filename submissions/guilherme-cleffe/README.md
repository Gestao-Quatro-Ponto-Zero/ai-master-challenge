# Submissão — Guilherme Cleffe — Challenge 003 (Lead Scorer)

## Sobre mim

- **Nome:** Guilherme Cleffe, CFA, PMP
- **LinkedIn:** https://www.linkedin.com/in/guilherme-cleffe
- **Challenge escolhido:** 003 — Lead Scorer (Vendas / RevOps)

---

## Executive Summary

Construí uma ferramenta de priorização de leads de forma a melhorar o foco e produtividade da equipe de vendas. Key insights: curva de distribuição dos leads fechados (entre 14 e ~100 dias de aging), filtrar os leads zumbis (muitos), sem sensibilidade a preços, etc. Cada regra foi baseada em hipóteses extraídas sobre a base de dados. 

---

## Solução

### Como executar

Pré-requisitos: Python 3.10+.

```bash
cd submissions/guilherme-cleffe/solution
pip install -r requirements.txt          # apenas pandas

# 1. Reconstruir o datalake a partir dos CSVs brutos (validação embutida)
python src/build_datalake.py
#    -> data/lake/  (CSVs limpos + crm.db SQLite + fact_deals com 8.800 deals)

# 2. Pontuar o pipeline aberto
python src/scorer.py score
#    -> data/lake/scored_pipeline.csv  (2.089 deals: score 0-100, ação, explicação)

# 3. Avaliar o modelo (backtest com corte temporal, sem vazamento)
python src/scorer.py backtest
```

Saídas prontas para consumo:
- `solution/data/lake/scored_pipeline.csv` — a fila priorizada, com explicação em linguagem natural por deal
- `solution/data/lake/prospecting_enriched.csv` — os 500 leads de prospecção triados e ranqueados
- `docs/monday-morning-email.md` / `.html` — o boletim "Segunda de Manhã" gerado a partir dos scores

### Abordagem

Método **Architect/Builder**: eu (Architect) defini hipóteses e decisões de negócio; o Claude Code (Builder) implementou, validou e desafiou cada hipótese com dados antes de virar regra. Sequência:

1. **Datalake primeiro** — parametrização das 4 tabelas, correção de inconsistências (`GTXPro`≠`GTX Pro` teria descartado ~1.480 deals silenciosamente), centralização em SQLite + CSVs com gate de validação.
2. **Hipóteses antes de regras** — cada intuição de negócio foi testada: perfil de deals ganhos, regra das 2 semanas, triagem de prospecção, segmentação por conta.
3. **Scorer baseado em regras validadas** — sem ML caixa-preta; score 0–100 decomposto em fatores nomeados que um vendedor entende.
4. **Eval antes de confiar** — backtest com corte temporal derrubou o fator mais "sofisticado" do modelo antes de ele chegar ao usuário.

### Resultados / Findings

| Finding | Evidência |
|---|---|
| **Linha dos 138 dias** | 0 vitórias em 6.711 deals fechados após 138 dias de ciclo. 1.291 deals abertos (81% do Engaging) já passaram dela — $2,02M de forecast fictício |
| **Regra das 2 semanas estava invertida** | P(ganhar \| sobreviveu ≥14d) = 69% e sobe com a idade; metade das perdas morre até o dia 14. Matar deals "frios" cedo destruiria valor |
| **Conta vinculada é pré-requisito estrutural** | 100% dos deals que fecharam tinham conta; só 32% dos zumbis têm. 546 deals abertos ($756k) estão congelados por um campo de CRM |
| **Receita vem do mix, não da taxa** | Win rate plana ~63% para todos; agentes do topo de receita vendem 53% de produtos premium vs 33% da base — mesmas chances, prêmio maior |
| **ICP firmográfico não existe nestes dados** | Win rate 61–66% em todos os setores, tamanhos e regiões — pontuar "fit" seria codificar ruído |
| **Histórico de win rate não prediz** | Backtest temporal: AUC 0,487; win rates por conta correlacionam **-0,17** entre períodos (ruído revertendo à média) |

Ações geradas para a semana: **43 EMPURRE JÁ · 29 FOCO · 546 CORRIJA A CONTA · 163 TRIAGEM · 17 NUTRIR · 1.291 PURGA.**

### Recomendações

1. **Purga de zumbis até sexta** — 1.291 deals, $2,02M. O Oeste concentra 562 ($992k). Forecast fica honesto imediatamente.
2. **Vincular conta nos 546 deals congelados** — um campo de CRM, $756k destravados, custo zero de tempo de venda.
3. **Coaching por mix premium, não por win rate** — win rate como KPI recompensa cherry-picking (os agentes de maior win rate são os que mais abandonam deals).
4. **Processo dedicado para o GTK 500** — 44% de travamento no carro-chefe de $26,8k; sponsor executivo por deal.
5. **Instrumentar o CRM** — timestamps por estágio, log de atividades, papéis de contato, motivos de perda. Sem isso, nenhum modelo (nosso ou ML) enxerga sinais de compra reais.

### Limitações

- **Sem dados de atividade/intenção**: o dataset não tem interações, contatos nem motivos de perda — o scoring usa valor + momentum + regras estruturais, que foi o que sobreviveu à validação.
- **Preço dos perdidos invisível**: `close_value = 0` em todo deal perdido; objeção de preço não é mensurável.
- **337 leads de prospecção sem conta** não são enriquecíveis internamente (não há chave); em produção, usaria enriquecimento externo (Apollo/ZoomInfo).
- **Snapshot fixo (31/12/2017)**: dataset histórico; em produção o pipeline rodaria diário contra o CRM vivo.
- **Interface**: a fila priorizada é entregue via CSV + boletim de e-mail; o app Streamlit ("visão de segunda-feira" interativa com filtros por vendedor/gerente/região) está desenhado no ROADMAP.md como próxima fase.
- **Guardrails de LLM**: desnecessários hoje (motor determinístico); tornam-se obrigatórios se o "próximo passo sugerido por IA" do roadmap for implementado.

---

## Process Log — Como usei IA

> Log completo, sessão por sessão, com prompts, decisões e erros: **[process-log/process-log.md](process-log/process-log.md)**

### Ferramentas usadas

| Ferramenta | Para que usei |
|------------|--------------|
| Claude Code (Fable 5) | Todo o ciclo: perfilamento dos dados, ETL, validação de hipóteses, scorer, backtest, boletim de e-mail e documentação — sob método Architect/Builder |
| pandas + SQLite | Análise exploratória e datalake (escolhidos pela IA por dependência mínima) |

### Workflow

1. **Sessão 1 — Fundação de dados:** extração do ZIP, perfilamento das 4 tabelas, descoberta de 5 problemas de qualidade, ETL com gate de validação, datalake centralizado, roadmap e acordo de trabalho (CLAUDE.md).
2. **Sessão 2 — Validação de hipóteses:** minhas 3 hipóteses de negócio testadas contra os dados; 1 confirmada parcialmente, 1 **refutada e invertida** (regra das 2 semanas), 1 viável para 1/3 dos casos.
3. **Sessão 3 — Forense do playbook:** quartis de agentes, distribuição de momentum, KPIs por funil, enriquecimento dos 500 leads, PLAYBOOK.md com seção "testado e rejeitado".
4. **Sessão 4 — Scorer + eval:** segmentação winners/zumbis com controle de safra, scorer v1, backtest temporal que **derrubou o fator de win-prob**, redesenho honesto do score.
5. **Sessão 5 — Boletim de segunda:** e-mail executivo com números reais do pipeline pontuado, versões texto e HTML com design próprio.
6. **Sessão 6 — Submissão:** tradução pt-BR, checklist de conformidade, este README.

### Onde a IA errou e como corrigi

- **A própria IA desenhou um fator ruim** — o scorer v1 incluía "probabilidade de vitória" por histórico de conta×agente×produto, com spread in-sample convincente (contas de 53–75%). Exigi avaliação antes de confiar; o backtest temporal que a IA construiu expôs AUC 0,487 e correlação **negativa** entre períodos. O fator foi removido e o episódio documentado no PLAYBOOK como evidência de que eval vem antes de confiança.
- A IA inicialmente sugeriu segmentação por conta como "o sinal mais forte" — corrigido pela mesma evidência e registrado como correção explícita na documentação.

### O que eu adicionei que a IA sozinha não faria

- **As hipóteses de negócio** (perfil de ganhos, regra das 2 semanas, triagem de prospecção) que dirigiram a investigação — inclusive a que estava errada, cuja refutação virou o achado mais valioso do projeto.
- **A exigência de validar antes de codificar regras** e de rodar eval antes de confiar no modelo — as duas decisões que mudaram o produto final.
- **Contexto GTM**: cliente não sensível a preço → foco em segmentação; leitura de que zumbis são falha de processo gerencial (não individual) → recomendação virou ação de gerente, não de vendedor.
- Decisões de escopo: PR-only, estrutura da submissão, priorização datalake-primeiro dentro do budget de 4–6h.

---

## Evidências

- [x] Narrativa escrita passo a passo: [process-log/process-log.md](process-log/process-log.md)
- [x] Git history na branch `guilherme-cleffe` (commits por fase)
- [x] Documentação técnica com decisões e rejeições: [docs/PLAYBOOK.md](docs/PLAYBOOK.md), [docs/DATA_DICTIONARY.md](docs/DATA_DICTIONARY.md)
- [x] Deliverable executivo gerado dos dados: [docs/monday-morning-email.md](docs/monday-morning-email.md)

---

_Submissão enviada em: 17/07/2026_
