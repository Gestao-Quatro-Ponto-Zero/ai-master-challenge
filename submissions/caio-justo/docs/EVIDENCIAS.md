# Evidências científicas

Cada decisão da ferramenta abaixo se apoia em uma fonte. Título, autores e ano foram conferidos pelo DOI no OpenAlex, e as citações usam o que está nos resumos publicados. Vários estudos vêm de outros contextos, e isso está indicado.

## Por que testar, em vez de só dar uma nota

| Fonte | O que ela mostra | Como usei |
|---|---|---|
| Kohavi, Tang e Xu (2020), *Trustworthy Online Controlled Experiments*, Cambridge University Press. [DOI](https://doi.org/10.1017/9781108653985) | Guia de líderes de experimentação de Google, LinkedIn e Microsoft: conseguir números é fácil, conseguir números confiáveis é difícil. Cita o efeito carryover como armadilha. | Base do sorteio embutido |
| Nygård e Mezei (2020), HICSS. [DOI](https://doi.org/10.24251/HICSS.2020.177) | Estimaram a probabilidade de compra de leads com aprendizado supervisionado, usando dados de comportamento como navegação e e-mails. | Contraste: este dataset não tem nenhum dado de comportamento, o que ajuda a entender por que o cadastro não prevê |
| Kaufman, Rosset, Perlich e Stitelman (2012), *ACM TKDD*. [DOI](https://doi.org/10.1145/2382577.2382579) | Vazamento é usar informação sobre o alvo que não estaria disponível de forma legítima. | `close_date` e `close_value` não entram na nota |

## Como o teste foi desenhado

| Fonte | O que ela mostra | Como usei |
|---|---|---|
| Johari, Koomen, Pekelis e Walsh (2017), KDD, e (2021), *Operations Research*. [DOI](https://doi.org/10.1145/3097983.3097992), [DOI](https://doi.org/10.1287/opre.2021.2135) | Valores-p e intervalos comuns ficam pouco confiáveis quando as pessoas acompanham o teste e decidem no meio dele. | O placar não mostra taxa nem veredito antes da meta. Eles propõem um método que permite acompanhar; escolhi o caminho mais simples, de horizonte fixo |
| Blake e Coey (2014), ACM EC. [DOI](https://doi.org/10.1145/2600057.2602837) | Numa campanha de e-mail do eBay, ignorar a interferência entre grupos inflou o efeito em cerca de duas vezes. | Aviso na tela: o sorteio por negócio não prova receita total. O contexto é outro, mas o risco é análogo, porque o tempo do vendedor é limitado |
| Hudgens e Halloran (2008), *JASA*. [DOI](https://doi.org/10.1198/016214508000000292) | Quando há interferência dentro de grupos, sortear primeiro o grupo e depois os indivíduos permite separar efeitos diretos e indiretos. | Próxima fase: sortear vendedores e depois negócios |
| Hemming, Haines, Chilton, Girling e Lilford (2015), *BMJ*. [DOI](https://doi.org/10.1136/bmj.h391) | No stepped wedge, grupos passam ao tratamento de forma sorteada e sequencial, o que ajuda quando a logística impede um teste comum. O efeito pode se confundir com tendência no tempo. | Opção para levar a ferramenta a todos os managers aos poucos |
| Bojinov, Simchi-Levi e Zhao (2022), *Management Science*. [DOI](https://doi.org/10.1287/mnsc.2022.4583) | Trata de switchback, alternando tratamento no tempo, e do carryover, o tempo em que o efeito continua agindo. | Descartei alternar por semana: o ciclo mediano é de 45 dias, então o efeito de uma semana cairia na seguinte |

## Como medir

| Fonte | O que ela traz | Como usei |
|---|---|---|
| Neyman (1934), *JRSS*. [DOI](https://doi.org/10.2307/2342192) | Amostragem estratificada. | Sorteio dos 100 parados por produto. Só o título e o tema estão no resumo; a alocação proporcional ao valor é aplicação minha |
| Wilson (1927), *JASA*. [DOI](https://doi.org/10.1080/01621459.1927.10502953) | Intervalo para uma proporção. | Taxa de cada grupo |
| Newcombe (1998), *Statistics in Medicine*. [DOI](https://doi.org/10.1002/(SICI)1097-0258(19980430)17:8%3C873::AID-SIM779%3E3.0.CO;2-I) | Comparou onze métodos; combinar intervalos de Wilson teve bom desempenho e é simples de calcular. | Diferença entre os grupos, com um teste de valor conhecido |
| Hanley e McNeil (1982), *Radiology*. [DOI](https://doi.org/10.1148/radiology.143.1.7063747) | A área sob a curva ROC é a chance de ordenar certo um caso positivo acima de um negativo. | Medida do porteiro |

## Por que a tela é assim

| Fonte | O que ela mostra | Como usei |
|---|---|---|
| Dietvorst, Simmons e Massey (2015), *Journal of Experimental Psychology: General*. [DOI](https://doi.org/10.1037/xge0000033) | Em 5 estudos, ver um algoritmo errar reduziu a confiança nele mais do que ver um humano errar, mesmo quando ele era melhor. As tarefas eram de previsão, não de vendas. | Não prometer acerto: a tela mostra o motivo e o que ainda não foi provado |
| Dietvorst, Simmons e Massey (2018), *Management Science*. [DOI](https://doi.org/10.1287/mnsc.2016.2643) | Em 3 estudos, as pessoas aceitaram mais um algoritmo imperfeito quando podiam ajustá-lo, mesmo que pouco. | Botão Adiar: o vendedor mexe na ordem sem alterar o sorteio |
| Luo, Qin, Fang e Qu (2021), *Journal of Marketing*. [DOI](https://doi.org/10.1177/0022242920956676) | Em experimentos de campo com vendedores e coaches de IA, os de pior desempenho sofreram com excesso de informação, e limitar o feedback ajudou. Os melhores resistiram mais à IA. A combinação de IA e gestor foi a melhor. | Foco limitado a 5 negócios por tela, confirmação do vendedor na sugestão da LLM e decisão final do RevOps. O estudo é sobre treinamento, não priorização |
| Dawes (1979), *American Psychologist*. [DOI](https://doi.org/10.1037/0003-066X.34.7.571) | Modelos lineares simples, até com pesos não otimizados, superaram a intuição clínica ao prever critérios numéricos a partir de preditores numéricos. | Ajuda a defender regra simples e explicável. Não prova que esta regra vence o feeling, e por isso ela entra em teste |

## O que procurei e não usei

- **Wu, Andreev e Benyoucef (2023)**, *The state of lead scoring models and their impact on sales performance*, [DOI](https://doi.org/10.1007/s10799-023-00388-w). Parece o estudo mais próximo do tema, mas o texto ficou bloqueado e o resumo não veio na base. Não cito nenhuma conclusão dele.
- **Söhnchen e Albers (2010)**, *Pipeline management for the acquisition of industrial projects*, [DOI](https://doi.org/10.1016/j.indmarman.2010.04.001). Mesmo motivo.
- **Hussey e Hughes (2007)** e **Athey e Imbens (2017)**: resumos indisponíveis na base.

## O que não encontrei

Busquei um experimento de campo que testasse uma lista de priorização de deals em vendas B2B, e a busca não trouxe nenhum. A busca foi curta, então isso não prova que ele não existe, mas o sorteio embutido da ferramenta é justamente uma forma de produzir essa evidência dentro da empresa.
