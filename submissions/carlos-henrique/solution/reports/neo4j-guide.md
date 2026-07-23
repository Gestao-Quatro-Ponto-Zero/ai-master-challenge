# Guia Neo4j do JourneyGraph

## Pré-requisitos

Neo4j 5.x e acesso local ao diretório de import. O gate principal não exige Neo4j, Docker, credenciais ou rede.

## Constraints

Execute `constraints.cypher` antes da carga para garantir chaves únicas.

## Indexes

Execute `indexes.cypher` após constraints para acelerar escopo, estabilidade, taxonomia e evento.

## Import

Copie os CSVs derivados para o diretório de import e adapte o comando documentado em `import.cypher`. EventInstance usa amostra determinística de 250 jornadas; os GraphML preservam o grafo completo.

## Consultas

`example_queries.cypher` contém dez consultas equivalentes às investigações NetworkX.

## Limitações

Nenhum servidor externo foi iniciado. CSVs não contêm account_id bruto, source event id ou PII. Centralidade, padrões e MRR permanecem descritivos.

## Reprodução local

Execute `python solution/scripts/run_journey_graph.py`; valide hashes e, opcionalmente, importe os CSVs em uma base Neo4j descartável.
