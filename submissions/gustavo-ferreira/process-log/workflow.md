# Process Log — Narrativa Escrita

> **Formato escolhido:** Narrativa escrita — passo a passo documentando raciocínio, prompts, erros, correções, e decisões que tomei por conta própria.

---

## Antes de tudo: como decompus o problema

Comecei lendo o README do challenge duas vezes. Na primeira leitura, foquei no contexto: empresa com ~30K tickets/ano, Diretor de Operações pedindo diagnóstico + automação + protótipo. Na segunda, foquei nos critérios de avaliação. Dois me chamaram atenção:

- *"Automatizar 100% é red flag"* — ou seja, o avaliador quer ver que eu sei onde parar
- *"Usou ambos os datasets?"* — preciso cruzar os dois, não usar só um

Antes de abrir qualquer ferramenta de IA, documentei minhas hipóteses:
1. "CSAT provavelmente correlaciona com tempo de resolução — clientes que esperam mais devem ficar mais insatisfeitos"
2. "Os textos das descrições devem ter padrões suficientes para treinar um classificador NLP"
3. "O Dataset 2 (48K tickets de TI) pode complementar o Dataset 1 na classificação via transfer learning"
4. "Prioridade deve influenciar tempo de resolução — tickets Critical devem ser resolvidos mais rápido"

Essas hipóteses guiaram minha exploração inicial. Spoiler: **todas estavam erradas**, e descobrir isso mudou completamente minha abordagem.

---

## Ferramentas de IA que usei e por quê

| Ferramenta | Para quê | Por que esta |
|------------|----------|-------------|
| **Claude Opus 4.6 (via Antigravity/Cursor)** | EDA, código Python, protótipo Streamlit, documentação | Minha ferramenta principal — permite iteração com contexto do projeto inteiro no editor |
| **Python + Pandas** | Análise dos datasets, cálculos estatísticos | Padrão da indústria para dados tabulares |
| **Plotly** | Gráficos interativos | Renderiza no Streamlit com zoom/hover, melhor que matplotlib estático |
| **Streamlit** | Protótipo funcional | O avaliador roda com `streamlit run app.py` em 30 segundos |

Não usei ChatGPT, Gemini, ou outra ferramenta. O Claude foi meu único assistente de IA.

---

## Passo a passo: o que fiz, o que pedi, o que rejeitei

### Passo 1 — Download e primeira olhada nos dados

Baixei os datasets do Kaggle e pedi à IA para fazer uma EDA inicial: shape, dtypes, nulos, distribuições.

**Primeiro problema:** a IA tentou calcular `mean()` na coluna `First Response Time`. Deu erro de tipo. Ela assumiu que FRT era um número (horas), mas na verdade é uma string datetime. Eu corrigi manualmente: inspecionei as 10 primeiras linhas e vi timestamps tipo `2023-06-01 12:15:36`.

Aí reparei algo estranho: as compras são de 2020-2021, mas os FRT/TTR são todos de maio-junho de 2023. Pedi à IA para calcular a diferença entre `Date of Purchase` e `First Response Time`. O gap médio foi de mais de 2 anos. **Os timestamps foram gerados independentemente dos dados de compra.**

Mais: pedi para calcular `Time to Resolution` - `First Response Time` e 49% dos resultados eram negativos. Ou seja, o ticket foi "resolvido" antes de receber a primeira resposta. Impossível na vida real.

**Iterações:** 3. A primeira falhou no tipo. A segunda eu ajustei para datetime. A terceira confirmou o paradoxo temporal.

### Passo 2 — CSAT: a maior armadilha dos dados

A IA gerou gráficos de CSAT por canal, tipo e prioridade. Os números vieram assim:
- Chat: 3.08
- Phone: 2.95
- Email: 3.01
- Social media: 2.98

A IA interpretou: *"Chat é o canal com melhor satisfação. Recomendo investir em chat."*

**Eu rejeitei essa análise.** A diferença entre o maior e o menor CSAT é de 0.13 ponto numa escala de 5. Isso não é insight, é ruído. Pedi para a IA me mostrar a distribuição bruta de CSAT (contagem por nota):

| Rating | Contagem |
|--------|----------|
| 1 | 553 |
| 2 | 549 |
| 3 | 580 |
| 4 | 543 |
| 5 | 544 |

~550 por nota. **Perfeitamente uniforme.** Correlação de Pearson entre CSAT e tempo de resolução: r = -0.001. Minha hipótese 1 estava errada — não é que não correlaciona, é que **CSAT é dado aleatório**.

A IA não teria chegado nessa conclusão sozinha. Ela geraria o gráfico bonito de correlação e seguiria em frente.

**Iterações:** 2. Uma para a análise inicial (que rejeitei). Outra para a distribuição bruta (que revelou o problema).

### Passo 3 — Os textos: outra bomba

Pedi à IA para mostrar 5 exemplos completos de `Ticket Description`. O resultado:

> *"I'm having an issue with the {product_purchased}. Please assist."*

Placeholder literal. `{product_purchased}` aparece como texto, não substituído. Pedi para verificar a porcentagem: **100% dos tickets contêm esse placeholder.**

Depois pedi exemplos de `Resolution`:

> *"Try capital clearly never color toward story"*

Gibberish. Palavras aleatórias. Sem estrutura frasal. Sem valor semântico.

A IA tinha proposto "fazer análise de sentimento nas descrições". Eu descartei por completo. Também tinha sugerido "usar os textos de resolução para construir uma base de FAQ". Descartei também — são palavras aleatórias.

**Iterações:** 1. Bastou ver os exemplos.

### Passo 4 — Dataset 2: esperança e frustração

Com o Dataset 1 comprometido textualmente, olhei o Dataset 2 com esperança. 48K tickets com categorias. Pedi à IA para mostrar exemplos de texto:

> *"microsoft locat server new locat appl mobil open safari chrome browser..."*

Textos tokenizados. Stopwords removidas. Não é linguagem natural. Também pedi a distribuição de categorias: 8 categorias, com "Access/Login" dominando (33%).

A IA sugeriu: *"Podemos treinar um classificador TF-IDF no Dataset 2 e aplicar no Dataset 1 para categorizar automaticamente."*

**Eu rejeitei.** Dois problemas fundamentais:
1. **Domain shift**: Dataset 2 é TI corporativa (Hardware, HR Support, Storage). Dataset 1 é suporte B2C (Billing, Refund, Cancellation). As categorias são diferentes.
2. **Formato**: Dataset 2 tem textos tokenizados. Dataset 1 tem templates com placeholders. Nenhum representa linguagem real.

**Iterações:** 2. Uma para explorar o Dataset 2. Outra para rejeitar a proposta de transfer learning.

### Passo 5 — O pivô: foco na SOLUÇÃO, não nos DADOS

Neste ponto eu parei de codar e pensei. Minha estratégia original estava toda baseada em premissas que se provaram falsas:

1. ~~Analisar correlações nos dados~~ → dados são ruído
2. ~~Treinar classificador NLP nos textos~~ → textos são sintéticos
3. ~~Usar Dataset 2 para transfer learning~~ → domain shift
4. ~~Correlacionar CSAT com variáveis~~ → CSAT é aleatório

**Decisão que tomei sozinho (sem a IA):** Chega de tentar extrair valor de dados ruins. Vou **pivotar o foco dos dados para a solução**.

O que isso significa na prática:
- O diagnóstico vai usar o que é **válido** nos dados (status, tipo, volume, canal) e vai ser **transparente** sobre o que é lixo (CSAT, timestamps, textos)
- O protótipo vai funcionar com **texto real** digitado pelo avaliador, não com os dados sintéticos
- O design de processo (4 níveis de roteamento) é **independente da qualidade dos dados** — é design de operação, não resultado de ML

A IA não teria tomado essa decisão. Se eu seguisse no automático, ela continuaria gerando análises de correlação, treinando modelos, produzindo métricas bonitas — tudo sobre ruído.

**Iterações:** 0. Foi decisão 100% minha.

### Passo 6 — Construção do diagnóstico

Pedi à IA para criar um script Python modular que gerasse um JSON com todos os achados. Especifiquei:
- 4 módulos: gargalos, CSAT, desperdício financeiro, qualidade dos dados
- Premissas financeiras explícitas: R$45/hora agente, AHT 20 min
- Output JSON para alimentar o dashboard

Inicialmente ela propôs usar `matplotlib` para gerar gráficos estáticos dentro do script. Eu neguei — os gráficos vão ficar no Streamlit com Plotly, o script só precisa gerar os dados. Simplificou bastante.

Também sugeri valores diferentes para as premissas financeiras. A IA tinha colocado R$60/hora e AHT 15 min (que daria uma economia inflada de ~R$70K). Eu ajustei para R$45/hora e 20 min — mais conservador e realista para o mercado brasileiro. Prefiro ser credível a impressionar com números inflados.

A versão final rodou de primeira. Resultado: R$42.405/ano de economia, 33.4% dos tickets automatizáveis.

**Iterações:** 2. Uma para acertar o escopo (tirar gráficos). Outra para ajustar premissas.

### Passo 7 — Construção do protótipo Streamlit

Pedi à IA para criar o app com 3 tabs: Dashboard, Simulador, Proposta.

**O que ajustei na primeira versão:**

1. A IA propôs classificação chamando API do Gemini. Eu neguei — queria que funcionasse **offline**, sem chave de API. O avaliador não deveria precisar configurar nada. Pedi para usar classificação por regras semânticas (keywords em português).

2. A IA gerou exemplos de tickets em inglês. Eu mandei refazer em português. Os exemplos precisam soar como um cliente brasileiro real falando.

3. A IA não tinha incluído a seção "Explicação da Decisão". Eu pedi para adicionar — mostrar POR QUE classificou daquela forma (quais keywords detectou, quantos termos negativos). Transparência do algoritmo.

4. Eu adicionei a seção "O que NÃO automatizar" na tab de Proposta — com blocos vermelhos pros tipos de ticket que NUNCA devem ser automatizados (Cancellation, Refund). A IA não teria pensado nisso por conta própria.

5. Depois da auto-avaliação, percebi que faltava o Dataset 2 no protótipo. Adicionei uma 4ª tab de "Análise Cruzada" mostrando a distribuição de categorias do DS2, comparação lado a lado da qualidade textual dos dois datasets, e justificativa de por que NÃO fazer transfer learning. Isso atende o critério *"usou ambos os datasets?"* do avaliador.

**Iterações:** 4. Versão base + ajuste de classificação offline + exemplos em PT + tab do Dataset 2.

### Passo 8 — Documentação

Pedi à IA para gerar o README seguindo o template oficial. A primeira versão tinha o Process Log embutido no README com tabelas resumidas.

Eu não gostei. O process log precisa mostrar **processo real**, não um resumo limpo. Pedi para separar em arquivo dedicado (`process-log/workflow.md`) e reescrever como narrativa em primeira pessoa — este documento que você está lendo agora.

**Iterações:** 3. Template inicial + separação do process log + reescrita como narrativa.

---

## Total de iterações com a IA

| Passo | Iterações | O que aconteceu |
|-------|:---------:|----------------|
| EDA inicial (timestamps) | 3 | IA errou tipo → eu corrigi → confirmei paradoxo temporal |
| Análise CSAT | 2 | IA gerou insight falso → eu rejeitei → distribuição bruta revelou aleatoriedade |
| Textos (DS1) | 1 | Bastou ver exemplos para descartar NLP |
| Dataset 2 | 2 | IA propôs TF-IDF transfer → eu rejeitei por domain shift |
| Pivô de estratégia | 0 | 100% decisão minha |
| Diagnóstico (script) | 2 | Tirei gráficos do script + ajustei premissas financeiras |
| Protótipo (Streamlit) | 4 | Base + classificação offline + exemplos PT + tab DS2 |
| Documentação | 3 | Template + separação process log + reescrita narrativa |
| **Total** | **~17** | |

---

## Onde a IA errou e como corrigi

**Erro 1: FRT/TTR como números.** Tentou `mean()` numa coluna datetime. Eu inspecionei os dados e descobri que são timestamps fabricados com gap de 2+ anos.

**Erro 2: "3 Ticket Types".** Copiou do README sem verificar. `value_counts()` mostrou 5 tipos. Refund + Cancellation = 40.7% do volume — quase metade da operação que seria ignorada.

**Erro 3: "Chat tem melhor CSAT".** Gerou insight baseado em diferença de 0.13 ponto. Eu questionei, pedi a distribuição bruta, e provei que CSAT é uniforme/aleatório.

**Erro 4: Análise de sentimento no Dataset 1.** Propôs NLP nos textos. 100% contêm `{product_purchased}` literal. São templates, não linguagem natural.

**Erro 5: Transfer learning DS2 → DS1.** Propôs TF-IDF treinado em tickets de TI para classificar suporte B2C. Domain shift torna isso inviável.

**Erro 6: Premissas financeiras infladas.** Sugeriu R$60/hora e AHT 15 min. Eu ajustei para R$45/hora e 20 min — valores realistas para mercado BR.

**Erro 7: Classificação via API.** Propôs chamar API do Gemini no protótipo. Eu neguei — avaliador não deveria configurar chave de API. Troquei por regras semânticas offline.

---

## O que eu adicionei que a IA sozinha não faria

1. **Pensamento crítico sobre qualidade dos dados.** A IA geraria gráficos e insights sobre dados sintéticos sem questionar. Eu verifiquei cada coluna, questionei números que pareciam "bons demais" (CSAT uniforme, prioridade uniforme), e transformei a auditoria de qualidade em **diferencial competitivo**.

2. **O pivô dados → solução.** Quando os dados se mostraram sintéticos, a IA continuaria tentando fazer ML funcionar. Eu decidi que o protótipo funcional com tickets reais era mais valioso que análises estatísticas sobre ruído. Esse pivô redirecionou todo o projeto.

3. **Decisão de NÃO automatizar.** A IA tenderia a maximizar automação. Eu defini que Cancellation (risco de churn, oportunidade de retenção) e Refund (implicações legais, CDC/Procon) são zonas onde IA sem empatia **piora** o cenário. Essa decisão vem de entendimento de operações reais.

4. **Framework de 4 níveis de roteamento.** Auto-resolve, Agent Assist, Human Required, Escalação. Não saiu de um prompt — veio de entender que diferentes tipos de ticket precisam de níveis diferentes de intervenção humana.

5. **Premissas conservadoras.** Usei R$45/hora e AHT 20min (benchmarks BR) em vez de inflar números. A credibilidade de uma análise financeira está nas premissas, não na conclusão.

6. **Foco no avaliador.** Cada decisão de UX foi pensada para quem vai avaliar: exemplos em português, protótipo offline sem dependências, explicação do "por quê" de cada classificação, tab dedicada mostrando que usei os dois datasets.
