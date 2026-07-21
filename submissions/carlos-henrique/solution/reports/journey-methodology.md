# Metodologia de journey mining

## Contrato

Fonte: event log ativo da Fase 2; unidade: conta; quarentena excluída. Foram usadas 13927 linhas ativas.

## Medidas

- `support`: contas distintas contendo o padrão.
- `relative_support`: suporte dividido pelo denominador de contas.
- `confidence`: frequência condicional dentro do grupo definido.
- `lift`: frequência do grupo dividida pela referência, somente com denominador não zero.
- `coverage`: contas cobertas pelo padrão / contas do grupo.
- `leverage`: diferença entre frequência observada e produto das marginais, quando aplicável.
- `discriminative_ratio`: razão de frequências entre desfechos, com zero protegido.

## Mineração

Implementação própria testada; parâmetros: suporte ≥ 15 contas, comprimento ≤ 5, gap ≤ 5 eventos, gap ≤ 90 dias, apenas padrões fechados. Antes/depois do pruning: 5480/4996.

## Exposição e ordenação

Janelas fixas, landmarks, bandas quantílicas e suporte por conta. Ordem intradiária é técnica; dependência HIGH bloqueia promoção.

## Privacidade e uso

Artefatos contêm somente agregados. A taxonomia é descritiva, não causal, preditiva ou interventiva.
