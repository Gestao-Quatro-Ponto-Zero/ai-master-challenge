# Submissão — Bruno Reis — Challenge 002

## Sobre mim

- **Nome:** Bruno Reis
- **LinkedIn:** [linkedin.com/in/brunoreis](https://linkedin.com/in/brunoreis)
- **Challenge escolhido:** 002 — Redesign de Suporte

---

## Executive Summary

Analisei dois datasets complementares (~30K tickets operacionais + ~48K tickets classificados) para diagnosticar gargalos na operação de suporte e construir uma solução de automação assistida. O principal achado: a combinação Chat × Refund Request × High Priority concentra o pior TTR mediano da operação (16.7h — 43% acima do benchmark interno P25), e a correlação entre tempo de resposta e satisfação é praticamente nula (Spearman -0.01), indicando que o problema não é velocidade isolada, mas sim **onde** o tempo é gasto. A recomendação principal é implementar roteamento inteligente com human-in-the-loop, começando pelos fluxos de menor criticidade, onde o classificador SVM (Macro F1 0.853) tem maior confiança — o protótipo funcional entregue já demonstra esse fluxo rodando com dados reais.

---

## Solução

### Abordagem

Decompus o problema em três frentes, nesta ordem:

1. **Diagnóstico Operacional (Dataset 1)** — Comecei entendendo *onde* a operação perde tempo. Limpei os dados, converti timestamps em proxies de horas relativas, e cruzei TTR/FRT por canal × tipo × prioridade para encontrar os gargalos reais. Também testei correlação Spearman entre tempos e satisfação para validar (ou refutar) a hipótese de que "responder mais rápido = cliente mais feliz".

2. **Modelagem e Estratégia (Dataset 2)** — Treinei um classificador TF-IDF + Linear SVM (SGDClassifier) nos 47.8K tickets classificados em 8 categorias. Construí um motor de busca por similaridade (TF-IDF + Cosine Similarity) para sugerir tickets resolvidos similares. Defini limiares de confiança (55% / 75%) e regras de sensibilidade por categoria para separar o que pode ser automatizado do que exige julgamento humano.

3. **Protótipo Funcional (Flask + SPA)** — Construí um dashboard completo que materializa a estratégia: Kanban de triagem com 3 colunas (Escalar / Revisão Humana / Auto-rotear), detalhe de ticket com barra de confiança e badges de sensibilidade, classificador em tempo real, e busca de similares. A interface usa dark theme premium, responsiva e pronta para deploy em VPS.

### Resultados / Findings

**1. Diagnóstico — Onde o fluxo trava (Dataset 1)**

| Gargalo | Canal | Tipo | TTR Mediano | Volume | Desperdício |
|---------|-------|------|-------------|--------|-------------|
| #1 | Chat | Refund Request (High) | 16.7h | 41 | 205h |
| #2 | Chat | Product Inquiry (Low) | 18.5h | 28 | 190h |
| #3 | Social Media | Product Inquiry (High) | 17.2h | 32 | 176h |

- **Desperdício total estimado**: ~5.337h sobre 37.098h totais (14%), usando benchmark interno P25.
- **Satisfação**: sem correlação com TTR/FRT (Spearman -0.01 / -0.04). Diferenças aparecem mais por segmento — pior canal: Phone (2.95); pior tipo: Refund Request (2.93).

> Relatório completo: [docs/diagnostic_summary.md](./docs/diagnostic_summary.md)

**2. Proposta de Automação — O que automatizar e o que NÃO (Datasets 1+2)**

| Ação | Quando | Justificativa |
|------|--------|---------------|
| **Auto-rotear** | Confiança ≥ 75% + categoria não-sensível | Billing, Storage, Internal Project têm alto F1 e baixo risco |
| **Revisão humana** | Confiança 55-75% OU categoria sensível | Access (F1 0.90 mas risco de segurança), Purchase (risco financeiro) |
| **Escalar** | Confiança < 55% | Hardware × HR Support × Misc (confusão recorrente: 184 casos) |

**O que NÃO automatizar e por quê:**
- **Access / Administrative Rights**: mesmo com confiança alta, envolvem permissões e segurança — erro = exposição de dados.
- **Purchase**: risco financeiro direto — aprovação humana obrigatória.
- **Qualquer ticket com confiança < 55%**: o classificador confunde Hardware ↔ HR Support ↔ Miscellaneous nessa faixa.

**Fluxo proposto ponta a ponta:**
1. Ticket entra → classificador retorna categoria + confiança
2. Motor de similaridade recupera top 5 tickets resolvidos similares
3. Regras de negócio decidem: Auto-rotear / Revisão / Escalar
4. Agente recebe ticket já categorizado + sugestões de resolução
5. Feedback do agente alimenta re-treino (loop de melhoria contínua)

> Estratégia completa: [docs/ticket_automation_strategy.md](./docs/ticket_automation_strategy.md)

**3. Protótipo Funcional**

Dashboard SPA com Flask servindo API REST + frontend JS puro:

![Dashboard — KPIs, distribuição por categoria e por ação recomendada](./process-log/screenshots/dashboard_initial_state_1774365697498.png)

![Kanban Board — 3 colunas de triagem com 100 tickets reais do Dataset 2](./process-log/screenshots/kanban_board_1774365719574.png)

**Como rodar:**
```bash
cd submissions/bruno-reis/solution
pip install -r requirements.txt
python app.py
# Acesse http://localhost:8000
```

O protótipo processa 100 tickets reais do Dataset 2, classificando cada um em tempo real e organizando-os no Kanban por ação recomendada. O classificador e o motor de similaridade são treinados no startup da aplicação.

### Recomendações

1. **Começar pelo roteamento assistido** — O auto-route para categorias de baixa criticidade (Billing, Product Inquiry) já pode economizar ~190h/mês com risco mínimo. É o quick win.
2. **Calibrar limiares por categoria** — Os 55%/75% são ponto de partida; em produção, monitorar confiança vs. acurácia real por categoria e ajustar.
3. **Investir no motor de similares** — A busca TF-IDF/Cosine já sugere resoluções passadas. Integrar isso como "Macros sugeridas" na ferramenta do agente reduz retrabalho.
4. **Não automatizar respostas (ainda)** — Auto-resposta só em piloto controlado, opt-in, começando por FAQs. Rollout amplo sem medir precisão real é risco.

### Limitações

- **Semântica dos textos**: Os campos de resolução do Dataset 1 contêm muito ruído textual (placeholders, frases genéricas), limitando inferências causais a partir do texto.
- **Taxonomia cruzada**: Dataset 1 tem 5 tipos de ticket e Dataset 2 tem 8 categorias — o mapeamento é conceitual, não 1:1, o que impede cruzamento direto.
- **Métricas de tempo são proxies**: TTR/FRT foram derivados de timestamps relativos, não de SLAs reais. Os ganhos estimados são comparativos, não valores absolutos.
- **Classificador baseline**: Macro F1 de 0.853 é um bom começo, mas embeddings (BERT/sentence-transformers) provavelmente melhorariam o recall nas classes menores (Administrative Rights: F1 0.727).

---

## Process Log — Como usei IA

> **Este bloco é obrigatório.** Sem ele, a submissão é desclassificada.

### Ferramentas usadas

| Ferramenta | Para que usou |
|------------|--------------|
| **Antigravity (Agente de IA autônomo)** | Orquestração completa: análise exploratória, geração de código Python, pipeline de ML, construção do frontend e verificação automatizada. |
| **Python + Pandas + Scikit-learn** | Limpeza de dados, análise estatística cruzada (TTR × canal × tipo × prioridade), treinamento do SVM e motor de similaridade TF-IDF. |
| **Flask** | Backend do protótipo — API REST para servir classificações, tickets e estatísticas. |
| **Browser Subagent** | Verificação automatizada da UI: navegação em todas as páginas, teste de classificação em tempo real, captura de screenshots como evidência. |

### Workflow

1. **Decomposição do problema** — Antes de promptar qualquer IA, li o challenge inteiro e separei mentalmente em 3 entregas: diagnóstico (Dataset 1), estratégia (cruzamento 1+2), e protótipo (Dataset 2). Isso evitou o erro comum de pular direto pro código.

2. **Análise exploratória (Dataset 1)** — Pedi à IA para carregar o CSV, padronizar colunas, e gerar análises cruzadas de TTR/FRT por canal × tipo × prioridade. Revisei cada output e pedi que calculasse correlação Spearman (satisfação ~ tempo) para validar minha hipótese de que TTR não é o único fator de insatisfação. A correlação de -0.01 confirmou.

3. **Treinamento do classificador (Dataset 2)** — Instruí a IA a construir um pipeline TF-IDF + SGD Classifier, avaliar com classification_report, e gerar matriz de confusão visual. Foram 3 iterações: a primeira usava CountVectorizer (pior resultado), a segunda TF-IDF sem sublinear_tf, a terceira com sublinear_tf=True e max_features=50K (resultado final: F1 0.853).

4. **Definição de regras de negócio** — Aqui entrou meu julgamento: defini manualmente quais categorias são "sensíveis" (Access, Administrative Rights, Purchase) e por quê. A IA não tem como saber que um erro de classificação em "Access" pode significar exposição de dados — esse contexto veio de mim.

5. **Construção do protótipo** — Pedi um Flask app com endpoints REST. A IA gerou a primeira versão com um layout básico. Depois, enviei uma imagem de referência (dashboard dark moderno) e pedi redesign completo. A IA gerou CSS/HTML/JS para uma SPA com Kanban, mas precisei de 2 iterações pra corrigir responsividade mobile e animação dos contadores.

6. **Verificação automatizada** — Usei o browser subagent para navegar pelo Dashboard, Kanban, Detalhe de Ticket e Classificação Manual, capturando screenshots em cada etapa. Testei com o texto "I cannot access my email account" e o sistema retornou "Access" com 97.4% de confiança + "Revisão Humana" (correto: categoria sensível).

### Onde a IA errou e como corrigi

- **Automação agressiva**: A primeira versão da estratégia sugeria auto-resposta para qualquer ticket com confiança > 70%. Corrigi para: auto-*roteamento* (não resposta) apenas acima de 75%, e revisão humana obrigatória para categorias sensíveis independente da confiança.

- **Confusão de métricas**: A IA inicialmente tratou First Response Time e Time to Resolution como durações absolutas em horas. Na verdade, os valores no dataset são timestamps relativos. Corrigi explicitando que são proxies comparativas, não SLAs reais — isso mudou toda a narrativa do diagnóstico.

- **Layout mobile**: A sidebar do dashboard ficava sobre o conteúdo em telas pequenas. Instruí a IA a implementar menu colapsável com botão hambúrguer e overlay semitransparente.

- **CountVectorizer vs TF-IDF**: A primeira versão do classificador usava CountVectorizer simples. O F1 era 0.82. Pedi para trocar por TfidfVectorizer com sublinear_tf=True, o que subiu para 0.853.

### O que eu adicionei que a IA sozinha não faria

- **Julgamento de risco por categoria**: A decisão de que Access, Administrative Rights e Purchase nunca devem ser 100% automatizadas é uma decisão de negócio, não estatística. O modelo pode ter 95% de confiança em "Access", mas um falso positivo nessa categoria é exposição de dados. Esse tipo de regra vem de experiência com operações, não de um classificador.

- **Kanban por ação, não por status**: A organização natural seria por status (Aberto/Pendente/Fechado). Optei por organizar por *ação recomendada* (Escalar/Revisar/Auto-rotear) porque isso é o que um supervisor de suporte precisa ver no dia a dia: "o que precisa da minha atenção agora?"

- **Honestidade sobre limitações**: A IA tende a apresentar resultados de forma otimista. Eu forcei a inclusão de limitações reais: ruído nos textos, taxonomia cruzada imperfeita, métricas proxy. Isso é o que separa uma análise séria de um output genérico.

- **Estimativa de ROI conservadora**: Em vez de projetar cenários otimistas, usei cenário A (30% dos tickets, 20% de redução) = ~2.226h e cenário B (20% sobre desperdício) = ~1.068h. Números conservadores que um Diretor de Operações pode levar a sério.

---

## Evidências

- [x] Screenshots do protótipo funcionando (ver `process-log/screenshots/`)
- [x] Screen recording do workflow de verificação (`process-log/screenshots/ui_verification_1774365678693.webp`)
- [x] Narrativa escrita detalhada (`process-log/PROCESS_LOG.md`)
- [x] Git history com evolução do código
- [x] Protótipo funcional rodando com dados reais em `solution/`

---

_Submissão enviada em: 25/03/2026_
