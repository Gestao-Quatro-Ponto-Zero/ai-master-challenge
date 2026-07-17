# Relatório de qualidade dos dados

## Resultado executivo

O arquivo é estruturalmente utilizável: 52.214 linhas, 27 colunas, chaves únicas, datas parseáveis, métricas positivas e metadados de patrocínio coerentes. Porém, há fortes sinais de dados sintéticos e limitações severas de validade externa. Resultados podem demonstrar método e associações internas, mas não devem ser apresentados como estimativas confiáveis de uma operação real sem validação externa.

## Perfil observado

- Plataformas: Bilibili 10.598; YouTube 10.495; Instagram 10.423; RedNote 10.402; TikTok 10.296.
- Conteúdo: vídeo 31.500; imagem 10.303; mixed 5.213; texto 5.198.
- Categoria: beauty 21.023; lifestyle 20.761; tech 10.430.
- Patrocinado: 22.314; orgânico: 29.900.
- Creators distintos: 5.000.
- Missing: `hashtags` 8.743; `comments_text` 8.688; demais colunas sem vazios.
- Duplicidades: zero em `id` e `content_id`.
- Datas inválidas, métricas negativas, zeros em métricas, interação maior que views e inconsistência de patrocínio: zero.

## Distribuições críticas

| Campo | min | Q1 | mediana | Q3 | max |
|---|---:|---:|---:|---:|---:|
| views | 9.676 | 10.032 | 10.100 | 10.168 | 10.551 |
| likes | 1.354 | 1.484 | 1.510 | 1.536 | 1.668 |
| shares | 227 | 288 | 300 | 312 | 380 |
| comments | 140 | 190 | 200 | 210 | 258 |
| followers | 1.013 | 250.811 | 498.488 | 749.797 | 999.998 |
| content length | 10 | 95 | 174 | 360 | 599 |

## Problemas e decisões

| ID | Severidade | Achado | Tratamento |
|---|---|---|---|
| DQ-001 | MAJOR | Todas as 5.000 `creator_id` possuem múltiplos `creator_name` | ignorar nome; usar somente ID e registrar limitação |
| DQ-007 | MAJOR | `follower_count` varia dentro do mesmo `creator_id` quase tanto quanto na população | tratar followers/faixa como atributo do post; não como cadastro estável do creator |
| DQ-002 | MAJOR | Performance concentrada em banda estreita e sem posts zerados | declarar provável geração sintética; evitar extrapolação/survivorship claims |
| DQ-003 | MAJOR | Sem custos/receita | proibir ROI; tratar patrocínio como associação/eficiência |
| DQ-004 | MAJOR | Timezone ausente | preservar horário local sem inferir UTC |
| DQ-005 | MINOR | Hashtags/comentários vazios | preservar ausência; usar indicador/contagem, sem imputação textual |
| DQ-006 | MAJOR | Audiência é uma categoria agregada por post | evitar inferência individual/falácia ecológica |

## Gate DQ

`PASS` em 16 de julho de 2026. O pipeline produziu 52.214 linhas e 34 colunas; o teste de dados passou e o SHA-256 processado foi reconciliado como `410E2D8101CA5206BAFB2825DE4417F33AB5922EA85B2DE2ACB0C5FC0EE649F0`. A validade externa permanece como limitação obrigatória downstream, não como falha mecânica do arquivo.

Durante o teste foi detectada e corrigida uma dependência indevida de locale: decimais inicialmente saíam com vírgula em `pt-BR`. O pipeline agora serializa taxas com cultura invariável e ponto decimal.
