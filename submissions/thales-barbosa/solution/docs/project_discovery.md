# FASE 0 — Project Discovery

**Challenge 002 — Redesign de Suporte (G4 Educação · AI Master Challenge)**
**Data da descoberta:** 2026-07-16
**Autor:** Thales Barbosa (com Claude Code)

---

## 1. Objetivo do projeto

Atuar como AI Master da área de Suporte ao Cliente de uma empresa de tecnologia (~30.000 tickets/ano via email, chat, telefone e redes sociais) e responder ao Diretor de Operações:

1. **Onde estamos perdendo tempo?** → Diagnóstico operacional com dados.
2. **O que pode ser automatizado com IA?** → Proposta de automação (incluindo o que NÃO automatizar).
3. **"Me mostre algo rodando."** → Protótipo funcional.

Mais um entregável obrigatório: **Process Log** (sem ele = desclassificado).

---

## 2. Estrutura do repositório local

```
ai-master-challenge-thales/
├── SYSTEM_INSTRUCTIONS.md        ← Plano mestre em 8 fases (fonte de verdade do processo)
├── PROJECT_CONTEXT.md            ← Resumo do objetivo e entregáveis
├── challenge-docs/
│   ├── README-main.md            ← README geral do processo seletivo
│   ├── README-challenge-002.md   ← Brief completo do Challenge 002
│   ├── CONTRIBUTING.md           ← Regras de submissão via Pull Request
│   └── SUBMISSION-GUIDE.md       ← O que enviar e o que torna uma submissão forte/fraca
├── data/
│   ├── customer_support_tickets.csv           ← Dataset 1 (métricas + texto)
│   └── it_service_ticket_classification.csv   ← Dataset 2 (texto classificado)
├── docs/                         ← (vazio; este documento é o primeiro artefato)
├── notebooks/                    ← (vazio)
├── process-log/                  ← (vazio)
├── submissions/                  ← (vazio; destino final: submissions/thales-barbosa/)
└── .venv/                        ← Python 3.13.11, ainda sem pacotes (só pip 25.3)
```

**Validação da estrutura:** ✅ Conforme o plano. Pastas de trabalho existem e estão vazias (esperado — nada foi executado ainda).

**Lacuna identificada:** o arquivo `templates/submission-template.md`, referenciado por CONTRIBUTING.md e SUBMISSION-GUIDE.md, **não está presente na pasta local**. Ação: obter do repositório original do G4 antes da FASE 7 (documentação final). Se indisponível, seguir a estrutura recomendada no SUBMISSION-GUIDE (Executive summary → Abordagem → Resultado → Recomendações → Limitações).

---

## 3. Datasets (verificação factual — contagem via parser CSV)

### Dataset 1 — `customer_support_tickets.csv`
- **8.469 registros × 17 colunas** (verificado por parsing; `wc -l` mostra ~29,8k linhas físicas porque `Ticket Description` contém quebras de linha)
- Fonte: Kaggle — Customer Support Ticket Dataset (CC0)
- Colunas: `Ticket ID`, `Customer Name`, `Customer Email`, `Customer Age`, `Customer Gender`, `Product Purchased`, `Date of Purchase`, `Ticket Type`, `Ticket Subject`, `Ticket Description`, `Ticket Status`, `Resolution`, `Ticket Priority`, `Ticket Channel`, `First Response Time`, `Time to Resolution`, `Customer Satisfaction Rating`

> ⚠️ **Discrepância documentada:** o brief do challenge afirma "~30.000 registros", mas o arquivo real tem **8.469**. Premissa de trabalho: tratar o dataset como **amostra representativa** de uma operação de ~30.000 tickets/ano e extrapolar volumes/custos com essa premissa explícita no modelo de ROI. Limitação a validar na FASE 1 (janela temporal dos dados).

> ⚠️ **Texto sintético/templated:** a `Ticket Description` contém placeholders como `{product_purchased}` e trechos aparentemente aleatórios. Impacto na qualidade de NLP sobre o Dataset 1 será avaliado na FASE 1.

### Dataset 2 — `it_service_ticket_classification.csv`
- **47.837 registros × 2 colunas** (verificado)
- Fonte: Kaggle — IT Service Ticket Classification Dataset (CC0)
- Colunas: `Document` (texto do ticket, já pré-processado/lowercase sem stopwords aparentes), `Topic_group` (8 categorias: Hardware, HR Support, Access, Storage, Purchase, etc. — cardinalidade exata a confirmar na FASE 1)
- Uso principal: treinar/avaliar o **classificador de tickets** e a **busca semântica** (FASES 4–6)

**Critério-chave do challenge:** usar **ambos** os datasets — Dataset 1 dá as métricas operacionais, Dataset 2 dá o corpus de texto classificado. O poder está no cruzamento.

---

## 4. Exigências e entregáveis

| # | Entregável | Obrigatório? | Onde será produzido |
|---|-----------|--------------|---------------------|
| 1 | Diagnóstico operacional (gargalos, drivers de satisfação, desperdício quantificado) | ✅ Obrigatório | FASES 1–3 → `docs/` + notebooks |
| 2 | Proposta de automação com IA (automatizar / parcial / não automatizar + fluxo proposto) | ✅ Obrigatório | FASE 4 → `docs/automation_strategy.md` |
| 3 | Protótipo funcional (Streamlit: dashboards, AI Copilot, ROI Simulator) | 🔶 Diferencial (trataremos como obrigatório) | FASES 5–6 → `solution/app.py` + `src/` |
| 4 | Process Log | ✅ Obrigatório (sem ele = desclassificado) | FASE 8 → `process-log/` (atualização contínua) |

### Formato de submissão
- **Exclusivamente via Pull Request** ao repositório do G4
- Branch: `submission/thales-barbosa` · Pasta: `submissions/thales-barbosa/`
- Título do PR: `[Submission] Thales Barbosa — Challenge 002`
- Só modificar arquivos dentro da própria pasta de submissão
- Estrutura final planejada:

```
submissions/thales-barbosa/
├── README.md                 ← segue submission-template (a obter)
├── solution/
│   ├── app.py                ← Streamlit
│   ├── notebooks/
│   ├── src/
│   ├── docs/
│   ├── assets/
│   └── requirements.txt
└── process-log/
    ├── ai-usage.md
    ├── decisions.md
    ├── iterations.md
    ├── prompts.md
    └── screenshots/
```

---

## 5. Critérios de qualidade (extraídos dos docs do challenge)

**O que os avaliadores checam:**
1. Usou **ambos** os datasets?
2. O diagnóstico tem **números concretos** ou é genérico?
3. A proposta de automação é **realista**? (automatizar 100% é red flag)
4. Sabe distinguir **onde IA ajuda** de onde humano é insubstituível?
5. O protótipo funciona com **dados reais** (não 3 exemplos cherry-picked)?

**O que torna a submissão forte:** entendimento do problema antes de executar; IA usada estrategicamente; output acionável; process log com iteração e julgamento; comunicação clara para técnico e não-técnico.

**O que torna fraca:** output genérico; zero verificação; process log de 1 prompt; documento de 40 páginas onde 5 resolveriam.

**Aviso do G4 sobre baseline:** eles já rodaram o brief em vários modelos de IA. A entrega precisa **superar substancialmente** o que a IA produz sozinha — profundidade, julgamento, execução, criatividade.

**Time budget declarado:** 4–6 horas (inteligência no uso do tempo é avaliada).

---

## 6. Perguntas obrigatórias a responder (com dados)

1. **Onde o fluxo trava?** — gargalos por `Ticket Channel` × `Ticket Type` × `Ticket Priority`; tempos médios/medianas/percentis; piores combinações; horas desperdiçadas.
2. **O que impacta a satisfação?** — efeito de `Time to Resolution`, `First Response Time`, tipo, canal e prioridade sobre `Customer Satisfaction Rating` (Spearman, ANOVA, regressão, Random Forest + feature importance).
3. **Quanto estamos desperdiçando?** — horas/ano, FTE, custo operacional, economia potencial → modelo de ROI com premissas, fórmulas e limitações explícitas.

### Análise especial obrigatória (FASE 1)
Investigar o significado real de `First Response Time` e `Time to Resolution` **sem assumir**:
- **Hipótese A:** Time to Resolution = tempo total desde a abertura.
- **Hipótese B:** Time to Resolution = tempo após a primeira resposta.
- Validar via tempos negativos, coerência, distribuições, percentis e relação entre colunas. Documentar evidências e limitações.

---

## 7. Roadmap das 8 fases e status

| Fase | Descrição | Artefato principal | Status |
|------|-----------|--------------------|--------|
| 0 | Descoberta do repositório | `docs/project_discovery.md` | ✅ **Concluída (este documento)** |
| 1 | Auditoria dos dados (+ análise especial FRT/TTR) | `docs/data_audit.md` + gráficos | ⏭️ **Próximo passo** |
| 2 | Preparação / feature engineering | `docs/feature_engineering.md` | ⬜ |
| 3 | Responder as 3 perguntas do desafio | análises + ROI | ⬜ |
| 4 | Estratégia de automação | `docs/automation_strategy.md` | ⬜ |
| 5 | Machine Learning (classificador + busca semântica) | modelos + métricas | ⬜ |
| 6 | Protótipo Streamlit (dashboards, Copilot, ROI Simulator) | `app.py` | ⬜ |
| 7 | Documentação final | `README.md` da submissão | ⬜ |
| 8 | Process Log (contínuo desde já) | `process-log/*` | 🔄 iniciar em paralelo |

---

## 8. Riscos e pendências registradas na FASE 0

| # | Item | Tipo | Ação |
|---|------|------|------|
| 1 | Dataset 1 tem 8.469 registros, não ~30k | Discrepância | Tratar como amostra; premissa explícita no ROI |
| 2 | `templates/submission-template.md` ausente localmente | Lacuna | Obter do repo original antes da FASE 7 |
| 3 | Texto do Dataset 1 é sintético (placeholders `{product_purchased}`) | Limitação de dados | Avaliar impacto no NLP na FASE 1; usar Dataset 2 como corpus principal de texto |
| 4 | `.venv` sem pacotes instalados | Setup | Instalar dependências (pandas, scipy, sklearn, sentence-transformers, faiss-cpu, streamlit, plotly) e congelar em `requirements.txt` |
| 5 | Repo em branch `master`; submissão exige branch `submission/thales-barbosa` no fork do repo do G4 | Processo | Definir estratégia de git na FASE 7 |
| 6 | Process Log deve ser contínuo | Processo | Criar arquivos do `process-log/` já na próxima fase e atualizar a cada decisão |
