# Submissao - Jeferson Alves - Challenge 003

## Sobre mim

- Nome: Jeferson da Silva Alves
- LinkedIn: https://www.linkedin.com/in/jefersonalves21/
- Challenge escolhido: Challenge 003 - Lead Scorer

## Executive Summary

Construí uma aplicacao em Streamlit para priorizacao comercial usando os CSVs reais do desafio. A ferramenta transforma o pipeline aberto em uma lista acionavel de deals, com score de 0 a 100, justificativa legivel e proxima acao sugerida. Em vez de depender de um modelo opaco, a solucao usa heuristicas explicaveis combinadas com historico real de conversao por vendedor, conta, produto, manager e regiao. A principal recomendacao e usar o app como camada operacional de priorizacao semanal, especialmente para filtrar deals em Engaging com alto score e alta receita esperada.

## Solucao

Entreguei um app funcional em Streamlit dentro de `solution/`.

### Abordagem

Comecei validando os requisitos do challenge e a estrutura obrigatoria de submissao. Em seguida, inspecionei os quatro CSVs reais para entender o schema, a distribuicao dos estagios e os problemas de qualidade do dado. A partir dessa leitura, montei uma logica de score explicavel baseada em historico de ganho e sinais operacionais do pipeline, evitando depender de ML pesado sem necessidade.

Decisoes principais:

- Solucao escolhida: aplicacao web em Streamlit, porque atende o pedido de algo que o vendedor possa abrir e usar sem barreira tecnica.
- Priorizacao: score entre 0 e 100 com pesos transparentes.
- Explainability: cada deal mostra os principais motivos do score e uma acao sugerida.
- Usabilidade: filtros por regiao, manager, vendedor e etapa; ranking de deals; visao resumida por time.
- Confiabilidade: normalizei a chave de produto para corrigir o mismatch `GTXPro` no pipeline versus `GTX Pro` no catalogo.

### Resultados / Findings

O app gera uma fila priorizada para os 2.089 deals abertos do pipeline.

Principais achados do dado:

- O historico de deals fechados tem win rate de aproximadamente 63,2%.
- A maior parte do pipeline aberto esta em `Engaging`, que naturalmente merece foco maior que `Prospecting`.
- Existe variacao material de conversao entre vendedores, contas e managers, entao priorizar apenas por valor do deal seria uma decisao fraca.
- O dado tem lacunas relevantes, como contas ausentes em parte do pipeline e divergencia de nomenclatura de produto, o que exigiu normalizacao antes do join.

Funcionalidades entregues:

- Ranking de deals por score
- Filtros por regiao, manager, vendedor e etapa
- Visualizacoes para score, receita esperada e concentracao de oportunidades
- Explicacao textual por deal
- Breakdown do score por componente
- Proxima acao sugerida para cada oportunidade
- Visao agregada por vendedor e manager

### Recomendações

1. Colocar o app como ritual semanal de planejamento comercial para cada vendedor.
2. Usar os deals `Hot` e `Focus` como carteira ativa do ciclo, com revisao dos deals envelhecidos.
3. Corrigir a qualidade do CRM em duas frentes: preenchimento de conta e padronizacao de produto.
4. Na proxima iteracao, registrar atividades comerciais e ultimo contato para enriquecer o score com sinal comportamental real.

### Limitações

- O dataset nao traz historico de atividades, emails, calls ou meetings, entao o score nao mede intensidade de execucao comercial.
- `Prospecting` tem menos contexto temporal do que `Engaging`, porque parte dos registros nao tem `engage_date` preenchida.
- O valor esperado de deals abertos usa preco de catalogo como aproximacao quando nao ha valor negociado.
- A logica atual e heuristica e explicavel; com mais tempo, eu compararia esse baseline com um modelo supervisionado calibrado.

## Setup

### Estrutura

- `solution/app.py`: interface Streamlit
- `solution/lead_scoring.py`: carga, joins, tratamento e calculo do score
- `solution/data/`: copia autocontida dos CSVs reais

### Como rodar

1. Entre em `submissions/jeferson-alves/solution`
2. Instale as dependencias com `pip install -r requirements.txt`
3. Rode `streamlit run app.py`
4. Abra a URL local informada pelo Streamlit, normalmente `http://localhost:8501`

## Process Log - Como usei IA

Este bloco e obrigatorio. Sem ele, a submissao e desclassificada.

### Ferramentas usadas

| Ferramenta | Como usei |
| --- | --- |
| GitHub Copilot (GPT-5.4) no VS Code | Estruturei a submissao, inspecionei o challenge, gerei o app e refinei a logica de score |
| Python runtime local | Validei distribuicoes do dataset, taxas de conversao e comportamento das features |

### Workflow

1. Li o README do challenge, o template de submissao, o guia e o CONTRIBUTING para garantir aderencia ao formato.
2. Explorei os CSVs reais para entender volumes, estagios, nulos e relacoes entre as tabelas.
3. Identifiquei um problema de dado relevante: `GTXPro` no pipeline contra `GTX Pro` na tabela de produtos.
4. Defini uma estrategia de scoring explicavel, com pesos claros e uso de historico real de conversao.
5. Implementei o app em Streamlit com filtros, ranking, detalhes do deal e visao do time.
6. Validei localmente as dependencias e a subida da aplicacao.

### Onde a IA errou e como corrigi

- A primeira exploracao de dados falhou porque o ambiente Python ainda nao tinha `pandas` instalado. Corrigi configurando as dependencias do workspace.
- A leitura inicial do dataset mostrava o join de produtos como se fosse direto, mas os valores reais nao batiam por causa de `GTXPro` versus `GTX Pro`. Corrigi com uma chave normalizada para evitar score incorreto.
- O score poderia cair na armadilha de virar "ordenacao por valor". Corrigi isso mantendo o valor com peso baixo e deixando etapa, historico e frescor dominarem a priorizacao.

### O que eu adicionei que a IA sozinha nao faria

O principal julgamento foi tratar o problema como ferramenta operacional, nao como demo de ML. Em vez de buscar o modelo mais sofisticado, foquei em uma experiencia que responde a pergunta real do vendedor: "qual deal merece meu tempo hoje e por que?". Tambem escolhi explicabilidade como requisito de produto, nao so como detalhe tecnico.

## Evidências

- Narrativa do processo em `process-log/narrative.md`
- Historico de arquivos e commits locais da implementacao
- Codigo funcional dentro de `solution/`

Submissao enviada em: 2026-03-20
