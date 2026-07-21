---
subject: Padrões de codificação Bash
author: dcvr@
---


# Escopo

- Este documento define os padrões de codificação em Bash adotados na Polya Technologies,
  abrangendo estrutura de scripts, nomenclatura, uso de aspas, controle de fluxo, funções,
  tratamento de erros e documentação;
- O shell alvo é o GNU Bash, e a portabilidade para o POSIX sh ou outros shells não é um
  objetivo;
- Estes padrões aplicam-se a todos os scripts Bash mantidos pela equipe;
- A palavra-chave "deve" denota um requisito obrigatório, a palavra-chave "recomenda-se" denota
  uma recomendação forte que admite exceções justificadas e a palavra-chave "pode" denota uma
  escolha discricionária que deve permanecer internamente consistente;
- A conformidade é verificada com `shellcheck` sempre que uma regra puder ser imposta
  mecanicamente;
- Reescreva um script em Common Lisp quando este exceder aproximadamente uma página, exigir
  estruturas de dados além de cadeias e arranjos planos ou exigir tratamento de erros não
  trivial.


# Estrutura do Script

## Shebang e Opções do Shell

- Inicie todo script executável com o shebang `#!/usr/bin/env bash`;
- Habilite as opções estritas `set -euo pipefail` imediatamente após o shebang;
- Defina e restaure `IFS` explicitamente onde a divisão em palavras importa, em vez de confiar
  em seu valor herdado.

## Disposição

- Limite a linha de código a 96 colunas;
- Recue com dois espaços, e não utilize caracteres de tabulação exceto onde um here-document
  `<<-` exigir tabulações iniciais;
- Defina a lógica executável dentro de funções e invoque uma única função `main` como a última
  linha, chamada como `main "$@"`;
- Nomeie scripts executáveis sem extensão e bibliotecas reutilizáveis com a extensão `.sh`, e
  torne as bibliotecas não executáveis.


# Nomenclatura

## Nomes de Funções

- Nomeie funções em minúsculas com palavras separadas por sublinhados;
- Defina uma função como `name() { ... }` e omita a palavra-chave `function`;
- Nomeie uma função pela única ação que ela executa.

## Variáveis e Constantes

- Nomeie variáveis locais em minúsculas com palavras separadas por sublinhados;
- Nomeie variáveis de ambiente e constantes em maiúsculas com palavras separadas por
  sublinhados;
- Declare constantes e variáveis exportadas com `readonly` ou `declare -r`;
- Nomeie uma variável pelo conceito que ela representa em vez de por sua representação.


# Variáveis e Uso de Aspas

## Localidade

- Declare toda variável utilizada dentro de uma função com `local`;
- Minimize o estado global mutável, e passe dados por argumentos e saída em vez de por variáveis
  globais;
- Declare uma variável e atribua uma substituição de comando a ela em instruções separadas, de
  modo que o estado de saída do comando não seja mascarado.

## Uso de Aspas e Expansão

- Coloque entre aspas toda expansão de variável, como em `"$var"` e `"${array[@]}"`, a menos que
  a divisão em palavras seja explicitamente pretendida;
- Expanda os parâmetros posicionais como `"$@"` em vez de como `$*` ou `$@`;
- Prefira a expansão de parâmetros a um comando externo para a manipulação simples de cadeias;
- Envolva em chaves uma referência de variável como `"${name}"` onde o texto ao redor seria de
  outro modo ambíguo.


# Comandos e Controle de Fluxo

## Substituição de Comandos e Aritmética

- Substitua comandos com `$(...)` em vez de com crases;
- Realize aritmética de inteiros com `(( ... ))` e `$(( ... ))`;
- Não realize aritmética de ponto flutuante em Bash, e delegue-a a `awk` ou a outra ferramenta
  adequada;
- Prefira uma cadeia de ferramentas padrão a um laço escrito à mão, e não analise a saída de
  `ls`.

## Condicionais e Laços

- Utilize `[[ ... ]]` para testes em vez de `[ ... ]` ou `test`;
- Compare cadeias com `==` e `!=` dentro de `[[ ... ]]`, e compare inteiros com operadores como
  `-eq` e `-lt` ou dentro de `(( ... ))`;
- Utilize `case` para ramificação de múltiplas vias sobre um único valor;
- Leia a entrada linha a linha com `while IFS= read -r line`, de modo que barras invertidas e
  espaços em branco iniciais sejam preservados.


# Funções e Tratamento de Erros

## Funções

- Atribua a cada função um único propósito e um escopo limitado;
- Retorne resultados na saída padrão, reporte diagnósticos no erro padrão e sinalize o desfecho
  por meio do estado de saída;
- Componha pequenos scripts e funções de propósito único por meio de pipes para realizar tarefas
  maiores.

## Tratamento de Erros

- Escreva mensagens de erro no erro padrão, prefixadas com o nome do programa;
- Encerre com um estado não nulo significativo em caso de falha;
- Verifique o estado de saída de um comando que possa falhar, e aborte com uma mensagem clara em
  vez de continuar em um estado inconsistente;
- Registre ações de limpeza com `trap` na condição `EXIT`, e crie arquivos temporários com
  `mktemp`.


# Documentação

## Cabeçalhos

- Documente no topo de cada arquivo o seu propósito e o modo como ele é invocado, incluindo os
  argumentos esperados;
- Preceda cada função com um comentário que declare o seu propósito, os seus argumentos, a sua
  saída e o seu estado de retorno.

## Comentários

- Comente qualquer construção concisa ou não óbvia, como uma expressão regular complexa, um
  programa `sed` ou `awk` ou uma expansão de parâmetros intrincada;
- Marque o código que requer atenção posterior com um comentário `TODO` em maiúsculas que
  identifique a pessoa responsável, e escreva datas na forma `YYYY-MM-DD`;
- Reescreva o código ruim em vez de explicá-lo com um comentário.


# Sinais de Alerta

- As construções listadas abaixo são sinais de alerta que devem motivar revisão, embora a
  maioria delas também ocorra em situações legítimas;
- Revise qualquer uso de `eval`;
- Revise qualquer expansão de variável sem aspas que ocorra em um contexto de palavra;
- Revise qualquer análise da saída de `ls`;
- Revise qualquer `cd` cujo estado de saída não seja verificado;
- Revise qualquer uso de crases para substituição de comandos;
- Revise qualquer uso de `[ ... ]` ou `test` onde `[[ ... ]]` serviria.
