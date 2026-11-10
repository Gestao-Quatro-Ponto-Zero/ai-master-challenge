# G4 Sight: especificação das telas Pipeline e Leads

> Especificação para aprovação. Nada de código nem de banco. Marco 1 da decisão 25: especificar as telas e derivar delas o modelo de dados.
> Segue as premissas de desenvolvimento aprovadas (ARQ, BD, BE e FE). Referências: [DESENHO-ACOES.md](DESENHO-ACOES.md) (usuários, escrita e auditoria), [DESENHO-CRM.md](DESENHO-CRM.md) (importação CSV) e [DESENHO-NEXT.md](DESENHO-NEXT.md) (estrutura e marca).
> As perguntas para o Leandro estão marcadas **[P1]**, **[P2]**… e reunidas no fim.

## 0. Interpretação e números de partida

**[P1] Interpretação a confirmar:**
- **Pipeline** = os deals abertos (Prospecting e Engaging) em colunas por estágio, para trabalhar o dia.
- **Leads** = a base inteira de deals (abertos e fechados), com cadastro, importação, ações em lote, tags e comentários.
- "Lead" e "deal" são a mesma linha de `sales_pipeline`. A tela Leads chama de lead; a ficha e o Pipeline chamam de deal.

**[P2] "Perfil" no filtro = perfil da empresa** (setor e porte). Só existe para deals com empresa: 664 dos 2.089 abertos (32%) e todos os 6.711 fechados.

O que o dataset tem (dados limpos, data de referência 31/12/2017):

| Medida | Valor |
|---|---|
| Deals na base | 8.800 (2.089 abertos: 500 Prospecting e 1.589 Engaging; 6.711 fechados: 4.238 Won e 2.473 Lost) |
| Abertos sem empresa | 1.425 (68%); nenhum fechado está sem empresa |
| Prospecting sem data de entrada | 500 (todos) |
| Período | `engage_date` de 20/10/2016 a 27/12/2017; `close_date` de 01/03/2017 a 31/12/2017 |
| Time | 35 vendedores (30 com deals), 6 managers, 3 regiões |
| Maior pipeline aberto | Darcel Schlecht, 194 deals; o menor é Wilburn Farren, com 31 |
| Setores | 10 (marketing, entertainment, software, technology, services, retail, employment, telecommunications, medical, finance) |
| Histórico de contatos | **não existe** no dataset |

## 1. Peças comuns às duas telas

### 1.1 Cartão do deal (Pipeline) e linha do lead (Leads)

As duas telas mostram os mesmos dados, em formatos diferentes.

```
┌──────────────────────────────────────────────────┐
│ 82  ▓▓▓▓▓▓▓░░░   Focar                ⚠ Esfriando │  nota, barra dos componentes, ação sugerida, marcador
│ GTX Pro · Hottechi                                │  produto · empresa (ou "Sem empresa")
│ technology · grande                               │  perfil da empresa (some se não houver empresa)
│ US$ 3.064 esperado   ·   entrou há 47 dias        │
│ Último contato: há 3 dias  (ou "Sem contato")     │
│ Anna Snelling                     #urgente  +2    │  vendedor (só manager/admin) · até 2 tags
└──────────────────────────────────────────────────┘
```

### 1.2 Origem de cada dado visível

Legenda: **D** = vem do dataset · **C** = calculado · **N** = dado novo do CRM (nasce vazio).

| Dado na tela | Tipo | Origem exata | Observação |
|---|---|---|---|
| ID do deal | D | `sales_pipeline.opportunity_id` → `core_deals.opportunity_id` | Só em "Ver detalhes". Deal criado no CRM recebe um id de 8 caracteres (A–Z, 0–9), no mesmo formato |
| Produto | D | `sales_pipeline.product` → `core_deals.produto_nome` → `core_produtos.nome` | "GTXPro" já corrigido para "GTX Pro" na limpeza |
| Série do produto | D | `products.series` → `core_produtos.serie` | Filtro e ficha |
| Preço de tabela | D | `products.sales_price` → `core_produtos.preco` | Inteiro em dólar (BD-05) |
| Empresa | D | `sales_pipeline.account` → `core_deals.conta_nome` | Nula em 1.425 abertos: mostra "Sem empresa" e oferece "Preencher empresa" |
| Setor | D | `accounts.sector` → `core_contas.setor` | Mostrado em português na tela (ex.: "varejo" para retail); o valor gravado continua o do dataset |
| Porte | C | faixa de `accounts.employees` → `core_contas.funcionarios`: pequena (até 1.428), média (até 4.540) e grande | Tercis calculados na limpeza. **[P3]** Porte por funcionários (proposta) ou por receita (`accounts.revenue`)? |
| Vendedor | D | `sales_pipeline.sales_agent` → `core_deals.vendedor_nome` | |
| Manager e região | D | `sales_teams.manager`, `sales_teams.regional_office` → `core_vendedores.manager_nome` → `core_managers.escritorio_nome` | |
| Estágio | D | `sales_pipeline.deal_stage` → `core_deals.estagio` | Na tela: Prospecção, Em negociação, Ganho e Perdido |
| Data de entrada | D/N | `sales_pipeline.engage_date` → `core_deals.data_entrada`. Deal criado no CRM: a data de criação | Os 500 Prospecting do dataset ficam **sem data de entrada**. **[P4]** |
| Dias no pipeline | C | `data_referencia − data_entrada` | "Sem data" quando não há entrada |
| Último contato | N | o registro mais recente de contato em `acao_registros` → `core_deals.ultimo_contato_em` | O dataset não tem contatos: sem a proposta da **[P5]**, nasce vazio para os 8.800 |
| Lead score (0–100) | C | `score_deals.score` da execução ativa (gerado em Python) | Só para deals abertos. Sem nota (deal novo ou importado depois da rodada): "Sem nota ainda". As regras dependem da decisão do score (decisão 10, em aberto) |
| Componentes e motivos da nota | C | `score_componentes`, `score_motivos` | Na ficha do deal e na barra do cartão; nomes finais vêm da decisão do score |
| Ação sugerida | C | `score_deals.acao_sugerida` (focar, requalificar, desistir) | Selo do cartão |
| Marcadores | C | `score_deals.marcadores` (esfriando, sem_conta, sem_data) | Ex.: ⚠ Esfriando |
| Valor esperado | C | `score_deals.valor_esperado` | Inteiro, calculado no servidor (BD-05) |
| Valor de fechamento | D | `sales_pipeline.close_value` → `core_deals.close_value` | Só em Won; Lost = 0 |
| Data de fechamento | D | `sales_pipeline.close_date` → `core_deals.close_date` | Só em Won e Lost |
| "Atualizado depois da nota" | C | `core_deals.atualizado_em > score_execucoes.gerado_em` | Avisa que a nota é de antes da última mudança |
| Tags | N | `acao_deal_tags` + `config_tags` | Nascem vazias |
| Comentários (quantidade e texto) | N | `acao_comentarios` | Nascem vazios |
| Quem mudou e quando | N | `system_auditoria` | Histórico na ficha do deal |

### 1.3 Relógio do CRM

**[P6]** O dataset termina em 31/12/2017, mas as ações no CRM acontecem hoje. Proposta: enquanto o CRM estiver em modo demonstração, "hoje" é a data de referência (`config_parametros.data_referencia` = 31/12/2017).
- Idade, dias sem contato e filtros de data contam a partir dela.
- Contato, comentário e deal registrados agora ganham duas datas: a **data do negócio** (a data de referência, usada nas contas) e o momento real (usado na auditoria).
- Sem isso, um contato registrado hoje apareceria "8 anos depois" de todos os outros dados.

### 1.4 O que cada perfil vê (vale para as duas telas)

| | Vendedor | Manager | Admin |
|---|---|---|---|
| Deals | os dele | os do time | todos |
| Filtros de vendedor, manager e região | escondidos | vendedor (só do time) | todos |
| Coluna/linha "vendedor" | escondida | visível | visível |
| Ações | as dele, nos deals que vê | também importação e lote do time | também importação, lote geral e criação de tags |

O servidor não bloqueia por dono do deal (decisão 16, BD-04). O perfil decide o que a tela oferece.

## 2. Tela Pipeline

### 2.1 Objetivo e ação principal

- **Objetivo:** trabalhar o dia. Ver os deals abertos por estágio, na ordem da prioridade, e mover cada um para frente.
- **Ação principal (FE-02, uma por tela):** **Abrir o próximo deal**. Abre a ficha do deal de maior nota, dentro do filtro atual, que ainda não teve contato registrado hoje. Dois toques: o botão e a ação na ficha (FE-05).

### 2.2 Layout

```
┌ topo: G4 Sight · Pipeline | Leads · usuário (Anna Snelling, vendedora) · Trocar perfil ─────────────┐
│ [ Filtrar: ex. "nota alta sem contato há 15 dias"                 ]   Ordenar: Nota ▾   [Abrir o próximo deal] │
│ Entendi assim:  (Nota ≥ 70 ×)  (Sem contato há 15+ dias ×)                     Limpar filtros        │
├──────────────────────────────────────────┬──────────────────────────────────────────┤
│ Prospecção · 18 deals · US$ 24.300       │ Em negociação · 94 deals · US$ 151.200   │
│ ┌ cartão ┐                              │ ┌ cartão ┐                               │
│ ┌ cartão ┐                              │ ┌ cartão ┐                               │
│ … 50 por coluna · Mostrar mais          │ … 50 por coluna · Mostrar mais           │
└──────────────────────────────────────────┴──────────────────────────────────────────┘
   ao arrastar um cartão aparecem à direita duas áreas: [Ganho] [Perdido]
```

- Duas colunas: **Prospecção** e **Em negociação**. O cabeçalho de cada uma mostra a quantidade e a soma do valor esperado no filtro.
- Até 50 cartões por coluna, na ordem escolhida, e "Mostrar mais" de 50 em 50. Em negociação chega a 1.589 deals para o admin.
- Ganhos e Perdidos não são colunas: ao arrastar, aparecem duas áreas de soltar para encerrar o deal.
- Clicar no cartão abre a ficha do deal (painel lateral, `?deal=ID`): nota com componentes e motivos, dados da tabela 1.2, ações, tags, comentários e histórico.
- **Celular:** as colunas viram duas abas (Prospecção | Em negociação) com a lista, e mover de estágio é pelo botão na ficha.

### 2.3 Filtros e ordenação

- **Campo livre** (seção 4) e as etiquetas que ele gera.
- **Atalhos ao lado do campo**, que geram as mesmas etiquetas: Nota (alta, média, baixa), Data de entrada, Último contato, Perfil (setor e porte), Vendedor (só manager e admin).
- Os filtros ficam no link (`/pipeline?f=...`), para mandar para alguém e para o "Voltar" do navegador.
- **Ordenação dentro da coluna:** Nota (padrão, maior primeiro), Valor esperado, Dias sem contato, Dias no pipeline, Data de entrada.

### 2.4 Funções nesta tela

| Função | Como |
|---|---|
| Mover de estágio | Arrastar de Prospecção para Em negociação, ou botão na ficha. Pede a data de entrada, que vem preenchida com "hoje" (relógio do CRM) |
| Encerrar | Soltar em Ganho (pede o valor de fechamento) ou em Perdido (pede confirmação) |
| Registrar contato e ações | Na ficha: Liguei, Requalifiquei, Desisti |
| Preencher empresa | Na ficha, para deals sem empresa: busca entre as 85 cadastradas |
| Tags e comentários | Na ficha |
| Lote | Não há nesta tela; o lote fica em Leads, para o Pipeline ficar simples |

As regras de cada função estão na seção 5.

### 2.5 Estados

| Estado | O que aparece |
|---|---|
| Carregando | as duas colunas com 4 cartões-esqueleto cada; o campo de filtro já pode ser usado |
| Vazio (sem deals abertos) | "Você não tem deals abertos. Cadastre um lead ou importe uma planilha em Leads." + botão "Ir para Leads" |
| Vazio (filtro sem resultado) | "Nenhum deal com estes filtros." + as etiquetas e "Limpar filtros" |
| Erro | "Não foi possível carregar o pipeline. Tente de novo em alguns segundos." + "Tentar de novo"; o código para suporte fica em "Ver detalhes" |
| Só leitura (banco fora, BE-05) | faixa: "Modo somente leitura: mudanças estão desligadas agora." Cartões não arrastam e os botões de ação somem. Os dados vêm do arquivo de reserva |
| Sem permissão | sem perfil escolhido: vai para "Quem é você?" e volta |

## 3. Tela Leads

### 3.1 Objetivo e ação principal

- **Objetivo:** cuidar da base inteira, abertos e fechados: encontrar, cadastrar, importar, marcar com tags, comentar e agir em lote sobre o que o filtro encontrar.
- **Ação principal:** **Novo lead** (cadastro). Importar e as ações em lote são secundárias, mas sempre à vista.

### 3.2 Layout

```
┌ topo ───────────────────────────────────────────────────────────────────────────────┐
│ [ Filtrar: ex. "varejo grande ganhos em 2017"                     ]   [Importar CSV]  [Novo lead] │
│ Entendi assim: (Setor: varejo ×) (Porte: grande ×) (Estágio: Ganho ×) (Fechou em 2017 ×)        │
│ 1.204 leads · US$ 2,1 mi fechados                                                     │
├──┬──────────────────────┬──────────────┬───────────────┬──────┬────────────┬────────┬────────┬──────┤
│☐ │ Lead                 │ Vendedor     │ Estágio       │ Nota │ Valor      │ Entrada│ Últ.   │ Tags │
│  │ produto · empresa    │              │               │      │            │        │ contato│ 💬 n │
├──┼──────────────────────┼──────────────┼───────────────┼──────┼────────────┼────────┼────────┼──────┤
│☐ │ GTX Pro · Hottechi   │ Anna Snelling│ Em negociação │ 82   │ US$ 3.064 e│ 14/11  │ há 3 d │ #urg │
│☐ │ MG Special · Cancity │ Moses Frase  │ Ganho         │  —   │ US$ 55     │ 20/10  │ —      │      │
└──┴──────────────────────┴──────────────┴───────────────┴──────┴────────────┴────────┴────────┴──────┘
 50 por página · Mostrar mais
 ── ao marcar linhas, sobe uma barra: "12 selecionados · Selecionar os 1.204 do filtro · [Aplicar tag] [Comentar] [Mais ▾]"
```

- **Colunas:** Lead (produto · empresa), Vendedor (só manager e admin), Estágio, Nota (só abertos; fechados mostram "—"), Valor (esperado nos abertos; fechamento nos ganhos), Entrada, Último contato, Tags e a quantidade de comentários.
- **Perfil da empresa** (setor · porte) aparece abaixo do nome da empresa, em texto menor.
- Clicar na linha abre a mesma ficha do deal do Pipeline.
- 50 linhas por vez, e o total no topo vem do mesmo filtro.
- **Celular:** a tabela vira lista de cartões (o mesmo cartão do Pipeline, com o estágio), e a seleção é por toque longo.

### 3.3 Filtros e ordenação

- O mesmo campo livre da seção 4. Aqui ele aceita também estágio e resultado (abertos, ganhos, perdidos), data de fechamento, produto, série, tag e "com comentário".
- **Atalhos:** Estágio, Nota, Data de entrada, Último contato, Perfil, Vendedor, Tag.
- **Ordenação por coluna:** Nota, Valor, Entrada, Último contato, Fechamento, Vendedor e Lead (A–Z). Padrão: abertos primeiro, por nota; depois os fechados, do mais recente.

### 3.4 Funções nesta tela

Cadastro, importação CSV, ações em lote, tags e comentários. Regras na seção 5.

### 3.5 Estados

| Estado | O que aparece |
|---|---|
| Carregando | a tabela com 8 linhas-esqueleto; o total aparece quando chega |
| Vazio (base vazia) | "Ainda não há leads. Importe uma planilha ou cadastre o primeiro." + [Importar CSV] [Novo lead] |
| Vazio (filtro sem resultado) | "Nenhum lead com estes filtros." + as etiquetas e "Limpar filtros" |
| Erro | "Não foi possível carregar os leads. Tente de novo." + "Tentar de novo" e "Ver detalhes" |
| Só leitura | faixa de somente leitura. O arquivo de reserva só tem os abertos, então a tela avisa: "Mostrando só os 2.089 deals abertos; a base completa volta quando o banco voltar." Cadastro, importação, lote, tags e comentários ficam escondidos |
| Sem permissão | vendedor tentando importar ou aplicar lote fora do que a tela oferece: "Esta ação é feita pelo manager ou pelo admin." |

## 4. Filtro em campo livre: interpretador por regras

**Como funciona:**
- Uma função pura (`src/lib/interpretar-filtro.ts`), sem IA, que transforma a frase em **etiquetas**. Cada etiqueta é um filtro estruturado.
- As etiquetas aparecem embaixo do campo ("Entendi assim:"), e cada uma pode ser removida.
- O que o interpretador não reconhece vira a etiqueta **Contém "…"**, uma busca de texto em produto, empresa, vendedor, id, tag e comentário.
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
| `entrou em novembro` | Entrada: 01/11/2017 a 30/11/2017 (o ano é o da data de referência) |
| `entrou depois de 1/10` · `entrada a partir de outubro` | Entrada ≥ 01/10/2017 |
| `há mais de 90 dias no pipeline` | Dias no pipeline > 90 |
| `sem data de entrada` | Data de entrada vazia |
| `varejo` · `setor varejo` · `retail` | Setor: varejo |
| `empresas grandes` · `porte pequeno` | Porte: grande / pequena |
| `sem empresa` | Empresa: não preenchida |
| `Hottechi` | Empresa: Hottechi |
| `GTX Pro` · `série MG` | Produto: GTX Pro / Série: MG |
| `do Darcel` · `vendedor Anna` | Vendedor: Darcel Schlecht / Anna Snelling (manager e admin) |
| `time da Cara` | Manager: Cara Losch (admin) |
| `região leste` · `East` | Região: East (admin) |
| `esfriando` | Marcador: esfriando |
| `para focar` · `requalificar` · `desistir` | Ação sugerida: … |
| `abertos` · `ganhos` · `perdidos` | Estágio (só Leads) |
| `prospecção` · `em negociação` | Estágio: … |
| `ganhos em 2017` · `fechou em março` | Estágio: Ganho + Fechamento em … (só Leads) |
| `valor acima de 3000` · `mais de 5 mil` | Valor esperado ≥ 3.000 / ≥ 5.000 |
| `#urgente` · `tag urgente` · `sem tag` | Tag: urgente / Sem tag |
| `com comentário` | Tem comentário |
| `nota alta sem contato há 15 dias do time da Cara` | Nota ≥ 70 · Último contato há 15+ dias · Manager: Cara Losch |
| `varejo grande xyz` | Setor: varejo · Porte: grande · Contém "xyz" |

- **Faixas de nota:** alta ≥ 70, média 40–69, baixa < 40. Os cortes ficam em `config_parametros` e devem ser revistos quando o score for decidido.
- **Sinônimos** (setores em português, regiões, estágios): uma tabela fixa no código, testada frase a frase. A tabela de exemplos acima vira o teste.
- **Etiquetas → consulta:** o servidor recebe as etiquetas (não a frase), valida com zod e monta a consulta. A frase original vai só para o link.

## 5. Funções e regras

Regras comuns a todas as escritas:
- passam pelo servidor e por uma função no banco;
- gravam `usuario_id` e `correlation_id`, e o gatilho de auditoria guarda antes e depois (ARQ-04, BD-04);
- nenhuma apaga nada;
- a resposta na tela é imediata ("Salvo") e, quando a ação tem desfazer, aparece "Desfazer" por 10 segundos.

| Função | Quem pode (tela) | Validação | Auditoria e registros | Desfazer |
|---|---|---|---|---|
| **Cadastrar lead** (Novo lead) | todos; o vendedor cadastra para si, manager e admin escolhem o vendedor | produto existente (obrigatório); empresa existente ou vazia; estágio Prospecção (padrão) ou Em negociação (pede a data de entrada); vendedor existente | `core_deals` insert; id gerado pelo banco | "Desfazer" por 10 s marca o deal como Perdido com motivo "cadastro desfeito"; depois disso, o caminho é encerrar |
| **Importar CSV** | manager e admin | por linha, conforme [DESENHO-CRM.md](DESENHO-CRM.md): colunas do `sales_pipeline`, FKs existentes, datas e valores coerentes, id repetido no arquivo recusado | `core_deals` insert por linha + `system_importacoes`; reimportar não duplica (`on conflict do nothing`) | Não há desfazer em massa: os deals importados são encerrados como Perdido em lote, filtrando pela importação |
| **Mover de estágio** | todos | Prospecção → Em negociação (pede a data de entrada); voltar para Prospecção não é permitido | `core_deals` update | 10 s |
| **Encerrar** (Ganho / Perdido) | todos | Ganho pede valor inteiro > 0; Perdido pede confirmação; só deal aberto (BE-02) | `core_deals` update (`estagio`, `close_date` = data do negócio, `close_value`) | 10 s; depois disso, **reabrir** só manager e admin |
| **Preencher empresa** | todos | só entre as contas cadastradas (decisão (a) em aberto) | `core_deals` update | 10 s |
| **Registrar contato e ações** (Liguei, Requalifiquei, Desisti) | todos | só deal aberto; nota opcional até 280 caracteres | `acao_registros` insert; o gatilho atualiza `ultimo_contato_em` | 10 s (update `desfeita_em`) |
| **Comentar** | todos | texto de 1 a 1.000 caracteres; sem HTML | `acao_comentarios` insert | o autor edita (fica "editado") ou arquiva (some da lista, com "Ver arquivados"); nada é apagado |
| **Aplicar ou remover tag** | todos aplicam e removem | só tags existentes e ativas; no máximo 10 tags por deal | `acao_deal_tags` insert; remover = update `removida_em` | 10 s |
| **Criar tag** | manager e admin **[P7]** | nome de 1 a 30 caracteres, único sem diferenciar maiúsculas; cor escolhida entre 6 tokens do tema (FE-03, nada de hex) | `config_tags` insert | arquivar a tag (update `ativa = false`) |
| **Ações em lote** | manager e admin; o vendedor, nos próprios deals **[P8]** | ver abaixo | `system_lotes` + uma linha de auditoria por deal, com o mesmo `correlation_id` | "Desfazer este lote" por 24 h (ver abaixo) |

### 5.1 Ações em lote (tela Leads)

**Seleção:**
- Marcar linhas, ou **Selecionar os N do filtro**. Neste caso, o servidor recalcula a lista com as mesmas etiquetas na hora de aplicar, para não agir sobre o que o filtro não mostra mais.
- Até **500 deals por lote** (parâmetro em `config_parametros`). Acima disso: "Selecione até 500 por vez; refine o filtro."

**Ações disponíveis:**
- Aplicar tag; remover tag.
- Adicionar o mesmo comentário em todos.
- Mover Prospecção → Em negociação (data de entrada = hoje no relógio do CRM).
- Encerrar como Perdido.
- Ganho em lote não existe, porque cada deal tem o próprio valor.

**Confirmação:** antes de aplicar, a tela mostra o que vai acontecer, com a quantidade e 5 exemplos ("Aplicar a tag #urgente em 128 leads"). O botão repete a ação e o número.

**Execução:** tudo numa transação: aplica em todos ou em nenhum. Os deals que não se aplicam são pulados e contados no resultado (ex.: encerrar um deal já fechado): "120 encerrados, 8 já estavam fechados."

**Desfazer este lote:** durante 24 h, o próprio autor, o manager ou o admin desfaz o lote. A função lê o "antes" da auditoria e devolve cada deal ao estado anterior, desde que ele não tenha mudado depois. Os que mudaram são pulados e listados.

## 6. Estados comuns (FE-06)

Toda tela tem carregando, vazio, erro, só leitura e sem permissão, como nas seções 2.5 e 3.5. Regras gerais:
- Nenhum erro cru: frase simples com o próximo passo. O código para suporte (`correlation_id`) fica em "Ver detalhes".
- Conflito de versão (duas pessoas no mesmo deal): "Este deal foi alterado por Cara Losch às 14:32. Recarregue para ver a versão atual." (409).
- Limite de taxa (BE-06): "Muitas mudanças seguidas. Espere alguns segundos e tente de novo."

## 7. O que o banco precisa (derivado destas duas telas)

Esta seção atualiza o modelo de [DESENHO-ACOES.md](DESENHO-ACOES.md). Segue BD-01 (prefixos, snake_case, plural), BD-02 (FK com índice e `on delete restrict`), BD-03 (RLS sem política pública) e BD-05 (dinheiro em inteiro de dólar).

### 7.1 Tabelas

| Tabela | Situação | Colunas que as telas exigem |
|---|---|---|
| `core_escritorios` | já desenhada | `nome` |
| `core_managers` | já desenhada | `nome`, `escritorio_nome` FK |
| `core_vendedores` | já desenhada | `nome`, `manager_nome` FK |
| `core_produtos` | **muda** | `nome`, `serie`, `preco` **int** (BD-05) |
| `core_contas` | **muda** | `nome`, `setor`, `ano_fundacao`, `receita_milhoes` numeric (é medida, não dinheiro do CRM), `funcionarios`, `porte` (pequena/media/grande, gravado na carga a partir dos tercis), `pais`, `empresa_mae_nome` FK |
| `core_deals` | **muda** | as colunas já desenhadas, mais: `close_value` **int**; `data_entrada` date (= `engage_date` na carga; data do negócio no cadastro); `ultimo_contato_em` date (mantida por gatilho); `criado_em` timestamptz (nulo nos 8.800 do dataset); `criado_por` FK `config_usuarios`; `importacao_id` FK `system_importacoes` (nulo fora de importação) |
| `config_usuarios` | já desenhada | sem mudança |
| `config_parametros` | já desenhada | novas chaves: `data_referencia`, `faixas_nota`, `limite_lote`, `max_tags_por_deal` |
| `config_tags` | **nova** | `id`, `nome` (único sem diferenciar maiúsculas), `cor_token` (um dos 6 tokens), `ativa`, `criada_por` FK `config_usuarios`, `criada_em` |
| `score_execucoes`, `score_deals`, `score_componentes`, `score_motivos` | já desenhadas | `score_deals.valor_esperado` **int** |
| `acao_registros` | **muda** | as já desenhadas, mais `data_negocio` date (relógio do CRM, [P6]) |
| `acao_comentarios` | **nova** | `id`, `opportunity_id` FK, `usuario_id` FK, `texto` (1–1.000), `data_negocio`, `criado_em`, `editado_em`, `arquivado_em`, `arquivado_por` FK |
| `acao_deal_tags` | **nova** | `id`, `opportunity_id` FK, `tag_id` FK, `usuario_id` FK, `criado_em`, `removida_em`, `removida_por` FK; índice único parcial (`opportunity_id`, `tag_id`) onde `removida_em is null` |
| `system_auditoria` | já desenhada | mais `lote_id` FK `system_lotes` (nulo fora de lote) |
| `system_eventos` | já desenhada | novos tipos: `lote_aplicado`, `lote_desfeito`, `filtro_nao_entendido` (só a contagem, para melhorar o interpretador) |
| `system_importacoes` | desenhada em DESENHO-CRM | sem mudança |
| `system_lotes` | **nova** | `id`, `usuario_id` FK, `tipo` (tag, remover_tag, comentario, avancar_estagio, encerrar_perdido), `parametros` jsonb, `etiquetas` jsonb (o filtro usado), `quantidade`, `aplicados`, `pulados`, `correlation_id`, `criado_em`, `desfeito_em`, `desfeito_por` FK |

Total: 20 tabelas: as 15 de DESENHO-ACOES, `system_importacoes` (de DESENHO-CRM) e 4 novas (`config_tags`, `acao_comentarios`, `acao_deal_tags`, `system_lotes`).

### 7.2 Chaves estrangeiras novas (todas com índice e `on delete restrict`)

| De | Para |
|---|---|
| `core_deals.criado_por` | `config_usuarios.id` |
| `core_deals.importacao_id` | `system_importacoes.id` |
| `config_tags.criada_por` | `config_usuarios.id` |
| `acao_comentarios.opportunity_id` | `core_deals.opportunity_id` |
| `acao_comentarios.usuario_id`, `.arquivado_por` | `config_usuarios.id` |
| `acao_deal_tags.opportunity_id` | `core_deals.opportunity_id` |
| `acao_deal_tags.tag_id` | `config_tags.id` |
| `acao_deal_tags.usuario_id`, `.removida_por` | `config_usuarios.id` |
| `system_lotes.usuario_id`, `.desfeito_por` | `config_usuarios.id` |
| `system_auditoria.lote_id` | `system_lotes.id` |

### 7.3 Índices para os filtros e as ordenações

| Índice | Atende |
|---|---|
| `core_deals (estagio, vendedor_nome)` | colunas do Pipeline por perfil |
| `core_deals (data_entrada)` | filtro e ordenação por entrada |
| `core_deals (ultimo_contato_em)` | "sem contato há N dias" |
| `core_deals (close_date)` | "fechou em …" (Leads) |
| `core_contas (setor, porte)` | filtro de perfil |
| `score_deals (execucao_id, score desc)` | ordenação e faixa de nota |
| `acao_deal_tags (tag_id) where removida_em is null` | filtro por tag |
| `acao_comentarios (opportunity_id, criado_em desc)` | quantidade e lista de comentários |

A busca "Contém …" não tem índice de texto: 8.800 linhas cabem numa varredura. Rever acima de 100 mil (pg_trgm).

### 7.4 Views

- `score_deals_atuais`: as notas da execução ativa (`config_parametros.execucao_ativa`).
- `core_deals_visao`: o deal com equipe, perfil da empresa, nota atual, ação sugerida, marcadores, tags ativas (lista), quantidade de comentários e "atualizado depois da nota". É a única fonte de leitura das duas telas.

### 7.5 Functions

Todas as de escrita recebem `p_usuario_id` e `p_correlation_id`, fazem `set_config` para a auditoria e recusam deal inexistente ou fechado quando a regra pede deal aberto.

| Function | Tipo | Usada por |
|---|---|---|
| `core_buscar_deals(p_etiquetas jsonb, p_escopo jsonb, p_ordem text, p_limite int, p_cursor text)` | leitura (`stable`) | Pipeline (por coluna) e Leads; devolve as linhas e o total |
| `core_resumir_colunas(p_etiquetas, p_escopo)` | leitura | cabeçalho das colunas (quantidade e soma do valor esperado) |
| `core_criar_deal` | escrita | Novo lead |
| `core_importar_deals` | escrita | Importar CSV |
| `core_atualizar_deal` | escrita | mover estágio, preencher empresa |
| `core_encerrar_deal` / `core_reabrir_deal` | escrita | Ganho, Perdido, reabrir (manager e admin) |
| `acao_registrar` / `acao_desfazer` | escrita | Liguei, Requalifiquei, Desisti |
| `acao_comentar` / `acao_editar_comentario` / `acao_arquivar_comentario` | escrita | comentários |
| `config_criar_tag` / `config_arquivar_tag` | escrita | tags |
| `acao_aplicar_tag` / `acao_remover_tag` | escrita | tags no deal |
| `system_executar_lote(p_tipo, p_parametros, p_ids text[], p_etiquetas)` | escrita | lote; recusa acima do limite |
| `system_desfazer_lote(p_lote_id)` | escrita | "Desfazer este lote" (24 h) |

### 7.6 Triggers

| Trigger | Em | Faz |
|---|---|---|
| `system_auditar` (after insert/update) | `core_deals`, `core_contas`, `config_usuarios`, `config_parametros`, `config_tags`, `acao_registros`, `acao_comentarios`, `acao_deal_tags`, `system_lotes` | grava antes, depois, usuário, papel, momento, `correlation_id` e `lote_id`; recusa a escrita sem usuário ou `correlation_id` |
| `system_bloquear_delete` (before delete) | todas as tabelas | recusa qualquer DELETE (junto com o `revoke delete, truncate`) |
| `core_marcar_atualizacao` (before update) | `core_deals` | preenche `atualizado_em` e `atualizado_por`; confere a versão enviada (conflito → erro tratado como 409) |
| `acao_atualizar_ultimo_contato` (after insert/update) | `acao_registros` | recalcula `core_deals.ultimo_contato_em` com o contato mais recente não desfeito |
| `acao_limitar_tags` (before insert) | `acao_deal_tags` | recusa acima de `max_tags_por_deal` tags ativas no deal |

## 8. Perguntas para o Leandro

| # | Pergunta | Proposta |
|---|---|---|
| P1 | Pipeline = deals abertos em colunas; Leads = a base inteira com cadastro, importação, lote, tags e comentários? | Sim |
| P2 | "Perfil" no filtro é o perfil da empresa (setor e porte)? | Sim; só existe para os deals com empresa |
| P3 | Porte por funcionários ou por receita? | Funcionários (tercis da limpeza) |
| P4 | Os 500 Prospecting do dataset não têm data de entrada. Ficam "sem data" ou recebem uma data? | Ficam sem data, filtráveis por "sem data de entrada"; nada é inventado |
| P5 | O dataset não tem contatos. "Último contato" nasce vazio para todos, ou usa `engage_date` como primeiro contato dos deals em negociação? | Usar `engage_date` como primeiro contato dos 1.589 em negociação (o dataset define como o início da negociação) e deixar vazio nos Prospecting; os contatos registrados no CRM atualizam a partir daí. O que conta como contato: Liguei e Requalifiquei |
| P6 | Relógio do CRM: "hoje" é 31/12/2017 enquanto o CRM estiver em modo demonstração? | Sim, com a data do negócio separada do momento real (auditoria) |
| P7 | Quem cria tags novas? | Manager e admin; o vendedor aplica as que existem |
| P8 | O vendedor pode usar ações em lote nos próprios deals? | Sim, com o mesmo limite de 500 |
| P9 | Desfazer cadastro (10 s) = encerrar como Perdido com motivo "cadastro desfeito"? | Sim (não há DELETE) |
| P10 | Quem pode reabrir deal encerrado? | Manager e admin (já estava em aberto) |
