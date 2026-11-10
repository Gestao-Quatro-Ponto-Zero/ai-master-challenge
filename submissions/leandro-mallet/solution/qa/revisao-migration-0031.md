# Revisão e aplicação — migration 0031 (funil com 5 etapas)

**Veredito: pode rodar. Aplicada em 10/11/2026, sem erro.** Nenhum achado de segurança. Nenhum dado gravado pelos testes.

Ordem O-33. Arquivo `solution/db/migrations/0031_funil_cinco_etapas.sql`, sha256 `51da2c34000c571838b54a1e0fb27d7aa00b6cbf1a6d3c985bd4337515cc795d`: igual ao informado, conferido na cópia e de novo na hora de aplicar. Registrado em `supabase_migrations.schema_migrations` com o mesmo hash. As 0026–0030 do repositório são idênticas às aplicadas.

## Revisão

| Ponto | Resultado |
|---|---|
| Nada destrutivo | ✅ o único `drop` remove a regra `acao_registros_acao_check` e a recria na mesma transação, só acrescentando `'contato'`; nenhum dado é tocado. Também entra a regra `acao_registros_contato_completo_chk` (contato exige tipo e comentário) |
| Linhas existentes na regra nova | ✅ o nome da regra no banco confere; as 9 linhas de `acao_registros` (4 `prioridade_feita`, 4 `prioridade_pulada`, 1 `liguei`) passam nas duas regras novas (0 falhas, conferido antes de aplicar) |
| Função nova `acao_registrar_contato` | ✅ começa por `system_iniciar_contexto`; exige tipo ativo que conta como contato e comentário de 1 a 280 sem HTML; só deal aberto; sem execução para public, anon e authenticated (conferido no banco: anon e authenticated não executam; service_role e system_carga executam) |
| Contexto, limites, auditoria | ✅ nenhuma função de segurança foi tocada; o registro passa pela auditoria e pelo gatilho de último contato da 0023 |
| `core_linha_do_tempo` | ✅ mesma assinatura e mesmo retorno (`data_negocio, momento, tipo, descricao, autor, desfeito, referencia`), então mantém as permissões |
| `core_rotulo_estagio` | ✅ mesma assinatura; Won → "Fechado" |
| Moeda "R$" na linha do tempo | ✅ não é erro: a 0015 escrevia "US$", e a troca segue a decisão 44 do process log (mostrar em reais, com os mesmos valores, sem conversão), que o app já usa |

## Validação (Postgres em memória, sem conexão)

| Validador | Resultado |
|---|---|
| `validar_tudo.mjs --com-dataset` (0001–0031) | ✅ catálogo ok: 61 FKs RESTRICT, 76 funções, 87 gatilhos, 106 índices |
| `validar_tudo.mjs` (uso) | ✅ 135 linhas ok, 0 falha |
| `validar_0030.mjs` | ✅ 21 linhas ok, 0 falha |
| `validar_0031.mjs` | ✅ 16 linhas ok, 0 falha |

## Depois de aplicar

| Medida | Antes | Depois |
|---|---|---|
| Funções com prefixo | 75 | **76** |
| Gatilhos / índices / FKs | 87 / 106 / 61 | 87 / 106 / 61 |
| Deals | 8.801 | **8.801** |
| Notas da execução 7 (ativa) | 2.089 | **2.089** (a execução 5 continua com 2.089) |
| `core_rotulo_estagio('Won')` | Ganho | **Fechado** |
| `acao_registros` | 9 | 9 |
| Auditoria | max id 9227 | 9227 (nenhuma linha nova) |

## Teste da função nova

| Teste | Resultado |
|---|---|
| Lead de teste 88UBTBQ8, chamada real como service_role (Anna) | recusado, GS422: "Só é possível registrar atendimento em deal aberto." O 88UBTBQ8 está encerrado (Perdido) desde os testes anteriores, então não havia como registrar atendimento nele. **Nada gravado** |
| Teste positivo, em transação desfeita, no lead aberto 10ALJD82 (Prospecting da Anna, sem contato) | aceito: registro `contato`, tipo `ligacao`, comentário sem os espaços das pontas; `ultimo_contato_em` passou de vazio para 31/12/2017 (o lead continua Prospecting e passa a aparecer como Atendimento); linha do tempo: "Atendimento: Ligação — …". Depois do rollback: `ultimo_contato_em` vazio de novo e nenhum registro novo |

Não ficou nada gravado no banco por estes testes.
