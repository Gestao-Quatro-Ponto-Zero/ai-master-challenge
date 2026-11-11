# Auditoria do Dataset 2

Arquivo: `all_tickets_processed_improved_v3.csv`. Base: 47.837 textos, 2 colunas (`Document`, `Topic_group`).

## 1. Integridade

| Verificação | Resultado |
|---|---|
| Valores vazios | 0 |
| Textos duplicados exatos | 0 |
| Duplicados após normalizar (minúsculas, só letras) | 0 |
| Mesmo texto com rótulos diferentes | 0 |
| Textos com 3 palavras ou menos | 49 |
| Textos com mais de 200 palavras | 1.097 |

## 2. O texto já vem pré-processado

| Marca | Textos |
|---|---|
| Com letra maiúscula | 0 |
| Com dígito | 0 |
| Com @ (e-mail) | 0 |
| Com pontuação (. , ! ?) | 16 |
| Com caractere fora do ASCII | 0 |

O texto está em inglês, em minúsculas, sem números, sem e-mails e quase sem pontuação. Esse tratamento foi feito antes da publicação. Para o classificador, isso quer dizer que um ticket novo precisa passar pelo mesmo tratamento antes de ser classificado.

## 3. Categorias

| Categoria | Textos | % | Mediana de palavras |
|---|---|---|---|
| Hardware (Hardware) | 13.617 | 28.5% | 32 |
| Suporte de RH (HR Support) | 10.915 | 22.8% | 24 |
| Acesso (Access) | 7.125 | 14.9% | 22 |
| Diversos (Miscellaneous) | 7.060 | 14.8% | 27 |
| Armazenamento (Storage) | 2.777 | 5.8% | 21 |
| Compra (Purchase) | 2.464 | 5.2% | 30 |
| Projeto interno (Internal Project) | 2.119 | 4.4% | 24 |
| Direitos de administrador (Administrative rights) | 1.760 | 3.7% | 30 |

A maior categoria tem 7.7 vezes o volume da menor. Acurácia geral esconde as categorias pequenas, então o classificador será medido por categoria.

## 4. Textos-modelo repetidos

17 começos de texto (6 primeiras palavras) se repetem em 20 textos ou mais, cobrindo 1.138 textos (2.4%). Em 13 deles todos os textos têm a mesma categoria.

| Começo do texto | Textos | Categorias | Categoria principal | % na principal |
|---|---|---|---|---|
| new purchase po purchase po dear | 415 | 2 | Compra | 99.8% |
| purchase request for it final owner | 101 | 1 | Compra | 100.0% |
| access request for a list or | 78 | 3 | Hardware | 55.1% |
| please action direct reports missing time | 71 | 3 | Suporte de RH | 91.5% |
| new purchase po friday pm purchase | 60 | 1 | Compra | 100.0% |
| new purchase po wednesday pm purchase | 59 | 1 | Compra | 100.0% |
| new purchase po thursday pm purchase | 53 | 1 | Compra | 100.0% |
| new starter access card enabling bucharest | 49 | 3 | Suporte de RH | 95.9% |

Os textos que começam com "new purchase po" e são de Compra somam 1.210, 49.1% da categoria Compra (2.464). São formulários automáticos, fáceis de acertar, e podem inflar o acerto dessa categoria. O classificador será medido também sem esses textos-modelo.

## 5. Palavras que aparecem em várias categorias

| Palavras | Textos | Distribuição pelas 3 categorias principais |
|---|---|---|
| password, login, locked, unlock | 1.960 | Acesso 69.5%, Hardware 19.8%, Direitos de administrador 6.1% |
| leave, holiday, salary, payroll, vacation | 3.526 | Suporte de RH 58.3%, Hardware 15.3%, Diversos 11.7% |
| admin rights, administrator, local admin | 3.369 | Compra 58.8%, Hardware 15.3%, Suporte de RH 10.2% |

Lendo os exemplos, a mesma palavra muda de sentido conforme o contexto: "leave" é férias em Suporte de RH e é o verbo "deixar" em Hardware; "locked" é conta bloqueada em Acesso e é aparelho bloqueado em Compra; "administrator" é a assinatura do formulário de compra (1.184 dos 1.980 textos de Compra com essas palavras começam com "new purchase po"). Isso não prova rótulo errado. Mostra que regra por palavra-chave erra e que o classificador precisa do contexto do texto inteiro.

## 6. O que a auditoria permite e o que não permite

- Permite: treinar um classificador de 8 categorias sobre textos sem vazio, sem duplicata e sem conflito de rótulo.
- Não permite: medir tempo, satisfação ou resolução, porque o Dataset 2 só tem texto e categoria.
- Não permite: ligar o Dataset 2 ao Dataset 1 (lacuna 12). As 8 categorias de TI interna não são os 5 tipos do Dataset 1 (reembolso, cancelamento etc.).
- Não permite afirmar que os rótulos estão todos certos: só a matriz de confusão do classificador vai mostrar onde as categorias se confundem.
