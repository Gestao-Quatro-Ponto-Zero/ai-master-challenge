# Política: IA decide / IA sugere / humano decide

## Premissa de transferência

A política tem duas camadas, porque os dois datasets não se encaixam: o DS1 é de suporte ao cliente e o DS2 é de TI interna.

1. **Roteamento** (para qual fila vai): medido no DS2, com as 8 categorias e as faixas da F3.
2. **Ação** (o que pode ser feito sem humano): definida pelos 5 tipos do DS1. É **regra de negócio declarada**, não resultado de modelo, porque o texto do DS1 é inutilizável (100% das descrições têm marcador de template não preenchido; `solution/outputs/f1_ds1_auditoria.json`, T2).

## Regra por categoria (fixada antes de ver o resultado)

Para cada categoria prevista, calcula-se o limite inferior (LI) de Wilson 95% da precisão dentro da faixa global "IA decide" (`p_max` ≥ 0,74). As metas são as da F3: 1 − *e*_inferior = 0,9680 e 1 − *e*_superior = 0,9545, com *e*_Q2 = 3,82%.

| Condição | Política da categoria |
|---|---|
| LI ≥ 0,9680 | **IA decide** |
| 0,9545 ≤ LI < 0,9680 | **IA sugere**, mesmo com `p_max` ≥ 0,74 |
| LI < 0,9545 | **humano decide** |

A política da categoria é um **teto**: pode rebaixar a faixa global de um ticket, mas nunca promovê-la.

Fontes: `solution/outputs/f4_politica_por_categoria.csv` e `f4_politica.json`, gerados por `solution/f4_politica.py`, a partir de `f3_probs_holdout_grupo.csv` e `f3_faixas.json`.

## Tabela única

Os exemplos foram sorteados com seed 42. Os ids estão em `solution/outputs/f4_exemplos_ids.csv` e `f4_exemplos_ds1.csv`. Os trechos do DS2 têm no máximo 120 caracteres, e o texto vem pré-processado (minúsculas, sem pontuação).

| Tipo | Camada | Política | Motivo (número e origem) | Exemplo real |
|---|---|---|---|---|
| Access | roteamento | **IA decide** | LI 0,9755 ≥ 0,9680 (precisão 98,59% em 852 tickets na faixa); F1 0,872 | id 2906, rótulo Access, p_max 0,944: "re card leaver re card leaver update stare si ca se december card leaver hello badge firma" |
| Purchase | roteamento | **IA decide** | LI 0,9815 ≥ 0,9680 (precisão 99,49% em 390); F1 0,917 | id 791, rótulo Purchase, p_max 0,997: "new purchase po hardware retrieval re purchase po hi mistake please correction purchased please log allocation please lo" |
| HR Support | roteamento | **IA sugere** | LI 0,9610: abaixo de 0,9680, acima de 0,9545 (precisão 97,12% em 1.387); principal confusão: Hardware previsto como HR Support (124) | id 917, rótulo HR Support, p_max 0,906: "leaver centre leaver form leave date location centre hello leaver form has filled by name leaving date location centre a" |
| Internal Project | roteamento | **IA sugere** | LI 0,9556 (precisão 98,24% em 227; n pequeno alarga o IC) | id 17539, rótulo Internal Project, p_max 0,957: "new project code oracle fusion pm hello please create code per creation form attached please make available both budgeti" |
| Miscellaneous | roteamento | **IA sugere** | LI 0,9659 (precisão 98,03% em 610) | id 33791, rótulo Miscellaneous, p_max 0,936: "role change ad wednesday july pm change role name hello starting july switched roles wondering also change officer where" |
| Storage | roteamento | **IA sugere** | LI 0,9649 (precisão 98,48% em 329) | id 17550, rótulo Storage, p_max 0,989: "wants to access resources pm wants resources accept decline" |
| Hardware | roteamento | **humano decide** | LI 0,9478 < 0,9545 (precisão 95,89% em 1.556); recebe HR Support (162) e Miscellaneous (155) | id 19701, rótulo Hardware, p_max 0,792: "db backups needed for career deploy to production march pm backups needed deploy production hello please log database ba" |
| Administrative rights | roteamento | **humano decide** | LI 0,9046 < 0,9545 (precisão 95,76% em 118); F1 0,715; 6 de 6 "original errado" na revisão (`f3_h2.json`) | id 46431, rótulo Administrative rights, p_max 0,399: "outlook errors minute edited se enough disk space ne si ref la ticket pare si data va sa pot line direct" |
| Refund request | ação (DS1) | **humano decide, sempre** | **Regra de negócio**, não resultado medido: movimenta dinheiro e é difícil de reverter. 1.752 tickets no DS1 (`f1_ds1_auditoria.json`, T8) | Ticket 1586: Refund request, assunto "Data loss", Phone, Medium |
| Cancellation request | ação (DS1) | **humano decide, sempre** | **Regra de negócio**, não resultado medido: movimenta dinheiro e é difícil de reverter. 1.695 tickets no DS1 (T8) | Ticket 4604: Cancellation request, assunto "Product compatibility", Email, Low |
| Billing inquiry | ação (DS1) | IA roteia (camada 1), **humano responde** | Não há resposta automática ao cliente nesta proposta. 1.634 tickets no DS1 (T8) | Ticket 7070: Billing inquiry, assunto "Network problem", Chat, Low |
| Technical issue | ação (DS1) | IA roteia (camada 1), **humano responde** | Idem. 1.747 tickets no DS1 (T8) | Ticket 8386: Technical issue, assunto "Product setup", Social media, Medium |
| Product inquiry | ação (DS1) | IA roteia (camada 1), **humano responde** | Idem. 1.641 tickets no DS1 (T8) | Ticket 3472: Product inquiry, assunto "Software bug", Phone, Low |

Os assuntos do DS1 não combinam com o tipo (ex.: Billing inquiry com assunto "Network problem"). Isso é coerente com o dado sintético da F1 e reforça que a camada de ação é regra declarada.

## Exemplos da faixa humana (sorteados, seed 42)

**3 tickets da faixa global humana** (`p_max` < 0,66):
- id 24744, rótulo Miscellaneous, previsto Miscellaneous, p_max 0,556: "add a new service tier friday december pm add tier hello please additional tier called tier same configuration tier late"
- id 2103, rótulo HR Support, previsto Miscellaneous, p_max 0,603: "new facing facing hello please add facing action needed due workstations replacement myself other details needed please "
- id 6007, rótulo Access, previsto Access, p_max 0,547: "access client access request project client hello please client members key hayes hayes these appropriate client user th"

**3 tickets marcados `ambíguo` na revisão adjudicada** (`process-log/revisao_rotulos_adjudicada.csv`):
- id 38735, rótulo Access, revisor Hardware, previsto Access, p_max 0,899: "license is not activated license activated hello shows cross red here what recovery assistant says link message above ar"
- id 28128, rótulo Hardware, revisor Miscellaneous, previsto Hardware, p_max 0,816: "request for display port october pm display port hi requested display adaptor thank information"
- id 5827, rótulo HR Support, revisor Miscellaneous, previsto HR Support, p_max 0,996: "former intern new starter hello please fill thank"

O modelo pode ter `p_max` alto num ticket ambíguo (0,996). É por isso que a faixa não substitui a regra por categoria nem a correção do atendente.

## Cobertura total esperada (holdout por grupo, depois da regra por categoria)

**IA decide 12,98%** (precisão 98,87%, IC 98,12–99,33) / **IA sugere 31,41%** (precisão 96,67%, IC 95,97–97,26) / **humano decide 55,61%** (precisão do modelo 75,30%). Fonte: `solution/outputs/f4_politica.json`, `cobertura_apos_politica`.

Sem a regra por categoria, a faixa global seria de 57,17% / 8,65% / 34,18% (`f3_faixas.json`). A diferença vem de Hardware (3.182 tickets previstos) e de Administrative rights irem para humano decide.

**Sensibilidade pós-hoc, não usada na decisão:** se as categorias abaixo de 1 − *e*_superior fossem para "IA sugere" em vez de "humano decide", a divisão seria IA decide 12,98% / IA sugere 52,84% (precisão 95,55%) / humano 34,18% (`solution/outputs/f4_sensibilidade.csv`).

## Economia (cenário A)

Com a cobertura da faixa IA decide da regra registrada (12,98%), a economia é de **R$ 6.815,62/ano** na base (3 min, R$ 35/h). Na grade de 3 × 3 premissas, vai de R$ 3.245,53 a R$ 12.982,13/ano (`solution/outputs/f4_economia.csv`). A faixa IA sugere **não está quantificada**: o tempo de confirmação do atendente deve ser medido no piloto.

A economia em `f3_faixas.json` (cobertura de 57,17%) foi **substituída por `f4_economia.csv`**.

## O que "IA sugere" significa na tela do atendente

A tela mostra a categoria mais provável e a segunda, com as probabilidades, e um botão para **confirmar** ou **corrigir**. A correção é registrada no log e entra no conjunto de avaliação.
