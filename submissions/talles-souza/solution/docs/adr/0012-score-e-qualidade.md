# ADR 0012: O score mede a qualidade do negócio; a ordem da tela e o valor ficam separados

**Status:** aceita (substitui, no ponto das respostas, o [ADR 0003](0003-metodo-e-politica-como-config.md))

## Contexto

O vendedor lê o número do cartão como "esse negócio é bom?". Um lead scorer precisa responder isso. Duas outras perguntas também estão na tela, e são diferentes: por onde começar (a ordem) e quanto está em jogo (o valor). Se o número do cartão misturasse as três, ele enganaria. Medido como posição na tela, um negócio sem decisor teria nota alta só por estar no grupo de cima. Com o preço dentro, um produto caro parado passaria um negócio vivo barato.

O histórico mede uma coisa só: a idade. Dos 19 fatores testados fora da amostra, só ela entrou no motor (AUC 0,830). As respostas do vendedor (quem decide, o problema confirmado, a próxima conversa com data) não existem no histórico.

## Decisão

- **Score 0–100 = qualidade** (`packages/dominio/src/score/qualidade.ts`):
  - **a idade:** `round(100 × chance da faixa de idade ÷ maior chance entre as faixas)`, com as chances do motor (conversão razão);
  - **as respostas do vendedor:** +10 por "Sim", −15 por "Não", sem resposta não muda; limite 0–100.
- **Os pesos das respostas são heurística declarada**, em `packages/dominio/src/score/qualidade.config.ts`, com o aviso "o histórico não tem essas respostas". Trocar a escolha é trocar o config.
- **Sem data de início:** sem resposta, o cartão diz "Score —" e o detalhe pede "Responda as perguntas para pontuar."; com pelo menos uma resposta, o score parte de 50.
- **O valor não entra no score.** O cartão mostra "{produto} · US$ {preço} em jogo" numa linha própria.
- **A ordem da tela não muda:** o grupo, depois o valor esperado (chance × preço; sem data, o preço). A posição ("Na sua lista: 1º de 88") aparece só no "ver por quê".
- As respostas mudam o score e a ação. Não mudam o grupo, a ordem, a chance do motor nem a receita esperada, que ficam só com o que foi medido.

## Consequências

- No `deals.json`, sem respostas: até 40 dias 90–100, 41–50 dias 61, 51–60 dias 41, 61–90 dias 15, acima de 90 dias 1. Toda a Nutrição fica em 15 ou menos; o Siga no ritmo nunca fica abaixo do Foque agora; os 500 sem data mostram "—" ([`score-qualidade-2026-10-23.txt`](../../../process-log/evidencias/score-qualidade-2026-10-23.txt)).
- O Foque agora pode estar no topo da tela com score menor que o do Siga no ritmo logo abaixo. A tela não esconde isso: o topo diz por onde começar (a chance está caindo), e o score diz quão bom o negócio é.
- Os pesos das respostas não foram medidos. Com respostas gravadas no banco e o desfecho dos negócios, dá para medi-los como o motor mede a idade.

## Alternativas consideradas

- **Score = posição na ordem da tela:** responde "por onde começar", não "é bom?"; o vendedor lê "lead bom" num negócio sem decisor.
- **Score = chance absoluta do motor:** 1.532 dos 2.089 abertos ficam abaixo de 10, e o vendedor não distingue um negócio bom de um mediano; a chance continua no detalhe.
- **Pôr o preço no score (valor esperado):** mistura qualidade com tamanho; um produto caro parado ganharia de um negócio vivo.
- **Respostas sem peso:** o vendedor responderia sem ver efeito, e o score ignoraria o que só ele sabe.
