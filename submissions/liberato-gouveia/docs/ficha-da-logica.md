# Ficha da lógica do Lead Scorer

> **Status:** proposta pela IA (Claude), testada nos dados reais e **aprovada pelo Liberato em 04/11/2026 às 20:00** (Registro 05). Todas as escolhas aprovadas coincidem com as opções que a IA recomendou. A versão anterior, ainda como proposta, está em `process-log/versoes/ficha-da-logica_v1_proposta.md`.
> Evidências: `process-log/analises/fase2_logica.py` e `process-log/analises/resultados/fase2_resultados.txt`.

## Princípio

A nota usa **só o que se sabe hoje** sobre um deal: a etapa em que está, há quantos dias está aberto e o preço do produto. Nada do que só se descobre quando o deal termina entra na conta. Produto, setor, empresa, gerente e vendedor também **não entram**, porque os testes mostraram que não preveem o resultado (Etapas 4 e 6 do diário).

## As 4 listas (situação em 31/12/2017)

| Lista | Quais deals entram | Ordem | Ação na tela | Deals |
|---|---|---|---|---|
| **1. Foco** | Em negociação, com até 138 dias, chance histórica acima de 0% e preço ≥ US$ 100 | Valor esperado | "Avançar este deal" | 228 |
| **2. Requalificar ou encerrar** | Em negociação há mais de 138 dias **ou com chance histórica 0%** (hoje, os de 138 dias, regra aprovada no Registro 08) | Preço | Preço ≥ US$ 4.000: "Ligar para requalificar" (354 deals). Abaixo disso: "Encerrar no CRM" (947 deals) | 1.301 |
| **3. Iniciar contato** | Em prospecção | Preço (sem % de chance) | "Fazer o primeiro contato" | 500 |
| **4. Automatizar** | Em negociação, com até 138 dias, chance acima de 0% e preço < US$ 100 | Valor esperado | "Incluir na cadência automática" | 60 |

Um deal sem empresa cadastrada mostra o aviso **"Empresa não cadastrada: complete o cadastro no CRM"** **nas 4 listas**. Para a lista Foco, essa foi decisão do Liberato no Registro 03. Para as 4 listas, ele aprovou no Registro 06 e reconfirmou em 04/11 às 21:20.

## A nota da lista Foco

**Valor esperado = chance pela idade × preço de tabela**

Chance de ser ganho para um deal aberto há X dias. É a curva oficial, montada com os deals iniciados entre 01/03 e 14/08/2017, os mais recentes cujo resultado já é conhecido:

| Idade | 0 d | 14 d | 30 d | 60 d | 75 d | 90 d | 100 d | 110 d | 120 d | 130 d | 138 d |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Chance | 47% | 44% | 42% | 39% | 34% | 26% | 18% | 11% | 5% | 1% | 0% |

- **Formato aprovado: os dois.** A lista mostra uma **nota de 0 a 100**, que diz qual porcentagem dos outros deals do Foco tem valor esperado menor (100 é o maior da empresa e 0 é o menor). O "porquê" mostra o **valor esperado em US$** com a conta completa.

## O que o vendedor lê (textos gerados pelo motor, Fase 3a)

- **Foco:** *"Valor esperado US$ 2.313 = preço US$ 5.482 (GTX Plus Pro) × 42% de chance. Na história da empresa, deals com 21 dias em negociação foram ganhos 42% das vezes."*
  - Deal com 90 dias ou mais acrescenta: *"Atenção: depois de 90 dias a chance cai rápido, e nenhum deal fechou depois de 138 dias."* (sugerido pela IA e aprovado pelo Liberato no Registro 08; muda só o texto, não a nota)
  - Chance abaixo de 1% aparece como *"menos de 1%"*, e não como "0%".
  - Nota: *"Nota 76 de 100: vale mais (em valor esperado) que 76% dos outros deals em Foco na empresa"*.
- **Requalificar (ligar):** *"Aberto há 150 dias. Nenhum deal da história fechou depois de 138 dias. Preço US$ 26.768 (GTK 500), igual ou acima de US$ 4.000: vale uma ligação para confirmar se ainda existe interesse antes de encerrar."*
- **Requalificar (encerrar):** *"Aberto há 139 dias. [...] Preço US$ 3.393 (MG Advanced), abaixo de US$ 4.000: encerre no CRM para limpar o pipeline."*
- **Iniciar contato:** *"Em prospecção: a base não tem histórico para estimar a chance de deals nesta etapa. Ordenado pelo preço: US$ 5.482 (GTX Plus Pro)."*
- **Automatizar:** *"Preço US$ 55 (MG Special) abaixo do mínimo de US$ 100 para atenção individual. Valor esperado US$ 25 (46% de chance para um deal com 9 dias)."*
- **Aviso, nas 4 listas** (decisão do Liberato, Registro 06): *"Empresa não cadastrada: complete o cadastro no CRM"*.

**Caso de borda resolvido (Registro 08):** 10 deals tinham exatamente 138 dias e chance histórica 0% (8 estavam no Foco e 2 no Automatizar). Com a aprovação do Liberato, eles passaram para "Requalificar ou encerrar" (`mover_chance_zero_para_requalificar: true`), com o texto: *"Aberto há 138 dias. Na história da empresa, nenhum deal com 138 dias ou mais em negociação foi ganho. [...]"*. O alerta dos 90 dias também foi aprovado.

## Parâmetros (ficam na configuração, não no código)

| Parâmetro | Valor | Como é definido | Opções e impacto |
|---|---|---|---|
| Limite de ciclo | 138 dias | **Automático:** o maior ciclo entre os deals fechados até a data de referência | — |
| Chance 0% vai para Requalificar | **sim (aprovado)** | Decisão do Liberato (Registro 08) | Move os 10 deals de 138 dias |
| Idade do alerta no texto | **90 dias (aprovado)** | Decisão do Liberato (Registro 08) | Muda só o texto |
| Valor mínimo do Foco | **US$ 100 (aprovado)** | Decisão do Liberato | US$ 100: Foco com 236 deals (~11 por vendedor), número calculado antes da regra da chance 0%; hoje são 228. US$ 600: 178 (~8). US$ 1.100: 123 (~6). |
| "Deal grande" na requalificação | **US$ 4.000 (aprovado)** | Decisão do Liberato | US$ 1.000: 766 ligações (~28 por vendedor). US$ 3.000: 563 (~21). US$ 4.000: 350 (~13). US$ 5.000: 153 (~6). |
| Início da observação | 01/03/2017 | É o primeiro dia com fechamentos registrados na base | — |

## Como sabemos que funciona: teste de volta no tempo

Fingimos que hoje era 30/09/2017 e montamos a lógica **só com dados até essa data**. Em seguida, conferimos o que aconteceu de fato até 31/12/2017 com os 2.409 deals que estavam em negociação (Gráfico 7):

| Lógica | Receita de out–dez que estava nos 20% de deals com maior nota | Taxa de ganho desses deals | Deals fora do padrão (>138 dias) entre eles |
|---|---|---|---|
| **Nossa (chance pela idade × valor)** | **68%** | **35%** | **0%** |
| Só valor | 47% | 23% | 23% |
| "Óbvia" (taxa de produto/setor/vendedor × valor) | 49% | 24% | 21% |
| "Óbvia" sem valor | 15% (pior que escolher ao acaso, que daria 20%) | 20% | 24% |

![Gráfico 7](../process-log/graficos/grafico7_backtest.png)

Se cada vendedor olhasse os seus 10 primeiros deals, a nossa lógica reuniria 50% da receita futura. As alternativas reuniriam 31%, 30% e 10%.

## Limitações conhecidas

- **As porcentagens absolutas dependem do período usado na curva.** Com os deals de mar–jun/2017, um deal novo tem 53% de chance. Com os de mar–ago/2017, tem 47%. A **ordem** dos deals praticamente não muda: a correlação entre as duas ordens é 0,997, e 1 seria idêntica.
- **Prospecção sem % de chance:** a base não guarda nenhum histórico de quantos deals saem da prospecção.
- **Sem dados de atividade:** ligações, e-mails e reuniões seriam o próximo sinal a testar numa base real.
- **Base fictícia:** os dados são da Maven Analytics.
- **Fim de trimestre:** 49% dos ganhos são registrados em mar/jun/set/dez, mas usar isso exigiria informação futura. Fica só como observação.
