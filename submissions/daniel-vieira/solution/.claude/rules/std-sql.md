---
subject: Padrões de codificação SQL
author: dcvr@
---


# Escopo

- Este documento define os padrões de codificação SQL adotados na Polya Technologies, abrangendo
  formatação, nomenclatura, estrutura de consultas, correção e portabilidade entre motores de
  banco de dados;
- PostgreSQL e DuckDB são os dois motores de destino, sendo que o PostgreSQL persiste dados de
  negociação programática e o DuckDB atende à pesquisa, à modelagem e à simulação;
- Estes padrões aplicam-se a todo o SQL mantido pela equipe, esteja ele embutido em Common Lisp,
  gerado por um script ou mantido em um arquivo autônomo;
- A palavra-chave "deve" denota um requisito obrigatório, a palavra-chave "recomenda-se" denota
  uma recomendação forte que admite exceções justificadas e a palavra-chave "pode" denota uma
  escolha discricionária que deve permanecer internamente consistente;
- A conformidade é verificada com `sqlfluff` sob o dialeto que corresponde ao motor de destino,
  visto que tanto o dialeto `postgres` quanto o dialeto `duckdb` são suportados;
- Estes padrões são independentes de qualquer editor, cliente ou ferramenta de banco de dados em
  particular.


# Portabilidade e Dialeto

## Linha de Base Portável

- Escrever em ANSI SQL uma consulta que deve executar em ambos os motores, que é a linha de base
  portável compartilhada por PostgreSQL e DuckDB;
- Preferir uma função SQL padrão a uma específica de fornecedor sempre que uma consulta se
  destine a ser portável;
- Restringir a portabilidade às consultas que genuinamente a exigem, em vez de restringir toda
  consulta ao subconjunto comum.

## Extensões Específicas de Motor

- Tratar uma consulta como vinculada a um único motor por padrão, e torná-la portável apenas
  quando o compartilhamento entre motores for um requisito explícito;
- Utilizar uma extensão específica de motor quando ela oferecer um benefício significativo sobre
  o seu equivalente portável;
- No DuckDB, utilizar os recursos analíticos que motivam o seu uso, tais como `ASOF JOIN` para
  correspondência temporal, `QUALIFY` para filtragem sobre funções de janela e os tipos list e
  struct;
- No PostgreSQL, utilizar extensões como `RETURNING`, `ON CONFLICT` e `DISTINCT ON` onde
  simplificam uma instrução;
- Marcar claramente o SQL específico de motor, de modo que a sua não portabilidade seja evidente
  a um leitor posterior.


# Formatação

## Palavras-Chave e Disposição

- Escrever palavras-chave reservadas e nomes de funções internas em maiúsculas, e escrever os
  identificadores em minúsculas;
- Colocar cada cláusula principal, tais como `SELECT`, `FROM`, `WHERE`, `GROUP BY` e `ORDER BY`,
  em sua própria linha;
- Recuar consistentemente o corpo de uma subconsulta, de uma tabela unida e de uma expressão de
  tabela comum;
- Escrever literais de data e hora na forma ISO-8601;
- Limitar uma linha a 96 colunas.

## Colunas e Aliases

- Listar explicitamente as colunas selecionadas, e não utilizar `SELECT *` em código que é
  retido;
- Qualificar toda referência de coluna com a sua tabela ou alias em uma consulta que nomeia mais
  de uma tabela;
- Introduzir um alias de tabela curto e significativo com a palavra-chave `AS`.


# Nomenclatura

## Identificadores

- Nomear todo identificador em minúsculas com palavras separadas por sublinhados, começando com
  uma letra;
- Não colocar identificadores entre aspas, e não utilizar uma palavra reservada como
  identificador;
- Evitar abreviações e prefixos de representação tais como `tbl_` ou a notação húngara.

## Tabelas e Colunas

- Nomear uma tabela com um substantivo coletivo ou plural, e nomear uma coluna no singular;
- Não dar a uma tabela o mesmo nome de uma de suas colunas;
- Não repetir o nome da tabela dentro do nome de uma coluna.


# Estrutura e Segurança das Consultas

## Junções e Subconsultas

- Unir tabelas com a forma explícita `JOIN ... ON`, e nunca com uma junção por vírgula ou uma
  condição de junção colocada na cláusula `WHERE`;
- Estruturar uma consulta complexa com expressões de tabela comuns introduzidas por `WITH`, em
  vez de subconsultas profundamente aninhadas;
- Expressar uma transformação como uma operação baseada em conjuntos, em vez de processamento
  linha a linha.

## Predicados e Tratamento de Nulos

- Testar o valor nulo com `IS NULL` e `IS NOT NULL`, e considerar a lógica de três valores do
  SQL;
- Tornar explícita toda conversão de tipo, em vez de depender de coerção implícita;
- Evitar envolver uma coluna em uma função no lado do predicado onde isso impediria o uso de um
  índice.

## Parâmetros e Mutação

- Passar valores como parâmetros vinculados, e nunca montar uma instrução concatenando entrada
  não confiável no texto SQL;
- Restringir todo `DELETE` e `UPDATE` com uma cláusula `WHERE`, a menos que um efeito sobre a
  tabela inteira seja pretendido;
- Envolver em uma transação uma alteração de múltiplas instruções sobre dados de negociação, de
  modo que ela seja confirmada ou revertida como uma unidade.


# Comentários

- Comentar uma consulta não óbvia, explicando a intenção de uma expressão de tabela comum,
  junção ou função de janela complexa;
- Escrever um comentário de linha com `--` e um comentário de bloco com `/* ... */`;
- Marcar o código que requer atenção posterior com um comentário `TODO` em maiúsculas que
  identifique a pessoa responsável, e escrever as datas na forma `YYYY-MM-DD`;
- Reescrever uma consulta opaca em vez de explicá-la com um comentário.


# Sinais de Alerta

- As construções listadas abaixo são sinais de alerta que devem motivar revisão, embora a
  maioria delas também ocorra em situações legítimas;
- Revisar qualquer uso de `SELECT *` em código que é retido;
- Revisar qualquer junção por vírgula ou qualquer condição de junção expressa na cláusula
  `WHERE`;
- Revisar qualquer SQL montado por concatenação de cadeias;
- Revisar qualquer `DELETE` ou `UPDATE` que não tenha cláusula `WHERE`;
- Revisar qualquer dependência de coerção implícita de tipo;
- Revisar qualquer referência de coluna não qualificada em uma consulta sobre múltiplas tabelas.
