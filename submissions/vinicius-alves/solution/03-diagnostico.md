# 03 · Diagnóstico operacional

O Diretor de Operações fez três perguntas: onde a gente perde tempo, o que mexe na satisfação, e quanto está sendo desperdiçado. A resposta curta é desconfortável: **os dados que ele tem não respondem as duas primeiras.** E isso já é um diagnóstico.

Todos os números abaixo saem de [`process-log/01-estado-da-arte/verificar_achados.py`](../process-log/01-estado-da-arte/verificar_achados.py). O detalhe de cada um está em [`process-log/01-o-que-ja-se-sabe.md`](../process-log/01-o-que-ja-se-sabe.md).

---

## Onde o fluxo trava?

**Não dá pra saber pelo tempo.** O registro operacional (Dataset 1) não tem a hora em que o ticket foi aberto. E em 49,3% dos tickets fechados a resolução aparece **antes** da primeira resposta. Todas as respostas e resoluções cabem numa janela de 27 horas, enquanto as compras são de 2020 e 2021. Qualquer ranking de "canal mais lento" feito com esses campos é ruído.

**O que dá pra ver é a fila:**

| Situação | Tickets | % |
|---|---|---|
| Aberto, sem nenhuma resposta | 2.819 | 33,3% |
| Esperando o cliente voltar | 2.881 | 34,0% |
| Fechado | 2.769 | 32,7% |

E a prioridade não prioriza: um ticket Crítico fecha em 34,1% dos casos, um Baixo em 31,2% (p = 0,23).

**Leitura:** dois em cada três tickets estão parados. Um terço nunca foi respondido e outro terço espera o cliente. Isso pode ser só o jeito que o arquivo foi gerado (os dados têm todas as marcas de sorteio), então trato como hipótese a medir, não como fato.

## O que impacta a satisfação?

**Nada que o arquivo registra.** As notas de 1 a 5 têm quase a mesma quantidade (de 543 a 580 cada). Canal, prioridade, tipo, gênero e assunto não mudam a nota. Um modelo com todas as colunas juntas acerta a nota em 20,5% das vezes, e chutar a nota mais comum acerta 20,9%.

**Leitura:** com esse registro, não dá pra dizer o que derruba a satisfação. Pra isso, a operação precisa registrar o que de fato aconteceu no atendimento. Qual foi a resposta, se ela prometeu algo, se o cliente precisou voltar.

## Quanto estamos desperdiçando?

Como o arquivo não mede tempo, não existe "horas desperdiçadas" medidas. As 48 entregas públicas deste desafio estimaram de **R$ 14 mil a R$ 1,95 milhão por ano** em cima do mesmo arquivo. Mais de 100 vezes de diferença, porque cada uma inventou as premissas.

Então entrego a conta como **fórmula, com cada premissa na mesa**, pra quem tem o número real trocar ([`diagnostico/conta.py`](diagnostico/conta.py)):

```
horas por ano = volume x [ %IA resolve x (tempo humano - revisão) + %resumo x triagem poupada ] / 60
```

| Entrada | De onde vem | Pessimista | Base | Otimista |
|---|---|---|---|---|
| Volume | Brief do desafio | 30.000 | 30.000 | 30.000 |
| % que a IA resolve sozinha | Medido nos 110 tickets de teste | 48% | 48% | 48% |
| % que vira resumo pro atendente | Medido nos 110 tickets de teste | 33% | 33% | 33% |
| Tempo humano por ticket | **Premissa** | 8 min | 12 min | 18 min |
| Triagem poupada pelo resumo | **Premissa** | 1,5 min | 3 min | 5 min |
| Revisão de cada resposta da IA | **Premissa** | 1 min | 0,5 min | 0,25 min |
| Custo da hora do atendente | **Premissa** | R$ 25 | R$ 35 | R$ 45 |
| **Horas por ano** | | **1.932** | **3.261** | **5.094** |
| **R$ por ano** | | **48 mil** | **114 mil** | **229 mil** |
| **Equivale a** | | **1,1 pessoa** | **1,9 pessoa** | **2,9 pessoas** |

**Três cuidados com esse número:**
1. **Os 48% são conservadores.** Os 110 tickets de teste foram escritos pra ser difíceis. Uma operação real tem mais dúvida simples.
2. **Não desconta o custo de construir e manter.** Isso depende de como a empresa implanta.
3. **Ele só vale depois do modo sombra.** No teste com tickets que o sistema nunca viu, ele ainda cometeu erros perigosos (seção 3 da [proposta](04-proposta.md)). Liberar automação antes disso troca horas economizadas por cliente perdido.

## O desperdício que o arquivo não mostra

Na minha experiência com atendimento por IA, o maior desperdício não está no tempo de resposta. Está no **retrabalho**: a IA ou o atendente responde errado, o cliente volta mais irritado, e o próximo atendimento custa o dobro. O Dataset 1 não registra isso. Mas aparece no caminho dos tickets: 34% esperando o cliente e um terço que nunca foi respondido.

É hipótese, não número. E é por isso que a proposta começa pela resposta, e não pela velocidade.

## Recomendação do diagnóstico

**Antes de automatizar, registrar cinco coisas em cada ticket:**
1. a hora de abertura
2. a hora de cada resposta
3. quem respondeu (IA ou pessoa)
4. o que foi prometido
5. se o cliente voltou pelo mesmo assunto

Com isso, as três perguntas do diretor passam a ter resposta em quatro semanas.
