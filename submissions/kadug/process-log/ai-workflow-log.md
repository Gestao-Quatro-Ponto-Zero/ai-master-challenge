# AI Workflow Log

## Sessao 1 - Entendimento e Arquitetura Inicial

**Data:** 2026-06-28

### Objetivo

Entender as regras do challenge 001 e transformar o direcionamento inicial em arquitetura e plano de execucao.

### Decisoes tomadas

- Challenge escolhido: `data-001-churn`.
- Entrega principal: diagnostico executivo de churn.
- Arquitetura principal: Analytics Core First + Presentation Adapters.
- Dashboard minimo: camada de apresentacao obrigatoria da nossa entrega, consumindo exports prontos.
- Estrategia de produto:
  - cruzar todas as tabelas;
  - transformar dados em narrativas;
  - transformar narrativas em acoes;
  - escrever para stakeholders nao tecnicos.

### Uso de IA

Usei Codex/GPT-5 para:

- ler o README principal, o README do challenge e o guia de submissao;
- identificar os criterios de qualidade;
- decompor a entrega em plano de 4h;
- desenhar uma arquitetura pragmaticamente alinhada ao timebox.

### Julgamento humano aplicado

- O dashboard foi classificado como diferencial, nao como dependencia.
- A analise e o process log foram definidos como itens nao cortaveis.
- A arquitetura favorece contratos simples para integracao futura com hub de ferramentas.
- A estrategia de produto foi separada da arquitetura tecnica para manter clareza entre stack, narrativa e acao.
- A decisao inicial de Angular com Worker foi revisada: Angular fica como possibilidade de produto futuro, nao como stack do challenge.
- Commits por checkpoint foram definidos como evidencia complementar de processo, sem tratar git como cronometro formal.

### Proximas iteracoes

1. Baixar dataset do Kaggle.
2. Validar schema real dos 5 CSVs.
3. Construir primeira camada analitica.
4. Fazer commits de checkpoint usando `git add -f` para a pasta ignorada `submissions/`.
5. Atualizar este log com erros, correcoes e prompts relevantes.

## Sessao 2 - Critiques Externos e Revisao Arquitetural

**Data:** 2026-06-28

### Entradas

- Critique Sonnet Max: `C:\Users\kadug\Downloads\critique-spec-churn.md`
- Critique Opus 4.6 Max: `C:\Users\kadug\Downloads\critique-spec-opus.antgvy.md`

### Decisoes aceitas

- Manter `Analytics Core First + Presentation Adapters`.
- Trocar dashboard Angular por Streamlit.
- Tratar exports como fonte da verdade.
- Adicionar `arr_at_risk` e `segment_size` em `risk_segments`.
- Criar `priority_accounts` como watchlist operacional.
- Criar `data_quality_report.md` antes dos findings.
- Incluir nota de causalidade por finding.
- Separar churn voluntario vs. involuntario quando o dataset permitir.
- Incluir comparacoes churners vs. non-churners com teste estatistico simples quando aplicavel.

### Decisoes rejeitadas ou rebaixadas

- Angular fica fora do escopo do challenge atual. Pode voltar como produto futuro, mas nao vale o custo no timebox.
- Modelo preditivo complexo nao sera prioridade. Se houver score, sera baseado em regras auditaveis.
- NLP sofisticado no feedback textual sera feito apenas se sobrar tempo; reason codes e temas basicos vem primeiro.

### Julgamento humano aplicado

Os dois critiques concordaram que a arquitetura estava correta, mas que a camada de apresentacao estava cara demais. A decisao final preserva a maturidade da arquitetura e troca a tecnologia de dashboard para reduzir risco de entrega.
