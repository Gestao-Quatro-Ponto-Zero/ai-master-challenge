# Model card: roteador de tickets

## O que faz

Lê o texto de um ticket de TI e escolhe uma de 8 filas (Acesso, Direitos de administrador, RH, Hardware, Projeto interno, Diversos, Compras, Armazenamento), com a probabilidade de cada uma. Uma política decide se o ticket segue sozinho, vai para o agente com duas sugestões ou vai para triagem humana.

## Modelo

- TF-IDF de palavras e pares de palavras (10 mil termos, tf sublinear) + regressão logística multinomial (C = 8)
- Treino em 33.485 tickets, limiares escolhidos em 7.176, medição em 7.176 (divisão estratificada, semente 42)
- Escolhido entre 5 candidatos pela calibração: ECE 0,011 contra 0,047 do SVM, que acerta 0,4 ponto a mais

## Desempenho no teste

| Métrica | Valor |
|---|---|
| Acerto | 85,6% |
| F1 macro | 0,856 |
| Erro de calibração (ECE) | 0,011 |
| Automático | 57,4% dos tickets, 96,2% de precisão |
| Assistido | 35,2%, fila certa entre as duas sugestões em 92,7% |
| Humano | 7,4% |
| Rejeição indevida pelas travas | 4,1% |

Pior fila: Direitos de administrador (70% de acerto, ECE 0,113). Por isso ela nunca é automática.

## Política (a primeira regra que dispara decide)

1. Vocabulário conhecido abaixo de 55% → humano
2. Similaridade com o histórico abaixo do percentil 2 da validação → humano
3. Pares de palavras conhecidos abaixo do percentil 2 da validação (9,4%) → humano. Pega texto embaralhado ou com palavra intercalada
4. Fila prevista é Direitos de administrador → assistido
5. Probabilidade somada de filas sensíveis ≥ 0,05 e fila prevista não sensível → assistido
6. Algum trecho de 8 palavras com probabilidade ≥ 0,70 numa fila sensível, e fila prevista não sensível → assistido. Pega o ticket disfarçado com palavras coladas
7. Confiança ≥ 0,79 → automático
8. Confiança ≥ 0,44 → assistido
9. Resto → humano

As regras 3 e 6 vieram do pentest ([`05_adversarial.py`](../solution/analysis/05_adversarial.py)); os parâmetros da 6 foram escolhidos na validação, nunca no teste.

Por população: disjuntor compara as últimas 200 previsões com a distribuição do treino (PSI); acima de 0,25, o automático pausa.

## Usos fora do escopo

- Tickets em outro idioma ou de outro domínio: vão para humano por desenho; não treinar resposta com eles
- Qualquer ação além de escolher a fila: conceder acesso, responder, aprovar
- Tickets do Dataset 1: o modelo não foi treinado nesse domínio

## Riscos conhecidos

- Fila nova não é detectada pelas travas (31% seguiriam sozinhos para fila errada no teste). Proteção: taxa de override por fila e retreino
- Evasão: com 5 palavras comuns coladas, 15% dos pedidos de administrador e 10% dos de RH ainda seguem sozinhos para outra fila (eram 42%). O dano é de rota: conceder acesso nunca depende da fila
- Com 10% ou mais de erro de digitação, a precisão do automático cai para 92% e 54% dos tickets vão para humano; a recalibração semanal do limiar devolve 96%
- O dataset vem pré-processado; em produção, treinar com o histórico real da operação

## Integridade

O arquivo do modelo leva o hash SHA-256 do conteúdo no nome, e o console confere o hash e a estrutura antes de usar. Um arquivo alterado no caminho é recusado (teste em `tests/model-loader.test.ts` e no pentest).

## Manutenção

Override por fila, auditoria cega de 2% do automático, recalibração semanal do limiar, retreino mensal ou na criação de fila.
