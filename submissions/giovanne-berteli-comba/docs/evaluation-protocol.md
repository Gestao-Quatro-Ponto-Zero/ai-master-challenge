# V00 — Protocolo de avaliação e ambiente

O protocolo foi definido antes de treinar classificadores. Foram preparados os
conjuntos IT e o ambiente isolado; **não há acurácia, F1 ou modelo escolhido nesta
etapa**. O próximo passo é I01, implementação da triagem assistida. O
[contrato técnico](../knowledge/evaluation-protocol.md) explica a execução; o
[JSON versionado](../data/evaluation-protocol.json) é a autoridade dos parâmetros.

## Separação dos dados

| Conjunto | Registros | Uso permitido |
| --- | ---: | --- |
| Treino | 33.485 | Ajustar vocabulário/modelos; exemplos de desenvolvimento/interface |
| Validação | 7.177 | Escolher candidato, limiar e referência de anomalias |
| Teste final | 7.175 | Avaliar a versão congelada em V01 |
| Quarentena | 0 | Componentes inválidos ou com conflito exato, se existirem |

Todas as oito classes aparecem nos três conjuntos. A separação mantém inteiros
44.683 grupos; 837 têm mais de um registro, e o maior tem 740. A busca encontrou
31.542 pares com similaridade de Jaccard de tokens ≥0,85. Nenhum par verificado
atravessa os conjuntos. Pares não são tickets adicionais, e grupos com rótulos
diferentes não provam erro de anotação. O
[manifesto](../data/evaluation-manifest.json) registra contagens por classe, regras
e hashes; a membership detalhada fica local e pode ser regenerada.

A regra inclui conexões transitivas e ignora ordem/repetição dos tokens. É uma
proteção contra a similaridade declarada; não comprova independência semântica ou
por pessoa. O arquivo completo já foi auditado, e o agrupamento leu seus textos;
“reservado” significa não usar previsões, desempenho ou exemplos do teste para
desenvolver/escolher a solução. Não significa um arquivo secreto jamais lido.

Document já vem processado, sem comprovação de disponibilidade na abertura do
ticket. A inspeção heurística de palavras de possível resultado usa apenas treino
e está nas evidências. Essas palavras também podem descrever solicitações; sua
presença/ausência não valida a cronologia. O benchmark será retrospectivo, sem
alegar desempenho prospectivo na operação de atendimento.

## Escolhas congeladas

- Quatro ajustes no máximo: classe majoritária, TF-IDF/Naive Bayes e duas regressões
  logísticas (C=0,5 e 2), sempre ajustados só em treino, sem reajuste com validação.
- Para ser elegível, a regressão precisa macro F1 ≥0,70, ganho ≥0,10 sobre a classe
  majoritária e perda de no máximo 0,01 frente ao baseline de texto, na validação.
- São 42 combinações de limiar de score e cauda da referência. Uma sugestão padrão
  precisa passar por todas as regras de S01. A escolha exige pelo menos 200 casos
  padrão, cobertura ≥10%, limite inferior de Wilson 95% da acurácia ≥90% e até 15%
  dos casos pontuados com possível anomalia. Referência insuficiente vai para revisão.
- Entre configurações viáveis, minimizar custo ilustrativo de revisão/erro. Os
  pesos são premissas adimensionais do agente, sem validação de negócio. A análise
  de sensibilidade usa validação; não altera a escolha primária.
- Sem candidato elegível ou configuração viável, registrar a limitação e manter
  encaminhamento à revisão. Nenhum limiar permissivo substitui um critério reprovado.

As metas são critérios prévios, não resultados nem garantia de produção. Usar a
mesma validação para seleção e referências não gera estimativa independente;
essa avaliação fica para o teste final. Todas as sugestões exigem confirmação
humana. Nenhuma referência/limiar será ajustado com o teste final. Se seus
resultados motivarem mudanças, a nova versão terá exposição declarada, sem alegar
outro teste limpo com os mesmos registros.

## Ambiente e reprodução

Execute na pasta da submissão, com Python 3.12 e suporte a venv/pip:

```bash
python3 -m venv .venv
.venv/bin/python -m pip --isolated install --no-cache-dir --only-binary=:all: -r requirements.lock
.venv/bin/python -m pip --isolated --no-cache-dir check
.venv/bin/python -I solution/check_evaluation_environment.py
python3 -I solution/prepare_evaluation.py
python3 -I scripts/check_evaluation_preparation.py
python3 -I -m unittest discover -s tests -v
python3 -I scripts/check_foundation.py --receipt docs/review-evidence/evaluation-current.json
```

[requirements.in](../requirements.in) registra as duas dependências diretas;
[requirements.lock](../requirements.lock) fixa o conjunto completo, incluindo pip.
O ambiente testado é Linux x86_64, Python 3.12.3, scikit-learn 1.9.1, Streamlit 1.66.1
e SQLite 3.45.1. Não há promessa de compatibilidade do lock em outros sistemas.
Os relatórios registram a versão do Python; para comparação byte a byte, use 3.12.3.
Os comandos D01/A01 continuam usando apenas a biblioteca padrão.

Neste host o Python de sistema não tinha pip/ensurepip. Foi criado venv com
`--without-pip` e usado pip 26.2.2 de outro Python apenas para instalar no destino
com `--python .venv/bin/python`; o runtime compartilhado não foi modificado.
Em um host equivalente, instale suporte a venv/pip ou use esse bootstrap com um
Python que já tenha pip. Não misture pacotes globais com o ambiente isolado.
O lock fixa versões, mas não contém hashes de wheels; downloads ainda dependem
da integridade/disponibilidade da fonte de pacotes.

## Verificações executadas

Os **37 testes passaram**, incluindo comparação do agrupamento com busca exaustiva,
limites de similaridade, componentes transitivos, conflitos exatos, escolha de
modelo/gate e custos. São testes de software com fixtures, sem métricas de IA.
As importações, os quatro candidatos ainda sem ajuste, a correspondência exata
do lock e o rollback SQLite em memória passaram. `pip check` não encontrou conflitos.
A preparação foi reproduzida em diretório temporário, copiando somente código,
configuração e CSV verificado; manifesto e membership ficaram idênticos byte a byte.
Isso não foi um segundo download nem uma execução do futuro protótipo.

Evidências: [testes](review-evidence/evaluation-tests.txt),
[preparação/reprodução](review-evidence/evaluation-checks.json),
[ambiente](review-evidence/evaluation-environment.json) e
[recibo de entradas](review-evidence/evaluation-current.json).
Dados brutos, membership local, venv, modelos e registros de revisão permanecem
ignorados pelo Git. I01 ainda deve implementar os fluxos e selecionar usando
treino/validação; V01 medirá a qualidade final e os fluxos de falha.

Fontes primárias para a estratégia:
[separação de dados e seleção](https://scikit-learn.org/stable/modules/cross_validation.html),
[filtragem exata de conjuntos, seção 2](https://www.vldb.org/pvldb/vol9/p636-mann.pdf),
[instalação Streamlit](https://docs.streamlit.io/get-started/installation/command-line).
