# 05 · Política de atendimento

As regras que decidem o que a IA faz com cada ticket. Escritas a partir da minha experiência com IA de atendimento e aprovadas por mim em 22/10/2026, respondendo um teste de 80 tickets difíceis.

**O princípio:** a IA nunca determina nada que comprometa a empresa. Ela informa, qualifica, resume e encaminha. Quem decide é uma pessoa, a não ser que exista uma regra objetiva escrita.

**Processo escrito vem antes da IA.** A IA só responde sozinha (A) ou resolve (B) quando existe um processo documentado que cobre o caso. Sem processo, a resposta certa depende de alguém, e o ticket vai pra uma pessoa. Uma IA sem processo não sabe, e quando não sabe, inventa.

## As 5 ações

| Ação | Quando |
|---|---|
| **A · Responde sozinha** | Informa ou orienta. Não decide nada pela empresa |
| **B · Resolve e encaminha** | Caso claro, com regra objetiva. Abre o processo pra equipe responsável |
| **C · Resume e passa pro atendente** | Ambíguo ou sensível. A IA qualifica, a pessoa decide |
| **D · Pessoa na hora, com prioridade** | Cliente irritado ou que pediu uma pessoa |
| **E · Pede o que falta** | Não dá pra seguir sem mais informação |

## As regras

| | Regra | Ação |
|---|---|---|
| **R1** | Cliente irritado, irônico, que já voltou várias vezes ou que pede uma pessoa | **D** |
| **R2** | Cliente num momento pessoal difícil (desemprego, luto, vulnerável). Precisa de acolhimento humano | **C** |
| **R3** | Informação clara e regra objetiva (dentro dos 7 dias, pedido não enviado, pedido duplicado) | **B** |
| **R4** | Dúvida de informação, ou pedido sem base que a IA pode recusar (reembolso de frete por 1 dia de atraso, troca sem nota) | **A** |
| **R5** | Caso complexo ou com risco (valor diferente do esperado, suspeita de falsificação, dano a outro produto) | **C** |
| **R6** | Depende de a empresa aceitar uma exceção (desconto, cobrir preço, devolver diferença) | **C** |
| **R7** | Ameaça (Reclame Aqui, chargeback) ou pedido de confirmação por escrito | **C** |
| **R8** | Falta informação pra seguir | **E** |
| **R9** | Risco físico (bateria estufada, cheiro de queimado, choque, fogo) | **D** |
| **R10** | Urgente e sem processo documentado que cubra o caso (fraude no cartão, por exemplo). Se o processo existe e cobre, a IA responde | **D** |
| **R11** | O cliente claramente tem direito, mas alguém precisa apurar quem causou o problema (entregador, centro de distribuição). Exemplo: celular que chegou como tijolo. Não é pra negar o reembolso, é pra entender o que aconteceu | **C** |

Quando mais de uma regra vale ao mesmo tempo, a ordem é: segurança (R9), irritação (R1), urgência (R10), e depois as outras.

**Observação:** se a entrega foi há poucos dias, vale um contato mais próximo.

## Casos que as regras não cobriam

Saúde, fraude, dado pessoal e pagamento ficaram fora das regras acima. Nesses 8 casos do teste, a IA sugeriu e eu aprovei:

| Tema | Ação |
|---|---|
| Saúde (sintoma, criança) | **C** |
| Fraude ou golpe | **C** |
| Exclusão de dados (LGPD) | **C** |
| Pedido de documento de outra pessoa | **A**, a IA recusa |
| Dúvida de pagamento sem exceção | **A** |
