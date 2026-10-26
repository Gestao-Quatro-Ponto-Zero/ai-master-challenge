# G4 AI Master Challenge 003 — Sales Execution Cockpit (RC4)

> **Status:** RC4 homologada funcional e visualmente pelo usuário. Aplicação local de demonstração, não produto pronto para produção.

## Visão geral

Cockpit de execução comercial para três perspectivas: **Head de RevOps**, **Manager** e **Seller**. Combina análise do pipeline, priorização explicável, qualificação, fila de Rework, histórico e encerramento de oportunidades (Won/Lost). A solução utiliza snapshots históricos de CRM, CSVs de demonstração e persistência operacional em SQLite. **Não pressupõe Salesforce nem conexão ativa com CRM externo.**

## Guia visual rápido

| Persona | Evidência | O que observar |
|---|---|---|
| Head | ![Head Executive Command Center](docs/uat_evidencias/uat-01.png) | Visão executiva e KPIs |
| Head | ![Head filtros](docs/uat_evidencias/uat-02.png) | Segmentação por região, gerente e setor |
| Manager | ![Manager](docs/uat_evidencias/uat-03.png) | Indicadores e filtros comparáveis aos do Head |
| Seller | ![Seller Pipeline](docs/uat_evidencias/uat-04.png) | Pipeline e priorização |
| Seller | ![Opportunity 360](docs/uat_evidencias/uat-05.png) | Contexto e decisão por oportunidade |

As 12 evidências e o roteiro completo estão em [USER_GUIDE.md](USER_GUIDE.md) e [UAT_EVIDENCE.md](UAT_EVIDENCE.md).

## Execução local

Requisito: **Python 3.10+**. O servidor utiliza a biblioteca padrão do Python; `requirements.txt` não exige pacotes externos para executar o app.

```bash
cd solution
python app.py
```

Acesse **http://127.0.0.1:8050** e escolha Head, Manager ou Seller na tela de seleção de persona. Para alterar a porta, defina a variável de ambiente `PORT`. Para direcionar o SQLite a um arquivo isolado, use `G4_DB_PATH`.

**Importante:** o arquivo `data/workspace.sqlite3` distribuído é um snapshot operacional de demonstração. Para avaliar um ambiente novo sem alterar o snapshot, configure `G4_DB_PATH` apontando para outro arquivo SQLite. Não apague a base original para realizar testes.

## Principais workflows

- **Head:** filtrar região, gerente e setor; analisar indicadores executivos e segmentos.
- **Manager:** selecionar região e gerente; aplicar o filtro de setor e examinar desempenho.
- **Seller:** selecionar vendedor; consultar pipeline, Opportunity 360, Next Best Action, qualificação e histórico.
- **Rework:** detectar pendência, executar ação corretiva, verificar o resultado e retornar o Deal ao fluxo comercial.
- **Deal Closure:** registrar Won com valor negociado e evidência, ou Lost com motivo e evidência. Fechamentos operacionais persistem no SQLite e alimentam a reconciliação dos indicadores.

## Modelo de priorização

A pontuação é uma **heurística explicável de suporte à decisão**, não uma probabilidade de conversão calibrada. Consulte [SCORING_POLICY_V3.md](SCORING_POLICY_V3.md) e `scoring_v3.py` para a política e seus detalhes. Não confundir **preço de catálogo**, **valor negociado no fechamento** e **receita faturada**.

## Verificação

```bash
python -m pytest -q
python -m unittest discover -s tests -v
```

Na auditoria de 26/10/2026, `pytest` executou **101 testes com sucesso**. A validação de sintaxe de `static/app.js` com `node --check` e a compilação dos módulos Python também passaram. Os prints documentam a homologação visual, mas não substituem os testes automatizados.

## Limitações e governança

- **Demo Mode:** seleção de persona livre para avaliação; não é autenticação corporativa com SSO/MFA.
- O backend implementa controles de escopo por persona, mas não deve ser exposto à internet ou receber dados corporativos sensíveis sem revisão de segurança.
- Dados históricos de CRM são snapshots, não sincronização em tempo real.
- Indicadores históricos e encerramentos operacionais usam reconciliação; não representam faturamento efetivo.
- O ganho de receita não foi demonstrado causalmente; não declarar uplift financeiro medido.

## Documentação

- [USER_GUIDE.md](USER_GUIDE.md) — instruções ilustradas de uso.
- [ARCHITECTURE.md](ARCHITECTURE.md) — arquitetura, fluxos e decisões.
- [UAT_EVIDENCE.md](UAT_EVIDENCE.md) — inventário e critérios das 12 evidências.
- [SUBMISSION_CHECKLIST.md](SUBMISSION_CHECKLIST.md) — verificações antes da submissão.
- [PROCESS_LOG.md](PROCESS_LOG.md) — registro histórico de desenvolvimento.
- [README_RC4.md](README_RC4.md) e demais `README_RC4_*` — documentação incremental original, preservada para rastreabilidade.

## Estrutura

```text
solution/
  app.py                 # servidor HTTP, regras e APIs
  scoring_v3.py          # política de scoring
  static/                # interface HTML, CSS, JS
  data/                  # CSVs e snapshot SQLite
  tests/                 # testes automatizados
  docs/uat_evidencias/   # 12 capturas homologadas
  README.md              # esta visão consolidada
```
