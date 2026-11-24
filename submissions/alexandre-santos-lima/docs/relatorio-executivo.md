# RavenStack: diagnóstico de cancelamentos

**Para:** CEO · **Período analisado:** jan/2023 a dez/2024 · **Painel interativo:** https://ravenstack-churn.apsolutions-technology-services.workers.dev

## Em uma frase

**Não há sinal de que os clientes estejam cancelando mais. A empresa cresceu, e anota mal os cancelamentos.** Antes de gastar com
retenção, é preciso conseguir medir quem sai, quando e por quê.

## O que está acontecendo

**1. Os cancelamentos subiram porque a empresa cresceu.** Os cancelamentos por mês foram de 16 (dez/23) para 117 (dez/24), 7 vezes
mais. No mesmo período, os clientes ativos foram de 437 para 3.174, também 7 vezes mais. De cada 100 clientes que entram, cerca de
10 cancelam: 12 de quem entrou em 2023 e 9 de quem entrou em 2024. O número de clientes explica 96% da variação mensal dos
cancelamentos. Não há época do ano comprovadamente pior.

**2. O uso não cresceu.** O produto é usado o mesmo tanto (cerca de 10 mil vezes por mês) desde 2023. Como os clientes
aumentaram, o uso por cliente caiu 83% em 2024. Mas usar menos **não** explica quem cancela: descontado o crescimento, não há relação.

**3. A satisfação "ok" não enxerga o cliente insatisfeito.** 4 de cada 10 atendimentos ficam sem nota, e nenhum dos 2.000
recebeu nota 1 ou 2. A média boa (4 de 5) vem só de quem respondeu.

**4. A empresa não sabe ao certo quem saiu, nem por quê.** Esta é a causa de "algo não bate":

- os dois registros de cancelamento discordam em 312 das 500 contas, e as 110 contas marcadas como "canceladas" seguem pagando algo;
- 211 dos 216 contratos anuais cancelados aparecem encerrados antes de um ano (103 em menos de um mês): a data está errada;
- o motivo anotado não combina com o que o cliente escreveu (ex.: motivo "preço", comentário "troquei pelo concorrente");
- 99 de cada 100 clientes "cancelados" seguem usando o produto do mesmo jeito depois do cancelamento registrado;
- a receita registrada também não é confiável: é sempre usuários × preço de tabela (US$ 19, 49 ou 199 por usuário), sem
  nenhum desconto, e metade dos clientes tem 8 ou mais assinaturas ativas ao mesmo tempo. A receita mensal somada
  (US$ 10,2 mi) provavelmente está inflada e não deve ser usada como valor real.

## Quem está em risco

Nenhuma característica do cliente (setor, país, plano, canal, receita, uso, atendimento), sozinha, separa quem cancela de quem
fica: foram 117 testes. Dois grupos chamam atenção, mas podem ser coincidência: empresas de DevTools (31% contra 19% nos demais)
e clientes vindos de eventos (30% contra 20%). Medindo pela receita cancelada em vez do número de clientes, a ordem muda: DevTools
volta para a média (quem sai são clientes menores), e França, Reino Unido e clientes de eventos ficam no topo, ainda dentro da
margem de erro. **Clientes vindos de eventos são os únicos no topo nas duas medidas:** é a primeira hipótese a investigar. Confirmar esperando mais clientes levaria 4 e 6 anos. O caminho rápido é ouvir
quem saiu: o painel traz a lista das **15 contas para ligar primeiro** (as de maior valor entre as 75 em que os dois registros
concordam, US$ 216 mil por mês em serviços cancelados).

## O que fazer, em ordem

| Quando | Ação | Quem | Como saber que deu certo |
|---|---|---|---|
| 1º mês | Uma regra única para "cancelou", aplicada pelo sistema | Dados e Financeiro | Registros concordam em 100% das contas |
| 1º mês | Data do cancelamento vinda do sistema de cobrança | Financeiro | Nenhum contrato anual encerrado antes do prazo sem rescisão |
| 1º mês | Uso e chamados registrados já com o cliente certo | Produto e Engenharia | Quase nenhum uso fora do período contratado |
| 1º mês | Motivo de saída em lista curta + texto livre lido por IA | Atendimento e Produto | Quase nenhum "desconhecido"; motivo e texto concordam |
| 1º mês | Pesquisa que capte insatisfação (notas 1 a 5, quem não responde) | Atendimento | Aparecem notas baixas; resposta acompanhada por cliente |
| 1º mês | Receita copiada do sistema de cobrança; renovação encerra a assinatura anterior | Financeiro | Uma assinatura ativa por serviço; receita somada = total faturado |
| 2º–3º mês | Ligar para as 15 contas da lista e refazer a análise com dados arrumados | Atendimento e Dados | Motivos confirmados; hipóteses confirmadas ou descartadas |
| a partir do 4º mês | Testar cada ação de retenção em parte dos clientes, com comparação | Atendimento e Dados | Ação só é ampliada se quem recebeu cancela menos |

**Tamanho da oportunidade:** cada cliente a menos cancelando, em cada 100, mantém cerca de 38 assinaturas, entre US$ 52 mil e
US$ 110 mil por mês em receita. É uma conta direta, não uma promessa.

**O que acompanhar:** quantos, de cada 100 clientes que entram, acabam cancelando (hoje cerca de 10, entre 9 e 11). Não o total
de cancelamentos por mês, que sobe sempre que a empresa cresce. Com o número atual de clientes, o normal é ter entre 57 e 114
cancelamentos registrados por mês sem que nada tenha mudado.

## Limites desta análise

- Os dados são sintéticos (dataset público). As conclusões valem para estes dados; o método vale para dados reais.
- Com dois anos de histórico, não dá para descartar de vez uma época do ano pior; só dizer que nenhuma apareceu.
- Com as datas de cancelamento erradas, não dá para medir a velocidade com que cada turma de clientes cancela. Por isso a
  conclusão é "não há sinal de piora", e não "os cancelamentos caíram".
- Não há previsão por data: dependeria de prever o crescimento da empresa, e as datas anotadas não são confiáveis.
