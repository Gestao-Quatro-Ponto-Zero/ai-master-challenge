---
id: P8V4
project: LeadScorer
subject: Allowlist por literal exato na varredura de segredos da transcricao
author: dcvr@
status: accepted
created: 2026-07-19
updated: 2026-07-19
---


# Contexto (por que a decisao e necessaria)

O ADR J7K4 estabeleceu a varredura de segredos fail-closed de 'scripts/export-session'. A propria
propriedade fail-closed recusa a exportacao de uma transcricao que contenha cadeias com forma de
segredo comprovadamente benignas, a saber, chaves de exemplo publicas documentadas e as cadeias
sinteticas usadas nas fixtures de teste. Concretamente, a transcricao da sessao H3V6-1, que
construiu o proprio scanner, ficou sem versao por esse motivo, e qualquer sessao-meta que discuta
deteccao de segredos incorre no mesmo bloqueio.

Os scanners de segredo consagrados (gitleaks, detect-secrets) suportam allowlists de literais
benignos exatamente por esse motivo, sem enfraquecer a deteccao de segredos reais. Era necessario
decidir o mecanismo de isencao sob o principio de seguranca desde a concepcao: um allowlist e, por
natureza, um furo no gate fail-closed, de modo que o furo deve ser o minimo possivel, explicito,
auditavel e incapaz de suprimir um segredo real.


# Decisao (o que foi decidido)

- A isencao e por IGUALDADE EXATA do texto casado, aplicada APOS a deteccao. A varredura continua
  casando; um achado so e limpo quando o seu texto casado e exatamente uma entrada do arranjo
  'ALLOWLIST'. Qualquer casamento nao isentado ainda aborta, de modo que o gate fail-closed e
  preservado e nenhum override automatico e introduzido;
- A comparacao e por igualdade de cadeia, nunca por substring. Para que uma entrada jamais suprima
  um segredo real que apenas a contenha como prefixo, as regras de comprimento fixo usam
  quantificador aberto ('{n,}'), de modo que 'grep -o' emita o token maximal: um token maior gera
  um casamento distinto da entrada e nao e isentado;
- So constam do allowlist chaves de exemplo publicas documentadas (por exemplo, a chave de exemplo
  da AWS 'AKIAIOSFODNN7EXAMPLE') e as cadeias sinteticas das fixtures de teste. Uma entrada e
  listada na forma exata em que a sua regra a captura; como a regra 'labeled-secret-assignment'
  captura rotulo mais operador mais valor, o mesmo valor benigno pode exigir uma entrada nua e uma
  entrada rotulada ('token=...');
- Os segredos dos testes fail-closed sao montados em tempo de execucao a partir de fragmentos, de
  modo que nenhum literal com forma de segredo nao isentado fique versionado nas fixtures nem
  apareca na transcricao. Isso preserva a exportabilidade das sessoes-meta que sigam a mesma
  disciplina.


# Alternativas consideradas (o que mais foi ponderado)

- Sentinela ou stopword ao estilo gitleaks, isentando um casamento que contenha um marcador
  benigno curado (por exemplo, 'EXAMPLE'): mais ergonomico, porem de furo mais largo (uma chave
  real que contivesse o marcador como substring seria suprimida) e insuficiente aqui, dado que o
  literal sintetico OpenAI ja gravado na transcricao de H3V6 nao contem marcador e nao seria
  isentado, o que forcava o literal exato de qualquer modo;
- Extracao do valor-nucleo, isto e, remover o rotulo e o operador antes de comparar, unindo
  as formas nua e rotulada do mesmo valor benigno em uma unica entrada: reduziria a verbosidade
  da lista, mas acrescenta logica de extracao cuja seguranca o revisor teria de validar; num
  gate de seguranca, a lista explicita com igualdade exata e mais auditavel;
- Delegar a um scanner externo com allowlist proprio (gitleaks): rejeitado ja em J7K4 pelas mesmas
  razoes de dependencia, sem mudanca aqui;
- Supressao ampla ou desativacao de regras: rejeitada por enfraquecer a deteccao.


# Consequencias (o que resulta da decisao)

- Favoravel: furo minimo, explicito e auditavel no gate; fail-closed preservado, pois qualquer
  casamento nao isentado ainda aborta; transcricao de H3V6-1 provisionada; sessoes-meta futuras
  exportaveis por meio de segredos de teste montados em runtime; zero dependencias novas;
- Desfavoravel: o mesmo valor benigno capturado por regras distintas exige uma entrada por
  span, o que introduz verbosidade na lista; aceito em favor da auditabilidade. O allowlist
  acopla-se a cadeias sinteticas especificas das fixtures, aceitavel por serem constantes
  benignas;
- Manutencao: introduzir um novo literal benigno de formato coberto exige acrescentar ao
  arranjo a forma exata do seu casamento; a disciplina de montar segredos de teste em runtime
  deve ser seguida para que as transcricoes permanecam exportaveis;
- Esta decisao estende J7K4, que permanece 'accepted'; o gate, a higienizacao deny-by-default
  e a segunda-barreira por regex seguem inalterados.


# Relações

- supersedes:
- superseded-by:
- related-tasks: K2R7
