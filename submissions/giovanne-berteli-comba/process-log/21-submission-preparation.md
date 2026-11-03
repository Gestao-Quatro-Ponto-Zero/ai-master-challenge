# Preparação final e resultado observado — P01

O candidato pediu avanço à última etapa e forneceu nome/LinkedIn. O agente
conferiu o briefing, template, regras do repositório e diff contra a main oficial
atual. A branch estava limpa no início, com M07 já commitado pelo candidato.

## Ensaio encontrado

Havia um ensaio completo no banco local, identificado como Operador (declarado),
com assistido → manual. O agente não executou essas decisões. Extraiu um snapshot
consistente somente leitura e publicou resultado, decisões e trilhas sem nomes,
textos ou banco original. O inventário completo de tentativas foi preservado.

Assistido: 52,723028 s, 7/8 concordâncias, nenhuma correção/falha de sugestão.
Manual: 41,582005 s, 1/8 concordâncias. A diferença de −11,141023 s foi mantida;
não houve redução de tempo. A qualidade desigual e as limitações de treino,
ordem/experiência/amostra pequena impedem inferir produtividade equivalente ou
economia de produção. Não há observação independente da identidade/atenção do
participante nem adjudicação dos rótulos. [Relatório](../docs/workflow-rehearsal.md).

## Revisão e preparação

Nome/LinkedIn e estado H01 foram atualizados nos documentos atuais; evidências
históricas M07 continuam descrevendo o estado de sua própria captura. O README
expõe o resultado desfavorável em tempo. O material final inclui título/corpo do
PR, checklist, teste de setup preparado e 93 testes de software aprovados.
Auditoria das 7.175 decisões salvas passou sem novo ajuste/predição. Um comando
usou Python do sistema e foi recusado pelo guard de ambiente; a repetição na
.venv bloqueada passou, sem alterar os resultados congelados.

Consulta pública ao GitHub identificou o pai oficial do fork e nenhum PR desta
branch no momento da consulta. Fetch da main confirmou a referência já conhecida;
o diff é exclusivo da submissão. Uma primeira checagem de arquivos usou pathspec
da raiz a partir da subpasta e retornou zero arquivos; foi corrigida para a raiz:
190 arquivos versionados, 1.795.198 bytes, nenhum raw/modelo/banco/ambiente ou
arquivo acima de 5 MB. O conjunto será conferido novamente após os novos exports.

Captura26: 15 mensagens novas de cinco turnos, hasMore=true; inclui conclusão M07,
roteiro do instrutor, commit, pedido P01 e identidade informada. Atualizações
posteriores, decisão de publicação e final atual ficam fora do corte. O agente
preparou os arquivos; commit, push e PR ainda não foram realizados nesta etapa.

Os CSVs exportados preservam BOM/CRLF e seus hashes. Uma regra local de
.gitattributes permite CRLF na checagem de whitespace desses dois exports, sem
normalizar ou alterar bytes. O diff final passou no git diff --check.

Após revisar o material concreto, o candidato escolheu fazer o commit e o envio
pessoalmente. O agente deixou os arquivos preparados, apenas intent-to-add nos
novos arquivos, sem conteúdo staged. Essa decisão veio após a captura26; sua
extração com ID e o final atual ficam pendentes da próxima captura.
