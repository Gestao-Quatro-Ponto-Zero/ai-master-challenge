# PREPARAÇÃO — Case 003 Lead Scorer (G4 AI Master)

**Candidato:** Vitor Veloso (GitHub: `vvitorveloso`)  
**Data de preparação:** 06/11/2026  
**Branch:** `submission/vitor-veloso`  
**Pasta de entrega:** `submissions/vitor-veloso/`  
**Status:** Ambiente preparado — solução a implementar com Vitor em sessão separada.

---

## 1. O que o case 003 pede

**Área:** Vendas / RevOps  
**Tipo:** Build (construir solução funcional, não documento)  
**Time budget:** 4–6 horas

### Contexto do problema

Time comercial com 35 vendedores em escritórios regionais, pipeline de **~8.800 oportunidades**. Hoje a priorização é feita "no feeling". A Head de RevOps quer uma ferramenta funcional — não um notebook no Jupyter — onde o vendedor abra, veja o pipeline e saiba onde focar.

> "Preciso de algo funcional — não um modelo no Jupyter Notebook que ninguém vai usar. Quero uma ferramenta que o vendedor abra, veja o pipeline, e saiba onde focar. Pode ser simples, mas precisa funcionar."

### Dataset

**[CRM Sales Predictive Analytics](https://www.kaggle.com/datasets/agungpambudi/crm-sales-predictive-analytics)** — licença CC0 (uso livre).

| Arquivo | Conteúdo | Registros | Chave |
|---|---|---|---|
| `accounts.csv` | Contas: setor, receita, nº funcionários, localização | ~85 | `account` |
| `products.csv` | Catálogo de produtos com série e preço | 7 | `product` |
| `sales_teams.csv` | Vendedores, manager, escritório regional | 35 | `sales_agent` |
| `sales_pipeline.csv` | **Tabela central**: oportunidades com stage, datas, vendedor, produto, conta, valor | ~8.800 | `opportunity_id` |

**Campos-chave do `sales_pipeline.csv`:**
- `deal_stage`: Prospecting, Engaging, Won, Lost
- `engage_date` / `close_date`: timeline do deal
- `close_value`: valor real de fechamento (0 se Lost)

### Deliverables obrigatórios

#### 1. Solução funcional (a peça principal)
Ferramenta que roda de verdade — não mockup, não PowerPoint.

**Exemplos válidos:**
- Aplicação web (Streamlit, React, HTML+JS)
- Dashboard interativo (Plotly Dash, Retool, Metabase)
- CLI/script que gera relatório priorizado
- API que recebe dados de um deal e retorna score + explicação
- Planilha inteligente com fórmulas de scoring
- Bot que envia prioridades por Slack/email

**Requisitos mínimos:**
- Precisa **rodar** (seguir instruções do README e funcionar)
- Precisa usar os **dados reais** do dataset
- Precisa ter **lógica de scoring/priorização** (não é só ordenar por valor)
- O vendedor precisa entender **por que** um deal tem score alto ou baixo (**explainability**)
- Bonus: filtro por vendedor/manager/região

#### 2. Documentação mínima
- **Setup:** Como rodar (dependências, comandos, URL)
- **Lógica:** Critérios de scoring usados e por quê
- **Limitações:** O que a solução não faz e o que precisaria pra escalar

#### 3. Process log (obrigatório — sem ele = desclassificado)
Evidências de como usou IA para construir. Formatos aceitos:
- Screenshots das conversas com IA (prompts + respostas)
- Screen recording (Loom, gravação de tela)
- Chat export (Claude, ChatGPT, etc.)
- Narrativa escrita: "primeiro fiz X, depois pedi Y ao Claude, ajustei Z porque..."
- Git history mostrando evolução com AI-assisted development

**O process log deve mostrar:**
- Quais ferramentas usou e por quê
- Como decompôs o problema antes de promptar
- Onde a IA errou e como corrigiu
- O que você adicionou que a IA sozinha não faria
- Quantas iterações foram necessárias

### Critérios de avaliação
- A solução funciona de verdade? Dá pra rodar seguindo as instruções?
- O scoring faz sentido? Usa as features certas? Vai além do óbvio?
- O vendedor (não-técnico) consegue usar e entender?
- A interface ajuda a tomar decisão ou só mostra dados?
- O código é limpo o suficiente pra outro dev dar manutenção?

### Dicas do case
- A Head de RevOps não pediu ML perfeito. Pediu algo **útil**. Comece simples, itere.
- Features óbvias: deal stage, tempo no pipeline, tamanho da conta, produto, vendedor. O que mais importa? Olhe os dados.
- Scoring baseado em regras + heurísticas bem apresentado **vale mais** que XGBoost sem interface.
- **Explainability ganha.** Vendedor entendendo POR QUE o deal tem score 85 = ferramenta 10x mais útil.
- Pense no uso real: vendedor abre isso na segunda-feira de manhã. O que ele precisa ver?

---

## 2. Regras de entrega

### Uso de IA (regras críticas)
- **Uso de IA é obrigatório.** O G4 quer ver *como* você usa, não se você usa.
- **Sem evidência de processo = desclassificado automaticamente.** Sem exceção.
- **Colar o prompt não funciona:** A G4 já rodou cada case em múltiplos modelos (Claude, GPT, Gemini) como baseline. Se sua resposta for parecida com esse baseline, você não agregou nada. A entrega precisa **superar substancialmente** o que a IA produz sozinha — em profundidade, julgamento, qualidade de execução ou criatividade.

### Processo de entrega (via Pull Request — único canal aceito)
1. Fork do repositório original → `github.com/vvitorveloso/ai-master-challenge`
2. Clone do fork: `git clone https://github.com/vvitorveloso/ai-master-challenge.git`
3. Branch: `submission/vitor-veloso` (já criada neste repo local)
4. Pasta: `submissions/vitor-veloso/` (já criada neste repo local)
5. Push da branch pro fork: `git push origin submission/vitor-veloso`
6. Abrir PR para `main` com título: `[Submission] Vitor Veloso — Challenge 003`

### Estrutura esperada da pasta de submissão
```
submissions/vitor-veloso/
├── README.md            ← Usar template de templates/submission-template.md
├── solution/            ← Código fonte da ferramenta
│   └── ...
├── process-log/         ← Evidências de uso de IA
│   ├── screenshots/
│   ├── chat-exports/
│   └── ...
└── docs/                ← Documentação adicional
```

### Regras do PR
- Modificar **apenas** arquivos dentro de `submissions/vitor-veloso/` — PRs que alteram outros arquivos são rejeitados
- Um PR por pessoa — se quiser atualizar, push na mesma branch
- Título do PR: `[Submission] Vitor Veloso — Challenge 003`

---

## 3. Checklist — o que falta fazer (sessão futura com Vitor)

### Pré-implementação
- [ ] Fazer o **fork** do repositório para `vvitorveloso/ai-master-challenge` (login no GitHub necessário)
- [ ] Atualizar o remote local: `git remote set-url origin git@github.com:vvitorveloso/ai-master-challenge.git`
- [ ] Baixar o dataset do Kaggle: https://www.kaggle.com/datasets/agungpambudi/crm-sales-predictive-analytics
- [ ] Explorar os dados (EDA rápida): entender distribuição de stages, win rates por vendedor/produto/conta, tempo médio no pipeline
- [ ] Decidir a abordagem da ferramenta (Streamlit? Dashboard? Script? API?)

### Implementação
- [ ] Construir a lógica de scoring com explainability
- [ ] Implementar a interface/ferramenta que o vendedor vai usar
- [ ] Garantir que roda com `README.md` de setup claro
- [ ] Testar com dados reais (não mock)

### Documentação e Process Log
- [ ] Atualizar `submissions/vitor-veloso/README.md` usando `templates/submission-template.md` como base
- [ ] Registrar o process log (screenshots/chat-export/narrativa escrita) em `submissions/vitor-veloso/process-log/`
- [ ] Documentar: lógica do scoring, critérios escolhidos e por quê, limitações
- [ ] Revisar se o process log mostra iteração real (não "1 prompt → 1 resposta → submit")

### Revisão pré-PR
- [ ] A solução **roda** seguindo as instruções do README?
- [ ] Scoring tem explainability (vendedor entende o "por quê")?
- [ ] Process log está completo e evidencia uso inteligente de IA?
- [ ] Nenhum arquivo fora de `submissions/vitor-veloso/` foi modificado?
- [ ] Fork feito e branch `submission/vitor-veloso` pusheada para o fork?

### Entrega
- [ ] `git push origin submission/vitor-veloso` (no fork)
- [ ] Abrir Pull Request: `[Submission] Vitor Veloso — Challenge 003`

---

## 4. Estado atual do ambiente

| Item | Status |
|---|---|
| Repositório original | ✅ Público, não arquivado, 2 branches, 5 commits |
| Clone local | ✅ `/home/vitor/g4-ai-master` (clonado do original) |
| Branch | ✅ `submission/vitor-veloso` criada |
| Pasta de submissão | ✅ `submissions/vitor-veloso/` criada |
| Fork no GitHub | ⏳ **Pendente de login** — GitHub não estava logado no neo; username confirmado: `vvitorveloso`; SSH auth funciona |

**Nota sobre o fork:** O SSH com a chave `~/.ssh/github` autentica como `vvitorveloso` ✅. Para fazer o fork, basta logar no GitHub no BrowserOS neo e acessar https://github.com/Gestao-Quatro-Ponto-Zero/ai-master-challenge → Fork. Depois atualizar o remote: `git remote set-url origin git@github.com:vvitorveloso/ai-master-challenge.git`.
