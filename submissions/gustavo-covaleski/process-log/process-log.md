# Process log — Challenge 002 (Gustavo Covaleski)

**Ferramentas e papéis**
- **Claude, no chat do Projeto:** planejamento, crítica, especificação de cada fase, revisão dos resultados e condução dos portões. Não executa código.
- **Claude Code, no meu computador:** executa as especificações, roda o código e gera os artefatos.
- **Repasse por arquivo:** `planning/F<n>-spec.md` → execução → `planning/F<n>-report.md` → revisão conferindo os números nos arquivos gerados → portão.
- Toda decisão é minha. A coluna "O que a IA sugeriu" registra a proposta antes da decisão.

## Decisões por fase

| # | Fase | O que pedi | O que a IA sugeriu | Decisão minha | Evidência | Tempo |
|---|---|---|---|---|---|---|
| 1 | F0 — Enquadramento | Reescrever o pedido do Diretor em 3 perguntas mensuráveis; plano de teste para cada armadilha conhecida dos dados; ranking das 7 hipóteses de diferenciação por impacto ÷ tempo; o que não fazer; escopo e orçamento | (a) Q1 tempo/CSAT por segmento com teste de permutação + Holm, e efeito mínimo detectável se nada passar; Q2 cobertura × acerto em holdout agrupado com limiar escolhido por custo do erro; Q3 custo, latência p50/p95, troca de rótulo sob injeção e golden set. (b) Cortar o braço de embeddings; testar o LLM só na faixa em que o clássico se abstém. (c) Fundir H1 + H4 (os testes de falha são o golden set); H6 e H7 como higiene, não diferencial. (d) Trocar "reabertura" por um evento genérico de mudança de status (inclui "aguardando cliente"), porque sem ele o TTR culpa o atendente pela espera do cliente. (e) Orçamento 345 min + 15 min de folga | Aprovado com 4 ajustes (ver "Portão F0" abaixo) | `02-contexto.md` §3–§6; pasta local vazia na hora; brief original não lido nessa resposta (acesso ao repo negado na sessão) | **60 min reais** (orçado 15; estouro de 45 min, 400%); inclui as linhas 2 e 3 |
| 2 | F0 → F1 — Planejamento | Consolidar o escopo aprovado em `planning/F0-escopo.md` e escrever `planning/F1-spec.md` para o Claude Code | Escopo com os 4 ajustes. F1 com: consequências pré-registradas por armadilha antes de ver os dados; holdout congelado antes de qualquer modelo; exposição a vazamento medida sem modelo; verificação de se o texto do DS2 já vem pré-processado (nome do arquivo sugere); arquivos com texto de ticket fora do repositório; CSV com `;` e UTF-8 com BOM para o Excel em português; variante cega opcional da planilha de revisão; alerta de que, num git rodando na VM Linux, 11 arquivos fora da pasta aparecem modificados só por fim de linha | | Documentos oficiais do repositório lidos; `git diff --ignore-cr-at-eol` vazio nos 11 arquivos | incluído nos 60 min da F0 |
| 3 | F0 → F1 — Decisões complementares | Incorporar as decisões complementares ao escopo e à spec, sem nova rodada de planejamento | Folga reduzida de 15 para 5 min para pagar a adjudicação sem passar de 360 min (revertido: folga voltou para 15 min com o corte do deploy). Revisão cega + adjudicação separadas numa linha própria do orçamento (50 min); total real 370 min | Variante cega; adjudicação; regra de decisão da Q2 em 3 faixas; cenários A/B de triagem; planilha adjudicada como evidência; commits só pelo Windows (ver "Decisões complementares") | `planning/F0-escopo.md` e `planning/F1-spec.md` atualizados | incluído nos 60 min da F0 |
| 4 | F1 — Auditoria dos dados | Executar `planning/F1-spec.md`: medir as armadilhas dos dois datasets, congelar grupos de quase-duplicados e holdout antes de qualquer modelo, gerar a planilha cega de revisão | Todas as 8 armadilhas do DS1 confirmadas (T3: 49,30% dos Closed resolvem antes da 1ª resposta; T5: CSAT com qui² p = 0,7968). DS2: texto pré-processado (0% maiúsculas); 0 duplicados exatos; 6,46% dos tickets em grupos de quase-duplicados (cos ≥ 0,90); 360 tickets em 61 grupos com rótulo conflitante; holdout aleatório expõe 5,89% do teste a vazamento, o por grupo 0%. Alerta: o `.gitignore` da raiz ignora `submissions/`, e `git add -f` levaria o `.venv/` junto | | `planning/F1-report.md`; `solution/outputs/f1_*.json`, `f1_ds1_fatos.csv`, `f1_splits.csv`; `pytest` 10 passed | ~15 min de execução (orçado 45) |

## Portão F0 — decisão humana (Gustavo, 03/11/2026)

**Aprovado como proposto:** ordem das hipóteses com H2 (ruído de rótulo) em primeiro; corte de embeddings; LLM só na faixa de abstenção; golden set unificado (H1 + H4) com medição de troca de rótulo sob injeção; instrumentação H5 com 5 eventos (`ticket_criado`, `resposta_agente`, `status_mudou`, `reatribuido`, `csat_respondido`); orçamento de 360 min; incompatibilidade DS1 × DS2 declarada como premissa; medição de vazamento aleatório × por grupo.

**Ajustes obrigatórios:**
1. **Critério da Q2 corrigido** para: limite inferior do IC 95% da precisão da faixa automática ≥ 1 − taxa de erro do rótulo humano. Justificativa: a faixa automática precisa acertar pelo menos tanto quanto o humano acerta; a versão da IA comparava precisão com taxa de erro.
2. **Q1 enxuta:** só a tabela de auditoria das armadilhas do DS1 e o efeito mínimo detectável; sem permutação por segmento, Holm, ε² nem bootstrap por segmento; teto de 20 min e até 5 linhas na entrega. Justificativa (texto proposto pela IA, confirmado pelo Gustavo): 46 das 57 submissões já mostraram que o DS1 é sintético ou sem sinal; testes por segmento sobre uma variável de tempo inválida custam tempo e não mudam a decisão.
3. **Deploy cortado** (revisão do ajuste original, que previa deploy só com folga): o protótipo roda só localmente. Justificativa (minha): "13+ submissões já publicaram, não diferencia; prefiro rodar local e preservar a folga." A folga volta para 15 min.
4. **Revisão manual de 60 tickets**, estratificada pelas 8 categorias, feita por mim (30–40 min), sem sugestão de rótulo pré-preenchida. Justificativa: não ancorar o meu julgamento; o rótulo de referência precisa vir de julgamento humano.

**Decisões complementares (Gustavo, 03/11/2026, antes de rodar a F1):**
1. **Revisão cega**, com etapa 4b de adjudicação: nos tickets em que o meu rótulo cego diverge do original, revelo o original e classifico como `original errado`, `eu errei` ou `ambíguo`. A taxa de erro da Q2 usa só `original errado`; os `ambíguo` alimentam a H2. +10 min no orçamento.
2. **Regra de decisão da Q2:** automatizo só se o limite inferior do IC da precisão passar em 1 − e_inferior (a meta mais exigente). Se passar só em 1 − e_superior, a faixa vira "IA sugere, humano confirma". O viés de ruído sistemático fica registrado como limitação.
3. **Triagem em dois cenários, sem a linha de 0,5 min:** (A) existe etapa separada de triagem, grade de 2–4 min; (B) não existe, a economia de triagem é zero e o ganho vem do reroteamento evitado, que não é calculável com estes dados e justifica o evento `reatribuido`. Vira achado do diagnóstico.
4. **Planilha de revisão:** arquivos de trabalho em `planning/F1-revisao/`; a planilha final adjudicada (60 linhas) entra em `process-log/` como evidência.
5. **Git:** commits só pelo Windows, com `git add submissions/gustavo-covaleski/`.
6. **Orçamento:** F2 cortada de 40 para 30 min, total orçado 360. Ordem de corte se a F3b estourar: (a) amostra do LLM de ~400 para ~150 chamadas; (b) curva de cobertura com 3 limiares. Os testes de falha da F5 nunca são cortados.
7. **Tempo:** a F0 levou 60 min contra 15 orçados (+45 min). Com isso, o total projetado é 405 min.

**Também definido no portão:** premissas de custo com sensibilidade; preço do Haiku consultado na página oficial na execução; divisão de trabalho chat × Claude Code; regras de repositório e git; chave de API só em `.env`.

## Erros da IA que eu peguei

| Erro | Como percebi | Correção |
|---|---|---|
| Critério da Q2 invertido: a IA propôs "limite inferior do IC da precisão ≥ taxa de erro do rótulo humano", comparando uma precisão com uma taxa de erro | Revisão do critério no portão F0 | Limite inferior do IC 95% da precisão ≥ 1 − taxa de erro do rótulo humano |
| F1-spec (chat do Projeto) pré-registrou a consequência de cada armadilha, mas não o critério de "confirmada"; o Claude Code definiu os critérios de T1–T8 depois de ver os dados (o de T5 é o mais frágil) | Apontado pelo Claude Code no F1-report, §4 | Registrado como critério definido após ver os dados; decisão sobre T5 no portão F1 |
| F1-report (Claude Code) destacou "360 tickets em 61 grupos com rótulo conflitante", número que infla o ruído: conta todo ticket de um grupo com qualquer conflito | Revisão do chat do Projeto, recalculando a partir de `f1_splits.csv` e do CSV bruto: só 118 tickets discordam da maioria do seu grupo (3,8% dos 3.092 em grupos), e 144 dos 360 estão num único grupo encadeado (Hardware 112, Storage 18, Miscellaneous 14) | Usar 118 / 3,8% como número de ruído entre quase-duplicados; o grupo de 144 vira pista de sobreposição Hardware × Storage para a H2 |

## O que eu acrescentei que a IA sozinha não faria

- **Premissas de custo** editáveis (R$ 35/h com encargos, base CLT ~R$ 3 mil; 3 min/ticket de triagem, citando o PR 227 como origem) e **sensibilidade obrigatória** (2 e 4 min; R$ 25 e R$ 50/h), com a exigência de dizer se a recomendação não se mantém. Origem: decisão minha de negócio.
- **Preço do LLM consultado na fonte oficial** no momento da execução, nunca de memória.
- **Revisão de rótulos feita por mim**, sem sugestão pré-preenchida, para não ancorar o julgamento.
- **Divisão de trabalho com repasse por arquivo** e conferência dos números nos arquivos gerados, não só no relatório.
- **Adjudicação depois da revisão cega**, separando erro do rótulo original, erro meu e ambiguidade, para que a taxa de erro humano não misture os três. Origem: decisão minha de método.
- **Regra de decisão em 3 faixas amarrada ao IC da taxa de erro humano** (automatizar só na meta mais exigente). Origem: decisão minha.
- **Cenário sem etapa de triagem**, em que a economia de triagem é zero, transformado em achado e em justificativa do evento `reatribuido`. Origem: regra de negócio.
- **Regras de repositório:** só a pasta da submissão é alterada; push e PR só no final; dados brutos fora do repositório; chave só em `.env`.
