---
subject: Padrões de codificação Common Lisp
author: dcvr@
---


# Escopo

- Este documento define os padrões de codificação Common Lisp adotados na Polya Technologies,
  abrangendo formatação, nomenclatura, documentação, formas idiomáticas e o projeto de
  abstrações;
- Estes padrões aplicam-se a todo o código-fonte Common Lisp mantido pela equipe;
- Estes padrões são independentes de qualquer editor, IDE, host de compilação ou backend de
  armazenamento e dizem respeito apenas à linguagem Common Lisp e às suas abstrações;
- A palavra-chave "deve" denota um requisito obrigatório, a palavra-chave "recomenda-se" denota
  uma recomendação forte que admite exceções justificadas e a palavra-chave "pode" denota uma
  escolha discricionária que deve permanecer internamente consistente.


# Princípios Gerais

## Comunicação

- O código-fonte é lido simultaneamente por leitores humanos, pelo compilador e pelas
  ferramentas de desenvolvimento, e o leitor humano é o público primário;
- O código é escrito de modo que qualquer passagem curta possa ser compreendida isoladamente,
  sem que o sistema inteiro seja mantido em memória;
- A complexidade é empacotada em abstrações nomeadas em vez de espalhada por variáveis globais e
  dependências implícitas.

## Máximas do Bom Estilo

- Seja explícito: forneça valores de argumento que de outro modo seriam consultados, e declare a
  informação de tipo conhecida tanto para o leitor quanto para o compilador;
- Seja específico: use a construção mais precisa que os dados e a intenção justifiquem, e não
  mais geral do que isso;
- Seja conciso: minimize o código escrito, e trate um teste repetido ou um resultado repetido
  como evidência de que existe uma forma mais simples;
- Seja consistente: no caso neutro escolha uma de duas construções equivalentes, de modo que o
  uso da outra sinalize algo incomum;
- Seja prestativo: organize a documentação em torno das tarefas que o leitor deve realizar, e
  não em torno do que o código porventura oferece;
- Seja convencional: espelhe os recursos existentes da linguagem e obedeça às convenções de
  nomenclatura, de modo que a intenção seja reconhecida sem leitura minuciosa;
- Construa abstrações em um nível que a próxima camada de código possa usar diretamente.


# Projeto e Abstração

## Decomposição

- Inicie o projeto pelas estruturas de dados, e derive delas a decomposição do código;
- Expresse cada função e módulo em uma única frase, visto que um nome que não pode ser enunciado
  de forma simples indica uma decomposição falha;
- Estratifique projetos complexos, de modo que as construções erguidas em cada nível sirvam de
  primitivas para o nível acima;
- Adie as decisões sobre a representação pelo maior tempo possível, e minimize as dependências
  de cada parte.

## Abstração de Dados

- Escreva o código em termos dos tipos de dados do problema, e não dos tipos da representação
  subjacente;
- Introduza tipos de registro com `defstruct` e tipos nomeados com `deftype`;
- Não use `defclass`, `defgeneric`, `defmethod` ou herança para modelar dados;
- Declare os slots de estrutura como somente leitura sempre que o valor não precise mudar;
- Forneça acessores para dados compostos, e não espalhe pelo código o acesso estrutural direto,
  tal como `(cadar x)`;
- Forneça informação de tipo por meio de opções `:type` de slot e de declarações, tanto para
  documentação quanto para o compilador.

## Abstração Funcional

- Dê a cada função um propósito único e específico, um nome significativo, uma estrutura
  simples, uma interface mínima e o menor número possível de dependências;
- Prefira uma função de utilidade geral a uma estreitamente vinculada a um único ponto de
  chamada;
- Fatore uma expressão repetida em uma função local com `flet` ou `labels` em vez de duplicá-la;
- Verifique o comportamento pretendido traduzindo o código concluído de volta para prosa e
  comparando-o com a especificação original.

## Abstração de Controle

- Expresse os padrões comuns de controle com as funções de ordem superior padrão para busca,
  ordenação, filtragem, mapeamento, redução e contagem, em vez de com recursão explícita;
- Substitua uma travessia manual de uma sequência pela função apropriada, tal como `some`,
  `every`, `find` ou `remove`;
- Evite o fluxo de controle não local em código comum, e use `catch` e `throw` apenas como
  subprimitivas dentro de macros de nível mais alto;
- Reserve a recursão para estruturas de dados genuinamente recursivas, e não confie nela como
  substituta da iteração, porque a eliminação de chamada de cauda não é garantida pelo padrão.

## Abstração Sintática

- Defina um macro apenas quando uma função não puder obter o efeito, como quando a avaliação de
  argumentos deve ser controlada ou uma nova sintaxe deve ser introduzida;
- Faça um macro expandir para uma chamada a uma função comum que realiza o trabalho, visto que a
  função é mais fácil de testar, de corrigir e de chamar diretamente;
- Avalie cada forma de argumento uma única vez e na ordem da esquerda para a direita, e não
  realize trabalho no momento da expansão do macro;
- Gere nomes novos com `gensym` para que os nomes introduzidos por um macro não capturem os
  nomes no chamador.


# Formatação

## Largura de Linha e Recuo

- Limite uma linha de código-fonte a 96 colunas;
- Recue o código com o recuo convencional de Common Lisp, aplicado de forma consistente por toda
  a base de código;
- Não recue manualmente de um modo que um indentador automático convencional não reproduziria;
- Recue o corpo de uma forma de vinculação em duas colunas e os dados de vinculação que precedem
  o corpo em quatro colunas, e alinhe os argumentos de chamada com o primeiro argumento ou,
  quando o primeiro argumento inicia uma nova linha, com o operador;
- Não use caracteres de tabulação para o recuo.

## Espaço em Branco e Parênteses

- Não insira espaço em branco horizontal imediatamente dentro de parênteses ou em torno de
  símbolos;
- Mantenha os parênteses de fechamento consecutivos na mesma linha, e nunca coloque um parêntese
  de fechamento sozinho em uma linha;
- Separe as formas sucessivas com um único espaço, e não alinhe as formas verticalmente ao longo
  de linhas consecutivas, exceto para enfatizar uma simetria significativa;
- Alinhe as formas aninhadas de modo consistente onde elas ocupam mais de uma linha.

## Espaçamento Vertical

- Separe as formas de nível superior com uma linha em branco;
- As linhas em branco podem ser omitidas entre formas de definição curtas e estreitamente
  relacionadas do mesmo tipo, tal como um grupo de definições de constantes;
- Divida uma função longa em funções menores em vez de separar as suas partes com linhas em
  branco.

## Estrutura de Arquivo

- Inicie cada arquivo de código-fonte com uma breve descrição do seu conteúdo, seguida da forma
  `(in-package #:name)` e de quaisquer declarações específicas do arquivo;
- Não coloque avisos de autoria ou de direitos autorais em arquivos de código-fonte individuais,
  porque essa informação pertence ao controle de versão;
- Defina sistemas com ASDF, e gerencie as dependências fixadas locais ao projeto com qlot sobre
  a distribuição Quicklisp em vez de por carregamento de arquivos ad hoc;
- Confine os caminhos absolutos a um único local, e assegure que o sistema compile de forma
  limpa a partir do zero.


# Nomenclatura

## Caixa e Separação de Palavras

- Escreva os símbolos em caixa baixa, porque Common Lisp converte a caixa e, portanto, as
  distinções por caixa não são confiáveis;
- Separe as palavras dentro de um símbolo com hifens, e não use "/" ou "." em seu lugar sem uma
  razão documentada;
- Evite abreviações em favor de palavras completas, e use apenas abreviações comuns ou de
  domínio, aplicadas de forma consistente;
- Onde existirem grafias corretas alternativas, escolha a grafia mais curta.

## Nomenclatura pela Intenção

- Nomeie uma variável pelo conceito que ela representa, e não pela sua representação subjacente;
- Não embuta o nome de um tipo agregado, tal como `list`, `array` ou `hash-table`, no nome de
  uma variável, exceto em código genérico sobre esse tipo;
- Refira-se a um valor pelo mesmo nome ao longo das funções pelas quais ele passa.

## Afixos Convencionais

- Nomeie as constantes globais com um "+" inicial e final, como em `+pi+`;
- Nomeie as variáveis especiais globais com um "*" inicial e final, como em `*default-stream*`;
- Termine o nome de uma função ou variável de predicado em "P", usando "P" quando o restante do
  nome for uma palavra e "-P" quando comportar várias;
- Não repita o nome de um pacote como prefixo dentro dos nomes dos seus próprios símbolos.

## Pacotes

- Um pacote define um espaço de nomes e uma interface, e apenas os símbolos destinados ao uso
  externo são exportados;
- Não referencie os símbolos internos de um pacote a partir de outro pacote, e não use o
  qualificador "::" em código de produção;
- Não sombreie os símbolos do pacote Common Lisp.


# Documentação

## Cadeias de Documentação

- Forneça uma cadeia de documentação para toda função, tipo, variável e macro exportados;
- Descreva o contrato na cadeia de documentação, a saber, o que a operação faz, o que os seus
  argumentos significam, o que ela retorna e quais condições pode sinalizar, em vez de como ela
  funciona internamente;
- Escreva os nomes dos símbolos, tais como os nomes de argumentos, em caixa alta dentro das
  cadeias de documentação.

## Comentários

- Use um comentário para explicar o que não é evidente a partir do código, tal como motivação e
  justificativa, e não reafirme o que o código diz claramente;
- Introduza um comentário com o número convencional de ponto e vírgula: quatro para um cabeçalho
  de arquivo ou de seção, três para um grupo de nível superior, dois para um comentário entre
  linhas dentro de uma forma e um para uma observação em linha;
- Coloque um único espaço após os ponto e vírgula, e inicie um comentário de frase completa com
  maiúscula e termine-o com um ponto final;
- Marque o código que requer atenção posterior com um comentário `TODO` em caixa alta que
  identifique a pessoa responsável, e escreva as datas na forma `YYYY-MM-DD`;
- Enuncie o propósito de qualquer forma concisa ou não óbvia, tal como uma expressão regular, em
  um comentário acompanhante;
- Reescreva o código ruim em vez de explicá-lo com um comentário.


# Estilo Funcional e Estado

## Efeitos Colaterais

- Prefira um estilo majoritariamente funcional, e evite efeitos colaterais desnecessários;
- Revincule as variáveis locais em vez de mutá-las, e defina os slots de estrutura na construção
  em vez de atribuí-los posteriormente;
- Torne as estruturas de dados tão imutáveis quanto o problema permita.

## Variáveis Especiais

- Use as variáveis especiais com parcimônia, porque cada uma constitui estado oculto que
  complica a leitura, o teste e a refatoração;
- Reserve uma variável especial para um contexto singleton que o código circundante trata como
  corrente, tal como a conexão corrente;
- Deixe uma variável especial sem uma vinculação global de nível superior, e vincule-a dentro de
  cada thread que a requeira.

## Atribuição

- Minimize o número de atribuições, em conformidade com um estilo majoritariamente funcional;
- Prefira `setf` a `setq`, e siga a convenção já em uso dentro de um dado pacote.


# Formas Condicionais e de Iteração

## Formas Condicionais

- Use a forma condicional mais específica que se aplique: `when` ou `unless` para um único ramo,
  `if` para dois ramos e `cond` para vários;
- Use `and` e `or` onde o valor for booleano e nenhum efeito colateral estiver envolvido, e não
  use `progn` dentro de uma cláusula `if`;
- Prefira `ecase` e `etypecase` a `case` e `typecase`, porque estas sinalizam um erro em um
  valor não correspondido, e não use `ccase` ou `ctypecase`;
- Não use formas citadas como chaves de `case`, porque um símbolo citado corresponde ao símbolo
  `QUOTE`;
- Corresponda os símbolos `T` e `NIL` com as chaves `((t) ...)` e `((nil) ...)`, e introduza a
  cláusula de fluxo residual com `otherwise`.

## Iteração e Recursão

- Use `dolist` e `dotimes` para a iteração simples, e reserve `loop` para os casos que requeiram
  as suas facilidades de vinculação, acumulação ou terminação;
- Não atribua a variável de iteração de uma forma `dotimes` dentro do corpo;
- Prefira a iteração ou as funções de mapeamento à recursão para a travessia de sequências;
- Documente explicitamente qualquer dependência da eliminação de chamada de cauda, porque o
  padrão não a exige.

## Igualdade e Comparação

- Use `eql` para a identidade, e não use `eq` para comparar números ou caracteres;
- Use `=` para a comparação numérica, `char=` para caracteres e `string=` para cadeias, e use as
  variantes insensíveis à caixa onde a caixa deva ser ignorada;
- Use `zerop`, `plusp` e `minusp` no lugar da comparação contra zero;
- Não aplique a comparação exata a números de ponto flutuante, e represente valores monetários
  com racionais em vez de valores de ponto flutuante.


# Definições e Parâmetros

## Constantes

- Use `defconstant` apenas para números, caracteres e símbolos, incluindo booleanos e palavras-
  chave;
- Defina uma constante de qualquer outro tipo com `alexandria:define-constant` e um `:test`
  apropriado, ou com `defparameter` onde o valor possa mudar;
- Mantenha a convenção de nomenclatura de "+" inicial e final para tais valores, para documentar
  a intenção de constância.

## Parâmetros de Função

- Use os parâmetros `&optional` e `&key` de forma criteriosa, evite os parâmetros `&aux` e evite
  `&allow-other-keys`, que enfraquece o contrato;
- Não combine os parâmetros `&optional` e `&key` em uma única lista lambda;
- Onde os parâmetros `&optional` e `&key` forem combinados, não dê aos parâmetros `&optional`
  valores padrão não-`NIL`;
- Declare os parâmetros de função não utilizados com `(declare (ignore ...))`;
- Evite o aninhamento excessivo de formas de vinculação, e divida uma função profundamente
  aninhada em funções menores.


# Condições e Asserções

## Asserções e Verificações de Tipo

- Use `assert` apenas para detectar defeitos internos, a saber, invariantes cuja violação indica
  que o próprio software está quebrado;
- Não trate a entrada externa inválida como uma violação de asserção, mas valide-a e reporte um
  erro genuíno;
- Prefira `check-type` a `(declare (type ...))` para validar as entradas de função;
- Use asserções e verificações de tipo liberalmente, e permita que apenas os caminhos críticos
  de desempenho e os auxiliares internos as omitam.

## Sinalização e Tratamento

- Sinalize `error` com um tipo de condição explícito em vez de com uma cadeia simples;
- Enuncie no contrato de uma função que ela sinaliza uma condição;
- Trate condições específicas em vez de todas as condições indiscriminadamente, e prefira um
  `handler-case` estreito à supressão de todo erro;
- Não chame `signal` diretamente em código de aplicação, e substitua `catch` e `throw` pela
  facilidade de restart onde um tratador deva testar um contexto estabelecido.

## Mensagens de Erro

- Escreva uma mensagem de erro como uma frase completa que começa com letra maiúscula e termina
  com um ponto final;
- Não inclua um prefixo tal como "Error:" ou uma solicitação inicial de linha nova, porque o
  sistema os fornece;
- Descreva a própria situação em vez das suas consequências, e não pressuponha qualquer
  interface de depuração específica;
- Dê à mensagem detalhe suficiente para distingui-la de outros erros e para apoiar o diagnóstico
  posterior.


# Armadilhas Comuns

## Referências a Funções e Lambda

- Referencie uma função passada como argumento com `#'`, como em `(mapcar #'f xs)`, em vez de
  com um símbolo citado, a menos que a redefinição dinâmica seja especificamente pretendida;
- Aplique as grafias `(lambda ...)` e `#'(lambda ...)` de forma consistente, e prefira a mais
  curta `(lambda ...)`.

## Caminhos de Arquivo

- Construa os caminhos de arquivo com utilitários de biblioteca em vez de montá-los à mão,
  porque os componentes de caminho carregam comportamento não óbvio, tal como marcadores curinga
  e não especificados e caixa dependente do host.

## Sinais de Alerta

- As construções listadas abaixo são sinais de alerta que devem motivar revisão, embora a
  maioria delas também ocorra em situações legítimas;
- Revise qualquer uso de `eval`;
- Revise qualquer uso de `gentemp`;
- Revise qualquer uso de `append`, que frequentemente oculta comportamento quadrático;
- Revise a ausência de um parâmetro `&environment` em um macro que chama `setf` ou
  `macroexpand`;
- Revise qualquer tratador de condição para `type-error`, incluindo qualquer uso de
  `ignore-errors`;
- Revise qualquer uso de um acessor `c...r` além da família `cadr`.
