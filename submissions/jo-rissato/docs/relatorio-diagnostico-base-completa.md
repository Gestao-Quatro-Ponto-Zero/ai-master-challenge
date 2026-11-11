# Diagnóstico com 100% dos tickets (Dataset 1)

Base: **8469 tickets**, todos. Desfecho: status do ticket, o único resultado que todo ticket tem.

## Funil geral

| Status | Tickets | % |
|---|---|---|
| Pending Customer Response | 2881 | 34.0% |
| Open | 2819 | 33.3% |
| Closed | 2769 | 32.7% |

## Alguma variável faz o ticket travar?

Teste qui-quadrado de cada variável contra o status (3 níveis). V de Cramér mede a força da relação (0 = nenhuma, 0,1 = fraca, 0,3 = moderada).

| Variável | Categorias | p-valor | V de Cramér | % sem resposta (min a max) | % fechado (min a max) |
|---|---|---|---|---|---|
| Faixa de idade | 5 | 0.073 | 0.029 | 31.7% a 37.0% | 30.4% a 34.1% |
| Assunto | 16 | 0.157 | 0.047 | 29.7% a 37.6% | 29.7% a 37.3% |
| Prioridade | 4 | 0.227 | 0.022 | 32.5% a 33.8% | 31.2% a 34.1% |
| Gênero | 3 | 0.299 | 0.017 | 32.8% a 34.2% | 31.6% a 34.1% |
| Tipo | 5 | 0.339 | 0.023 | 32.2% a 34.5% | 30.4% a 34.0% |
| Ano da compra | 2 | 0.513 | 0.013 | 32.7% a 33.9% | 32.3% a 33.1% |
| Produto | 42 | 0.663 | 0.067 | 26.2% a 40.4% | 24.1% a 40.0% |
| Canal | 4 | 0.771 | 0.014 | 32.7% a 34.5% | 32.2% a 33.6% |

## Modelo com todas as variáveis juntas

Random Forest, validação cruzada em 5 partes, prevendo o status de cada ticket.

| Alvo | Acurácia do modelo | Acurácia da linha de base (prever sempre a classe mais comum) |
|---|---|---|
| Status (3 níveis) | 34.2% | 34.0% |
| Fechou ou não | 67.3% | 67.3% |
| Ficou sem resposta ou não | 66.7% | 66.7% |

## Por canal e prioridade (100%)

| Canal | Prioridade | Tickets | Sem resposta | Aguardando cliente | Fechado |
|---|---|---|---|---|---|
| Phone | Low | 499 | 38.9% | 33.5% | 27.7% |
| Phone | High | 512 | 35.2% | 31.2% | 33.6% |
| Chat | Critical | 504 | 34.5% | 32.7% | 32.7% |
| Social media | High | 552 | 34.4% | 34.8% | 30.8% |
| Email | High | 504 | 34.3% | 31.2% | 34.5% |
| Phone | Medium | 595 | 33.9% | 33.8% | 32.3% |
| Email | Critical | 571 | 33.6% | 33.3% | 33.1% |
| Chat | Low | 501 | 33.5% | 35.1% | 31.3% |
| Social media | Medium | 503 | 33.2% | 35.8% | 31.0% |
| Chat | Medium | 551 | 33.0% | 37.4% | 29.6% |
| Email | Medium | 543 | 32.4% | 33.9% | 33.7% |
| Social media | Low | 538 | 32.3% | 35.1% | 32.5% |
| Social media | Critical | 528 | 31.4% | 33.9% | 34.7% |
| Chat | High | 517 | 31.1% | 32.3% | 36.6% |
| Email | Low | 525 | 30.5% | 36.4% | 33.1% |
| Phone | Critical | 526 | 30.4% | 33.7% | 35.9% |

## O que NÃO dá para calcular em 100%

| Métrica | Tickets com o dado | Motivo |
|---|---|---|
| Satisfação | 2769 | Só o fechado recebe nota |
| Tempo até resolver | 2769 | Só o fechado tem resolução |
| Tempo até a 1ª resposta | 0 | Não existe data de abertura do ticket |

Preencher nota ou tempo dos outros 5.700 com estimativa seria inventar dado. Esses números ficam com a base declarada (n = 2.769 ou 1.404).
