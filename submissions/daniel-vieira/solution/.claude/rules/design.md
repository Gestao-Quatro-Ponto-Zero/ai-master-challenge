---
subject: Documentação do design system principal
author: dcvr@
---


# Escopo da documentação

- Este arquivo é dedicado aos princípios, políticas e processos associados ao nosso sistema de
  design, visando assegurar consistência entre decks, apresentações, sites, aplicações e outros
  projetos que requeiram estilo e contexto institucionais;
- Os arquivos de estilo e de configuração (por exemplo, CSS, JSON, YAML), localizados em
  '../assets/', são a fonte canônica de verdade para quaisquer especificações ou valores que
  definam. Evite listar atributos, especificações e definições de propriedade neste documento.
- Os arquivos de estilo e de configuração devem seguir as melhores práticas atuais do setor para
  sintaxe, formatação e compatibilidade de plataforma, conforme os padrões listados na seção
  'Referências externas'.


# Processo orientado a exemplos para definir e revisar padrões de estilo

- Toda definição ou revisão de um padrão de estilo deve ser precedida pela produção de um
  artefato de demonstração, ilustrando a aplicação da nova definição, apresentando alternativas
  e (quando aplicável) comparando-a com a definição atual;
- Os artefatos de demonstração devem estar em conformidade com o próprio sistema de design e ser
  produzidos em HTML/CSS autônomo, incluindo suas próprias dependências (fontes, estilos,
  paletas, etc.) e nomeados no formato 'example-{topic}-{theme}.html';
- Tais artefatos devem ser preservados para referência futura, arquivados em
  '../assets/examples/'.


# Diretrizes de autoria para regras de design e tokens de estilo

- Os princípios, políticas e processos residem neste 'design.md'. Os valores concretos,
  atributos e definições de propriedade residem em arquivos de tokens e de configuração (CSS,
  JSON, YAML);
- Antes de adicionar qualquer cláusula, regra ou token, verifique se a sua ausência quebraria ou
  comprometeria a coerência do sistema de design. Caso contrário, a cláusula não deve ser
  adicionada;
- Os comentários em arquivos de tokens devem limitar-se a anotações diretas e factuais: o papel
  de um valor, a sua origem no sistema de design ou uma dica de uso concisa. Evite explicações
  extensas, justificativas ou exemplos além do essencial para interpretar o valor;
- Não inclua justificativas narrativas, anotações de sessão de trabalho, históricos de decisão
  ou debates de implementação em 'design.md' ou em arquivos de tokens. Tal material pertence ao
  worklog;
- Não reafirme em um arquivo um princípio ou especificação que já reside em outro. O arquivo que
  detém a definição canônica é a única fonte de verdade.


# Princípios de design e comunicação

## Escopo de linguagem e glossário

- O nosso público é composto por tomadores de decisão envolvidos na venda consultiva de
  educação, desenvolvimento pessoal e serviços de consultoria.
- Comunicamo-nos primariamente em português, utilizando linguagem formal e direta, fazendo uso
  criterioso e apropriado do glossário técnico relevante para o nosso campo.

## Estilo de fala e escrita

- A nossa voz é sóbria, franca, objetiva, concisa e precisa, refletindo essas características em
  todos os elementos de comunicação produzidos;
- O nosso discurso, tanto escrito quanto falado, é guiado por linguagem objetiva e orientado à
  apresentação de fatos e informações verificáveis, sempre apoiados por dados e outras
  referências.

## Atributos estéticos e visuais

- A nossa abordagem estética e visual é discreta, minimalista, aplicando esses princípios a
  todas as produções gráficas e digitais;
- A forma e o design devem ser utilizados como elementos de apoio à clareza, à usabilidade e à
  utilidade do conteúdo em recursos de comunicação e marketing.

## Antipadrões - Design e comunicação em geral

- A nossa comunicação não é ruidosa nem movida por hype ou FOMO. Não produzimos nem endossamos
  informações não verificáveis, não apoiadas por dados ou devidamente referenciadas;
- Os nossos materiais impressos e digitais não são estética ou visualmente exagerados e não
  utilizam cores vibrantes ou brilhantes. Não priorizamos a forma sobre o conteúdo e a
  usabilidade;
- Efeitos decorativos de profundidade, incluindo 'box-shadow', glow e outer-glow, não são
  utilizados. A elevação de superfície é obtida por meio de fundos em camadas combinados com
  bordas de fio de cabelo.


# Padrões de tipografia

## Tipografia padrão

- A 'família IBM Plex' é a nossa fonte tipográfica canônica. Todos os elementos de texto devem
  adotar uma das combinações válidas de peso, tamanho e estilo dessa família, nas variações
  Sans, Serif e Mono;
- As fontes devem ser servidas localmente por padrão. O uso da CDN do Google é permitido apenas
  quando a hospedagem local for impraticável, e requer divulgação em conformidade com a LGPD na
  política de privacidade.

## Hierarquia recomendada para uso de fontes

- IBM Plex Serif: wordmark, títulos principais, itens de índice, textos de destaque e citações;
- IBM Plex Sans: conteúdo textual em geral, títulos de subseção, de slides e de tabelas;
- IBM Plex Mono: código-fonte e dados de configuração, rótulos, notas de rodapé, enumerações e
  dados numéricos e científicos em geral;
- As cláusulas desta seção são uma recomendação e podem ser adaptadas para clareza, usabilidade
  e para manter o apelo estético do contexto.

## Formatação especial

- Os sinais numéricos são explícitos em números operacionais: valores positivos usam um '+'
  inicial quando a discriminação de sinal for relevante; valores negativos usam o menos Unicode
  '−' (U+2212), não um hífen '-'. Dados numéricos em colunas alinhadas usam algarismos tabulares
  ('font-variant-numeric: tabular-nums').

## Antipadrões - Tipografia

- Não utilize emojis e símbolos semelhantes em nossas construções de texto.


# Padrões cromáticos e de tema

## Paletas de cores

- A paleta de cores canônica é a rampa de cinzas do IBM Carbon Design System (Gray 10 até
  Gray 100);
- A aplicação de outras paletas de cores deve limitar-se a elementos específicos (por exemplo,
  rótulos, botões, avisos), com o objetivo de melhorar a clareza e a usabilidade do conteúdo,
  evitando combinações de cores saturadas.

## Temas

- O tema escuro canônico, a ser utilizado primariamente, é o 'IBM Carbon Design System -
  Gray 100';
- O tema claro alternativo é o 'IBM Carbon Design System - Gray 10'.


# Principais ativos de construção

- Leia @../assets/tokens/tokens.css para obter as principais definições de tokens de estilo;
- Leia @../assets/tokens/dark-theme-tokens.css para obter as definições de estilo do tema
  escuro;
- Leia @../assets/tokens/light-theme-tokens.css para obter as definições de estilo do tema
  claro.


# Referências externas

- [IBM Carbon Design System (The dark mode/approach)](https://carbondesignsystem.com/);
- [IBM Plex font family (Sans/Serif/Mono)](https://www.ibm.com/plex/);
- [MDN Web Docs](https://developer.mozilla.org/);
- [Google HTML/CSS style guide](https://google.github.io/styleguide/htmlcssguide.html);
- [Baseline](https://web.dev/baseline).
