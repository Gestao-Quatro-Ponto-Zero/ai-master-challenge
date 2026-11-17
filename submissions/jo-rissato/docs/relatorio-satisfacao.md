# O que impacta a satisfação?

## Base

| Item | Tickets | % da base |
|---|---|---|
| Base total | 8469 | 100% |
| Com nota de satisfação (todos fechados) | 2769 | 32.7% |
| Sem nota (abertos ou aguardando cliente) | 5700 | 67.3% |

A nota só existe quando o ticket fecha. Esta análise usa 100% das notas existentes. Para os outros tickets, a satisfação não foi coletada.

## Distribuição das notas

| Nota | Tickets | % |
|---|---|---|
| 1 | 553 | 20.0% |
| 2 | 549 | 19.8% |
| 3 | 580 | 20.9% |
| 4 | 543 | 19.6% |
| 5 | 544 | 19.6% |

Teste de aderência a uma distribuição uniforme (todas as notas iguais): p = 0.797. Acima de 0,05 = as notas não se distinguem de um sorteio de 1 a 5.

## Cada variável contra a nota (15 testes)

p-valor corrigido = p × número de testes (Bonferroni). Impacto real exige corrigido < 0,05.

| Variável | Tipo | p-valor | p corrigido | Efeito |
|---|---|---|---|---|
| Hora do dia da 1ª resposta | numérica | 0.033 | 0.502 | rho -0.040 |
| Dias entre compra e 1ª resposta | numérica | 0.041 | 0.619 | rho +0.039 |
| Ano da compra | categórica, 2 grupos | 0.057 | 0.849 | média de 2.94 a 3.04 |
| Tamanho da resolução | numérica | 0.124 | 1.000 | rho +0.029 |
| Registro de tempo impossível | categórica, 2 grupos | 0.156 | 1.000 | média de 2.95 a 3.03 |
| Horas entre 1ª resposta e resolução | numérica | 0.254 | 1.000 | rho +0.022 |
| Canal | categórica, 4 grupos | 0.278 | 1.000 | média de 2.95 a 3.08 |
| Gênero | categórica, 3 grupos | 0.625 | 1.000 | média de 2.97 a 3.03 |
| Prioridade | categórica, 4 grupos | 0.629 | 1.000 | média de 2.96 a 3.05 |
| Produto | categórica, 42 grupos | 0.667 | 1.000 | média de 2.54 a 3.22 |
| Tipo | categórica, 5 grupos | 0.699 | 1.000 | média de 2.93 a 3.03 |
| Tamanho da descrição | numérica | 0.770 | 1.000 | rho +0.006 |
| Assunto | categórica, 16 grupos | 0.807 | 1.000 | média de 2.80 a 3.18 |
| Idade | numérica | 0.832 | 1.000 | rho -0.004 |
| Faixa de idade | categórica, 5 grupos | 0.893 | 1.000 | média de 2.96 a 3.05 |

## Todas as variáveis juntas

Validação cruzada em 5 partes.

| Modelo | Resultado | Linha de base |
|---|---|---|
| Random Forest, nota exata | 21.2% de acerto | 20.9% (sempre a nota mais comum) |
| Random Forest, nota como número | R² = -0.013 | 0 (prever sempre a média) |
| Texto da descrição + resolução (TF-IDF, regressão logística) | 22.2% de acerto | 20.9% |

## Conferência do sinal no texto da descrição

Num primeiro teste, o texto da descrição acertou a nota acima do acaso (23,0% contra 20,1%,
p = 0,002 em 500 permutações). Antes de tratar como achado, foram feitas três conferências:

| Conferência | Resultado |
|---|---|
| Descrições repetidas carregam a mesma nota? | Não: 113 fechados em 24 grupos de texto idêntico, só 1 grupo com nota igual |
| Validação sem vazamento (vetorização do texto feita dentro de cada parte da validação, 10 divisões diferentes) contra 40 sorteios da nota | Real 21,7% (de 20,6% a 23,0%); acaso 20,2%, limite de 95% em 21,6%; p = 0,05 |
| Palavras que mais puxam a nota | Sem sentido de negócio: "right", "then", "buy" (média 2,35 a 2,56) contra "code", "check", "days" (3,33 a 3,39) |

O primeiro p = 0,002 estava inflado: o vocabulário do texto tinha sido aprendido com a base inteira,
inclusive com os tickets usados para testar. Na validação correta, o ganho cai para 1,5 ponto e fica
no limite (p = 0,05). Somado aos 15 testes anteriores, não passa da correção para testes múltiplos.
**Conclusão: o texto também não impacta a satisfação.**

## Resposta

Nenhuma variável registrada impacta a satisfação. Com 2769 notas, nenhum dos 15 testes passa da correção, os modelos não superam a linha de base (o texto da descrição chegou ao limite, p = 0,05, sem resistir à correção) e as notas se distribuem como sorteio. Para 5700 tickets (67.3%) a satisfação não existe no dado.
