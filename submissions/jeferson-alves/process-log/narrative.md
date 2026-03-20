# Process Log

## Objetivo

Construir uma ferramenta funcional para um vendedor priorizar deals do pipeline usando os dados reais do challenge, com score explicavel e setup simples.

## Linha do tempo resumida

1. Levantei os requisitos obrigatorios do challenge: solucao funcional, documentacao minima e process log.
2. Confirmei a estrutura de submissao exigida em `submissions/seu-nome/`, sem alterar outros arquivos do repositorio.
3. Inspecionei os CSVs e identifiquei os principais pontos do dado:
   - 8.800 oportunidades no total
   - 2.089 deals abertos
   - win rate historico de aproximadamente 63,2% nos deals fechados
   - lacunas de conta em parte do pipeline
   - inconsistencia de nomenclatura entre `GTXPro` e `GTX Pro`
4. Escolhi uma solucao em Streamlit por ser a forma mais curta de entregar software utilizavel por negocio.
5. Modelei um score com pesos claros, usando historico de ganho e sinais operacionais em vez de um modelo opaco.
6. Criei a interface com filtros, ranking, explicacao por deal e visao agregada por time.
7. Preparei a pasta de submissao de forma autocontida, incluindo os CSVs em `solution/data/`.

## Como usei IA em cada etapa

- Usei IA para resumir o challenge e as regras de submissao.
- Usei IA para explorar rapidamente o schema dos CSVs e levantar anomalias do dado.
- Usei IA para acelerar a implementacao do app, da pipeline de joins e do mecanismo de score.
- Usei IA para iterar na documentacao e manter a submissao aderente ao template oficial.

## Iterações relevantes

### Iteracao 1: descobrir o formato da entrega

A IA ajudou a consolidar challenge, template e guia de submissao, reduzindo o risco de entregar algo fora do formato.

### Iteracao 2: explorar os dados reais

A exploracao mostrou rapidamente que o dado tinha um problema de normalizacao de produto e varias contas faltantes. Isso mudou a implementacao do join e a logica de confianca do score.

### Iteracao 3: definir o score

A primeira tentacao seria usar um modelo de classificacao. Eu optei por nao seguir esse caminho de imediato porque o desafio pedia algo funcional e explicavel. Mantive um baseline heuristico, com uso de historico real e pesos transparentes.

### Iteracao 4: transformar analise em ferramenta

Em vez de parar em uma tabela, a IA ajudou a converter a logica em uma aplicacao navegavel com filtros, ranking, resumo executivo e detalhe de cada oportunidade.

## Erros e correções

- Erro: o ambiente local nao tinha `pandas` instalado.
  Correcao: instalei as dependencias minimas do projeto antes de continuar a analise.

- Erro: nomes de produto inconsistentes entre arquivos.
  Correcao: criei uma chave de produto normalizada removendo espacos e caracteres nao alfanumericos.

- Erro potencial: deixar o valor financeiro dominar o ranking.
  Correcao: reduzi o peso do valor e aumentei o peso de sinais mais ligados a chance real de fechar.

## Julgamentos humanos que fizeram diferença

- Priorizei utilidade operacional em vez de sofisticacao estatistica.
- Tratei explainability como requisito central da experiencia.
- Preferi uma entrega autocontida com os CSVs dentro da submissao para facilitar avaliacao.

## Resultado final

Uma aplicacao Streamlit que ordena o pipeline aberto, mostra o motivo do score, sugere a proxima acao e agrega a carteira por vendedor, manager e regiao.
