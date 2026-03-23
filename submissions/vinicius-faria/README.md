# Submissão — Vinicius Faria — Challenge 003

## Sobre mim

- **Nome:** Vinicius Faria
- **LinkedIn:** https://www.linkedin.com/in/viniciusfaria-artheno/
- **Challenge escolhido:** 003 — Lead Scorer

---

## Executive Summary

Construí uma aplicação web completa de priorização de pipeline comercial que resolve o problema central descrito pela Head de RevOps: vendedores gastando tempo em deals errados. A solução vai além de ordenar por valor — usa dados históricos reais do CRM para calcular um score baseado em probabilidade de fechamento, com explicação em linguagem natural do porquê cada deal recebeu aquela nota. O resultado é uma ferramenta que um vendedor abre na segunda de manhã e sabe exatamente o que fazer — sem precisar interpretar dados.

---

## Solução

### Abordagem

Antes de escrever qualquer código, passei pela análise exploratória completa dos 4 arquivos do dataset com Python. Essa etapa revelou decisões importantes que não teriam emergido "no feeling":

- **Win rate das contas** varia de 53% a 75% — o único fator com correlação real com fechamento nos dados
- **Preço do produto não prediz fechamento** — MG Special ($55) fecha 64,8%, GTK 500 ($26.768) fecha 60,0%. Incluir preço como fator positivo no score teria criado uma planilha ordenada por valor com maquiagem por cima
- **Receita da conta não prediz fechamento** — diferença de apenas 1,6pp entre o quartil mais rico e o mais pobre
- **1.425 deals sem conta vinculada** — 68% do pipeline ativo. O modelo precisa funcionar para esse caso sem punir excessivamente
- **O dataset não tem deals perfeitos** — o score bruto máximo alcançável é ~75, o que exigiria normalização relativa para comunicar urgência visual de forma útil
- **P75 histórico varia por produto** — GTX Pro fecha em mediana de 84 dias, GTK 500 em 107 dias. Um corte único de tempo seria impreciso

Com esses achados, a arquitetura do scoring ficou defensável com dados reais — não com intuição de vendas.

### Resultados

**Uma aplicação single-file (HTML/JS) que roda direto no navegador, sem servidor, sem build.**

**Motor de scoring em dois grupos:**

| Grupo | Critério | Score responde |
|---|---|---|
| Prospect | Stage = Prospecting | Qual abordar primeiro? |
| Engaging | Stage = Engaging | Onde focar a energia? |

**Fatores do score — Engaging:**

| Fator | Peso | Justificativa nos dados |
|---|---|---|
| Win rate da conta | 40% | Único fator com correlação real com fechamento |
| Tempo vs ciclo histórico do produto | 35% | Diferencia momentum de deals parados |
| Preço do produto | 15% | Impacto na meta do vendedor |
| Receita da conta | 10% | Proxy de capacidade de compra |
| Bônus do agente | ±8pts | Ajuste leve por performance histórica |

**Score exibido = normalização relativa.** Apliquei o score bruto como critério de ordenação dos deals. No entanto, ao validar os resultados, percebi que o score médio ficava muito baixo visualmente — o que atrapalha a percepção de valor e prioridade pelo vendedor. Então apliquei normalização relativa: o número exibido é reescalado dentro do conjunto visível para o usuário. O melhor deal sempre aparece entre 95–98, o pior entre 2–5. Isso resolve o problema visual de um dataset sem deals perfeitos, sem mentir nos dados — a ordenação continua sendo pelo score bruto.

**Zonas de risco por tempo:**
- Verde: dentro do ciclo histórico do produto
- Âmbar: últimos 20% antes do limite
- Vermelho: além do limite até 138 dias (máximo histórico absoluto de Won)
- Vermelho crítico: além de 138 dias

**Três níveis de usuário com visões radicalmente diferentes:**
- **Vendedor** — seu pipeline priorizado, score relativo, explicação por deal
- **Manager** — ranking do time com score de desempenho, posição global, alertas
- **Diretor** — visão por região, drill-down para managers, pipeline global com score bruto

**Explicação do score em linguagem natural** — função JavaScript interna com 40+ templates cobrindo todos os cenários do dataset. Responde primeiro "por que este score", depois sugere ação. Zero dependência de API externa para essa funcionalidade — funciona offline e garante que o avaliador veja a funcionalidade principal sem nenhuma configuração. A abordagem com templates foi escolhida para entregar uma solução enxuta e robusta, mas a substituição por uma chamada a um LLM é trivial e representa o caminho natural de evolução do produto.

Exemplo de explicação gerada:
> *"O score de 97 é puxado principalmente pela taxa de fechamento de Newex — 72,5% é um dos números mais altos da sua carteira, e isso carrega o maior peso no cálculo. O deal está há 37 dias em negociação, ainda dentro do prazo histórico para o GTX Pro. Conta certa, momento certo, produto certo. Ligue hoje, confirme os próximos passos e não deixe essa janela fechar."*

**Assistente AI** — botão flutuante com OpenAI gpt-4o-mini, contextualizado com o pipeline do usuário ativo. Implementa diretamente o modelo de *"API que recebe dados de um deal e retorna score + explicação"* descrito no challenge. A chave OpenAI é inserida pelo próprio usuário na interface — escolha deliberada para demonstrar como essa funcionalidade se comportaria em produção, onde cada empresa ou usuário teria sua própria integração. Acredito que assistentes contextuais integrados ao CRM não são mais o futuro — já deveriam ser o presente de qualquer operação comercial séria.

### Recomendações

**1. Vincular as 1.425 contas sem identificação é a ação operacional mais impactante disponível agora.** Esses deals representam 68% do pipeline ativo e recebem scores imprecisos por falta de dado. Um processo simples de enriquecimento de dados — mesmo manual — muda a qualidade da priorização de forma imediata. Nenhuma ferramenta de inteligência funciona bem sobre dados sujos.

**2. O ranking de managers revelou uma anomalia que merece investigação.** O range de win rate entre os 6 managers é de apenas 2,3 pontos percentuais (62,1%–64,4%) — performance quase idêntica. Mas o valor gerado varia de $1,09M a $2,25M. A diferença não é taxa de fechamento, é volume e qualidade do pipeline. Isso sugere que o problema de priorização não é individual dos vendedores — é sistêmico na gestão do funil.

**3. O GTK 500 merece tratamento comercial separado.** São apenas 14 deals ativos e $26.768 por fechamento — cada GTK perdido tem impacto desproporcional na receita. Além disso, o produto mais caro da linha fecha menos que os demais (60,0% vs média de 63%), o que pode indicar ciclo de venda mal calibrado ou perfil de abordagem inadequado para esse ticket.

**4. O ciclo de fechamento do dataset tem distribuição bimodal.** 43% dos deals Won fecham em menos de 30 dias e 25% fecham entre 61 e 90 dias — dois picos distintos, não uma curva normal. Isso sugere que existem dois perfis de deal completamente diferentes no pipeline: fechamentos transacionais rápidos e negociações consultivas longas. Tratar os dois com o mesmo processo comercial é um erro estrutural.

**5. 24% dos deals Won fecharam além do P75 do produto.** Isso significa que cerca de 1 em cada 4 deals "frios" ainda fechou. A ferramenta sinaliza esses deals para reengajamento — mas a empresa precisa ter um processo ativo para trabalhar esse grupo, não apenas identificá-lo. Deals nessa categoria, especialmente com contas de bom histórico, têm retorno real sobre o esforço de reativação.

**6. A concentração de deals em poucas contas é um risco não visível no pipeline atual.** Algumas contas como Kan-code aparecem com 14+ deals ativos simultâneos. Múltiplos deals abertos na mesma conta podem indicar oportunidade real — ou pode ser fragmentação artificial de pipeline que infla os números. Vale investigar se esses deals são independentes ou se competem entre si internamente.

**7. O setor da conta é um preditor relevante para prospecção.** Marketing e Entertainment fecham 65% dos deals, Finance fecha 61%. Para um time de 35 vendedores trabalhando 500 prospects, priorizar por setor antes de qualquer contato aumenta a taxa de conversão do topo do funil sem nenhum custo adicional.

### Limitações

**Dados:**
- 1.425 deals sem conta vinculada — score funciona com fallback, perde precisão
- Dataset estático de 2016–2017 — data de referência fixa em 31/dez/2017
- Amostra pequena de dados históricos para alguns produtos em relação ao período de tempo analisado — limita a confiabilidade do ciclo histórico calculado
- A ausência de histórico de interações, atividades e notas no CRM limita significativamente o potencial do Assistente AI — um assistente com acesso a histórico de conversas, e-mails e reuniões poderia analisar padrões de engajamento, sugerir próximos passos contextualizados e até receber relatos por áudio ou texto do vendedor, transformando o CRM de repositório passivo em ferramenta ativa de gestão
- A falta de etapas intermediárias reais no pipeline (o dataset tem apenas Prospecting e Engaging, sem sub-etapas como Proposta Enviada, Negociação, Aprovação) reduz a granularidade do score e das sugestões de ação

**Produto:**
- Autenticação simulada via seletor — sem login real
- Dados carregados de CSVs estáticos — sem atualização em tempo real
- Sem persistência de estado entre sessões
- Assistente AI requer chave OpenAI inserida pelo usuário

**Funcionalidades futuras documentadas:**
- Cross-sell por novo produto — sem dados de sequência de compra no dataset atual
- Integração com LLM para sofisticar e desenvolver novas funcionalidades — explicações dinâmicas, análise de padrões históricos, sugestões de abordagem personalizadas por perfil de conta
- Enriquecimento automático de dados de conta via APIs externas (ex: LinkedIn, Clearbit) — resolveria diretamente o problema dos 1.425 deals sem conta identificada

---

## Process Log — Como usei IA

### Ferramentas usadas

| Ferramenta | Para que usou |
|---|---|
| Claude Sonnet (claude.ai) | Parceiro de análise durante todo o processo — exploração dos dados, decisões de scoring, arquitetura de produto, design de interface |
| Claude Code / Antigravity | Construção e iteração da aplicação web |
| Gemini | Revisão crítica dos pesos de scoring — trouxe perspectiva externa que resultou em ajustes reais |
| OpenAI gpt-4o-mini | Assistente contextual dentro da aplicação |

### Workflow

1. **Entendi o challenge, analisei os dados do dataset, depois comecei a delinear o projeto com o workflow que estou acostumado a conduzir, com base no Lean Startup** — entender o problema real antes de qualquer solução, validar hipóteses com dados antes de implementar, iterar rápido com feedback visual. Rodei Python nos 4 CSVs para entender distribuições, nulos, ranges e anomalias. Descobri o typo GTXPro, os 1.425 deals sem conta, a ausência de correlação preço×win rate e receita×win rate. Essa etapa mudou completamente o modelo de scoring que eu teria feito "no feeling".

2. **Definição da lógica de scoring iterativamente.** Propus, testei nos dados, validei os resultados, ajustei. Por exemplo: inicialmente incluí preço como fator alto no score. Os dados mostraram que produto mais caro fecha menos — removi. Testei normalização absoluta, vi que o máximo alcançável era 75, então implementei a normalização relativa por conjunto do usuário.

3. **Revisão externa com Gemini.** Apresentei os pesos ao Gemini como crítico externo, após pedir para trazer relações de acordo com o mercado. Ele identificou que a penalização para deals sem conta (score 10) estava matando 68% do pipeline ativo. Ajustei para 35 — incerteza, não punição. Também reduzi o peso do tempo de 25% para 10% na versão intermediária por conta de ciclos longos legítimos.

4. **Construção do sistema com Claude Code via Antigravity.** Cada módulo foi construído e validado antes do próximo: motor de scoring → normalização relativa → templates de explicação → interface por nível de usuário → diretor com drill-down.

5. **Iteração visual com screenshots.** Cada problema identificado nos screenshots foi documentado, diagnosticado no código, e corrigido com prompt cirúrgico — não modificação completa do arquivo.

### Onde a IA errou e como corrigi

**Erros recorrentes na construção da interface.** Mesmo após fornecer skills de UI/UX, rascunhos de interface e regras anti-vibe-code, o Claude Code errou repetidamente em proporção de cards, disposição de elementos, hierarquia visual e aplicação dos prompts. Cada iteração exigiu diagnóstico preciso no screenshot, identificação do problema no código e prompt cirúrgico para corrigir só o que estava errado — sem deixar a IA refatorar o que estava funcionando.

**Score nunca chegava a 100.** A IA inicialmente não identificou que o win rate das contas varia apenas de 53% a 75% — multiplicar esse número direto pelo peso de 45% limita o score máximo a ~88. A solução (normalização relativa por conjunto do usuário) foi minha proposta, não da IA.

**Pesos implementados incorretamente.** O código chegou a usar WR 45% + Preço 25% + Receita 20% + Tempo 10% — o inverso do que foi definido. Identifiquei ao comparar os scores gerados com os dias no pipeline nos screenshots.

**Gemini propôs score composto para managers.** Os dados mostraram que o range de win rate entre managers é de 2,3pp — insuficiente para um score confiável. Preferi ranking simples por valor gerado, mais honesto com os dados.

**"P75" e "win rate" aparecendo na interface.** A IA gerou termos técnicos em textos visíveis ao usuário repetidamente. Corrigi com instrução explícita de nunca expor esses termos — toda a linguagem da interface deve ser de vendas, não de análise de dados.

### O que eu adicionei que a IA sozinha não faria

- **A decisão de separar Prospect e Engaging como grupos distintos com scores diferentes** — a IA inicialmente propunha um único score com Stage como fator. Eu identifiquei que são produtos mentais completamente diferentes para o vendedor: Hunter vs Closer.

- **A normalização relativa como solução para o teto de 75** — a IA não identificou o problema estrutural do dataset. Fui eu que propus reescalar o score dentro do conjunto do usuário.

- **Rejeitar win rate do agente como fator de score individual** — a IA propôs várias vezes. Argumentei que win rate do agente é constante para todos os seus deals — não diferencia deals entre si, diferencia agentes. Serve para o ranking do manager, não para o score do deal.

- **O insight sobre preço não predizer fechamento** — depois de ver os dados, propus reduzir preço no score. A IA e o Gemini resistiram inicialmente com argumentos de "impacto na meta". Mantive preço com peso reduzido (15%) como fator de desempate, mas argumentei que ele não pode dominar um score de probabilidade de fechamento.

---

## Evidências

- [x] Chat export da conversa com Claude: [Evidência de uso de IA](./process-log/chat-exports/Claude%20Chat%20-%20G4%20Challenge.pdf)
- [x] PRD completo v3.0 documentando todas as decisões de produto e scoring (`docs/PRD_LeadScorer.md`)
- [x] Git history da construção incremental
---

*Submissão enviada em: 22/03/2026*
