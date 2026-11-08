# Score de prioridade — avaliação e plano do novo modelo

Data: 2026-11-07 · Base: dados reais de `backend/data` (8.800 oportunidades, referência 2017-12-31) e modelo ativo `v2026.11.1`.
Nada no backend foi alterado; tudo foi medido com o `model-lab`.

## 1. Para que serve o score hoje
Ordenar a carteira do vendedor: 0–100 = percentil do **valor esperado** (`p_win calibrada × preço de tabela`) entre os deals abertos não-zumbis.
Regras do backend (`lead_core/bands.py`, `constants.py`):

| Regra | Condição | Efeito |
|---|---|---|
| Prospecting | sem engage_date | sem score, aba própria |
| Review (zumbi) | idade > maior ciclo já fechado (138 dias) | sem score, fora da lista padrão |
| Stale risk ("Decidir") | idade > P90 do ciclo (104 dias) | **mantém o score** |
| Foco / Acompanhar / Baixa | score ≥ 80 / 40–79 / < 40 | prioridade Alta / Média / Baixa |

O modelo é um LightGBM que prevê *"este deal vai terminar Won?"*, treinado com fotos semanais **só dos deals que já fecharam**.

## 2. Por que aparece score alto em lead parado
1. **O score é quase só o preço.** Spearman score × preço = 0,98. O p_win varia pouco (0,50–0,83): GTK 500 é sempre 100, MG Special sempre ~10.
2. **O modelo acha que deal velho é melhor.** Os perdidos morrem rápido (mediana de 14 dias) e os ganhos demoram (57 dias). Como os deals que ficam parados para sempre nunca entram no treino, o modelo vê "sobreviveu = vai ganhar":

| Idade do deal | p_win atual | Score médio | Ganhou em 30 dias (real) |
|---|---|---|---|
| 0–15 | 0,64 | 47 | 15% |
| 46–90 | 0,68 | 51 | 20% |
| 105–138 (parado) | **0,70** | **55** | **8%** |
| 139+ (zumbi) | **0,71** | — | **0%** |

3. **Stale mantém o score.** Hoje, 30 dos 62 deals com score ≥ 80 estão parados (> 104 dias).
4. **O limiar de zumbi é frágil.** É o *máximo* histórico. Na simulação, quando alguns zumbis antigos fecham (limpeza de carteira), o máximo sobe e centenas de zumbis voltam com score: os deals com score ≥ 80 passaram de 88 para ~330, e 78% deles estavam parados.
5. **O portão de qualidade não vê dado novo.** O backtest usa sempre as mesmas datas fixas de 2017 (`DEFAULT_BACKTEST_SNAPSHOTS`): o AUC ficou em 0,547–0,550 nos 7 dias e todo retreino foi promovido.

Conclusão: o que torna a lista atual útil é a **regra** que tira os zumbis, não o modelo. Ordenar só por preço tem o mesmo poder de prever ganho em 30 dias que o valor esperado do modelo (AUC 0,50 vs 0,49).

## 3. Desafiante testado
Mesmos dados e mesmas features + `age_vs_max_cycle` (idade / P99 do ciclo). O alvo muda para **"ganhou em até 30 dias a partir de hoje"**, que é observável para todo deal aberto (os parados entram como 0). Score = percentil de `p30 × preço` (receita esperada no mês). Parada antecipada por AUC e calibração Platt.

### Backtest real (13 datas, jun–nov/2017, horizonte de 30 dias)
| Métrica | Atual (lista) | Novo receita 30d | Novo conversão 30d | Só preço |
|---|---|---|---|---|
| AUC ganhou em 30d | 0,611 | 0,652 | **0,712** | 0,501 |
| Receita capturada pelo top 20% | 56,4% | **64,4%** (+14%) | 33,2% | 43,1% |
| Top-5 de cada vendedor que ganhou em 30d | 16,3% | 22,4% (+37%) | **26,5%** | 12,6% |
| Receita no top-5 dos vendedores | US$ 148 mil | **US$ 183 mil** (+24%) | US$ 106 mil | US$ 114 mil |
| Parados no top 20% | 14,0% | **9,5%** | 11,7% | 39,9% |

O novo (receita) vence o atual em 10 de 13 datas na receita do top 20% e em 12 de 13 no acerto do top-5 do vendedor.

### Simulação de 7 dias (mocks + retreino diário com o `run_training` de produção)
| | Atual | Novo |
|---|---|---|
| Spearman com a receita verdadeira em 30d (média dos 8 dias) | 0,82 | **0,98** |
| Ganhos dos dias seguintes que estavam no top 20% da véspera | 2,4 de 9,6 | **4,6 de 9,6** |
| AUC "ganhou nos dias seguintes" | 0,51 | **0,66** |
| Estabilidade (PSI máximo entre dias) | 0,011 | — |
| Regras de negócio (zumbi/prospecting sem score, 0–100) | ok | — |

Veredito do lab: **score atual não condizente** (falha no critério "score alto não é deal parado"); **desafiante muito melhor**.

Limitações: o dataset não tem atividades (último contato, reuniões); a probabilidade p30 ainda está mal calibrada em algumas faixas de idade (por isso o plano exibe só o ranking); o mundo mock é estimado do real, com uma suposição explícita para os zumbis.

## 4. Parecer do vendedor sênior (revisão independente)
> "Na prática ele me diz 'venda o produto mais caro'… O sistema premia justamente o que eu deveria largar."

**Veredito: APROVO COM CONDIÇÕES.**
- Padrão = **receita em 30 dias** ("vivo de quota em dinheiro"), com uma aba/filtro de **conversão** para a última semana do mês.
- Condições: piloto com 2–3 vendedores contra o grupo que segue na lista atual; portão avaliando dados recentes; "maior ciclo" robusto, que não muda com limpeza de carteira.
- Regras: Foco só dentro do ciclo saudável; Decidir em fila própria (score só ordena; nunca prioridade Alta) com ação avançar/rebaixar/perder em 7 dias; Revisar com "encerrar como Lost em lote".
- Para confiar: (1) motivos em linguagem de vendedor; (2) dados de atividade; (3) ação sugerida por deal; (4) acompanhamento "quantos do meu top-5 de 30 dias atrás fecharam"; (5) aviso quando o modelo muda.

## 5. Plano de implementação
Referência executável: `notebooks/novo_modelo_receita_30d.ipynb`. O contrato da API não muda (`score`, `band`, `expected_value`, `p_win`); o esquema SQLite congelado também não.

| # | Etapa | Onde | Esforço |
|---|---|---|---|
| 1 | Alvo `won_within_30d` com fotos até T−30, todos os deals abertos | `lead_trainer/training.py` (`build_train_30d`) | M |
| 2 | Feature `age_vs_max_cycle` (idade / P99), também no what-if | `lead_core/features.py` | S |
| 3 | Parada antecipada por AUC + calibração Platt; `calibration.useful` continua decidindo se a probabilidade aparece | `training.py`, `lead_trainer/calibration.py` | S |
| 4 | Limiares robustos: stale = P90, review = P99, congelados no model card; stale nunca é Alta | `lead_core/bands.py` | S |
| 5 | Backtest com datas **móveis** (últimas 4 fotos até T−30) e métricas de vendedor (receita top 20%, acerto top-5) | `lead_trainer/evaluation.py` | M |
| 6 | Portão campeão/desafiante: promover só se não perder em receita top 20% e top-5 nas datas recentes | `quality_gate` | S |
| 7 | Textos: `expected_value` = receita esperada em 30 dias (model card, "Como funciona") | API/front | S |
| 8 | Visão "conversão 30d" como ordenação extra (`VIEWS`) | `lead_core/constants.py` | S |
| 9 | Piloto A/B de 4 semanas com 2–3 vendedores; medir receita fechada e acerto do top-5 | operação | M |
| 10 | Rodar `model-lab` (pytest) a cada lote novo de dados antes de promover | cron/CI | S |
| 11 | Próximo salto de acurácia: dados de atividade (último contato, próxima reunião, e-mail respondido) e feedback `deal_feedback` como sinal de avaliação | fonte de dados | L |

Critério de saída do piloto: receita do top 20% ≥ +10% e acerto do top-5 ≥ +20% sobre o grupo controle, sem aumento de deals parados no Foco.
