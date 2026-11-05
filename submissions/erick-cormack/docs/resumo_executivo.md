# Pipeline de Vendas — Resumo Executivo

05/11/2026 · Erick M. Cormack

Versão online: https://claude.ai/artifact/9MMx5jPRZnsMCwHHBquL6G (o mesmo conteúdo aparece no app, no botão "Detalhar mais" da página inicial)

## Em 30 segundos

O time não perde vendas por escolher mal os deals. Perde tempo com deals que já morreram e continuam abertos no CRM.

- **81% dos deals em negociação estão parados há mais tempo que qualquer venda já fechada** (138 dias). Eles travam US$ 3,2 milhões, 64% dos US$ 5,0 milhões em aberto.
- **Produto, setor, região ou vendedor não indicam se um deal vai fechar.** O que indica é o tempo, e o valor define a prioridade.
- **Recomendação:** limpar o pipeline e concentrar o time nos 298 deals ainda vivos (US$ 694 mil), ordenados por valor e momento.

## O que descobrimos

Analisamos 8.800 oportunidades de 35 vendedores. O time ganha 63% dos deals que fecha, e essa taxa quase não muda de um grupo para outro.

| Pergunta | Resposta |
| --- | --- |
| Produto, setor, região ou vendedor indicam se um deal fecha? | **Não.** Todos ficam entre 60% e 65% de ganho. As diferenças são do tamanho do acaso. |
| Um modelo com o histórico de vendas preveria melhor? | **Não.** Testado com dados do passado, ele acertaria quase como cara ou coroa. |
| O que realmente indica o resultado? | **O tempo.** Quem perde, perde nas duas primeiras semanas. E nenhum deal fechou depois de 138 dias. |
| Como decidir a prioridade, então? | **Pelo valor**, combinado com o tempo. Um deal vale de US$ 55 a US$ 26.768, quase 500 vezes de diferença. |

Um score do tipo "esse vendedor ou setor costuma ganhar" pareceria inteligente, mas estaria ordenando ruído.

## Onde está o problema

O pipeline parece ter US$ 5,0 milhões em aberto, mas só uma pequena parte disso está viva. Qualquer previsão de receita feita sobre ele está inflada.

| Indicador | Número | O que significa |
| --- | --- | --- |
| Deals em negociação parados há mais de 138 dias | 1.291 de 1.589 (81%) | Estão fora de qualquer padrão histórico de venda |
| Valor travado nesses deals | US$ 3,2 milhões (64% do aberto) | Receita que provavelmente não virá |
| Deals em negociação ainda vivos | 298 (US$ 694 mil) | É onde o time deve concentrar o esforço |
| Deals abertos sem a empresa cliente cadastrada | 1.425 de 2.089 (68%) | O CRM está incompleto, e isso vale para todos os times |
| Escritório Central | 99% dos deals em negociação parados, todos abertos num bloco de jul–ago/2017 | O time segue vendendo; um lote inteiro ficou para trás |

O caso do Central pede uma conversa com a gestão: o que aconteceu com esse lote de julho?

## O que recomendamos

A primeira ação é de gestão, não de tecnologia: limpar o pipeline.

1. **Limpar o pipeline em até duas semanas.** Cada vendedor requalifica ou encerra seus deals parados há mais de 138 dias, começando pelo escritório Central.
2. **Colocar em uso a ferramenta de priorização.** Toda segunda-feira o vendedor vê seus deals vivos ordenados por valor e momento, com o motivo de cada posição. Os parados ficam numa fila separada.
3. **Tornar obrigatório o cadastro da empresa cliente no CRM.** Sem isso, não dá para analisar setor ou porte em dois terços do pipeline.
4. **Registrar as atividades de venda no CRM** (reuniões, e-mails, propostas). É o dado que falta para prever resultados com mais precisão.
5. **Revisar casos pontuais:** possíveis lançamentos duplicados e 80 vendas fechadas acima de 120% do preço de lista.

## Ressalvas

Os números são um retrato do CRM em 31/12/2017. Os dados têm sinais de serem simulados: por exemplo, há tantos deals iniciados no sábado e no domingo quanto em dias úteis. Com dados reais e o registro de atividades, é provável que vendedor e cliente passem a ter algum peso, e o modelo deve ser recalibrado. A análise completa, com todos os testes estatísticos, está no notebook do projeto.
