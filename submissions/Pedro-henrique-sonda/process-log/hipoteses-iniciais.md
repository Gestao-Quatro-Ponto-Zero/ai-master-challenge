# Hipóteses Iniciais 

## 1. Entendimento do Problema

### A dor
Os vendedores não têm critério objetivo para priorizar oportunidades. Hoje, a decisão de "quem ligar primeiro" é baseada em feeling, o que significa que leads com alto potencial esfriam enquanto o vendedor gasta tempo em deals que talvez, nunca vão fechar. O custo disso é faturamento perdido de forma invisível.

### O usuário
35 vendedores distribuídos em escritórios regionais. A rotina: chega no escritório, pega o café, abre os emails, e em seguida abre o pipeline. Hoje, se encontra perdido, chama um por um sem priorização real, dependendo de sorte para acertar.

### O que precisa existir
Uma ferramenta que o vendedor abra na segunda-feira de manhã e em **10 segundos** saiba: esses são os 5 deals que eu PRECISO atacar nos próximos 30 minutos. Sem interpretação, sem dúvida, apenas ação imediata.

## 2. O que significa "Score"

O score representa o **potencial de fechamento** de uma oportunidade aberta (por vezes baseada nos históricos de fechamento). Não é uma medida do passado, é uma previsão aplicada a deals que ainda estão em andamento (Prospecting e Engaging).

O score deve considerar duas dimensões:
- **Probabilidade de fechar** (chance de virar Won)
- **Valor potencial** (quanto vale se fechar)

Um deal com 80% de chance de fechar e valor de R$10k pode ter score maior que um deal com 20% de chance e valor de R$50k. A fórmula precisa balancear essas duas forças. 

Além das features óbvias do pipeline. O score deve ser baseado também em tendências de fechamentos anteriores, indicando uma probabilidade de se repetir o que já aconteceu, em detrimento de hipóteses baseadas em dados passados inexistentes. 

## 3. Hipóteses — O que acredito que influencia o fechamento

### Hipóteses sobre features disponíveis nos dados

| # | Hipótese | Justificativa |

| 1 | **O stage atual do deal importa** Um deal em Engaging já teve interação real — está mais quente que um em Prospecting. O stage indica onde o deal está na jornada e muda a probabilidade de conversão. Porém é interessante ressaltar que não necessariamente um deal em Engaging sempre vai ter um score maior que um deal em prospecting. 
| 2 | **Tempo no pipeline + stage contam uma história** | Isolado, o tempo pode não dizer muito. Mas combinado com o stage, revela momentum: Engaging há 5 dias = promissor. Engaging há 90 dias = provavelmente morto. Porém é necessario entender particularidades sobre o processo de decisão e prazos do cliente para chegar a esta conclusão |
| 3 | **O setor da conta faz diferença** | Setores diferentes têm ciclos de venda e orçamentos diferentes, o que pode mudar o produto ofertado e o valor final. |
| 4 | **O tamanho da empresa influencia** | Empresas maiores (mais receita, mais funcionários) provavelmente geram deals de maior valor e podem ter processos de compra mais estruturados. Porém, podem levar mais tempo, o que reforça ao que foi dito na hipotése 2, que não necessariamente um deal com um tempo mais longe entre stages, seja um deal com baixo score. É necessário cruzar informaçõs e compreender as tendências para cada caso, nunca esquecendo de levar em consideração suas particularidades. |
| 5 | **Alguns produtos convertem mais que outros** | Cada produto tem um perfil diferente de complexidade e preço, a taxa de conversão histórica por produto provavelmente varia. |
| 6 | **O vendedor faz diferença na conversão** | Vendedores com mais experiência ou melhor técnica provavelmente convertem mais, independente do deal. Porém é importante ressaltar que, um vendedor que desenvolve um volume maior de atividades, tende a ter um resultado mais expressivo que um vendedor mais com mais experiencia e tecnica que desenvolve um volume menor. |
| 7 | **O valor do deal influencia a chance de fechar** | Deals muito grandes podem ter ciclos mais longos e mais objeções. Deals menores podem fechar mais rápido. Priorizar volume de deals antes de seu valor, pode ser uma estratégia eficaz para ter um cicle time de vendas mais baixo, carteira de clientes maior, podendo gerar mais recomendações de novos clientes, e talvez, faturamento maior devido ao alto volume de vendas, mesmo com valores mais baixos.|

### Hipóteses sobre combinações (além do óbvio)

| # | Hipótese | Por que investigar |

| 8 | **Setor + Produto**: certas combinações convertem muito mais | Um produto pode ser perfeito para um setor e irrelevante para outro. 
| 9 | **Empresa-mãe (subsidiárias)**: contas com empresa-mãe se comportam diferente | Subsidiárias podem ter orçamento pré-aprovado ou processo mais burocrático, preciso verificar. 
| 10 | **Valor do deal vs tamanho da conta**  Um deal grande numa conta pequena pode indicar risco (a conta não comporta). Um deal grande numa conta grande é mais natural. 
| 11 | **Velocidade de transição entre stages**  Deals que passaram rápido de Prospecting para Engaging podem ter mais urgência e fechar mais. 
| 12 | **Manager / escritório regional**  Talvez times inteiros performem melhor por gestão, treinamento ou mercado regional mais aquecido. 
| 13 | **Sazonalidade**  Deals fechados em certos meses podem converter mais, sazonalidade do mercado ou do orçamento do cliente. 

---

## 4. Perguntas em aberto (para investigar nos dados)

- Qual a taxa de conversão geral (Won vs Lost)?
- Existe diferença significativa de conversão por setor?
- Qual produto tem a maior e a menor taxa de conversão?
- Quanto tempo em média um deal leva para fechar? E os que são perdidos, levam mais ou menos tempo?
- A distribuição de close_value é uniforme ou tem outliers?
- Algum vendedor tem taxa de conversão muito acima ou abaixo da média?
- Algum manager tem o time inteiro performando acima?
- Contas com empresa-mãe têm comportamento diferente?
- Existe correlação entre receita da conta e valor do deal?

---

## 5. Dado que considero essencial e NÃO existe no dataset

**Origem do lead (lead source).** No mundo real, saber se o lead veio por recomendação de um cliente, rede social, anúncio pago, evento, outbound ou inbound muda completamente a priorização. Leads por recomendação historicamente têm taxas de conversão muito superiores a leads frios de anúncio.

Esse dado não está disponível nas 4 tabelas do CRM. Isso é uma **limitação real do dataset** que precisa ser reconhecida na entrega. Em uma implementação real, a primeira recomendação seria: incluir o campo `lead_source` no CRM para enriquecer o modelo de scoring no futuro.

---

## 6. Premissas para a construção do scoring

1. O scoring será aplicado apenas em **deals abertos** (Prospecting e Engaging)
2. Deals Won e Lost serão usados como **dados de treinamento** ,para entender padrões históricos
3. O score precisa ser **explicável**, o vendedor precisa entender o porquê, não só ver um número
4. A ferramenta precisa ser **funcional**, algo que rode e que alguém use com facilidade, não um documento teórico.

---

*Este documento foi escrito antes da análise exploratória dos dados. As hipóteses serão confrontadas com os dados reais na próxima etapa.*
