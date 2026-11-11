# Prompt: resumo do gestor

> Não usado nesta versão. `ia/briefing.py` roda só com `template_gestor`, validado por
> `ia/validar.py`. Este arquivo é o contrato para quando a chamada à API for ligada.

## Entrada

`fatos_gestor(scored, gerente)`: nome do gerente, semana do trimestre, número de
vendedores, quantos sem deal, contagens de fechar e encerrar do time, e os valores
aberto, vivo e vencido.

## Regra de escrita

- Mesmas regras de `briefing_vendedor.md`: número só em marcador, nenhuma conta ou
  produto fora dos fatos (aqui, nenhum), nenhuma palavra de promessa.
- Não afirmar chance de decisão em 28 dias quando `n_fechar` do time é 0.
- Foco: cobertura do time (quantos vendedores têm deal) e onde o valor aberto está
  concentrado (vivo vs. vencido), não detalhe de deal individual.

## Saída esperada

Texto corrido, curto (3 a 5 linhas), em português, usando só os marcadores de
`ia.validar.marcadores_validos(fatos)`.
