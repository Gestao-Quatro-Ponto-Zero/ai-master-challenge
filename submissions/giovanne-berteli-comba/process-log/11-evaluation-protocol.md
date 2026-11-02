# Protocolo de avaliação — 02/11/2026

## Pedido e escolhas

Após o commit `f699801` da S01, o usuário pediu “continue”. Codex executou V00,
antes de implementar/treinar: [protocolo](../knowledge/evaluation-protocol.md),
[configuração](../data/evaluation-protocol.json), conjuntos, critérios e ambiente.
As escolhas são premissas do agente dentro do trabalho autorizado, não aprovação
humana de custos de negócio nem comprovação de qualidade.

A separação por linha aleatória foi preterida pelo risco de textos semelhantes
atravessarem conjuntos. Foi escolhida busca exata de Jaccard de tokens com filtros
de prefixo/tamanho, em vez de busca aproximada que poderia perder pares. Componentes
transitivos ficam inteiros; conflitos de rótulo em textos apenas semelhantes não
são corrigidos ou descartados. Identidades por entidade continuam indisponíveis.

O orçamento foi fixado em quatro ajustes futuros: majoritária, Naive Bayes e duas
regressões logísticas, com TF-IDF aprendido só no treino. Critérios macro F1 e de
erro/cobertura, 42 combinações de gate/referência, custos ilustrativos e desempates
ficaram explícitos antes de resultados. Não haverá reajuste com validação nem
afrouxamento de metas se nenhum candidato/configuração for elegível. O fallback
continua revisão humana. O teste final só avaliará artefatos congelados em V01.

## Execução e validação

- 33.485 registros de treino, 7.177 de validação e 7.175 de teste; oito classes
  presentes nos três conjuntos, sem quarentena nesta versão.
- 44.683 grupos, 837 não unitários, maior com 740 registros. Foram encontrados
  31.542 pares similares e nenhum par verificado atravessa conjuntos. A garantia
  é para a regra declarada, não independência semântica ou por pessoa.
- Membership e manifesto reproduzidos byte a byte em pasta limpa a partir de
  código/configuração/CSV verificado. Isso não foi novo download nem treino.
- O teste de Jaccard foi comparado a busca exaustiva com fixtures aleatórias e
  limites exatos. Componentes/conflitos, seleção, Wilson e custos também foram
  testados. A tolerância de 1e-12 evita rejeição indevida no limite de diferença
  macro F1 por representação de ponto flutuante. Os 37 testes passaram.
- Instalado ambiente isolado Python 3.12.3, scikit-learn 1.9.1 e Streamlit 1.66.1,
  com transitivas e pip fixados. Imports, construções sem fit, SQLite em memória,
  igualdade exata com lock e `pip check` passaram. Sem UI, banco de aplicação ou
  modelo ajustado. Instalação testada apenas em Linux x86_64, sem hashes de wheels.

O sistema não tinha pip/ensurepip. Foi criado `.venv --without-pip`; pip 26.2.2 do
runtime Python fornecido no ambiente serviu apenas de bootstrap com `--python`
apontando para o venv. Download PyPI foi autorizado pelo mecanismo de aprovação;
nenhum runtime compartilhado ou Python global foi alterado. Os comandos de setup
e as limitações estão no [relatório](../docs/evaluation-protocol.md).

A inspeção heurística somente no treino encontrou palavras como resolved/fixed;
essas palavras podem descrever pedidos ou resultados. Não se inferiu cronologia,
não se apagaram tokens como suposta correção validada. Document é processado e
o benchmark permanece retrospectivo. A fonte completa já foi auditada e lida para
agrupamento; reserva do teste significa ausência de previsões/métricas/escolhas
com esse conjunto, não alegação de segredo ou de nunca ter lido seus textos.

## Evidência e estado

[Reprodução/integridade](../docs/review-evidence/evaluation-checks.json),
[ambiente](../docs/review-evidence/evaluation-environment.json),
[testes](../docs/review-evidence/evaluation-tests.txt) e
[recibo](../docs/review-evidence/evaluation-current.json) identificam o escopo.
Os donos operacionais, tabela F02, plano e handoff foram atualizados. Resultados
D01/A01 foram regenerados e os recibos revalidados após as mudanças documentais.
Nenhuma métrica de IA, acerto de anomalia, revisão humana real ou economia foi medida.

V00 concluída; I01 implementará a solução e a seleção treino/validação. Dados
brutos, membership, venv, caches e futuros artefatos locais permanecem ignorados.
Arquivos públicos novos foram preparados para revisão no diff, sem commit/push.

## Conversa

A [captura 15](chat-exports/15-evaluation-protocol-chat.md) preserva nove mensagens
novas de quatro turnos retornados, após deduplicação, incluindo final da S01 e
troca de nome de commit. `hasMore=true` indica histórico anterior fora da página.
Mensagens posteriores à captura e a resposta final V00 ficam para o próximo
export; não foram reconstruídas. Ferramentas/instruções/raciocínio privado não
integram o arquivo.
