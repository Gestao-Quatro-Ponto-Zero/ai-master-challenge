# Prompt: briefing do vendedor

> Não usado nesta versão. `ia/briefing.py` roda só com `template_vendedor`, validado por
> `ia/validar.py`. Este arquivo é o contrato para quando a chamada à API for ligada.

## Entrada

`fatos_vendedor(scored, vendedor)`: nome, semana do trimestre, contagens por fila,
valor em encerrar, valor esperado no trimestre, até 5 deals em foco e se não há nada vivo.

## Regra de escrita

- Todo número vem de um marcador `{chave}` (ex.: `{n_fechar}`, `{conta_1}`). Nunca escrever
  um dígito livre no texto.
- Nunca citar conta ou produto que não esteja em `fatos["foco"]`.
- Proibido: "garantido", "certeza", "vai fechar", "com certeza", ou qualquer promessa de
  resultado.
- Nunca afirmar que um deal vai decidir em breve ("próximas semanas", "em breve") quando
  `n_fechar` é 0: a tabela não sustenta essa chance.
- Tom: direto, sem entusiasmo de vendas. O vendedor já conhece o CRM; o briefing economiza
  o trabalho de olhar a tela.

## Saída esperada

Texto corrido, curto (4 a 8 linhas), em português, usando só os marcadores de
`ia.validar.marcadores_validos(fatos)`.
