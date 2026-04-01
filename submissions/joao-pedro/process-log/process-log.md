## Process Log — Como Usei IA

## Descrição do Process Log

Este documento registra o processo iterativo de desenvolvimento de uma solução de priorização de deals de vendas, detalhando como a IA foi utilizada como ferramenta de apoio — incluindo onde funcionou, onde falhou, e como as correções foram feitas através de julgamento humano.


| Tópico                    | O que é                                                             |
| ------------------------- | ------------------------------------------------------------------- |
| **Ferramentas Usadas**    | Resumo das ferramentas de IA utilizadas e seus pontos fortes/fracos |
| **Workflow Real**         | Registro cronológico das iterações, com erros (🔴) e acertos (🟢)   |
| **Onde a IA Errou**       | Análise detalhada de 3 falhas específicas e como foram corrigidas   |
| **O Que Eu Adicionei**    | 5 contribuições humanas que a IA sozinha não faria                  |
| **Transcrições Literais** | Exemplos reais de interações com screenshots como evidência         |

> **Obs:** Em `/process-log/screenshots/` há 14 imagens que comprovam as interações descritas neste documento, além de outras capturas adicionais do processo.

### Ferramentas Usadas


| Ferramenta         | Para Que Usei                                     | Quando Funcionou                                    | Quando Falhou                                               |
| ------------------ | ------------------------------------------------- | --------------------------------------------------- | ----------------------------------------------------------- |
| Claude (chat)      | Análise exploratória, design de modelo, debugging | Geração rápida de hipóteses, validação quantitativa | Sugeriu ML tradicional (prob×valor) sem considerar contexto |
| Cursor (assistant) | Protótipos de interface, visualizações            | Interface funcional em minutos, iteração rápida     | Primeiro layout era genérico demais, tive que redesenhar    |


---

### Workflow Real (Com Erros e Correções)

#### 🔴 ITERAÇÃO 1: Falha — Solução Óbvia (Rejeitada)

**Contexto do trecho inicial:**

> "Tenho 8.800 deals. Quais nossas opções sem pensar em algo extremamente complexo?"

**Resposta do Claude:**

```
Construa modelo preditivo:
1. Feature engineering (dias, valor, vendedor, produto)
2. Train/test split
3. XGBoost para predição de win probability
4. Ordenar por expected_value = prob × value
```

**Indaguei a ele:**

- Não responde "o que fazer segunda-feira de manhã"
- Ignora contexto de capacidade do vendedor
- Ignora o que reforcei sobre priorizar simplicidade
- Pouco intuitivo ao vendedor
- O que podemos construir equilibrando simplicidade mas impacto visual? - nasce a ideia do "feed".

---

#### 🔴 ITERAÇÃO 2: Erro — Close Value para Deals Abertos

**Contexto do meu input**
Apenas deals_won possuem close_value
Deals em Engaging não têm `close_value` - só quando fecham
Precisamos criar a lógica de projeção de receita por vendedor - e consequentemente por squad, região, etc.

**Claude sugeriu:**

> "Use o sales_price do produto como proxy."

**Contexto do meu retorno**
"Nada mais óbvio do que usar sales_price"
O que me diferencia de outros participantes?
Juntamos uma boa base de contexto sobre operação
Me ajude a pensar em lógicas que prezam a simplicidade mas que 
correlacione o histórico de métricas acumulado de sellers, products e accounts

> Houve um contexto consideravelmente grande até alcançar um modelo que combinasse simplicidade 
>
> e diferencial competitivo

**Modelo alcançado:**
Opção híbrida:

1. Média histórica vendedor × produto (≥3 deals)
2. Média histórica produto geral (≥5 deals)
3. Sales price do catálogo
4. Mediana geral (fallback)

---

#### 🟢 ITERAÇÃO 3: Acerto — Viabilidade Separada

**Contexto: A primeira lógica criada não separava viabilidade do vendedor como fator de score**

> "Score alto mas vendedor com 150 deals, a gente não está resolvendo nada aqui"

**Contexto de retorno do Claude:**

> "Penalizar score pela carga do vendedor."

**Minha ideia:**
"Não gosto da ideia do mesmo deal ter scores diferentes para vendedores diferentes"

**Contrapropus:**
Score = importância objetiva (igual para todos)
Viabilidade = capacidade contextual (personalizada)
Ação = f(score, viabilidade)

**Claude refinamento:**
Criou matriz de ação (score × viab → PUSH/TRANSFER/DISCARD)

**Resultado:**
Arquitetura final da tese central do modelo - viabilidade do vendedor como fator de score.

---

#### 🔴 ITERAÇÃO 4: Erro — Lógica de Transfer

**Claude gerou inicialmente:**

```python
# Encontrar vendedor com menor carga
target = min(sellers, key=lambda s: s.active_deals)
```

**O que percebi:**
Deals estavam sendo transferidos sem qualquer tipo de regra
Ignorava hierarquia organizacional (team, região).

**Minha correção:**
Criar hierarquia:

1. Same team (mesmo manager)
2. Same region (mesma região, outro team)
3. Other region
4. Escalate (nenhum disponível)

**Claude implementou:**
Lógica de scoring dentro de cada nível (prosp + carga + especialização).

**Bug encontrado depois:**
Transfer recomendava vendedor com 0 prospecting (protetor de deals).

**Correção:**
Filtro eliminatório: prospecting = 0 → excluir da lista de targets.

---

#### 🔴 ITERAÇÃO 5: Erro — Streamlit Travando

**Problema:**
Primeira versão carregava 8.800 deals toda vez (lento).

**Indaguei:**
Vamos inserir um sistema de cache para armazenamento de certos contextos, a
navegação e o carregamento estão sobrecarregados

**Problema adicional:**
Claude criou 47 páginas no Streamlit (uma para cada análise).

**Minha decisão:**
Consolidar em 9 páginas hierarquizadas (Macro → Data → Analysis).

---

### Onde a IA Errou e Como Corrigi

#### Erro #1: Close Value para Deals Abertos

**O que Claude fez:**
Sugeriu usar `sales_price` direto do catálogo.

**Por que estava errado:**
Sales price é teórico. Deals reais têm descontos, negociações.

**Como detectei:**
Validei distribuição de `close_value` em Won. Variação era 3× sales_price.

**Como corrigi:**
Criei lógica híbrida (média vendedor×produto → média produto → sales_price → mediana).

---

#### Erro #2: Transfer para Vendedor Protetor

**O que Claude fez:**
Recomendou transfer para vendedor com carga baixa (31 deals).

**Por que estava errado:**
Vendedor tinha 0 prospecting (protetor de deals, não pipeline saudável).

**Como detectei:**
Analisei padrão: vendedores com 0 prospecting têm deals mais antigos (círculo vicioso).

**Como corrigi:**
Filtro eliminatório: `prospecting = 0` → excluir de targets.

---

#### Erro #3: Streamlit com 47 Páginas

**O que Claude fez:**
Criou uma página para cada tipo de análise (seller individual, produto individual, etc).

**Por que estava errado:**
Menu lateral ficou poluído, navegação confusa.

**Como detectei:**
Testei interface, percebi que usuário se perdia.

**Como corrigi:**
Consolidei em 9 páginas hierarquizadas (Macro → Data → Analysis).

---

### O Que Eu Adicionei Que a IA Sozinha Não Faria

#### 1. **Insight da Tese Central**

**IA disse:**
"Deals em Engaging demoram mais. Vamos criar modelo preditivo."

**Eu percebi:**
Won fecha em 57d, Lost em 14d. Se Engaging demora 165d, o problema não pode ser só dificuldade.
Além disso, medianas históricas de deals_won/lost são consideravelmentes inferiores.

---

#### 2. **Separação Score × Viabilidade**

**IA sugeriu:**
Penalizar score pela carga do vendedor.

**Eu propus:**
Score objetivo (importância) + Viabilidade contextual (capacidade) → Ação.

**Por que isso importa:**
Mantém score "justo" (mesmo deal = mesmo score) mas personaliza ação.

---

#### 3. **Hierarquia de Transfer**

**IA fez:**
Transferir para vendedor com menor carga.

**Eu adicionei:**
Respeitar hierarquia organizacional:

1. Same team (minimize atrito)
2. Same region (proximidade)
3. Other region (último recurso)

**Por que a IA não fez:**
IA não entende dinâmica organizacional (manager, região, relações).

---

#### 4. **Value-First Design**

**IA criou:**
Sistema que pede input de vendedor (atualizar deal_stage, engajamento).

**Eu mudei:**
Usar APENAS dados existentes e criar uma espécie de "feed". 
Um cockpit rápido que responde "o que o vendedor precisa segunda-feira de manhã"

**Por que isso importa:**
Vendedores abandonam CRM se não veem sentido em usar. Value-first garante adoção.

---

#### 5. **Trade-off Consciente: Regras > ML**

**IA podia ter feito:**
XGBoost com 71% acurácia.

**Eu escolhi:**
Regras com 65% acurácia, mas 100% explicabilidade.

**Por que:**
Modelo 70% preciso que vendedor USA > Modelo 95% preciso que vendedor IGNORA.

---

### Transcrições literais: casos de interação

Exemplos de interações + evidência screenshot:

> 1. Uma das primeiras interações sobre o projeto: /process-log/screenshots/Interaction-example-1.png

"Analise os exemplos de soluções válidas descritas na descrição do desafio: Exemplos de soluções válidas:

- Aplicação web (Streamlit, React, HTML+JS, qualquer coisa)
- Dashboard interativo (Plotly Dash, Retool, Metabase)
- CLI tool ou script que gera relatório priorizados
- API que recebe dados de um deal e retorna score + explicação
- Planilha inteligente com fórmulas de scoring
- Bot que envia prioridades por Slack/email

Prontamente veio a minha cabeça construir uma espécie de "CRM" ou algo do tipo, de forma a "simular" a utilização real de um possível vendedor. Mas percebi que em nenhum momento me questionei e refleti sobre minha escolha. Analise os exemplos citados e o contexto que pensei, vamos falar sobre"

> Essa interação exemplifica um dos casos de uso mais comuns a mim. 
>
> Sempre priorizo CTAs como "Vamos falar sobre", sobretudo em momentos inicias de planejamento
>
> Evidência - /process-log/screenshots/Interaction-example-1.png"

> 1. Ainda em uma das primeiras interações:  /process-log/screenshots/Interaction-example-3.png

"O entendimento sobre a lógica de score ficou claro. O que preciso é que você me justifique cada escolha com base no solicitado no desafio + dados que você absorveu".

> Mais um exemplo de uso "vamos falar sobre"
>
> Evidência: /process-log/screenshots/Interaction-example-3.png

> 1. Trecho de início da conversa que origina a tese central: /process-log/screenshots/Interaction-example-6.png

"Sim, vamos seguir nesse sentido, mas antes preciso rapidamente verificar uma possível falácia: Verifique os CSVS necessários para confirmar a tese: o tempo média de deals_engage em aberto está desproporcional à média de deals_won".

> Acabei "negando a possível falácia", mas exemplifica um uso de caso para reflexão de pontos já "decididos"
>
> Evidência: /process-log/screenshots/Interaction-example-6.png

> 1. Interação sobre uma possível alteração de ângulo de análise : /process-log/screenshots/Interaction-example-14.png

"Vamos sim criar o doc em markdown, mas antes, veja essa provocação que quero inserir na heurística: 

É sabida a dificuldade em geral dos vendedores no preenchimento correto de atualizacoes e dados em ferramentas de CRM. 

Por dificuldade técnica ou não aproximação tecnológica, isso é um fato. 

Essa minha visão não conflita com a tese, ainda tenho convicção que devemos nos fundamentar no aspecto de "proteger deals pela falta deles". 

Mas fiquei pensando sobre a possibilidade e como deveria abordar esse ponto adicional da necessidade de preenchimento de atualizações e andamentos com o sistema, afim de que ele não se torne abandonado. 

Me responda se estou viajando ou se voce tambem enxerga alguma relacao nisso".

> Evidência:  /process-log/screenshots/Interaction-example-14.png

