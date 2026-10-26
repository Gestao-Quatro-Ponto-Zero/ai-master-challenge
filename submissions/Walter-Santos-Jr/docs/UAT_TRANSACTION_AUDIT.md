# G4 AI Master Challenge 003 — Auditoria UAT e Transacional RC4 | V2

**Data:** 26/10/2026  
**Baseline imutável:** `G4_Challenge_003_RC4_DEV_Manager_Sector_Light_Fix_Walter-Santos-Jr.zip`  
**Fontes:** `uat_evidencias(3).zip`, testes e código contidos no ZIP RC4, `G4_RC4_CROSS_AUDIT_V1.md`.  
**Escopo:** inspeção visual de imagens estáticas, execução de testes e verificação transacional isolada. Não é certificação de produção ou de impacto econômico.

## 1. Inventário visual e rastreabilidade UAT

As 12 imagens foram abertas em conjunto para inspeção visual (contact sheet). Todas têm resolução original próxima de 4400 × 2128 pixels. As capturas contêm anotações e textos de orientação produzidos durante a coleta UAT; estes são explicações do usuário, não logs de execução.

| Evidência | O que é visível | Critério apoiado | Limite da evidência |
|---|---|---|---|
| `uat-01.png` | Head — Executive Command Center, indicadores e visão executiva | Visão Head e KPIs presentes | Captura não valida fórmulas ou origem dos números |
| `uat-02.png` | Head — filtros de região/manager/setor e indicadores segmentados, com anotações | Segmentação gerencial e estrutura de filtros | Captura isolada não prova recálculo nem compara filtros antes/depois |
| `uat-03.png` | Manager — filtros regionais/gerenciais/setoriais e visão de desempenho | Workspace Manager e escopo gerencial | A igualdade quantitativa Head × Manager requer teste de dados |
| `uat-04.png` | Seller — pipeline, scores, painéis e ações | Priorização e visualização de oportunidades | Não prova ordenação correta em todos os casos |
| `uat-05.png` | Seller — Opportunity 360, score e componentes explicativos | Explicabilidade e contexto do deal | Não substitui validação da fórmula |
| `uat-06.png` | Seller — modal de qualificação com campos de decisão | Entrada de qualificação e fluxo de Rework | Não comprova persistência após F5 |
| `uat-07.png` | Seller — formulário de fechamento Won | Presença de fluxo Won e dados de fechamento | Captura do formulário não comprova transação concluída |
| `uat-08.png` | Seller — formulário de fechamento Lost e motivo | Presença de fluxo Lost e motivo de perda | Captura do formulário não comprova transação concluída |
| `uat-09a.png` | Seller — pipeline original e fila de Rework | Estado inicial de referência | Comparação depende da sequência completa |
| `uat-09b.png` | Rework — pendência de Account em detalhe | Identificação de causa de bloqueio e fila de pendências | Evidência de UI, não da regra de banco isoladamente |
| `uat-09c.png` | Rework — Account corrigida e feedback da operação | Correção cadastral e feedback | Não prova validação em cadastro mestre externo |
| `uat-09d.png` | Seller — retorno ao pipeline após correção | Visibilidade após Rework | Sequência documentada pelo usuário; não é replay automatizado |

**Parecer visual:** cobertura documental consistente com os cenários planejados; nenhuma sobreposição crítica óbvia na visualização conjunta. **Não declarar homologação independente de todos os estados de navegador** sem sessão interativa reproduzida. Em particular, o contraste Dark/Light não foi comparado como teste A/B nesta auditoria.

## 2. Regressão automatizada — execução reproduzida

Em uma cópia extraída isoladamente do ZIP RC4:

```text
python -m pytest -q --disable-warnings --maxfail=1
101 passed in 9.42s
```

**Resultado:** PASS (101/101). A suíte inclui verificações de hierarquia, escopo Manager/Head, score, sincronização de qualificação/Rework, ausência de deadlock no fechamento e overlay de closures. Não equivale a teste de navegador ou a mensuração de uplift comercial.

## 3. Verificação transacional independente — banco temporário

Foi utilizado `tempfile.TemporaryDirectory()` para definir `app.DB_PATH` para um banco novo e isolado; a aplicação RC4 foi importada sem alterar os arquivos originais. Selecionou-se uma oportunidade do CSV operacional, com `quality_gate` elegível e estágio aberto. O teste:

1. Registrou qualificação positiva (`decision_maker=yes`, `timeline=yes`, `budget=yes`).
2. Confirmou ausência de jobs pendentes na oportunidade escolhida.
3. Executou `close_deal(..., outcome='Won', close_value=1234.56, evidence=..., actor='AUDIT')`.
4. Consultou `deal_closures` e `reconciled_historical_rows()`.

**Resultado observado:**

| Indicador | Antes | Depois |
|---|---|---|
| Oportunidade `5URQT67R` | Engaging | Won |
| Total de linhas históricas reconciliadas | 8.800 | 8.800 |
| Ocorrências do ID na visão reconciliada | 1 | 1 |
| Registros de fechamento para o ID | 0 | 1 |
| `closure_source` | `historical_csv` | `operational_sqlite` |
| `close_value` | sem fechamento operacional | `1234.56` (valor de teste) |

**Resultado:** PASS para este cenário específico. O código implementa overlay por `opportunity_id`, substituindo os campos de estágio, data e valor sem acrescentar linha histórica duplicada. O valor 1234.56 é sintético, criado somente para testar persistência, **não receita real**.

### Limites transacionais

- A reconciliação por ID e a persistência Won foram demonstradas em uma transação; isso não prova exaustivamente todas as combinações de filtros, todos os KPIs ou cenários Lost.
- A suíte `test_rc4_kpi_reconciliation.py` valida unicidade dos IDs e correspondência do estágio com `deal_closures`; `test_rc4_manager_sector.py` confronta contagens de Head/Manager por região e setor. A suíte **não constitui uma auditoria independente de todas as fórmulas financeiras**.
- Não foi medida latência, concorrência multiusuário real, segurança de autenticação ou causalidade de conversão.
- A validação visual das capturas depende de estados registrados pelo usuário, e não de uma navegação autônoma no navegador nesta auditoria.

## 4. Rastreabilidade BIOS

| Decisão BIOS | Evidência de execução | Evidência de validação |
|---|---|---|
| Business First → decisão acionável | Workspaces Head/Manager/Seller e Opportunity 360 | UAT-01 a UAT-05 |
| Scoring explicável e dimensões separadas | `scoring_v3.py` e `SCORING_POLICY_V3.md` | Testes da política e UAT-05 |
| Quality Gate + Human-in-the-Loop | Qualificação, Account Correction, Rework | UAT-06, UAT-09a–d; testes de sincronização |
| Closed Loop → execução rastreável | `close_deal`, `deal_closures`, `sales_action_events` | Teste transacional isolado; UAT-07/08 como evidência da UI |
| Governança e reconciliação | `reconciled_historical_rows()` | 101 testes + cenário de overlay sem duplicação |
| Value Realization | Métricas e proposta de mensuração | Impacto incremental **não demonstrado** |

## 5. Gate de liberação

| Item | Status |
|---|---|
| 12 evidências visuais presentes e examinadas | PASS — inspeção de capturas |
| 101 testes automatizados | PASS — execução isolada |
| Persistência de um fechamento Won e overlay por ID | PASS — cenário isolado |
| Reconciliação de contagens Head/Manager por setor | PASS — testes automatizados |
| Validação de todos os KPIs financeiros em todos os filtros | PARCIAL — requer auditoria específica |
| Sessão UAT independente em navegador e Dark/Light | PENDENTE |
| Auditoria histórica completa do Process Log | EM ANDAMENTO |
| Submission Pack definitivo / Pull Request | PENDENTE |

**Decisão recomendada:** prosseguir com a montagem documental sem modificar o código homologado; manter os itens parciais explícitos até o gate final.
