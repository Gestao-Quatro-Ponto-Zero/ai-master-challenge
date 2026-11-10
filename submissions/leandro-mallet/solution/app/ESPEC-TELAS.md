# G4 Sight: especificação das telas Pipeline, Leads (com Contas) e Painel

> Especificação para aprovação. Nada de código nem de banco. Marco 1 da decisão 25: especificar as telas e derivar delas o modelo de dados.
> Segue as premissas de desenvolvimento em revisão final (ARQ, BD, BE e FE). Referências: [DESENHO-ACOES.md](DESENHO-ACOES.md) (usuários, escrita e auditoria), [DESENHO-CRM.md](DESENHO-CRM.md) (importação CSV) e [DESENHO-NEXT.md](DESENHO-NEXT.md) (estrutura e marca).
> As perguntas para o Leandro estão marcadas **[P1]**, **[P2]**… e reunidas no fim.

## 0. Interpretação e números de partida

**[P1] Interpretação a confirmar:**
- **Pipeline** = os deals abertos (Prospecting e Engaging) em colunas por estágio, para trabalhar o dia.
- **Leads** = a base inteira de deals (abertos e fechados), com cadastro, importação, ações em lote, tags e comentários.
- "Lead" e "deal" são a mesma linha de `sales_pipeline`. A tela Leads chama de lead; o Pipeline e o modal chamam de deal.

**[P2] "Perfil" no filtro = perfil da empresa** (setor e porte). Só existe para deals com empresa: 664 dos 2.089 abertos (32%) e todos os 6.711 fechados.

O que o dataset tem (dados limpos, data de referência 31/12/2017):

| Medida | Valor |
|---|---|
| Deals na base | 8.800 (2.089 abertos: 500 Prospecting e 1.589 Engaging; 6.711 fechados: 4.238 Won e 2.473 Lost) |
| Abertos sem empresa | 1.425 (68%); nenhum fechado está sem empresa |
| Prospecting sem data de abertura | 500 (todos) |
| Período | `engage_date` de 20/10/2016 a 27/12/2017; `close_date` de 01/03/2017 a 31/12/2017 |
| Time | 35 vendedores (30 com deals), 6 managers, 3 regiões |
| Maior pipeline aberto | Darcel Schlecht, 194 deals; o menor é Wilburn Farren, com 31 |
| Setores | 10 (marketing, entertainment, software, technology, services, retail, employment, telecommunications, medical, finance) |
| Histórico de contatos | **não existe** no dataset |

## 1. Peças comuns às telas

### 1.1 Cartão do deal e linha do lead

O cartão do Pipeline está em 2.3 e a linha da tela Leads em 3.2. Os dois mostram os mesmos dados, com a origem da tabela abaixo.

### 1.2 Origem de cada dado visível

Legenda: **D** = vem do dataset · **C** = calculado · **N** = dado novo do CRM (nasce vazio).

| Dado na tela | Tipo | Origem exata | Observação |
|---|---|---|---|
| Nome do deal | N | `core_deals.nome` | O dataset não tem nome de deal: a migração preenche "Empresa · Produto" ou "Sem empresa · Produto"; editável. **[P11]** |
| Contato principal (nome, cargo, e-mail, telefone) | N | `core_deals.contato_id` → `core_contatos` | O dataset não tem contatos: nasce vazio para os 8.800 ("+ Adicionar contato"). **[P12]** |
| ID do deal | D | `sales_pipeline.opportunity_id` → `core_deals.opportunity_id` | Só em "Ver detalhes". Deal criado no CRM recebe um id de 8 caracteres (A–Z, 0–9), no mesmo formato |
| Produto | D | `sales_pipeline.product` → `core_deals.produto_nome` → `core_produtos.nome` | "GTXPro" já corrigido para "GTX Pro" na limpeza |
| Série do produto | D | `products.series` → `core_produtos.serie` | Filtro e modal |
| Preço de tabela | D | `products.sales_price` → `core_produtos.preco` | Inteiro (BD-05); mostrado em reais, com os mesmos números (P15) |
| Empresa | D | `sales_pipeline.account` → `core_deals.conta_nome` | Nula em 1.425 abertos: mostra "Sem empresa" e oferece "Preencher empresa" |
| Setor | D | `accounts.sector` → `core_contas.setor` | Mostrado em português na tela (ex.: "varejo" para retail); o valor gravado continua o do dataset |
| Porte | C | faixa de `accounts.employees` → `core_contas.funcionarios`: pequena (até 1.428), média (até 4.540) e grande | Tercis calculados na limpeza. **[P3]** Porte por funcionários (proposta) ou por receita (`accounts.revenue`)? |
| Vendedor | D | `sales_pipeline.sales_agent` → `core_deals.vendedor_nome` | |
| Manager e região | D | `sales_teams.manager`, `sales_teams.regional_office` → `core_vendedores.manager_nome` → `core_managers.escritorio_nome` | |
| Estágio | D | `sales_pipeline.deal_stage` → `core_deals.estagio` | Na tela (O-31): Novo lead, Atendimento (Prospecting sem e com contato registrado), Em negociação, Fechado e Perdido |
| Data de abertura | D/N | `sales_pipeline.engage_date` (o início da negociação, pela definição do dataset) → `core_deals.data_abertura`. No CRM: a data em que o deal passa para Em negociação | Os 500 Prospecting ficam sem data e mostram "Não iniciado". **[P4]** |
| Dias desde a abertura | C | `data_referencia − data_abertura` | "Não iniciado" quando não há abertura |
| Ícone (super hot, em risco, esfriou) | C | estágio, dias desde a abertura e preço de tabela, com os cortes de `config_parametros` | Critérios e contagens em 2.4. **[P13]** |
| Último contato | N | o registro mais recente de contato em `acao_registros` → `core_deals.ultimo_contato_em` | O dataset não tem contatos: sem a proposta da **[P5]**, nasce vazio para os 8.800 |
| Lead score (0–100) | C | `score_deals.score` da execução ativa (gerado em Python) | Só para deals abertos. Sem nota (deal novo ou importado depois da rodada): "Sem nota ainda". As regras dependem da decisão do score (decisão 10, em aberto) |
| Componentes e motivos da nota | C | `score_componentes`, `score_motivos` | No modal (2.5); o cartão mostra só a barra da nota. Os nomes finais vêm da decisão do score |
| Ação sugerida | C | `score_deals.acao_sugerida` (focar, requalificar, desistir) | Selo do cartão |
| Marcadores | C | `score_deals.marcadores` (esfriando, sem_conta, sem_data) | Saída do score, usada nos filtros e nos motivos do modal. Não é o ícone do cartão (2.4), que vem de critérios medidos nos dados |
| Valor esperado | C | `score_deals.valor_esperado` | Inteiro, calculado no servidor (BD-05) |
| Valor de fechamento | D | `sales_pipeline.close_value` → `core_deals.close_value` | Só em Won; Lost = 0 |
| Data de fechamento | D | `sales_pipeline.close_date` → `core_deals.close_date` | Só em Won e Lost |
| "Atualizado depois da nota" | C | `core_deals.atualizado_em > score_execucoes.gerado_em` | Avisa que a nota é de antes da última mudança |
| Tags | N | `acao_deal_tags` + `config_tags` | Nascem vazias |
| Comentários (quantidade e texto) | N | `acao_comentarios` (sem os apagados) | Nascem vazios |
| Linha do tempo | D/N | `engage_date`, `close_date` + `system_auditoria`, `acao_registros`, `acao_comentarios` | Detalhe em 2.5 |
| Motivo da perda | N | `core_deals.motivo_perda` | Só se a **[P14]** aprovar |
| Quem mudou e quando | N | `system_auditoria` | Na linha do tempo do modal |

### 1.2b Entrada (O-37)

- A raiz `/` sempre mostra a entrada, mesmo com perfil escolhido antes: bloco de destaque no azul do deck com "G4 Sight" e "CRM do time comercial com a prioridade do dia dentro do pipeline.", e a escolha do papel em 3 cartões grandes (Vendedor, Manager, Admin). Vendedor e manager escolhem o nome; admin entra direto. Sem login nem senha (decisão 16).
- Com perfil na sessão, a entrada oferece também "Continuar como <nome>".
- O perfil fica num cookie **de sessão do navegador** (`g4_perfil`, sem validade): fechou o navegador, escolhe de novo.
- Rota interna sem perfil continua mandando para a entrada com `?voltar=` e, depois da escolha, volta para lá (só caminhos internos do app).

### 1.3 Relógio do CRM

**[P6]** O dataset termina em 31/12/2017, mas as ações no CRM acontecem hoje. Proposta: enquanto o CRM estiver em modo demonstração, "hoje" é a data de referência (`config_parametros.data_referencia` = 31/12/2017).
- Idade, dias sem contato e filtros de data contam a partir dela.
- Contato, comentário e deal registrados agora ganham duas datas: a **data do negócio** (a data de referência, usada nas contas) e o momento real (usado na auditoria).
- Sem isso, um contato registrado hoje apareceria "8 anos depois" de todos os outros dados.

### 1.4 O que cada perfil vê (vale para todas as telas)

| | Vendedor | Manager | Admin |
|---|---|---|---|
| Deals | os dele | os do time | todos |
| Filtros de vendedor, manager e região | escondidos | vendedor (só do time) | todos |
| Coluna/linha "vendedor" | escondida | visível | visível |
| Ações | as dele, nos deals que vê | também importação e lote do time | também importação, lote geral e criação de tags |

O servidor não bloqueia por dono do deal (decisão 16, BD-04). O perfil decide o que a tela oferece.

## 2. Tela Pipeline

Requisitos do Leandro para esta tela:
- cada deal com **nome e contato** visíveis e a **data de abertura**;
- **barra da nota** preenchida, com cor por faixa;
- **ícone na ponta** do cartão para deal super hot ou em risco de esfriar;
- ao clicar, um **modal com uma tela só** sobre o deal: linha do tempo visual, explicação da nota e comentários (postar e apagar);
- mover o deal entre colunas **ou** trocar o estágio dentro do cartão.

### 2.1 Objetivo e ação principal

- **Objetivo:** trabalhar o dia. Ver os deals abertos por estágio, na ordem da prioridade, e mover cada um para frente.
- **Ação principal (FE-02, uma por tela):** **Abrir o próximo deal**. Abre o modal do deal de maior nota, dentro do filtro atual, que ainda não teve contato registrado hoje. Dois toques: o botão e a ação no modal (FE-05).

### 2.2 Layout

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
- Até 50 cartões por coluna, na ordem escolhida, e "Mostrar mais" de 50 em 50.
- **Celular:** as colunas viram abas que rolam para o lado, e a etapa muda pelo controle do cartão.

### 2.3 Cartão do deal

```
┌────────────────────────────────────────────────────┐
│ Hottechi · GTX Pro                            [🔥] │ ① nome do deal          ⑥ ícone na ponta
│ Maria Souza, Compras        (ou + Adicionar contato)│ ② contato principal
│ ███████████████░░░░░░  72                          │ ③ barra da nota (cor pela faixa)
│ Aberto em 14/11/2017 · 47 dias  (ou Não iniciado)  │ ④ data de abertura e idade
│ R$ 4.821 esperado          [ Em negociação ▾ ]    │ ⑤ valor e seletor de estágio
│ Anna Snelling                       #urgente  +2   │ vendedor (manager e admin) e até 2 tags
└────────────────────────────────────────────────────┘
```

| # | Elemento | Regra |
|---|---|---|
| ① | **Nome do deal** | `core_deals.nome`, editável no modal. O dataset não tem nome de deal: a migração preenche "Empresa · Produto" ou, sem empresa, "Sem empresa · Produto". **[P11]** |
| ② | **Contato principal** | O contato do deal em `core_contatos` (nome e cargo). O dataset não tem contatos: nasce vazio para os 8.800 e mostra o link "+ Adicionar contato". **[P12]** |
| ③ | **Barra da nota** | Preenchida de 0 a 100, com o número ao lado. A cor vem da faixa: alta (≥ 70) em `--color-nota-alta` (marinho), média (40–69) em `--color-nota-media` (bronze) e baixa (< 40) em `--color-nota-baixa` (cinza). Trilho em `--color-dourado-claro`. Sem nota: barra vazia e "Sem nota ainda". Os componentes da nota ficam no modal |
| ④ | **Data de abertura** | `engage_date` → `core_deals.data_abertura`, com a idade em dias até a data de referência. Prospecção sem data: "Não iniciado" |
| ⑤ | **Valor e estágio** | Valor esperado (`score_deals.valor_esperado`, inteiro). O seletor de estágio só mostra as transições válidas (2.6) |
| ⑥ | **Ícone na ponta** | Super hot, em risco de esfriar ou esfriou (2.4); no máximo um. Tem rótulo para leitor de tela e, ao passar o mouse, a frase do motivo |

As cores da barra cumprem o contraste mínimo de objeto gráfico (3:1) sobre o fundo do cartão: marinho 16,6:1, bronze 3,8:1 e cinza 4,2:1. O dourado (2,2:1) não é usado como preenchimento.

### 2.4 Ícones: super hot e risco de esfriar (critérios medidos nos dados)

O que os dados mostram (dados limpos e `analysis/findings.md`):
- **Só o tempo tem sinal.** Deals que passam dos primeiros 14 dias fecham como ganho 67% das vezes; os que fecham antes, 54%. Metade dos perdidos encerra em até 14 dias. Depois disso, a taxa fica plana.
- **Ciclo dos ganhos:** mediana 57 dias, p75 88, p90 **106**, máximo **138**. Nenhum deal fechado passou de 138 dias.
- **O pipeline aberto está quase todo parado:** dos 1.589 em negociação, 1.291 (81%) estão abertos há mais de 138 dias.

**Proposta [P13]:**

| Ícone | Critério | Deals abertos que caem nele hoje | Frase ao passar o mouse |
|---|---|---|---|
| 🔥 **Super hot** | Em negociação **entre 15 e 106 dias** (passou da janela em que os perdidos caem e está dentro do ciclo de 90% dos ganhos). Sem critério de ticket desde a 0030 (O-24): o valor não entra na nota (decisões 28 e 29) | **150** (7% dos abertos); com o antigo corte de R$ 3.000 eram 66 | "Na fase em que mais deals viram ganho." |
| ⚠ **Em risco de esfriar** | Em negociação **entre 107 e 138 dias**: já passou do tempo em que 90% dos ganhos fecharam e se aproxima do maior ciclo já visto | **141** (7% dos abertos) | "Aberto há 120 dias. 90% dos ganhos fecham em até 106 dias." |
| ❄ **Esfriou** (ícone cinza, mais discreto) | Em negociação **há mais de 138 dias**: mais tempo que qualquer deal já fechado | **1.291** (62% dos abertos) | "Aberto há 210 dias, mais que qualquer deal já fechado (138). Requalifique ou encerre." |
| sem ícone | Prospecção (sem data de abertura) e negociação com menos de 15 dias | 500 + 7 | — |

- **Por que três ícones e não dois:** se o "em risco" incluísse os parados há mais de 138 dias, ele apareceria em 69% dos cartões e deixaria de chamar atenção. Separar o "esfriou" mantém o alerta raro e útil. **[P13]** decide se fica assim ou se os dois viram um só.
- **Depois que o CRM estiver em uso:** "sem contato registrado há 14 dias ou mais" também passa a contar como risco. O número 14 vem da janela dos perdidos, mas o dataset não tem contatos para medir esse critério; ele fica como parâmetro em `config_parametros`.
- Os cortes (15, 106 e 138 dias) ficam em `config_parametros.icone_cortes`; `preco_min_quente` = null (sem ticket).
- O cálculo dos ícones fica no servidor (`core_deals_visao`), não na tela.

### 2.5 Modal do deal (uma tela só)

Clicar no cartão abre um modal sobre o Pipeline (`?deal=ID` no link, que abre direto no modal). Tudo numa tela, sem abas:

```
┌ Hottechi · GTX Pro  ✎                                   [🔥 Super hot]      × ┐
│ Maria Souza, Compras · maria@… · (11) …   ✎   │  Estágio: [ Em negociação ▾ ]   │
│ Anna Snelling · time de Dustin Brinkmann · Central │  R$ 4.821 esperado         │
├───────────────────────────────────────────────┬─────────────────────────────────┤
│ LINHA DO TEMPO                                │ POR QUE A NOTA É 72              │
│ ●── 14/11/2017  Aberto (entrou em negociação) │ ███████████████░░░░ 72 (alta)    │
│ │                                             │ • frase do motivo 1              │
│ ●── 02/12/2017  Anna: Liguei — "pediu…"       │ • frase do motivo 2              │
│ │                                             │ Componentes:                     │
│ ●── 05/12/2017  Tag #urgente                  │  Tempo ........ 30 de 40         │
│ │                                             │  Valor ........ 25 de 30         │
│ ●── 06/12/2017  Comentário de Cara Losch      │  … (nomes finais vêm do score)   │
│ ○── hoje        [ Liguei ] [ Requalifiquei ]  │                                  │
│                                               │ COMENTÁRIOS                      │
│                                               │ [ Escreva um comentário…  ] [Postar] │
│                                               │ Cara Losch · 06/12 · Apagar      │
├───────────────────────────────────────────────┴─────────────────────────────────┤
│ Ver detalhes (ID, código para suporte, execução da nota)   Histórico completo da auditoria │
└──────────────────────────────────────────────────────────────────────────────────┘
```

**Linha do tempo visual**, da mais antiga para a mais recente, com um marcador por tipo:

| Evento | Origem |
|---|---|
| Aberto (entrou em negociação) | dataset: `engage_date`; no CRM: a mudança de estágio em `system_auditoria` |
| Mudança de estágio, encerramento (Ganho com valor, Perdido com motivo) e reabertura | dataset: `close_date` e `close_value`; no CRM: `system_auditoria` (campo `estagio`) |
| Criado no CRM ou importado | `core_deals.criado_em` / `importacao_id` |
| Ações (Liguei, Requalifiquei, Desisti) | `acao_registros` (as desfeitas aparecem riscadas) |
| Comentários | `acao_comentarios` (os apagados não aparecem) |
| Tags aplicadas e removidas, contato e empresa preenchidos, nome alterado | `system_auditoria` |

- Para os deals do dataset, entre a abertura e hoje não há nenhum registro. A linha do tempo mostra isso como um trecho tracejado com o texto "Sem registros entre 14/11/2017 e hoje", sem inventar eventos.
- Datas na data do negócio (relógio do CRM, [P6]). O momento real fica em "Ver detalhes".

**Explicação da nota:** a mesma barra do cartão, a faixa, os motivos em frase simples (`score_motivos`) e os componentes com "X de Y pontos" (`score_componentes`). Os nomes e as regras vêm da decisão do score (decisão 10). Sem nota: "Este deal ainda não tem nota; ela aparece na próxima rodada."

**Comentários: postar e apagar:**
- **Postar:** texto de 1 a 1.000 caracteres, sem HTML. Aparece no topo da lista e na linha do tempo.
- **Apagar = remoção lógica (BD-04, nada é apagado do banco):**
  - O comentário some da lista e da linha do tempo.
  - No banco, ele continua em `acao_comentarios`, com `removido_em` e `removido_por` preenchidos.
  - A remoção fica registrada em `system_auditoria` (quem, quando, com o texto no "antes").
  - Quem pode: o autor do comentário, o manager e o admin. A tela pede confirmação ("Apagar este comentário?") e mostra "Desfazer" por 10 segundos.
  - Na tela não há lixeira nem "ver apagados". A recuperação depois dos 10 segundos é pela auditoria, com o admin.
- **Editar:** o autor edita e o comentário mostra "editado". O texto anterior fica na auditoria.

**Outras ações no modal:** editar o nome do deal, adicionar ou trocar o contato, preencher a empresa, trocar o estágio, registrar Liguei, Requalifiquei ou Desisti, e aplicar ou remover tags.

### 2.6 Mudança de estágio

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

- Toda mudança grava antes e depois em `system_auditoria` e aparece na linha do tempo.
- "Desfazer" por 10 segundos, pelo próprio autor, devolve o estágio anterior.
- **Conflito de edição:** se o deal mudou desde que a tela leu, a mudança é recusada (409), o cartão volta para a coluna de onde saiu e aparece "Este deal foi alterado por Cara Losch às 14:32. Recarregue para ver a versão atual."
- **[P14] Motivo da perda:** proposta de lista curta (preço, concorrente, sem orçamento, sem resposta, outro + texto), obrigatória ao perder ou descartar, para virar filtro e relatório depois. Alternativa: sem motivo, só a confirmação.

### 2.7 Filtros e ordenação

- **Campo livre** (seção 5) e as etiquetas que ele gera.
- **Atalhos ao lado do campo**, que geram as mesmas etiquetas: Nota (alta, média, baixa), Ícone (super hot, em risco, esfriou), Data de abertura, Último contato, Perfil (setor e porte), Vendedor (só manager e admin).
- Os filtros ficam no link (`/pipeline?f=...`), para mandar para alguém e para o "Voltar" do navegador.
- **Ordenação dentro da coluna:** Nota (padrão, maior primeiro), Valor esperado, Dias sem contato, Dias desde a abertura, Data de abertura.

### 2.8 Estados

| Estado | O que aparece |
|---|---|
| Carregando | as duas colunas com 4 cartões-esqueleto cada; o campo de filtro já pode ser usado. O modal abre com o esqueleto da linha do tempo |
| Vazio (sem deals abertos) | "Você não tem deals abertos. Cadastre um lead ou importe uma planilha em Leads." + botão "Ir para Leads" |
| Vazio (filtro sem resultado) | "Nenhum deal com estes filtros." + as etiquetas e "Limpar filtros" |
| Vazio (modal) | linha do tempo só com a abertura e o trecho "Sem registros"; comentários: "Nenhum comentário ainda. Escreva o primeiro." |
| Erro | "Não foi possível carregar o pipeline. Tente de novo em alguns segundos." + "Tentar de novo"; o código para suporte fica em "Ver detalhes" |
| Só leitura (banco fora, BE-05) | faixa: "Modo somente leitura: mudanças estão desligadas agora." Cartões não arrastam; seletor de estágio, comentários e ações somem. O modal mostra a nota e a abertura, sem linha do tempo do CRM |
| Sem permissão | sem perfil escolhido: vai para "Quem é você?" e volta. Vendedor tentando reabrir: "Reabrir um deal encerrado é feito pelo manager ou pelo admin." |

### 2.9 Repasse por falta de atendimento

Regras do Leandro (os números quem fecha é o score, #3):
- **Lead sem contato que muda de faixa de tempo é repassado** a outro vendedor com encaixe parecido (FIT próximo no mesmo cohort), pelo mesmo roteamento do lead novo.
- **Linha do tempo:** "Repassado: sem contato em 2 dias; Anna tem encaixe parecido."
- **Avisos:** o vendedor que perdeu o lead e o que recebeu ganham um aviso no topo do CRM ("Você recebeu 1 lead repassado" / "1 lead seu foi repassado por falta de contato"), que some ao ser lido.
- **Mini penalidade:** quem perde lead por repasse leva uma penalidade pequena no roteamento (parâmetro em `config_parametros`), por um período definido pelo score.
- **Visão do manager:** contador "Perdidos por falta de atendimento" por vendedor (Painel, 4.7).
- O repasse é feito pela rotina do servidor, nunca pela tela. A tela só mostra o resultado.

| Dado | Tipo | Origem |
|---|---|---|
| Evento de repasse na linha do tempo | N | `acao_repasses` (de, para, motivo, faixa de tempo) |
| Aviso para os dois vendedores | N | `system_avisos` (usuário, texto, lido em) |
| Contador por vendedor | C | quantidade de `acao_repasses` em que ele perdeu o lead, na janela do Painel |

## 3. Tela Leads

### 3.1 Objetivo e ação principal

- **Objetivo:** cuidar da base inteira, abertos e fechados: encontrar, cadastrar, importar, marcar com tags, comentar e agir em lote sobre o que o filtro encontrar.
- **Ação principal:** **Novo lead** (cadastro). Importar e as ações em lote são secundárias, mas sempre à vista.

### 3.2 Layout

```
┌ topo ───────────────────────────────────────────────────────────────────────────────┐
│ [ Filtrar: ex. "varejo grande ganhos em 2017"                     ]   [Importar CSV]  [Novo lead] │
│ Entendi assim: (Setor: varejo ×) (Porte: grande ×) (Estágio: Ganho ×) (Fechou em 2017 ×)        │
│ 1.204 leads · R$ 2,1 mi fechados                                                     │
├──┬──────────────────────┬──────────────┬───────────────┬──────┬────────────┬────────┬────────┬──────┤
│☐ │ Lead                 │ Vendedor     │ Estágio       │ Nota │ Valor      │Abertura│ Últ.   │ Tags │
│  │ nome · contato       │              │               │      │            │        │ contato│ 💬 n │
├──┼──────────────────────┼──────────────┼───────────────┼──────┼────────────┼────────┼────────┼──────┤
│☐ │ Hottechi · GTX Pro   │ Anna Snelling│ Em negociação │ 82   │ R$ 3.064 e│ 14/11  │ há 3 d │ #urg │
│☐ │ Cancity · MG Special │ Moses Frase  │ Ganho         │  —   │ R$ 55     │ 20/10  │ —      │      │
└──┴──────────────────────┴──────────────┴───────────────┴──────┴────────────┴────────┴────────┴──────┘
 50 por página · Mostrar mais
 ── ao marcar linhas, sobe uma barra: "12 selecionados · Selecionar os 1.204 do filtro · [Aplicar tag] [Comentar] [Mais ▾]"
```

- **Colunas:** Lead (nome do deal, com o contato principal embaixo), Vendedor (só manager e admin), Estágio, Nota (barra com a cor da faixa; só abertos, fechados mostram "—"), Valor (esperado nos abertos; fechamento nos ganhos), Abertura, Último contato, Tags e a quantidade de comentários. O ícone (2.4) aparece na ponta da linha.
- **Perfil da empresa** (setor · porte) aparece abaixo do nome da empresa, em texto menor.
- Clicar na linha abre o mesmo modal do deal do Pipeline.
- 50 linhas por vez, e o total no topo vem do mesmo filtro.
- **Celular:** a tabela vira lista de cartões (o mesmo cartão do Pipeline, com o estágio), e a seleção é por toque longo.

### 3.3 Filtros e ordenação

- O mesmo campo livre da seção 5. Aqui ele aceita também estágio e resultado (abertos, ganhos, perdidos), data de fechamento, produto, série, tag e "com comentário".
- **Atalhos:** Estágio, Nota, Ícone, Data de abertura, Último contato, Perfil, Vendedor, Tag.
- **Ordenação por coluna:** Nota, Valor, Abertura, Último contato, Fechamento, Vendedor e Lead (A–Z). Padrão: abertos primeiro, por nota; depois os fechados, do mais recente.

### 3.4 Funções nesta tela

Cadastro, importação CSV, ações em lote, tags e comentários. Regras na seção 6.

### 3.5 Estados

| Estado | O que aparece |
|---|---|
| Carregando | a tabela com 8 linhas-esqueleto; o total aparece quando chega |
| Vazio (base vazia) | "Ainda não há leads. Importe uma planilha ou cadastre o primeiro." + [Importar CSV] [Novo lead] |
| Vazio (filtro sem resultado) | "Nenhum lead com estes filtros." + as etiquetas e "Limpar filtros" |
| Erro | "Não foi possível carregar os leads. Tente de novo." + "Tentar de novo" e "Ver detalhes" |
| Só leitura | faixa de somente leitura. O arquivo de reserva só tem os abertos, então a tela avisa: "Mostrando só os 2.089 deals abertos; a base completa volta quando o banco voltar." Cadastro, importação, lote, tags e comentários ficam escondidos |
| Sem permissão | vendedor tentando importar ou aplicar lote fora do que a tela oferece: "Esta ação é feita pelo manager ou pelo admin." |

### 3.6 Aba Contas

Requisito do Leandro: uma aba **Contas** dentro de Leads, ao lado da lista de leads, com o cadastro da empresa, o histórico e o padrão calculado dela.

**Contexto do score (decisão 33):** NOTA = 0,7 × FIT + 0,3 × HEAT + **Extra Bonus** (0 a 20; a nota vai até 120).
- O bonus é por empresa: cresce com o tamanho do histórico e com a empresa estar na janela de compra usual (periodicidade e mês).
- É recalculado todo domingo. A fórmula é da #3.
- Até ela entregar, os campos do padrão mostram "Calculado no domingo".

**Abas da tela Leads:** `Leads | Contas` (`/leads?aba=contas`). A ação principal da aba Contas é **Nova empresa**.

**Lista das empresas** (85 no dataset):

| Coluna | Tipo | Origem |
|---|---|---|
| Empresa | D | `accounts.account` → `core_contas.nome` |
| Setor | D | `accounts.sector` (em português na tela) |
| Porte | C | tercil de `accounts.employees` |
| Sede | D | `accounts.office_location` → `core_contas.pais` |
| Empresa-mãe | D | `accounts.subsidiary_of` (15 são subsidiárias) |
| Deals abertos | C | deals abertos da empresa (até 14 hoje) |
| Compras | C | deals ganhos da empresa (de 23 a 115; mediana 47) |
| Receita ganha | C | soma de `close_value` dos ganhos (de R$ 51.632 a R$ 341.455) |
| Padrão | N | selo **Na janela de compra** / **Fora da janela** / **Sem padrão**, com o bonus atual (0 a 20). Antes da primeira rodada: "Calculado no domingo" |

**Ficha da conta** (modal, no mesmo padrão do modal do deal):
- **Cadastro editável:** nome (só na criação), setor, funcionários, receita, ano de fundação, sede e empresa-mãe. "Nova empresa" cria; "Editar" altera. Tudo auditado. Isto responde à decisão (a): cadastrar empresa nova passa a existir. **[P19]**
- **Histórico:**
  - compras ganhas e perdidas por mês, num gráfico de barras simples com tokens (marinho = ganho, cinza = perdido);
  - produtos comprados (quantidade e receita por produto);
  - ticket médio dos ganhos;
  - primeira e última compra.
- **Padrão calculado** (do score):
  - intervalo típico entre compras;
  - mês habitual;
  - próxima compra esperada;
  - bonus atual;
  - frase de explicação (ex.: "Compra a cada 45 dias, mais em março; a próxima deve vir até 15/01").
  Sem rodada: "Calculado no domingo".
- **Deals abertos da empresa:** lista com nome, estágio, nota e ícone. Tocar abre o modal do deal.

**Filtro livre na aba** (mesmo interpretador da seção 5, com etiquetas de conta):

| Frase | Etiquetas |
|---|---|
| `na janela de compra` · `fora da janela` · `sem padrão` | Padrão: … |
| `setor varejo` · `varejo` | Setor: varejo |
| `empresas grandes` | Porte: grande |
| `mais de 50 compras` | Compras > 50 |
| `com deal aberto` · `sem deal aberto` | Deals abertos > 0 / = 0 |
| `receita acima de 200 mil` | Receita ganha ≥ 200.000 |
| `subsidiárias` · `independentes` | Empresa-mãe preenchida / vazia |
| `bonus acima de 10` | Bonus ≥ 10 |
| `sede Estados Unidos` | Sede: United States |

**Ordenação:** Receita ganha (padrão), Compras, Deals abertos, Bonus, Empresa (A–Z).

**Estados:**

| Estado | O que aparece |
|---|---|
| Carregando | 8 linhas-esqueleto; ficha com esqueleto do gráfico |
| Vazio | "Nenhuma empresa cadastrada. Cadastre a primeira ou importe uma planilha de leads." + [Nova empresa] |
| Vazio (filtro) | "Nenhuma empresa com estes filtros." + "Limpar filtros" |
| Erro | "Não foi possível carregar as empresas. Tentar de novo." |
| Só leitura | sem "Nova empresa" e sem "Editar"; a lista e a ficha continuam |

## 4. Tela Painel

Requisitos do Leandro para esta tela:
- só **dados quantitativos**: números e o funil;
- o visual da referência adaptado ao tema;
- os cartões de transferências e reuniões trocados por um bloco **Prioridades do dia**. A pessoa dá ✓ ou ✗, a lista anda, e cada marcação vai para a linha do tempo do lead.

### 4.1 Objetivo e ação principal

- **Objetivo:** em segundos, ver como está o pipeline (números e funil) e trabalhar a lista do dia.
- **Ação principal (FE-02):** **✓ no primeiro item das Prioridades do dia**. É o único botão em destaque da tela. Os cartões de número não têm botão; tocar num deles abre a tela Leads ou Pipeline já com o filtro correspondente.

### 4.2 Layout

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

### 4.3 Cartões e origem de cada número

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

**Aviso de calendário (ⓘ no cartão de conversão e no de fechamentos):** dezembro fecha um trimestre. No histórico, os ganhos se concentram no último mês de cada trimestre (padrão do gerador dos dados, `findings.md`), por isso a conversão salta de 53,7% para 78,7%. O ⓘ abre a frase: "Dezembro fecha o trimestre; no histórico, os ganhos se concentram no último mês. Compare com o mesmo mês de outro trimestre." Assim o manager não lê como melhora do time.

**Escopo por perfil:** vendedor vê os números dele, manager os do time e admin tudo, com os filtros de região, manager e vendedor no topo (como no Pipeline). O servidor calcula com o mesmo escopo das outras telas.

### 4.4 Situação do funil

| Barra (O-31) | Quantidade | Valor | Origem |
|---|---|---|---|
| Novo lead | 500 (dataset) | valor esperado | `estagio = 'Prospecting'` e sem contato registrado |
| Atendimento | 0 no dataset; enche com o uso | valor esperado | `estagio = 'Prospecting'` e com contato registrado |
| Em negociação | 1.589 | valor esperado | `estagio = 'Engaging'` |
| Fechado | 4.238 | `close_value` | `estagio = 'Won'` |
| **Perdido** (em cinza, separado por uma linha, à parte) | 2.473 | preço de tabela do que se perdeu | `estagio = 'Lost'` |

- **Alternância Quantidade | Valor**, e cada barra mostra o número no fim.
- Tocar numa barra abre Leads (ou o Pipeline, para os abertos) filtrado naquele estágio.
- É a **situação atual da base** (quantos deals estão em cada estágio hoje), não uma coorte. O título diz isso: "Situação do funil hoje".
- Manager e vendedor veem o funil do próprio escopo (Dustin Brinkmann: 204 · 193 · 747 · 439; Anna Snelling: 55 · 57 · 208 · 128).

### 4.5 Prioridades do dia

**De onde vem a lista:**

| Perfil | Itens | Ordem |
|---|---|---|
| Vendedor | os deals abertos dele | a ordem abaixo |
| Manager **[P17]** | os deals abertos do time, pelo parâmetro `prioridades_gestor`: `atencao`, "só o que pede ação" (decisão do Leandro): atendimento atrasado, lead novo com FIT ≥ 75 e em risco de esfriar ⚠. O super hot não entra | a ordem abaixo; cada item mostra o vendedor |
| Admin **[P17]** | a mesma regra do manager, para todos os times | a ordem abaixo |

**Ordem (a mesma para todos, migration 0030):** 1) no topo, o lead novo (criado no CRM há até 1 dia, sem contato) com FIT ≥ 75, e acima de tudo os marcados "atendimento atrasado"; 2) depois, pela nota; 3) no empate, maior HEAT; 4) por fim, o código do deal. O valor esperado não entra.

**Cartão:** a linha de explicação é o 1º motivo da nota (`score_motivos`, ordem 1). O ícone aparece só como alerta (em risco, esfriou); o atendimento atrasado tem marca própria.

Ficam fora da lista do dia os deals que já tiveram ✓, ✗ ou contato registrado hoje.

**Visual (O-32):** bloco escuro no padrão do deck (degradê navy, texto claro, contador e nota em dourado). Cada lead ocupa uma linha (nome · produto, nota em dourado, ✕ e ✓ em pílula) e uma linha pequena embaixo (valor, há quantos dias e o alerta). O motivo da nota não aparece aberto: clicar no lead abre o deal na parte "Por que a nota é N", com FIT, HEAT e BONUS, os pontos de cada componente e todos os motivos. ✓ e ✕ não abrem o deal. O topo (título, alerta de risco e contador) fica fixo e a lista rola embaixo; no computador aparecem pelo menos 2 itens inteiros.

**Painel em todas as larguras (O-32):** ≥ 1280 px, a grade 4 × 4; de 1024 a 1279, Prioridades e funil em largura cheia no topo e os 8 números em 4 colunas; abaixo de 1024, Prioridades, números em 2 colunas e funil. Os números grandes usam fonte fluida e nunca quebram linha.

**Como a lista anda:**
- **Meta do dia de 20, todos à mostra** (O-34, pedido do Leandro; `config_parametros.meta_prioridades_dia`, migration 0032). Não há fila nem "5 por vez". A barra "3 de 20 feitas" mostra o avanço. Listas de hoje montadas com meta menor se completam até 20 na próxima abertura, sem tirar os itens que já estavam.
- Ao marcar ✓ ou ✗, o item **fica na lista**, esmaecido e com o estado ("Feito" ou "Pulado"); a lista não anda. No bloco azul a lista rola por dentro com o topo fixo; abaixo de 1280 px o bloco cresce.
- A lista do dia é montada na primeira abertura do dia e fica estável até o dia acabar. Exceção: se a execução de score ativa mudar, os itens ainda não marcados saem (ficam gravados como substituídos) e entram os da ordem nova; os já marcados ficam.

**O que ✓ e ✗ significam [P18]:**

| Marca | Significa | Grava | Na linha do tempo do lead | Muda o deal? |
|---|---|---|---|---|
| ✓ **Feito** | "trabalhei este deal hoje" | `acao_registros` com `acao = 'prioridade_feita'`, `data_negocio` = hoje e nota opcional | "Anna marcou como feito na prioridade do dia" | Não muda estágio. Proposta: **não** conta como contato; para registrar contato, o item tem também "Liguei" |
| ✗ **Pular** | "não vou trabalhar este deal hoje" | `acao_registros` com `acao = 'prioridade_pulada'` | "Anna pulou na prioridade do dia" | Não descarta nem muda nada. O deal pode voltar amanhã |

- **Para o manager e o admin**, ✓ significa "acompanhei este deal com o vendedor hoje" e ✗, "não vou acompanhar hoje". A gravação e a linha do tempo são as mesmas, com o nome de quem marcou.
- **Desfazer:** por 10 segundos, "Desfazer" devolve o item ao lugar (update `desfeita_em`). A marcação desfeita aparece riscada na linha do tempo.
- **Pulado várias vezes:** se o mesmo deal for pulado em 3 dias seguidos, o item volta com a pergunta "Pulado 3 vezes. Requalificar ou encerrar?", que abre o modal do deal. **[P18]**

**Quando a lista acaba:**
- **Lista concluída** (todos marcados): "Lista de hoje concluída: 18 ✓ e 2 ✗." no topo da lista, que continua à mostra. Não existe mais "Puxar mais 5".
- **Não há mais deals na fila** (todos marcados hoje, ou nenhum aberto): "Você passou por todos os seus deals abertos hoje." + "Ir para o Pipeline".

### 4.6 Estados

| Estado | O que aparece |
|---|---|
| Carregando | os 8 cartões e o funil com esqueleto do tamanho final; a lista com 5 itens-esqueleto. Os cartões aparecem juntos, não um a um |
| Vazio (sem deals no escopo) | cartões com 0 e "—" nas variações; funil vazio com "Sem deals ainda. Importe uma planilha ou cadastre um lead em Leads." |
| Variação sem base | quando a janela anterior é 0: "sem base para comparar" no lugar do selo (nunca "∞%") |
| Erro | por bloco: se o funil falhar, os cartões continuam. "Não foi possível carregar este bloco. Tentar de novo." O código para suporte fica em "Ver detalhes" |
| Só leitura (banco fora) | números e funil calculados do arquivo de reserva, que só tem os abertos. Aparecem Em negociação, Pipeline aberto e Em risco; os cartões que dependem de fechados mostram "Disponível quando o banco voltar". A lista de prioridades aparece sem ✓ e ✗ |
| Sem permissão | sem perfil escolhido: vai para "Quem é você?" e volta |

### 4.7 Bloco do time (manager e admin)

Abaixo do funil, só para manager e admin, uma tabela **Por vendedor**:

| Vendedor | Abertos | Em risco | Esfriaram | Prioridades feitas hoje | Perdidos por falta de atendimento (30 dias) |
|---|---|---|---|---|---|

O último contador vem de `acao_repasses`. Ele nasce em 0, porque o dataset não tem contatos, e passa a contar depois que o CRM estiver em uso. Tocar no vendedor abre o Pipeline filtrado nele.

**Prioridades do dia, regra nova:** um lead novo (criado ou importado hoje) só fura a fila da lista do dia se tiver **FIT ≥ 75**. Com FIT menor, ele entra na ordem normal. Corte em `config_parametros`.

## 5. Filtro em campo livre: interpretador por regras

**Como funciona:**
- Uma função pura (`src/lib/interpretar-filtro.ts`), sem IA, que transforma a frase em **etiquetas**. Cada etiqueta é um filtro estruturado.
- As etiquetas aparecem embaixo do campo ("Entendi assim:"), e cada uma pode ser removida.
- O que o interpretador não reconhece vira a etiqueta **Contém "…"**, uma busca de texto em produto, empresa, vendedor, id, tag e comentário. Com mais de uma palavra, o lead precisa ter todas, em qualquer ordem.
- Maiúsculas, acentos e plural não importam. Os nomes de pessoas aceitam só o primeiro nome quando ele é único no time.
- As etiquetas fora do escopo do perfil não são geradas: um vendedor que digita "do Darcel" recebe "Contém 'darcel'", sem filtro de vendedor.

**Exemplos (frase → etiquetas):**

| Frase digitada | Etiquetas geradas |
|---|---|
| `nota alta` | Nota ≥ 70 |
| `score acima de 60` · `nota > 60` | Nota ≥ 60 |
| `nota baixa` | Nota < 40 |
| `sem nota` | Sem nota ainda |
| `sem contato há 15 dias` · `parados há mais de 15 dias` | Último contato há 15+ dias (inclui "sem contato") |
| `nunca contatado` · `sem contato` | Sem contato registrado |
| `contato esta semana` | Último contato nos últimos 7 dias |
| `aberto em novembro` · `entrou em novembro` | Abertura: 01/11/2017 a 30/11/2017 (o ano é o da data de referência) |
| `aberto depois de 1/10` · `entrada a partir de outubro` | Abertura ≥ 01/10/2017 |
| `há mais de 90 dias no pipeline` · `aberto há mais de 90 dias` | Dias desde a abertura > 90 |
| `não iniciado` · `sem data de abertura` | Abertura vazia (Não iniciado) |
| `varejo` · `setor varejo` · `retail` | Setor: varejo |
| `empresas grandes` · `porte pequeno` | Porte: grande / pequena |
| `sem empresa` | Empresa: não preenchida |
| `Hottechi` | Empresa: Hottechi |
| `GTX Pro` · `série MG` | Produto: GTX Pro / Série: MG |
| `do Darcel` · `vendedor Anna` | Vendedor: Darcel Schlecht / Anna Snelling (manager e admin) |
| `time da Cara` | Manager: Cara Losch (admin) |
| `região leste` · `East` | Região: East (admin) |
| `super hot` · `quentes` | Ícone: super hot |
| `em risco` · `esfriando` | Ícone: em risco de esfriar |
| `esfriou` · `parados` | Ícone: esfriou |
| `sem contato principal` | Contato principal: não preenchido |
| `para focar` · `requalificar` · `desistir` | Ação sugerida: … |
| `abertos` · `ganhos` · `perdidos` | Estágio (só Leads) |
| `prospecção` · `em negociação` | Estágio: … |
| `fechados em 2017` · `ganhos em 2017` · `fechou em março` | Estágio: Fechado + Fechamento em … (só Leads) |
| `novo lead` · `novos leads` · `atendimento` · `em atendimento` | Estágio: Novo lead / Atendimento (O-31) |
| `valor acima de 3000` · `mais de 5 mil` | Valor esperado ≥ 3.000 / ≥ 5.000 |
| `#urgente` · `tag urgente` · `sem tag` | Tag: urgente / Sem tag |
| `com comentário` | Tem comentário |
| `nota alta sem contato há 15 dias do time da Cara` | Nota ≥ 70 · Último contato há 15+ dias · Manager: Cara Losch |
| `varejo grande xyz` | Setor: varejo · Porte: grande · Contém "xyz" |

- **Faixas de nota:** alta ≥ 70, média 40–69, baixa < 40. Os cortes ficam em `config_parametros` e devem ser revistos quando o score for decidido.
- **Sinônimos** (setores em português, regiões, estágios): uma tabela fixa no código, testada frase a frase. A tabela de exemplos acima vira o teste.
- **Etiquetas → consulta:** o servidor recebe as etiquetas (não a frase), valida com zod e monta a consulta. A frase original vai só para o link.

## 6. Funções e regras

Regras comuns a todas as escritas:
- passam pelo servidor e por uma função no banco;
- gravam `usuario_id` e `correlation_id`, e o gatilho de auditoria guarda antes e depois (ARQ-04, BD-04);
- nenhuma apaga nada;
- a resposta na tela é imediata ("Salvo") e, quando a ação tem desfazer, aparece "Desfazer" por 10 segundos.

| Função | Quem pode (tela) | Validação | Auditoria e registros | Desfazer |
|---|---|---|---|---|
| **Cadastrar lead** (Novo lead) | todos; o vendedor cadastra para si, manager e admin escolhem o vendedor | produto existente (obrigatório); empresa existente ou vazia; nome do deal (padrão "Empresa · Produto"); contato opcional; estágio Prospecção (padrão) ou Em negociação (pede a data de abertura); vendedor existente | `core_deals` insert; id gerado pelo banco | "Desfazer" por 10 s marca o deal como Perdido com motivo "cadastro desfeito"; depois disso, o caminho é encerrar |
| **Importar CSV** | manager e admin | por linha, conforme [DESENHO-CRM.md](DESENHO-CRM.md): colunas do `sales_pipeline`, FKs existentes, datas e valores coerentes, id repetido no arquivo recusado | `core_deals` insert por linha + `system_importacoes`; reimportar não duplica (`on conflict do nothing`) | Não há desfazer em massa: os deals importados são encerrados como Perdido em lote, filtrando pela importação |
| **Mudar de estágio** (arrastar ou seletor) | todos; reabrir só manager e admin | transições da tabela 2.6 | `core_deals` update por `core_mudar_estagio` | 10 s |
| **Encerrar** (Ganho / Perdido) | todos | Ganho pede valor inteiro > 0; Perdido pede confirmação e motivo (**[P14]**); só deal aberto (BE-02) | `core_deals` update (`estagio`, `close_date` = data do negócio, `close_value`) | 10 s; depois disso, **reabrir** só manager e admin |
| **Preencher empresa** | todos | só entre as contas cadastradas (decisão (a) em aberto) | `core_deals` update | 10 s |
| **Registrar contato e ações** (Liguei, Requalifiquei, Desisti) | todos | só deal aberto; nota opcional até 280 caracteres | `acao_registros` insert; o gatilho atualiza `ultimo_contato_em` | 10 s (update `desfeita_em`) |
| **Comentar** | todos | texto de 1 a 1.000 caracteres; sem HTML | `acao_comentarios` insert | o autor edita (fica "editado"; o texto anterior fica na auditoria) |
| **Apagar comentário** (remoção lógica) | autor, manager e admin | confirmação | `acao_comentarios` update de `removido_em` e `removido_por`; o comentário sai da tela e da linha do tempo e continua no banco; a remoção fica na auditoria | 10 s; depois disso, só o admin, pela auditoria |
| **Editar nome do deal** | todos | 1 a 120 caracteres | `core_deals` update | 10 s |
| **Adicionar ou trocar contato** | todos | nome obrigatório (1 a 120); cargo, e-mail (formato válido) e telefone opcionais; o contato fica na empresa do deal (ou sem empresa, se o deal não tiver) | `core_contatos` insert/update e `core_deals.contato_id` update; na auditoria, e-mail e telefone aparecem mascarados (ARQ-04) | 10 s |
| **Aplicar ou remover tag** | todos aplicam e removem | só tags existentes e ativas; no máximo 10 tags por deal | `acao_deal_tags` insert; remover = update `removida_em` | 10 s |
| **Criar tag** | manager e admin **[P7]** | nome de 1 a 30 caracteres, único sem diferenciar maiúsculas; cor escolhida entre 6 tokens do tema (FE-03, nada de hex) | `config_tags` insert | arquivar a tag (update `ativa = false`) |
| **Ações em lote** | manager e admin; o vendedor, nos próprios deals **[P8]** | ver abaixo | `system_lotes` + uma linha de auditoria por deal, com o mesmo `correlation_id` | "Desfazer este lote" por 24 h (ver abaixo) |

### 6.1 Ações em lote (tela Leads)

**Seleção:**
- Marcar linhas, ou **Selecionar os N do filtro**. Neste caso, o servidor recalcula a lista com as mesmas etiquetas na hora de aplicar, para não agir sobre o que o filtro não mostra mais.
- Até **500 deals por lote** (parâmetro em `config_parametros`). Acima disso: "Selecione até 500 por vez; refine o filtro."

**Ações disponíveis:**
- Aplicar tag; remover tag.
- Adicionar o mesmo comentário em todos.
- Mover Prospecção → Em negociação (data de abertura = hoje no relógio do CRM).
- Encerrar como Perdido.
- Ganho em lote não existe, porque cada deal tem o próprio valor.

**Confirmação:** antes de aplicar, a tela mostra o que vai acontecer, com a quantidade e 5 exemplos ("Aplicar a tag #urgente em 128 leads"). O botão repete a ação e o número.

**Execução:** tudo numa transação: aplica em todos ou em nenhum. Os deals que não se aplicam são pulados e contados no resultado (ex.: encerrar um deal já fechado): "120 encerrados, 8 já estavam fechados."

**Desfazer este lote:** durante 24 h, o próprio autor, o manager ou o admin desfaz o lote. A função lê o "antes" da auditoria e devolve cada deal ao estado anterior, desde que ele não tenha mudado depois. Os que mudaram são pulados e listados.

## 7. Estados comuns (FE-06)

Toda tela tem carregando, vazio, erro, só leitura e sem permissão, como nas seções 2.8, 3.5 e 4.6. Regras gerais:
- Nenhum erro cru: frase simples com o próximo passo. O código para suporte (`correlation_id`) fica em "Ver detalhes".
- Conflito de versão (duas pessoas no mesmo deal): "Este deal foi alterado por Cara Losch às 14:32. Recarregue para ver a versão atual." (409).
- Limite de taxa (BE-06): "Muitas mudanças seguidas. Espere alguns segundos e tente de novo."

## 8. O que o banco precisa (derivado destas três telas)

Esta seção atualiza o modelo de [DESENHO-ACOES.md](DESENHO-ACOES.md). Segue BD-01 (prefixos, snake_case, plural), BD-02 (FK com índice e `on delete restrict`), BD-03 (RLS sem política pública) e BD-05 (dinheiro em inteiro de dólar).

### 8.1 Tabelas

| Tabela | Situação | Colunas que as telas exigem |
|---|---|---|
| `core_escritorios` | já desenhada | `nome` |
| `core_managers` | já desenhada | `nome`, `escritorio_nome` FK |
| `core_vendedores` | já desenhada | `nome`, `manager_nome` FK |
| `core_produtos` | **muda** | `nome`, `serie`, `preco` **int** (BD-05) |
| `core_contatos` | **nova** | `id`, `conta_nome` FK `core_contas` (nulo para contato de deal sem empresa), `nome`, `cargo`, `email`, `telefone`, `criado_por` FK, `criado_em`, `atualizado_em`, `atualizado_por` FK, `inativo_em` (não há DELETE) |
| `core_contas` | **muda** | `nome`, `setor`, `ano_fundacao`, `receita_milhoes` numeric (é medida, não dinheiro do CRM), `funcionarios`, `porte` (pequena/media/grande, gravado na carga a partir dos tercis), `pais`, `empresa_mae_nome` FK |
| `core_deals` | **muda** | as colunas já desenhadas, mais: `nome` (1–120; preenchido na migração); `contato_id` FK `core_contatos`; `motivo_perda` e `motivo_perda_detalhe` (se a [P14] aprovar); `close_value` **int**; `data_abertura` date (= `engage_date` na carga; data do negócio quando passa para Em negociação); `ultimo_contato_em` date (mantida por gatilho); `criado_em` timestamptz (nulo nos 8.800 do dataset); `criado_por` FK `config_usuarios`; `importacao_id` FK `system_importacoes` (nulo fora de importação) |
| `config_usuarios` | já desenhada | sem mudança |
| `config_parametros` | já desenhada | novas chaves: `data_referencia`, `faixas_nota`, `limite_lote`, `max_tags_por_deal`, `icone_cortes` (15, 106 e 138 dias; R$ 3.000), `dias_sem_contato_risco` (14), `prioridades_visiveis` (5), `meta_prioridades_dia` (10), `dias_pulado_alerta` (3) |
| `config_tags` | **nova** | `id`, `nome` (único sem diferenciar maiúsculas), `cor_token` (um dos 6 tokens), `ativa`, `criada_por` FK `config_usuarios`, `criada_em` |
| `score_execucoes`, `score_deals`, `score_componentes`, `score_motivos` | já desenhadas | `score_deals.valor_esperado` **int** |
| `acao_registros` | **muda** | as já desenhadas, mais `data_negocio` date (relógio do CRM, [P6]); `acao` passa a aceitar também `prioridade_feita` e `prioridade_pulada` (Painel, 4.5) |
| `acao_prioridades` | **nova** | a lista do dia, montada na primeira abertura e estável até o dia acabar: `id`, `usuario_id` FK, `data_negocio`, `posicao`, `opportunity_id` FK, `criado_em`; único (`usuario_id`, `data_negocio`, `opportunity_id`) |
| `acao_comentarios` | **nova** | `id`, `opportunity_id` FK, `usuario_id` FK, `texto` (1–1.000), `data_negocio`, `criado_em`, `editado_em`, `removido_em`, `removido_por` FK (remoção lógica: "apagar" na tela) |
| `acao_deal_tags` | **nova** | `id`, `opportunity_id` FK, `tag_id` FK, `usuario_id` FK, `criado_em`, `removida_em`, `removida_por` FK; índice único parcial (`opportunity_id`, `tag_id`) onde `removida_em is null` |
| `system_auditoria` | já desenhada | mais `lote_id` FK `system_lotes` (nulo fora de lote) |
| `system_eventos` | já desenhada | novos tipos: `lote_aplicado`, `lote_desfeito`, `filtro_nao_entendido` (só a contagem, para melhorar o interpretador) |
| `system_importacoes` | desenhada em DESENHO-CRM | sem mudança |
| `system_lotes` | **nova** | `id`, `usuario_id` FK, `tipo` (tag, remover_tag, comentario, avancar_estagio, encerrar_perdido), `parametros` jsonb, `etiquetas` jsonb (o filtro usado), `quantidade`, `aplicados`, `pulados`, `correlation_id`, `criado_em`, `desfeito_em`, `desfeito_por` FK |

Total: 22 tabelas: as 15 de DESENHO-ACOES, `system_importacoes` (de DESENHO-CRM) e 6 novas (`core_contatos`, `config_tags`, `acao_comentarios`, `acao_deal_tags`, `acao_prioridades`, `system_lotes`).

Acrescentado pela aba Contas e pelo repasse (a #2 consolida em `solution/db/`):

| Tabela | Situação | Colunas |
|---|---|---|
| `score_contas_padrao` | **nova** (aba Contas) | `execucao_id` FK, `conta_nome` FK, `bonus` (0–20), `na_janela` (bool), `intervalo_tipico_dias`, `mes_habitual`, `proxima_compra_em`, `explicacao`, `calculado_em`; chave (`execucao_id`, `conta_nome`). Calculado pelo score todo domingo |
| `acao_repasses` | **nova** (repasse) | `opportunity_id` FK, `de_vendedor` FK, `para_vendedor` FK, `motivo`, `faixa_tempo`, `fit_de`, `fit_para`, `criado_em` |
| `system_avisos` | **nova** (repasse) | `usuario_id` FK, `tipo`, `texto`, `opportunity_id` FK (nulo), `criado_em`, `lido_em` |
| `config_parametros` | novas chaves | `fit_minimo_furar_fila` (75), `repasse` (faixas de tempo sem contato e penalidade no roteamento) |
| `core_contas` | criação e edição pela tela | functions `core_salvar_conta` (insert ou update, auditado) e leitura `core_buscar_contas(etiquetas, ordem)` com as agregações da lista |

### 8.2 Chaves estrangeiras novas (todas com índice e `on delete restrict`)

| De | Para |
|---|---|
| `core_deals.contato_id` | `core_contatos.id` |
| `core_contatos.conta_nome` | `core_contas.nome` |
| `core_contatos.criado_por`, `.atualizado_por` | `config_usuarios.id` |
| `core_deals.criado_por` | `config_usuarios.id` |
| `core_deals.importacao_id` | `system_importacoes.id` |
| `config_tags.criada_por` | `config_usuarios.id` |
| `acao_comentarios.opportunity_id` | `core_deals.opportunity_id` |
| `acao_comentarios.usuario_id`, `.removido_por` | `config_usuarios.id` |
| `acao_deal_tags.opportunity_id` | `core_deals.opportunity_id` |
| `acao_deal_tags.tag_id` | `config_tags.id` |
| `acao_deal_tags.usuario_id`, `.removida_por` | `config_usuarios.id` |
| `system_lotes.usuario_id`, `.desfeito_por` | `config_usuarios.id` |
| `system_auditoria.lote_id` | `system_lotes.id` |
| `acao_prioridades.usuario_id` | `config_usuarios.id` |
| `acao_prioridades.opportunity_id` | `core_deals.opportunity_id` |

### 8.3 Índices para os filtros e as ordenações

| Índice | Atende |
|---|---|
| `core_deals (estagio, vendedor_nome)` | colunas do Pipeline por perfil |
| `core_deals (data_abertura)` | filtro e ordenação por abertura |
| `core_deals (ultimo_contato_em)` | "sem contato há N dias" |
| `core_deals (close_date)` | "fechou em …" (Leads) |
| `core_contas (setor, porte)` | filtro de perfil |
| `score_deals (execucao_id, score desc)` | ordenação e faixa de nota |
| `acao_deal_tags (tag_id) where removida_em is null` | filtro por tag |
| `acao_comentarios (opportunity_id, criado_em desc) where removido_em is null` | quantidade e lista de comentários |
| `core_contatos (conta_nome)` | contatos da empresa no modal |
| `acao_prioridades (usuario_id, data_negocio, posicao)` | lista do dia no Painel |
| `acao_registros (usuario_id, data_negocio)` | "já marcado hoje" e meta do dia |
| `core_deals (estagio, close_date)` | fechamentos e conversão por janela no Painel |
| `system_auditoria (tabela, registro_id, criado_em)` | linha do tempo do deal (já desenhado) |

A busca "Contém …" não tem índice de texto: 8.800 linhas cabem numa varredura. Rever acima de 100 mil (pg_trgm).

### 8.4 Views

- `score_deals_atuais`: as notas da execução ativa (`config_parametros.execucao_ativa`).
- `core_painel_janelas`: para um escopo (vendedor, time ou todos) e uma data, os números dos cartões nas janelas de hoje, 30 dias e 30 dias antes. Calculada na consulta, sem tabela de resumo: 8.800 linhas cabem com folga. Rever com materialização se a base crescer muito.
- `core_deals_visao`: o deal com nome, contato principal, equipe, perfil da empresa, nota atual e faixa, ícone (2.4), ação sugerida, marcadores, tags ativas (lista), quantidade de comentários não apagados e "atualizado depois da nota". É a fonte de leitura do Pipeline e de Leads; o Painel usa as functions de agregação.

### 8.5 Functions

Todas as de escrita recebem `p_usuario_id` e `p_correlation_id`, fazem `set_config` para a auditoria e recusam deal inexistente ou fechado quando a regra pede deal aberto.

| Function | Tipo | Usada por |
|---|---|---|
| `core_buscar_deals(p_etiquetas jsonb, p_escopo jsonb, p_ordem text, p_limite int, p_cursor text)` | leitura (`stable`) | Pipeline (por coluna) e Leads; devolve as linhas e o total |
| `core_resumir_colunas(p_etiquetas, p_escopo)` | leitura | cabeçalho das colunas (quantidade e soma do valor esperado) |
| `core_criar_deal` | escrita | Novo lead |
| `core_importar_deals` | escrita | Importar CSV |
| `core_painel_numeros(p_escopo, p_data)` | leitura | os 8 cartões do Painel, com as variações (lê `core_painel_janelas`) |
| `core_painel_funil(p_escopo)` | leitura | Situação do funil, em quantidade e valor |
| `acao_prioridades_do_dia(p_usuario_id)` | leitura e escrita | devolve a lista do dia; na primeira chamada do dia, monta e grava em `acao_prioridades` (regra 4.5) |
| `acao_marcar_prioridade(p_usuario_id, p_correlation_id, p_opportunity_id, p_resultado, p_nota)` | escrita | ✓ ou ✗: grava em `acao_registros` e devolve o próximo item da fila |
| `core_linha_do_tempo(p_opportunity_id)` | leitura | modal: junta dataset, auditoria, ações e comentários não apagados, em ordem |
| `core_mudar_estagio(p_opportunity_id, p_versao, p_para, p_valor, p_motivo)` | escrita | arrastar e seletor; aplica a tabela 2.6 |
| `core_atualizar_deal` | escrita | nome, empresa e contato principal |
| `core_salvar_contato` | escrita | adicionar ou editar contato (insert ou update em `core_contatos`) |
| `core_encerrar_deal` / `core_reabrir_deal` | escrita | chamadas por `core_mudar_estagio` (Ganho, Perdido, reabrir) |
| `acao_registrar` / `acao_desfazer` | escrita | Liguei, Requalifiquei, Desisti |
| `acao_comentar` / `acao_editar_comentario` / `acao_remover_comentario` / `acao_restaurar_comentario` | escrita | comentários; remover = remoção lógica; restaurar = "Desfazer" dos 10 s e recuperação pelo admin |
| `config_criar_tag` / `config_arquivar_tag` | escrita | tags |
| `acao_aplicar_tag` / `acao_remover_tag` | escrita | tags no deal |
| `system_executar_lote(p_tipo, p_parametros, p_ids text[], p_etiquetas)` | escrita | lote; recusa acima do limite |
| `system_desfazer_lote(p_lote_id)` | escrita | "Desfazer este lote" (24 h) |

### 8.6 Triggers

| Trigger | Em | Faz |
|---|---|---|
| `system_auditar` (after insert/update) | `core_deals`, `core_contas`, `core_contatos` (e-mail e telefone mascarados), `config_usuarios`, `config_parametros`, `config_tags`, `acao_registros`, `acao_comentarios`, `acao_deal_tags`, `acao_prioridades`, `system_lotes` | grava antes, depois, usuário, papel, momento, `correlation_id` e `lote_id`; recusa a escrita sem usuário ou `correlation_id` |
| `system_bloquear_delete` (before delete) | todas as tabelas | recusa qualquer DELETE (junto com o `revoke delete, truncate`) |
| `core_marcar_atualizacao` (before update) | `core_deals` | preenche `atualizado_em` e `atualizado_por`; confere a versão enviada (conflito → erro tratado como 409) |
| `acao_atualizar_ultimo_contato` (after insert/update) | `acao_registros` | recalcula `core_deals.ultimo_contato_em` com o contato mais recente não desfeito |
| `acao_limitar_tags` (before insert) | `acao_deal_tags` | recusa acima de `max_tags_por_deal` tags ativas no deal |
| `core_validar_contato` (before insert/update) | `core_deals` | recusa contato de outra empresa: o `conta_nome` do contato tem que ser o do deal ou nulo |

## 9. Perguntas para o Leandro

| # | Pergunta | Proposta |
|---|---|---|
| P1 | Pipeline = deals abertos em colunas; Leads = a base inteira com cadastro, importação, lote, tags e comentários? | Sim |
| P2 | "Perfil" no filtro é o perfil da empresa (setor e porte)? | Sim; só existe para os deals com empresa |
| P3 | Porte por funcionários ou por receita? | Funcionários (tercis da limpeza) |
| P4 | Os 500 Prospecting do dataset não têm data de abertura. Ficam sem data ou recebem uma? | Ficam sem data ("Não iniciado"), filtráveis; nada é inventado |
| P5 | O dataset não tem contatos. "Último contato" nasce vazio para todos, ou usa `engage_date` como primeiro contato dos deals em negociação? | Usar `engage_date` como primeiro contato dos 1.589 em negociação (o dataset define como o início da negociação) e deixar vazio nos Prospecting; os contatos registrados no CRM atualizam a partir daí. O que conta como contato: Liguei e Requalifiquei |
| P6 | Relógio do CRM: "hoje" é 31/12/2017 enquanto o CRM estiver em modo demonstração? | Sim, com a data do negócio separada do momento real (auditoria) |
| P7 | Quem cria tags novas? | Manager e admin; o vendedor aplica as que existem |
| P8 | O vendedor pode usar ações em lote nos próprios deals? | Sim, com o mesmo limite de 500 |
| P9 | Desfazer cadastro (10 s) = encerrar como Perdido com motivo "cadastro desfeito"? | Sim (não há DELETE) |
| P10 | Quem pode reabrir deal encerrado? | Manager e admin (já estava em aberto) |
| P11 | Nome do deal: campo editável preenchido na migração como "Empresa · Produto" (ou "Sem empresa · Produto")? | Sim |
| P12 | Contato: tabela nova de contatos da empresa, com um contato principal por deal, que nasce vazio ("+ Adicionar contato")? | Sim; o contato pode existir sem empresa enquanto o deal não tiver empresa |
| P13 | Ícones: super hot (15–106 dias e ticket ≥ R$ 3.000: 66 deals), em risco (107–138 dias: 141) e esfriou (> 138 dias: 1.291, ícone cinza)? Ou um ícone de risco só, juntando os dois últimos (1.432 deals, 69% dos abertos)? | Três ícones, para o alerta de risco continuar raro |
| P14 | Ao encerrar como Perdido (ou descartar), pedir o motivo? | Sim, lista curta obrigatória (preço, concorrente, sem orçamento, sem resposta, outro + texto) |
| P15 | "Em reais": o dataset está em dólar, e converter exigiria uma cotação que não existe nos dados. Manter US$? | **Decidido pelo Leandro: reais, com os mesmos números, sem conversão.** O CRM mostra "R$" em todas as telas (formatador único `dinheiro` em `src/lib/calculos.ts`) |
| P16 | Trocar "atendimentos no momento" (não existe no dataset) por "Em risco de esfriar"? | Sim; "Contatos registrados hoje" entra depois, quando houver uso |
| P17 | Prioridades do dia do manager e do admin: os deals do escopo em risco ou super hot, por valor? | Sim; para o vendedor, a lista vem da nota |
| P18 | ✓ = "trabalhei hoje" e ✗ = "pulei hoje", sem mudar o deal? O ✓ conta como contato? Alerta depois de 3 dias pulado? | Sim; o ✓ não conta como contato (há "Liguei" no item); alerta depois de 3 dias |
| P19 | Quem cria e edita empresa? | Os três perfis, com auditoria; o nome não muda depois de criado |
| P20 | Repasse: quais faixas de tempo sem contato disparam o repasse, e qual a penalidade? | A #3 fecha os números; a tela só mostra o resultado |
