# Especificação das telas: versões anteriores

> Registro. Estes trechos saíram de `app/ESPEC-TELAS.md` porque não valem mais. O que vale hoje está em [../app/ESPEC-TELAS.md](../app/ESPEC-TELAS.md).

## Entrada com 3 cartões (substituída pela tela de login)

- A raiz `/` sempre mostra a entrada, mesmo com perfil escolhido antes: bloco de destaque no azul do deck com "G4 Sight" e "CRM do time comercial com a prioridade do dia dentro do pipeline.", e a escolha do papel em 3 cartões grandes (Vendedor, Manager, Admin). Vendedor e manager escolhem o nome; admin entra direto. Sem login nem senha (decisão 16).
- Com perfil na sessão, a entrada oferece também "Continuar como <nome>".
- O perfil fica num cookie **de sessão do navegador** (`g4_perfil`, sem validade): fechou o navegador, escolhe de novo.
- Rota interna sem perfil continua mandando para a entrada com `?voltar=` e, depois da escolha, volta para lá (só caminhos internos do app).

## Relógio parado e proposta inicial do relógio (substituídos pelo relógio que anda)

**[P6]** O dataset termina em 31/12/2017, mas as ações no CRM acontecem hoje. Proposta: enquanto o CRM estiver em modo demonstração, "hoje" é a data de referência (`config_parametros.data_referencia` = 31/12/2017).
- Idade, dias sem contato e filtros de data contam a partir dela.
- Contato, comentário e deal registrados agora ganham duas datas: a **data do negócio** (a data de referência, usada nas contas) e o momento real (usado na auditoria).
- Sem isso, um contato registrado hoje apareceria "8 anos depois" de todos os outros dados.
- **Atualizado (decisão 48, migration 0034): o relógio anda.** A data de negócio avança 1 dia por dia real, ancorada em 10/11/2026 (America/Sao_Paulo) = 31/12/2017: 17/11/2026 = 07/01/2018 (o 1º domingo), e assim por diante. As âncoras ficam em `config_parametros` (`data_ancora_real`, `data_ancora_negocio`); `system_data_negocio()` e o app (`src/lib/relogio.ts`) fazem a mesma conta. Dias no pipeline, faixas e linha do tempo andam juntos. As telas não mostram a data dos dados.
- **Rotina diária do score:** cron da Vercel todo dia às 03:00 de Brasília (`/api/rotina/diaria`, protegida por `CRON_SECRET`). Numa transação com o papel de carga (`g4_rotina` → `system_carga`): no domingo de negócio, o job semanal (FIT da janela de 3 meses, redistribuição, padrões de conta); todo dia, o diário (repasse por mudança de faixa sem contato e HEAT e nota novos em execução nova). Lead novo já recebe o dono na criação, pelo banco (`core_rotear_lead`). Cada repasse roda num savepoint: se o banco recusar um, só ele é desfeito e conta como recusado. Um dia de negócio roda uma vez só (registro em `system_eventos`); erro desfaz tudo e registra a falha. Teste manual: `POST /api/rotina/rodar-agora` com o mesmo segredo; com `?forcar=1`, roda mesmo com o dia já rodado e registra `rotina_forcada`. O cálculo do score fica em `src/lib/score/`, ligado à rotina em `src/server/motor/instalado.ts`.

## Pipeline com duas colunas (substituído pelas cinco etapas)

```
┌ topo: G4 Sight · Pipeline | Leads · Anna Snelling, vendedora · Trocar perfil ───────────────────────┐
│ [ Filtrar: ex. "nota alta sem contato há 15 dias"                 ]   Ordenar: Nota ▾   [Abrir o próximo deal] │
│ Entendi assim:  (Nota ≥ 70 ×)  (Sem contato há 15+ dias ×)                     Limpar filtros        │
├──────────────────────────────────────────┬──────────────────────────────────────────┤
│ Prospecção · 18 deals · R$ 24.300       │ Em negociação · 94 deals · R$ 151.200   │
│ ┌ cartão ┐                              │ ┌ cartão ┐                               │
│ … 50 por coluna · Mostrar mais          │ … 50 por coluna · Mostrar mais           │
└──────────────────────────────────────────┴──────────────────────────────────────────┘
   ao arrastar um cartão aparecem à direita duas áreas: [Ganho] [Perdido]
```

- **Atualizado (O-31, decisão do Leandro): cinco colunas, uma por etapa:** **Novo lead**, **Atendimento**, **Em negociação**, **Fechado** e **Perdido**. O desenho acima é o de antes.
  - O banco continua com 4 estágios. Novo lead e Atendimento são o `Prospecting` sem e com contato registrado (`core_deals.ultimo_contato_em`); a separação é feita no app.
  - O primeiro contato registrado (Liguei, Requalifiquei, ✓ com tipo que conta como contato, ou o registro de atendimento) leva o lead para Atendimento sozinho.
  - O cabeçalho de cada coluna mostra a quantidade e a soma do valor (abertos: valor esperado; Fechado: valor de fechamento; Perdido: preço de tabela).

## Transições com Prospecção e Ganho (substituídas pelas cinco etapas)

Dois jeitos, **a mesma função auditada** (`core_mudar_estagio`):
1. **Arrastar** o cartão entre as cinco colunas.
2. **Trocar no controle** do cartão ou do modal, que só oferece as transições válidas.

**Atendimento (O-31):** soltar um Novo lead em Atendimento (ou escolher "Registrar atendimento") abre o registro do contato, com tipo de atividade e comentário obrigatórios (`acao_registrar_contato`, migration 0031). Gravado o contato, o deal aparece em Atendimento; sem contato, não entra. Não existe voltar de Atendimento para Novo lead: o contato não se desfaz (só o "Desfazer" dos primeiros segundos). Na tabela abaixo, "Prospecção" vale para Novo lead e Atendimento, e "Ganho" passou a se chamar **Fechado**.

| De → Para | Permitido | O que pede |
|---|---|---|
| Prospecção → Em negociação | sim, todos | data de abertura (padrão: hoje no relógio do CRM) |
| Em negociação → Ganho | sim, todos | valor de fechamento, inteiro > 0 (sugerido: o preço de tabela) |
| Em negociação → Perdido | sim, todos | confirmação e, se a **[P14]** aprovar, o motivo |
| Prospecção → Perdido ("Descartar") | sim, todos | confirmação e motivo (**[P14]**). Fica sem data de abertura |
| Prospecção → Ganho | não | precisa passar por negociação. O seletor não oferece |
| Em negociação → Prospecção | não | a abertura já foi registrada. Só "Desfazer" nos 10 s |
| Ganho ou Perdido → Em negociação (reabrir) | só manager e admin **[P10]** | confirmação; limpa `close_date` e `close_value`, e o histórico fica na auditoria |
| Ganho ↔ Perdido | não direto | reabrir antes |

## Painel antes da grade 4 × 4

```
┌ topo: G4 Sight · Painel | Pipeline | Leads · Anna Snelling, vendedora · Trocar perfil ───────────────┐
│ Painel · dados até 31/12/2017                                         (moeda: R$, [P15])           │
├───────────────────────────────────────────────────────────────────────┬─────────────────────────────┤
│ ┌Leads novos ┐ ┌Em negociação┐ ┌Fechamentos ┐ ┌Conversão   ┐          │ PRIORIDADES DO DIA          │
│ │ 0 hoje     │ │ 1.589       │ │ 19 hoje    │ │ 78,7%      │          │ 3 de 10 feitas  ▓▓▓░░░░░░░  │
│ │ 117 em 30 d│ │ R$ 3,9 mi  │ │ 498 em 30 d│ │ em 30 dias │          │ ┌ Hottechi · GTX Pro    82 ┐│
│ │ ↓ 57%      │ │             │ │ ↑ 23%      │ │ ↑ 25 p.p. ⓘ│          │ │ ⚠ em risco · R$ 4.821   ││
│ └────────────┘ └─────────────┘ └────────────┘ └────────────┘          │ │        [✓ Feito] [✗ Pular]││
│ ┌Receita     ┐ ┌Pipeline     ┐ ┌Total de    ┐ ┌Em risco de ┐          │ └──────────────────────────┘│
│ │ ganha 30 d │ │ aberto      │ │ leads      │ │ esfriar    │          │ ┌ item 2 ┐                  │
│ │ R$ 1,10 mi│ │ R$ 4,97 mi │ │ 8.800      │ │ 141        │          │ ┌ item 3 ┐                  │
│ │ ↑ 17%      │ │             │ │            │ │            │          │ ┌ item 4 ┐                  │
│ └────────────┘ └─────────────┘ └────────────┘ └────────────┘          │ ┌ item 5 ┐                  │
│                                                                       │ Próximos: 5 na fila          │
│ SITUAÇÃO DO FUNIL                         [Quantidade | Valor]        │                              │
│ Prospecção     ████████                              500             │                              │
│ Em negociação  ██████████████████████              1.589             │                              │
│ Ganho          ███████████████████████████████████ 4.238             │                              │
│ ─────────                                                             │                              │
│ Perdido (à parte) ████████████████████             2.473             │                              │
└───────────────────────────────────────────────────────────────────────┴─────────────────────────────┘
```

- **À esquerda:** grade de 8 cartões de número (4 por linha no computador, 2 no celular) e, embaixo, o funil.
- **À direita:** o bloco Prioridades do dia, fixo na rolagem. No celular ele vem **primeiro**, antes dos números, porque é onde está a ação.
- **Cartão de número:**
  - ícone do tema;
  - rótulo curto;
  - número grande (Libre Baskerville);
  - linha secundária;
  - selo de variação "↑ 23% vs 30 dias antes", em marinho quando sobe e em bronze escuro quando cai, sempre com a seta (a cor nunca é a única pista).
- Só tokens do tema (FE-03). As barras do funil usam marinho (abertos), dourado médio (ganho) e cinza (perdido).

## Cartões do Painel na primeira versão (com "Em risco de esfriar" como cartão)

**Janelas:**
- "hoje" = data de referência (31/12/2017, relógio do CRM, [P6]);
- "30 dias" = 02/12 a 31/12/2017;
- "30 dias antes" = 02/11 a 01/12/2017.

Números conferidos nos dados limpos (`data/clean/deals.csv`) para os três perfis de exemplo:

| Cartão | Tipo | Origem e cálculo | Admin (todos) | Manager (Dustin Brinkmann) | Vendedora (Anna Snelling) |
|---|---|---|---|---|---|
| **Leads novos**: hoje e 30 dias, com variação | C | deals com `data_abertura` (de `engage_date`) no dia ou na janela, em qualquer estágio de hoje. Os Prospecting não têm data e não entram. Deals criados no CRM entram pela `data_abertura` | 0 hoje · 117 em 30 d · ↓ 57% (275 antes) | 0 · 18 · ↓ 40% | 0 · 7 · ↓ 12% |
| **Em negociação** | C | `estagio = 'Engaging'`: quantidade e soma do valor | 1.589 · R$ 3,89 mi | 193 · R$ 0,28 mi | 57 · R$ 95 mil |
| **Fechamentos**: hoje e 30 dias, quantidade e valor, com variação | D | `estagio = 'Won'` com `close_date` no dia ou na janela; valor = soma de `close_value` | 19 (R$ 41.764) hoje · 498 (R$ 1,10 mi) em 30 d · ↑ 23% | 6 · 91 · ↑ 36% | 2 · 26 · ↑ 18% |
| **Conversão em 30 dias**, com variação em pontos | C | Won ÷ (Won + Lost) com `close_date` na janela | 78,7% · ↑ 25,0 p.p. (53,7% antes) | 86,7% · ↑ 33,9 p.p. | 86,7% · ↑ 33,0 p.p. |
| **Receita ganha em 30 dias**, com variação | D | soma de `close_value` dos Won na janela (inteiro, BD-05) | R$ 1.101.152 · ↑ 17% | R$ 142.110 · ↑ 49% | R$ 36.454 · ↑ 74% |
| **Pipeline aberto** (valor) | C | soma de `score_deals.valor_esperado` dos abertos; **até o score existir**, soma do preço de tabela (`core_produtos.preco`), com o rótulo "pelo preço de tabela" | R$ 4.966.215 | R$ 585.616 | R$ 173.259 |
| **Total de leads** | D | todos os deals do perfil, em qualquer estágio | 8.800 | 1.583 | 448 |
| **Em risco de esfriar** (no lugar de "atendimentos no momento") | C | deals com o ícone ⚠ da 2.4 (em negociação há 107–138 dias); a linha secundária mostra os "esfriou" | 141 · 1.291 esfriaram | 3 · 190 | 1 · 56 |

**"Atendimentos no momento" sai:** o dataset não tem atendimento nem contato em tempo real. Proposta: trocar por **Em risco de esfriar**, que é medível hoje e leva direto à ação (tocar abre o Pipeline filtrado em "em risco"). Depois que o CRM estiver em uso, dá para acrescentar "Contatos registrados hoje" (de `acao_registros`), que nasce em 0. **[P16]**
