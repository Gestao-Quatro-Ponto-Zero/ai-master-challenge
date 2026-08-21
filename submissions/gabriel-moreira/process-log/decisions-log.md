# Decisions Log

Registro cronológico das decisões de produto/técnicas tomadas durante o challenge, e por quê. Diferente do [`process-log/narrative.md`](../process-log/narrative.md) — que documenta *como a IA foi usada* — este arquivo documenta *o que foi decidido e a lógica por trás*, para servir de base ao `architecture.md` e ao README final.

Regra deste arquivo: nenhuma entrada é escrita sem a decisão ter vindo de mim (Gabriel). O Claude Code pode propor opções, mas quem decide e assina a entrada sou eu.

---

## 2026-08-19 — Decisões de design da solução (consolidadas na sessão de grilling)

**Contexto:** análise exploratória (validação de AUC, testes de permutação, análise de dados) convergiram para uma conclusão: não há sinal firmográfico em win/loss (AUC 0.50 em todos os modelos testados, p=0.31–0.97 nos testes de permutação para agent/product/sector/account). Mas há sinal forte em **valor** (R²=0.98) — a diferença entre um negócio bom e um ruim é de até **400×**.

### Stack e interface

**Decisão:** FastAPI + React, com `scoring/` como módulo Python puro importado pelo API, CLI e script de validação. Streamlit foi descartado em favor de React para demonstrar engenharia sólida e separação clara entre scoring e apresentação.

**Por quê:** uma implementação de scoring usável em três contextos (API, CLI, validação) é mais credível que um número em uma UI de prateleira. React força uma arquitetura limpa e demonstra que o código é mantível por outro dev — critério explícito do challenge.

**Scope:** web app que um vendedor abre e vê o pipeline priorizado. Sem auth (documentado como limitation). Sem persistência além de em-memória pandas (Supabase é o path de produção, registrado em "o que precisaria pra escalar").

### Três lanes de pipeline

**Decisão:** separar os 2.089 abertos em três vistas:
- **Prioridades** (Engaging ≤138d): 298 deals, ~14 por agent, ordenados por score
- **Novos** (Prospecting): 500 deals, apenas `sales_agent` e `product` disponíveis, ordenados por valor
- **Zumbis** (>138d): 1.291 deals, com filtros, labeled como "fora de qualquer padrão histórico"

**Por quê:** nenhum deal na história fechou após 138d (n=2 à margem). Jogar esses na lista principal mascara a capacidade real. Routing explícito os torna acionáveis — o gerente vê "1.291 congelados US$2,3M" e toma uma decisão de purga. Prospecting sem `engage_date` não pode ter urgência imputada; rank-by-value é o único componente defensável.

### Lógica de scoring

**Decisão:** `score = 0.50·valor + 0.40·urgência + 0.10·zona`, com normalizações fixas e constantes:

| Componente | Fórmula | Refs fixas |
|---|---|---|
| `valor` | log₁₀(list_price) normalizado | $55→0, $26.768→100 |
| `urgência` | (age_days / 138) × 100 | age ∈ [9, 138] em produção |
| `zona` | 0 se age≤14d, 100 se 14<age≤138 | — |

**Por quê:** 
- Valor × Urgência quebra a 62-way tie entre os 62 deals de MG Special a $55 — mantém o rastreamento claro
- Pesos 50/40/10 dizem que valor e expiry importam igualmente, quando dados não determinam — é a decisão business default
- Referências fixas (não percentis) garantem que um deal não mude de tier porque outro foi adicionado ao funil — estabilidade temporal é mais valioso que balanceamento de bucket
- Zona de 3 etapas honra a bimodal distribution dos ciclos (picos em 0–19d e 60–90d, vale em 20–39d) — não fixa uma curva em ruído

**O que não entra:** setor (p=0.971 no teste qui-quadrado), região (p=0.604), gerente (p=0.786), vendedor (p=0.264), produto como preditor de win (p=0.372), account revenue (p=0.629), employees (p=0.778), year_established (p=0.368). Todos testados, nenhum significa. `MULT_PORTE` foi removido porque a razão close_value/list_price é 1.00 ± 0.01 em todas as portes — o efeito que parecia vir do porte é product mix, já capturado em `sales_price`.

### Tiers

**Decisão:** Diamante / Ouro / Prata / Bronze em cutoffs **congelados: 74 / 62 / 47**, derivados uma única vez da distribuição observada no funil atual.

**Por quê:** percentis recompem a cada dia que um deal entra/sai, fazendo com que o mesmo score migre de Diamante para Ouro porque o pipeline mudou — destroi confiança em uma ferramenta operacional. Cutoffs fixos significam movimento de tier = mudança real do deal, não artefato do método.

Mapeamento literal de metal → tier: Diamante=azul marinho com border gold (visual priority) / Ouro=#B9915B / Prata=#F5F4F3 / Bronze=brown.

### Explicabilidade

**Decisão:** cada deal mostra a aritmética: `Valor +37 · Urgência +37 · Estágio +10` + uma sentença templada em PT-BR + hover com *"Nenhum deal na história fechou após 138 dias."*

**Por quº:** a chief de RevOps pediu "o vendedor precisa entender por que." Componentes separados permitem que alguém discorde do peso e aponte a linha exata. Hover justifica o bound de 138d com uma referência a dados. Acima disso, cria uma narrativa que o vendedor vai repetir: não é "este deal é ruim," é "este deal tá fora do padrão histórico."

### KPI tiles e header

**Decisão:** seis tiles no topo: 8.800 negócios · 63,2% win rate · $10.005.534 receita ganha · $3.138.648 EV em aberto · **1.291 congelados >138d** (#AF4332 alarme) · maior negócio $30.288, com subtitle: 2016-10-20 → 2017-12-27 · 423 dias no deal mais velho aberto.

**Por quê:** os primeiros cinco são contexto. O sexto (1.291 congelados em vermelho-brick) é o action item que deveria impulsionar a gerência de primeiro escalão — é US$2,3M preso e 74% do funil. Sutil é uma economia de espaço; dados técnicos (data range, age) ficam lá para quem quer saber, sem ruído no painel principal.

### Validação e morte do modelo

**Decisão:** o script de validação (Q10) roda o modelo treinado + testes de permutação. Mostra AUC 0.505, p-values por agent/product/sector, e uma conclusão: "nenhum atributo firmográfico desloca a taxa de ganho; os dados justificam um score de valor, não um score de probabilidade."

**Por quê:** mata a tentação futura de "se a AUC subir para 0.70, usamos um modelo ML." Deixa claro por que se escolheu o caminho que se escolheu, e torna impossível para alguém depois descartar a premissa sem re-validar. Qualidade do challenge: submetendo a prova de que você testou sua própria ideia e a matou, não a prova de que um Jupyter notebook faz um número bonito.

### Segurança

**Decisão:** sem autenticação (documentado). Security review scoped a:
- CORS não `*`
- input validation no endpoint de scoring
- sem stack traces em erros 5xx
- dependências pinned
- sem file-path parameters

**Por quê:** API sem auth é incoerente com uma UI que também não tem, em uma ferramenta interna rodando em rede interna. "Production-ready" seria horas em teatro — auth middleware, JWT, refresh tokens — quando o challenge pede "rodar," não "preparar para produção." Limitação é honesta no README.

### O que ficou de fora e por quê

- **ML preditivo (AUC 0.50):** testado, validado, morto. Documentado. Não cabe.
- **Comportamento / intent score:** sem dados comportamentais nos CSVs. `analise-lead-scoring.md` §6 mapeia os campos que precisariam ser coletados; é o next step.
- **Rebalanceamento de portfolio:** "39,6% do esforço em 5,4% da receita" é insight, não prescrição. Fica em Gestão; vendedor não pode agir.
- **Exportação de CRM:** Zumbis tab exporta CSV de `opportunity_id` para bulk delete no CRM. Sem write-back — não temos um CRM para escrever.
- **Simulação de porte:** lead novo (sem account ainda) tem um "score de potencial de conta" separado. Prototipado; pode virar segundo MVP.

---

## 2026-08-19 — Revisão da fórmula, estados, RBAC, exportação e DoD de testes

**Contexto:** recebi uma especificação estatística mais rigorosa da fórmula de priorização, calibrada nos mesmos 6.711 negócios fechados, e pedi ao Claude Code para revisar o OpenSpec e a documentação de arquitetura para refletir essa versão — validando antes se ainda atende ao brief do challenge 003 e se a fórmula fica mais assertiva.

### Fórmula: de soma ponderada 0–100 para PRIORIDADE em dólares

**Decisão:** substituir `score = 0,50·valor + 0,40·urgência + 0,10·zona` (soma ponderada, componentes log-normalizados) por `PRIORIDADE = p̂ × VALOR × URGÊNCIA`, com `p̂` calculado por encolhimento hierárquico (*empirical Bayes*, `k` derivado estatisticamente, não escolhido), VALOR em dólares reais (preço de tabela × porte) e URGÊNCIA como `risco(idade)` — probabilidade real de resolução em 30 dias, suavizada por regressão isotônica. SCORE (0–100 de exibição) é o percentil de PRIORIDADE **contra a distribuição histórica de negócios ganhos** (os 4.238 "Won", cada um com PRIORIDADE calculada na idade real do fechamento) — não contra o funil aberto corrente.

**Por quê:** é mais assertiva porque cada peça agora tem uma origem estatística verificável (nada de pesos 50/40/10 escolhidos por não haver dado para otimizar), e PRIORIDADE em dólares é mais interpretável do que uma soma adimensional — "US$ 4.482 em risco de se resolver nos próximos 30 dias" comunica mais que "82,5 pontos". O achado mais contra-intuitivo se mantém e fica mais explícito: `p_ganho(t)` **sobe** com a idade, não desce — o que a idade consome é a janela de decisão (57 dias = metade das vitórias já ocorreram), não a chance de ganhar.

**Reversão explícita de duas decisões anteriores**, registrada para não parecer inconsistência não-intencional:
- **`MULT_PORTE` volta a entrar no score.** Antes eu tirei porque `close_value/list_price` por porte era ≈1,00 (preço praticado não muda por porte). A nova análise mede a decomposição de variância do *valor fechado* — produto+porte explica 98,7% contra 98,3% só produto — um ganho marginal real de 0,4pp que eu não tinha visto antes. Com prior neutro (1,00) quando a conta é desconhecida, essa é a peça que torna literal o "fazer lead scoring mesmo sem account": a ausência de conta custa no máximo 8%, nunca a viabilidade do score.
- **Normalização volta a ter um componente por percentil** (SCORE, não PRIORIDADE). Antes rejeitei percentil inteiro porque instabiliza a posição de um deal quando o funil muda. Minha primeira correção foi congelar o percentil por geração do dataset — funcionava, mas ainda usava o funil aberto como referência. Corrigi de novo (mesmo dia, ver nota abaixo): a referência do percentil é o **histórico de negócios ganhos**, não o funil aberto — uma população fixa que só muda no ciclo trimestral de recalibração. Resolve a instabilidade por completo, e dá ao número um significado direto: "vale mais que X% dos negócios que já viraram receita."

### Estados cruzam CONFIANÇA e SCORE — e absorvem as lanes

**Correção (mesmo dia, apontada por mim depois da primeira versão):** minha primeira proposta fazia ESTADO derivar quase só de CONFIANÇA (D→Desistir, C→Qualificar, B→Engajar, e só dentro de A um corte de SCORE separava Foco urgente de Acompanhar). Eu corrigi: **CONFIANÇA é o quanto devo acreditar no score; ESTADO é a ação recomendada, com base no score E no fundamento do score** — os dois eixos precisam cruzar de verdade, não um servir de critério principal e o outro de desempate só no topo.

**Decisão final:** Diamante/Ouro/Prata/Bronze → **Foco urgente, Acompanhar, Engajar, Qualificar, Desistir**, vindos de uma tabela 4×2 — CONFIANÇA (A/B/C/D) cruzada com SCORE (≥50 ou <50, sendo 50 a mediana da própria distribuição de referência de SCORE, não uma constante extra):

| CONFIANÇA | SCORE ≥ 50 | SCORE < 50 |
|---|---|---|
| A | Foco urgente | Acompanhar |
| B | Acompanhar | Engajar |
| C | Engajar | Qualificar |
| D | Desistir | Desistir |

Isso também absorve as três lanes antigas (Prioridades/Novos/Zumbis), que ficariam redundantes com os estados.

**Por quê a versão corrigida é melhor:** a diagonal faz o cruzamento aparecer de verdade — um SCORE alto com CONFIANÇA B não vira Foco urgente, vira Acompanhar (agir com urgência sobre um número em que não confio totalmente é o próprio risco que CONFIANÇA existe pra sinalizar); um SCORE baixo com CONFIANÇA C não é Desistir, é Qualificar (falta informação, não necessariamente falta valor). CONFIANÇA D é a única regra de mão única — abaixo do suporte histórico dos dados, nenhum SCORE calculado justifica outra ação que não revisão em lote.

### RBAC de 3 níveis, mapeado 1:1 na hierarquia real dos dados

**Decisão:** Sales Agent / Supervisor / Manager mapeados exatamente na hierarquia que já existe em `sales_teams.csv` — 35 agentes (`sales_agent`) → 6 supervisores (`manager`) → 3 managers (um por `regional_office`: Central/East/West). Sem senha: uma tela de seleção de identidade emite um token assinado no servidor com o escopo já resolvido; todo endpoint de dados aplica esse escopo — um filtro de cliente só restringe dentro do escopo, nunca amplia, e pedir fora do escopo dá 403.

**Por quê:** os dados já tinham a hierarquia certa para os três papéis pedidos, sem precisar inventar uma identidade sintética de "admin global". Isolamento "completo" só é verdade se aplicado no servidor — é por isso que a decisão antiga de separar API e UI (em vez de Streamlit) passou a ser um requisito de segurança, não só preferência de arquitetura: um app que manda tudo pro cliente e filtra na tela não isola nada.

**Limitação assumida:** isso é seleção de identidade, não autenticação — não valida senha, então qualquer um pode se passar por qualquer nome da lista. O que está garantido é que, uma vez emitido o token, o escopo é fixo e aplicado no servidor. Produção exigiria SSO/OIDC de verdade.

### Explicação + plano de ação por oportunidade

**Decisão:** cada oportunidade expõe não só a decomposição por componente, mas um texto de plano de ação específico do estado (ex.: Desistir → "revisão em lote com o gestor, fechar ou descartar, não trabalhar individualmente"), gerado por template determinístico a partir dos componentes calculados — nunca por um modelo não determinístico.

**Por quê:** o brief original já pedia "o vendedor precisa entender por que" — isso vai um passo além e responde também "e o que eu faço agora", que é a pergunta real de segunda-feira de manhã. Determinístico porque a alegação central da entrega é auditabilidade; um LLM gerando a explicação quebraria isso.

### CSV do dataset processado, como artefato de arquivo

**Decisão:** a cada carga de dados, o motor de scoring grava um CSV completo (2.089 oportunidades abertas, todos os campos tratados + PRIORIDADE + SCORE + CONFIANÇA + ESTADO + explicação) em disco, para consulta fora da aplicação. Download via API restrito a Manager.

**Por quê:** "consulta posterior" pede um artefato que sobrevive fora da aplicação — auditoria, carregar numa planilha, comparar entre execuções. Diferente da exportação de CSV filtrado que já existia na aba Desistir (essa continua, é outra coisa: IDs para triagem em massa).

### Testes unitários + e2e como parte do Definition of Done

**Decisão:** motor de scoring e resolução de escopo com testes unitários determinísticos; API com testes e2e cobrindo o ciclo completo (identificação → token → listagem respeitando escopo → tentativa fora do escopo → rollup restrito → download restrito), rodando contra uma instância real, não só contra funções isoladas.

**Por quê:** isolamento de dados é o tipo de coisa que quebra silenciosamente — um endpoint que esquece de aplicar o escopo ainda responde 200, só que com o dado errado. Só um teste que faz a requisição HTTP de verdade com um token de escopo restrito pega essa classe de regressão; teste unitário da função de filtro sozinha não pega.

### Validação do fit com o challenge

Revalidei contra `challenges/build-003-lead-scorer/README.md`: a fórmula continua sendo regra+heurística bem fundamentada em dado real (não "ML perfeito"), o vendedor ainda vê "por que" (agora com plano de ação também), o filtro por vendedor/manager/região virou isolamento de dados de verdade em vez de só filtro de UI — bate com o "bônus" explícito do brief, só que mais rigoroso do que o brief pedia. Nenhum dos requisitos mínimos do challenge foi contrariado pela revisão; o que mudou é a fundamentação estatística de PRIORIDADE e a superfície de acesso.

---

## 2026-08-19 — Achados técnicos da implementação (registrados pelo Claude, pendentes de revisão por Gabriel)

**Contexto:** esta entrada documenta três julgamentos técnicos que o Claude Code tomou durante a execução de `/opsx:apply add-lead-scorer` (implementação das 81 tarefas de `tasks.md`), sinalizados aqui em vez de decididos silenciosamente — por não se enquadrarem claramente em "decisão de produto" (onde a regra deste arquivo exige que a decisão venha de Gabriel) nem em "detalhe de implementação puro" (que não precisaria de registro). Ver `process-log/narrative.md`, entrada "Implementação completa via `/opsx:apply`", para o relato completo.

1. **`K_PRODUTO = 4` mantido como constante congelada** apesar de `validation/shrinkage_check.py` — implementado para reproduzir honestamente a fórmula `k = variância_esperada_por_acaso / variância_em_excesso` a partir do zero — mostrar que o nível de produto também colapsa (`k = ∞`) sob recomputação estrita nestes dados, mais fraco que qualquer atributo testado por permutação. Optei por manter a constante já documentada em todo o projeto (e exigida pelos exemplos de referência formais dos specs) em vez de recalcular e colapsar `p̂_produto` para 0,632 constante — o que reverteria uma decisão de design já registrada sem que Gabriel tivesse pedido essa reversão. **Pede confirmação:** manter `k=4` congelado (como está) ou aceitar o achado e simplificar `p̂_produto` para uma constante, atualizando specs e testes de referência.
2. **`lightgbm` substituído por `HistGradientBoostingClassifier`** (scikit-learn) em `validation/` — `lightgbm` falhou ao instalar neste ambiente por exigir `libomp` nativo via Homebrew, o que quebraria "partida por comando único, sem passos manuais" em qualquer máquina sem a lib. Mesmo papel (gradient boosting), sem dependência nativa. Baixo risco, não deveria precisar de reversão.
3. **Preço de GTX Basic no cenário de Prospecting do spec (`specs/lead-scoring/spec.md`) usa US\$ 1.585; o catálogo real (`products.csv`) tem US\$ 550.** Implementação seguiu o dado real. Não afeta nenhum teste formal (a task 2.15 não cobra esse número), mas vale corrigir o texto do spec numa próxima revisão para não ficar como uma inconsistência permanente entre spec e dado.

---

## 2026-08-20 — Refino de UX do pipeline: remoção do RBAC, paginação real, painel de detalhe

**Contexto:** revisão da entrega já validada (formula, ESTADO, RBAC), motivada por cinco pontos de atrito no uso real da ferramenta — identidade como portão de entrada, aba inicial escondendo 80% do funil, idade filtrada por digitação, CONFIANÇA sem legenda, e a linha da tabela sobrecarregada. Proposta formal em `openspec/changes/refine-pipeline-ux/proposal.md`.

### Remoção completa do RBAC — por deleção, não por desligamento

**Decisão:** `api/auth/` inteiro, `routes/identity.py`, `get_scope`, os endpoints `/identify` e `/identities`, o token de sessão assinado (`itsdangerous`) e os testes de isolamento de dados (`api/tests/test_scope_unit.py`) foram apagados — não desativados por flag. Vendedor, gerente e escritório regional deixam de ser identidades com escopo e passam a ser filtros ordinários sobre o funil completo, iguais a produto e confiança. Todo endpoint de dados responde sem cabeçalho `Authorization`.

**Por quê:** a entrada de 2026-08-19 já registrava a limitação de que isso era "seleção de identidade, não autenticação real" — mas o RBAC ainda assim colocava um portão de 44 opções antes de qualquer dado aparecer, e trocar de recorte custava derrubar a sessão inteira. Avaliando o uso real da ferramenta (comparar "o funil todo" com "o time do Melvin" em segundos), o custo de fricção da tela de identidade passou a pesar mais do que o valor de demonstrar isolamento server-side — especialmente porque o dataset é público e de demonstração, sem informação real de cliente, o que a entrada anterior já reconhecia. Mantida a maquinaria "desligável por config" foi descartada deliberadamente: duas superfícies de comportamento para manter e testar, quando a decisão real era remover a funcionalidade.

**Limitação assumida (substitui a anterior):** não há mais nenhum controle de acesso, nem sequer o "isolamento de escopo real, identificação sem senha" que existia antes. Qualquer cliente lê o funil inteiro. Aceitável apenas porque o dataset é público. Produção exigiria SSO/OIDC real e escopo por papel aplicado no servidor — ambos hoje inexistentes, não apenas desligados.

### Paginação no servidor, não no cliente — revertendo a primeira versão deste próprio design

**Decisão:** `GET /deals` passa a paginar (100 por página), ordenar (SCORE/PRIORIDADE/idade, com desempate obrigatório por `opportunity_id`) e filtrar inteiramente no servidor, devolvendo um envelope (`items`, `total`, `page`, `total_pages`, contagem por estado, contagem de excluídas por idade desconhecida) em vez do funil completo. Um módulo de consulta compartilhado (`api/query.py`) resolve filtro/ordenação/paginação uma única vez, reusado por `/deals`, `/kpis`, `/rollup` e a nova exportação de identificadores filtrados.

**Por quê:** a primeira versão deste design (dentro da mesma mudança, revisada antes de chegar à implementação) paginava no cliente — o servidor devolvia o recorte inteiro e o React fatiava em páginas de 100. Revisitada porque o problema real não era paginar, era continuar pagando o custo de trazer 2.089 linhas de JSON a cada filtro, mesmo mostrando só 100. Com o RBAC removido no mesmo passo — e as duas mudanças tocando as mesmas cinco rotas —, fazer as duas separadamente teria significado passar duas vezes pela mesma rota, o cenário exato em que um parâmetro esquecido sobrevive.

### Plano de ação em passos, mantendo o resumo de uma linha

**Decisão:** `scoring/scoring/explicacao.py` ganha `plano_de_acao_passos()` — 2 a 4 passos derivados de ESTADO, com o passo de enriquecimento de cadastro anexado no início quando falta conta e o de revisão em lote anexado no fim quando censurado. `plano_de_acao` (o texto de uma linha já existente, decisão de 2026-08-19) é mantido sem alteração — é o que a coluna atual do CSV consome, e quebrar isso quebraria quem já lê o arquivo.

**Por quê:** o texto de uma linha explica o quê; não dizia o como, passo a passo. Continua determinístico e testado pelo mesmo motivo que a decisão original de 2026-08-19 registrou: auditabilidade — um LLM geraria planos diferentes para o mesmo negócio em execuções diferentes.

### Documentação da entrega tratada como parte da mudança, não como acerto posterior

**Decisão:** `README.md`, `docs/architecture.md` (este arquivo você já está lendo a versão corrigida) e `analise-lead-scoring.md` foram atualizados no mesmo passo que o código, removendo toda descrição de controle de acesso por papel, com verificação final por busca textual pelos termos "escopo", "token", "papel" e "isolamento" em todo `submissions/gabriel-moreira/`.

**Por quê:** uma entrega que descreve um controle de acesso que não existe mais é pior do que uma que nunca teve — lê como omissão ou desonestidade, não como evolução documentada. O risco real desta mudança nunca foi técnico, foi de narrativa: apagar RBAC já testado e destacado no material do desafio exige que a documentação acompanhe a remoção linha por linha, não como tarefa de limpeza para depois.

---

## 2026-08-20 — Redesenho de SCORE/CONFIANÇA/ESTADO, via sessão de grilling (33 perguntas)

**Contexto:** ao revisar a entrega já validada, apontei três problemas de uso: PRIORIDADE em dólares lia como "venda o produto caro", CONFIANÇA D forçava Desistir para 61,8% do funil (dominada por idade, que já é o insumo de URGÊNCIA), e Acompanhar/Engajar davam o mesmo conselho. Pedi uma sessão de grilling ao Claude Code — 33 perguntas em rodadas, cada uma fundamentada em números medidos sobre os dados reais, não em opinião — para redesenhar as três peças sem tocar a fórmula em si.

### PRIORIDADE sai da tela; SCORE vira o único número de prioridade

**Decisão:** PRIORIDADE em dólares deixa de ser exibida e de ordenar a fila. SCORE (percentil 0–100 contra os 4.238 negócios ganhos) passa a ser o único número de prioridade — em tela, como ordenação padrão da API, e como insumo de ESTADO. PRIORIDADE continua calculada e exportada no CSV como valor auditável.

**Por quê:** medido, não suposto — a decomposição da variância de `log(PRIORIDADE)` atribui 87,3% a VALOR e 0,1% a `p̂`; `spearman(PRIORIDADE, preço_tabela) = 0,909`. O preço varia 486,7× entre produtos contra 1,074× de `p̂_produto`. O top 100 da fila antiga não continha uma única oportunidade de GTX Basic, MG Special ou GTX Plus Basic — três produtos que somam 1.190 das 2.089 oportunidades abertas.

### Três hipóteses de refinar o motor, testadas e rejeitadas

Ao investigar se PRIORIDADE deveria condicionar por mais variáveis (setor, produto), pedi para testar cada hipótese por validação cruzada antes de implementar qualquer uma. **As três pioraram a previsão fora da amostra** — reproduzível em `validation/backtest.py`, seções 6–8:

| Hipótese | Resultado (CV 5-fold ou permutação) |
|---|---|
| `p̂` por produto×setor | `logloss` 0,66016 vs. 0,65828 do prior global achatado — pior |
| Curva de aging por produto | `logloss` 0,65525 (0,65275 com encolhimento) vs. 0,64936 da curva global — pior |
| URGÊNCIA por produto | dispersão de medianas 22,0 dias vs. 28,9 dias sob rótulos embaralhados, valor-p 0,64 |

**Por quê manter a fórmula como está:** a curva de aging global é o único modelo que supera o prior achatado em qualquer teste — é o sinal real desta base, e reparti-lo por produto destrói o sinal em vez de refiná-lo. `GTK 500` (25 negócios fechados) nem teria amostra para uma curva própria. Valor do achado está em documentá-lo como resultado negativo reprodutível, não em implementar a hipótese.

### CONFIANÇA vira `min(completude, suporte)`, 0–100 — idade sai por completo

**Decisão:** CONFIANÇA deixa de ser A–D e passa a ser um número 0–100, `min(completude, suporte)`. **completude** é a fração de 5 campos de cadastro observados (engajamento, conta, funcionários, setor, time). **suporte** é `0,75 × s_idade + 0,25 × s_produto`, cada termo saturando em `min(1, n/50)` — sem idade conhecida, usa só o termo de produto (nunca zera o de idade, para não cobrar a mesma ausência duas vezes que completude já cobra).

**Por quê `min` e não média:** testado durante a sessão — 353 oportunidades com completude 100 e suporte 0 pontuariam 50 sob média (empatando com uma oportunidade parcialmente conhecida mas com precedente real), e 25 sob `min`. Conhecer todos os campos de uma oportunidade sem precedente histórico não a torna confiável — a metade mais fraca deve governar.

**Por quê idade sai por completo:** CONFIANÇA media majoritariamente há quanto tempo a oportunidade estava aberta, que já é o insumo de URGÊNCIA — misturar as duas fazia 61,8% do funil (tudo acima de 138 dias) herdar CONFIANÇA D e, por tabela, o estado Desistir.

**Ajuste de completude, mesmo dia:** a primeira versão usava só 2 campos (engajamento, funcionários), o que deixava a escala com só 3 valores possíveis. Pedi para expandir para os 5 campos que descrevem veracidade do cadastro, não só os que a fórmula consome diretamente — setor e time entram em completude mesmo não entrando em `p̂`.

### `revisao_lote` roteado por condição nomeada, não por corte de CONFIANÇA

**Decisão:** a árvore de ESTADO checa `sem_precedente` (nenhum negócio ganho fechou na faixa de idade) **antes** de olhar SCORE ou CONFIANÇA — não como um corte no valor combinado.

**Por quê:** medido durante a sessão — oportunidades novas sem cadastro (Prospecting sem conta) e oportunidades antigas sem precedente se aglomeram em valores adjacentes de CONFIANÇA (20 e 25), em **ordem invertida**. Nenhum corte único de CONFIANÇA separa as duas populações sem misturar oportunidades novas e saudáveis no mesmo balde das realmente abandonadas — testado explicitamente: um corte em 25 capturava 337 oportunidades em Prospecting junto com as antigas.

### ESTADO: árvore de 4 valores, substitui a tabela 4×2 de 5

**Decisão:**
```
1. sem_precedente        -> Revisão em lote
2. SCORE >= 95            -> Priorizar
3. CONFIANÇA < 50          -> Qualificar
4. caso contrário          -> Acompanhar
```
`Engajar` é absorvido por `Acompanhar` (mesmo plano de ação); `Desistir` é substituído por `Revisão em lote` (mesma população, mas roteada por precedente, não por CONFIANÇA, e nomeada como passivo de dados, não como recomendação de abandonar).

**Por quê os cortes:** SCORE ≥ 95 é o percentil 95 da própria distribuição de referência — 63 oportunidades nos dados de teste durante a sessão, contra 28 em p99 (fino demais para uma fila de time). CONFIANÇA < 50 significa "menos da metade do que o score afirma está apoiado em dado observado e precedente" — ancorado no significado, não ajustado por tentativa e erro.

**Distribuição final** sobre as 2.089 oportunidades abertas: Priorizar 54, Acompanhar 283, Qualificar 656, Revisão em lote 1.096 (fila trabalhável: 993).

### Achado incidental durante a implementação: bug em `classificar_porte`

**Achado:** `classificar_porte` só verificava `employees is None`, mas o merge com `accounts.csv` preenche funcionários ausentes com `NaN`, não `None` — e `NaN < limiar` é sempre `False` em Python. Toda oportunidade sem conta (1.425 de 2.089) caía silenciosamente em "Enterprise" (mult_porte 1,06) em vez do prior neutro (1,00) que o requisito de VALOR já prometia desde 2026-08-19.

**Decisão:** corrigido junto com o redesenho (`employees != employees` cobre NaN além de `None`), por afetar diretamente VALOR, PRIORIDADE e a completude de CONFIANÇA das 1.425 oportunidades sem conta. A correção moveu `Priorizar` de 63 para 54 oportunidades — menos oportunidades ultrapassam o percentil 95 sem o multiplicador indevido.

### Correção do cenário incorreto sobre `K_PRODUTO` na spec

**Decisão:** a spec de `scoring-validation` afirmava que o nível de produto reporta `k = 4`. Corrigido para afirmar o que o artefato de fato calcula: variância em excesso `-0,001199`, `k` infinito — o nível de produto colapsa junto com conta×produto e produto×setor. `K_PRODUTO = 4,0` passa a estar documentado explicitamente como aproximação retida por política (a mesma decisão já registrada em 2026-08-19, item 1 dos "achados técnicos"), nunca mais como resultado do cálculo.

**Por quê agora:** o teste existente (`report1.k == report2.k`) só verificava determinismo, nunca finitude — a divergência nunca falhou. `validation/backtest.py` ganhou uma falha visível caso o `k` do nível de produto se torne finito numa recalibração futura, para que a aproximação deixe de ser silenciosamente carregada adiante se a premissa que a sustenta mudar.

---

## 2026-08-20 — Fatores do score em linguagem de negócio + ESTÁGIO na listagem

### `score_fatores`: por que este SCORE, decomposto em frases sem jargão

**Decisão:** o painel de detalhe passa a exibir, na seção "Por que este score", uma lista de 4 frases geradas por template a partir dos mesmos componentes já calculados (`p̂`, VALOR, URGÊNCIA, porte da conta) — sem citar `p̂`, PRIORIDADE ou qualquer nome de variável. Novo campo `score_fatores: list[str]` em `scoring/scoring/explicacao.py::fatores_score()`, consumido por `DealDetailOut` e `ScoreAvulsaOut` (nunca por `OportunidadeOut` — mesma separação já aplicada a `plano_de_acao_passos` e `prioridade`: decomposição e razão ficam no painel de detalhe, não na linha da listagem).

Cada frase cobre um componente:
- **Valor do produto** — tercil do preço de tabela do produto dentro do catálogo de 7 produtos ("maior valor" / "mediano" / "menor valor").
- **Chance de fechamento** — nível de `p̂` (alta / dentro da média / abaixo da média) e, quando Engaging dentro da janela de censura (14–138 dias), menciona o achado contraintuitivo já documentado em 2026-08-19: negócios mais velhos têm chance histórica igual ou maior de fechar, não menor.
- **Urgência** — nível de `risco(t)` traduzido em "tende a se resolver em 30 dias" / "sem pressa extrema" / "tempo não é o fator crítico".
- **Dados da conta** — efeito do porte no multiplicador de VALOR ("eleva" / "reduz um pouco" / "sem conta vinculada, valor médio de mercado").

**Por quê template determinístico, não um resumo por IA:** mesma garantia de auditabilidade do plano de ação (Requirement "Explicabilidade do score e plano de ação") — cada frase é reproduzível a partir do mesmo componente exposto no grid numérico abaixo dela, nunca uma paráfrase não determinística.

**Exportação:** `score_fatores` entra em `EXPORT_COLUMNS` do CSV consolidado, serializado com o mesmo separador `" | "` já usado em `plano_de_acao_passos` — mantém "o número mostrado = o número validado = o número exportado" também para a explicação, não só para os componentes numéricos.

### ESTÁGIO (`deal_stage`) volta a aparecer na listagem

**Decisão:** a fila de trabalho (`DealTable`) ganha uma coluna "Estágio" (`Prospecting`/`Engaging`), entre VALOR e Idade — o campo já existia em `Oportunidade` e no painel de detalhe, só não era renderizado na linha.

**Por quê:** ESTÁGIO explica por que `age_days` é `—` para parte da fila (Prospecting nunca tem idade conhecida) sem exigir abrir o painel de detalhe para cada linha — a mesma leitura que já valia dentro do painel, agora disponível de relance na fila inteira.

---

## 2026-08-21 — Reclassificação de 200 dias, análise de carga e fit por vendedor

**Contexto:** `openspec/changes/add-analise-carga-fit` — proposta completa (proposal/design/specs) revisada antes da implementação. Duas dívidas identificadas: 653 oportunidades (31,3% do funil) abertas há 200+ dias distorciam qualquer análise de carga por vendedor, e não havia nenhuma comparação de carteira entre vendedores nem histórico de desempenho por produto/setor na interface.

### Reclassificação de 200d+ como `Lost`, com recalibração parcial

**Decisão:** oportunidade aberta com idade ≥ 200 dias (constante de política, `IDADE_RECLASSIFICACAO_DIAS`, distinta do limite **observado** de 138 dias) é tratada como `Lost` na carga, em memória — `sales_pipeline.csv` nunca é reescrito. Funil aberto cai de 2.089 para 1.436.

**Duas populações, não uma:** os 653 reclassificados entram em `fechados_calibracao` (alimenta taxa por produto e prior global de p̂ — 7.364 negócios, base rate 63,15% → 57,55%), mas **nunca** em `fechados_organicos` (alimenta as curvas de idade `p_ganho`/`risco` e a censura em 138d — permanece nos 6.711 originais). Alimentar as curvas com os reclassificados ensinaria "negócio velho perde" a partir de rótulos que nós mesmos atribuímos por serem velhos — circularidade pura. `validation/circularity_check.py` audita isso a cada execução: idade máxima orgânica (138) contra idade mínima reclassificada (200) nunca se sobrepõem, e nenhuma linha `reclassificado=True` pode aparecer em `fechados_organicos`.

**Consequência sobre `GLOBAL_WIN_RATE`:** a constante única virou duas — `GLOBAL_WIN_RATE_ORGANICO = 0,632` (censura, normalização de `p_ganho(0)`) e `GLOBAL_WIN_RATE_CALIBRACAO = 0,5755` (prior de encolhimento de p̂_produto). Confundir as duas faria a censura em 138d reverter para o prior errado.

**Achado não previsto pelo design original — nível de PRODUTO deixa de colapsar:** o encolhimento de p̂_produto (`K_PRODUTO = 4,0`, retido por política desde 2026-08-19) supunha que uma recomputação estrita colapsaria o nível de produto (`k = ∞`), como conta×produto e produto×setor. Com a população de calibração recalculada, `GTK 500` cai de n=25/60,0% para n=35/42,86% (−17,14pp, o dobro de qualquer outro produto) e passa a dominar a variância entre produtos: `validation/backtest.py` seção 3 agora deriva `k = 0,697` (finito) para o nível de produto — a amplitude entre produtos sobe de 4,84pp para 16,95pp. `K_PRODUTO = 4,0` continua congelado por política (não muda com esta entrada), mas o backtest agora reporta `AVISO` em vez de `NOTA` nessa seção, e `docs/decisions-log.md` (aqui) registra o motivo para a próxima recalibração trimestral decidir se `K_PRODUTO` deve ser revisto.

### Duas superfícies novas: carga por escritório e fit vendedor×produto/setor

**Decisão:** `scoring/carga.py` compara a contagem de cada vendedor, por ESTADO (`prioritize`/`acompanhar`/`qualificar` — nunca `revisao_lote`), com a média do próprio escritório regional naquele ESTADO. Sobrecarga = `contagem >= 1,5 × média` **e** `contagem >= 5` (piso absoluto — sem ele, `Central/prioritize` com média 0,10 sinalizaria 1 deal como 10× a média). Sobre o funil atual: 12 pares, 8 vendedores, 227 oportunidades.

`scoring/fit.py` calcula a taxa de vitória do vendedor por produto e por setor sobre `fechados_calibracao` (denominador sempre `Won + Lost`), com encolhimento em dois níveis (vendedor → escritório → global, `k_fit = 25`, constante de política). A sugestão de redistribuição (`rank = 0,5×folga + 0,5×fit_normalizado`) exclui os 5 vendedores de `sales_teams` sem nenhuma oportunidade registrada e nunca cruza escritório.

**Achado honesto sobre o fit — `validation/fit_permutation.py`:** o design previa que a mesma derivação de `k` colapsaria (k=∞) para vendedor×produto e vendedor×setor, e que testes de permutação reproduziriam ausência de sinal em ambos. A reprodução real mostra: vendedor×setor indistinguível de acaso (p≈0,20, k derivado=5,45), mas vendedor×produto fica **limítrofe** (p≈0,047, k derivado=3,87) — sinal fraco sobre 178 células testadas, sem correção para múltiplas comparações. `K_FIT = 25` (muito mais conservador que qualquer k derivado) permanece a constante de política; a ressalva estatística acoplada a todo fit exibido continua obrigatória — um p-valor limítrofe e não corrigido não é evidência robusta de mérito individual de vendedor. Registrado aqui em vez de forçar a redação do design a dizer "colapso" quando a reprodução honesta encontrou algo mais nuançado.

**Fronteira de exibição:** o vendedor sugerido aparece só na aba Sobrecarga e no painel de detalhe — nunca na listagem geral de Oportunidades, que recebe apenas o booleano `sobrecarregado` (dourado `#B9915B`, distinto do vermelho `#AF4332` exclusivo de `revisao_lote`). Fit nunca entra em `p̂`, VALOR, URGÊNCIA, PRIORIDADE, SCORE, CONFIANÇA ou ESTADO.

### Correção dos CSVs de análise entregues

**Achado:** os dois CSVs (`analysis_by_product_detailed.csv`, `analysis_by_sector_detailed.csv`) publicados antes desta mudança calculavam `Taxa Vitória % = Won / Total`, com `Total` incluindo `Engaging`+`Prospecting` — 159 de 179 linhas e 219 de 292 linhas incorretas, erro médio 14,89pp (máximo 62,50pp, `Wilburn Farren`/`GTX Plus Basic`: 37,5% publicado vs. 100% real).

**Decisão:** os artefatos passam a ser gerados por `scoring/export.py::build_analysis_table`, a mesma função usada pela API (via `scoring/fit.py::FitContext`) — taxa sempre `Won / (Won + Lost)`, sem coluna `Total`. `validation/denominator_check.py` audita isso a cada execução do backtest (seção 13).

---

## 2026-08-21 — `mult_setor` (ajuste produto×setor sobre p̂) e remoção de `K_PRODUTO`

**Contexto:** `openspec/changes/add-mult-setor` — proposta completa (proposal/design/specs) revisada numa sessão de grilling adversarial (13+ perguntas, 3 rounds) antes da implementação. O produto pediu uma variável de desempenho produto×setor para SCORE e CONFIANÇA, peso limitado a 10-15%. Antes de aceitar, reproduzimos a pergunta: `validation/backtest.py` seção 6 mede condicionar `p̂` por produto×setor via validação cruzada 5-fold sobre os 7.364 negócios de calibração — `logloss` 0,66974 contra 0,66795 do prior achatado por produto (70 células, mediana 86 negócios/célula) — **pior**, de forma monotônica, e o nível colapsa (`k=∞`) sob recomputação estrita. Construir a variável como "aumente `p̂` pela taxa de vitória da célula" embarcaria exatamente o que a validação já provou que piora a previsão.

### `mult_setor`: mesmo molde de `fit.py`, não o condicionamento direto

**Decisão:** `mult_setor(produto, setor)` encolhe a taxa bruta de cada célula produto×setor em direção a `p̂_produto` (não à taxa global) com uma constante de política `K_SETOR = 25` — reaproveitada de `K_FIT`, mesmo papel (sobrepor um colapso, de forma conservadora) — e limita o resultado a **[0,85, 1,15]**. Setor desconhecido (68,7% do funil aberto) → `mult_setor = 1,0`, neutro. `p̂ final = p̂(idade) × mult_setor`, aplicado tanto ao funil aberto quanto à reconstrução da distribuição de referência (testado empiricamente antes de decidir: aplicar só ao funil deslocaria SCORE de forma assimétrica entre numerador e denominador do percentil).

**Por quê não é uma contradição da seção 6 do backtest:** o condicionamento direto testado e rejeitado não tem encolhimento em direção a `p̂_produto` nem teto — é a taxa bruta da célula (ou encolhida em direção à taxa global). `mult_setor` é um mecanismo distinto: encolhimento pesado + teto apertado, o mesmo molde que `fit.py` já usa para vendedor×produto/vendedor×setor (sinal igualmente fraco, p≈0,047 no caso de vendedor×produto). A seção 6 do backtest **não foi apagada** — continua reproduzindo e imprimindo o resultado negativo a cada execução (agora um aviso permanente, não um portão de aceite — ver abaixo), e uma nova seção 6.1 reproduz `mult_setor` em si (comportamento do teto, célula grande vs. ínfima, consistência entre funil e referência).

**Medido sobre as 1.436 oportunidades abertas e os 4.238 negócios Won reais** (comparação direta entre o sistema antigo — `K_PRODUTO=4,0` congelado, sem `mult_setor` — e o novo, medida com `git stash`/`git stash pop` sobre o código, não estimada): SCORE desloca mediana 0,30pp, máximo 4,40pp; CONFIANÇA desloca mediana 0,00, p90 7,80, máximo 12,60. **Zero** oportunidades cruzam o corte SCORE≥95 ou CONFIANÇA<50 em qualquer direção; a distribuição de ESTADO é idêntica (Priorizar 54, Acompanhar 283, Qualificar 656, Revisão em lote 443).

**Achado colateral aceito, não corrigido — inflação cosmética da referência:** a mediana de PRIORIDADE da população de referência (4.238 negócios Won) sobe 6,75% (351,52 → 375,26) — efeito estrutural: células com taxa de vitória mais alta contribuem mais linhas Won à referência (por definição), então a própria população contra a qual `mult_setor` é medido absorve parte do mesmo sinal circularmente. Não distorce a *ordenação* do funil (SCORE não cruza cortes, ver acima), mas infla o valor absoluto de PRIORIDADE por um motivo que não é economia real. Corrigir exigiria um segundo mecanismo de cálculo (multiplicador *held-out* só para a referência) para consertar um número que nunca aparece a um vendedor — PRIORIDADE em dólares não é exibida desde o redesenho de 2026-08-20 — e cujo efeito sobre SCORE já é desprezível. Aceito conscientemente, documentado aqui para quem comparar PRIORIDADE entre gerações do CSV não confundir com mudança de mercado.

**CONFIANÇA ganha um terceiro termo de suporte:** `s_célula = min(1, n_célula/50)`, mesma saturação de `s_idade`/`s_produto`, omitido (nunca zerado) quando o setor é desconhecido, com pesos revisados `0,65 idade / 0,20 produto / 0,15 célula` (generaliza a regra de omissão que já existia só para idade ausente). Pesos escolhidos para manter a proporção original (0,75/0,25) quase intacta quando célula está ausente — renormalizado dá 0,765/0,235, 1,5pp de diferença, sem efeito prático no caso majoritário (68,7% do funil sem setor conhecido).

**`score_fatores` ganha uma frase nova**, no mesmo tom factual das demais ("histórico do produto neste setor: acima/dentro/abaixo da média, N negócios fechados nesta combinação") — sem linguagem de ressalva ("sinal fraco", "ruído amostral") por decisão explícita do dono do produto, mesmo com o nível colapsando (`k=∞`) sob recomputação estrita: declarar o fato e deixar quem lê julgar, o mesmo tom que `constants.py` já usa para `K_SETOR`/`K_FIT`.

### `K_PRODUTO` removido, não recalibrado para um novo valor congelado

**Decisão:** decidida a meio da sessão de grilling, não parte do escopo original — o dono do produto reverteu, depois de ver o design completo, a chamada inicial de deixar o aviso de `K_PRODUTO` desatualizado (registrado na entrada de 2026-08-21 acima, "Achado não previsto pelo design original") como pendência para a recalibração trimestral, e pediu "shrinkage graduado por tamanho amostral" no lugar da constante congelada. O nível de produto passa a chamar `shrinkage.level_stats` em tempo de carga (`pipeline.build_scoring_context`), exatamente como os níveis conta×produto e produto×setor já fazem — o `k` resultante (0,6966 nesta calibração) é usado diretamente, sem comparação contra constante alguma.

**Efeito medido:** sobre os 7.364 negócios de calibração, o `k` derivado (0,6966) produz `p̂_produto` idêntico ao congelado (diferença ≤0,01pp) para os seis produtos de maior volume, e um deslocamento de −1,22pp só para GTK 500 (n=35, o produto de menor amostra: 0,4436 → 0,4314). Combinado com `mult_setor`, o efeito agregado sobre o funil aberto — medido diretamente, não em separado — preserva os mesmos zero cruzamentos do corte SCORE≥95.

**Por quê agora:** resolve o aviso que o backtest já emitia (`k` derivado ≠ `K_PRODUTO` congelado) em vez de empurrá-lo para a próxima recalibração, e uniformiza a regra "k DEVE ser derivado, não escolhido à mão" para os quatro níveis da hierarquia, sem exceção — a única exceção manual que o requisito de encolhimento hierárquico já declarava.

### Seção 6 do backtest: de portão de aceite a aviso permanente

**Decisão:** `validation/backtest.py` seção 6 deixa de marcar a suíte como falha (`ok = False`) quando o condicionamento direto por produto×setor não for pior que o prior achatado — vira um aviso impresso, sempre presente, mas a execução nunca falha por causa dele. O resultado continua sendo reproduzido e reportado em toda execução, com ou sem essa mudança de comportamento — a suíte para de travar por causa dele, mas nunca para de contar a verdade sobre ele.

**Por quê:** o resultado negativo é real e permanece verdadeiro independentemente de `mult_setor` existir — `mult_setor` não é o condicionamento direto que esta seção testa e rejeita, é um mecanismo distinto (ver acima). Fazer a suíte falhar por um resultado que o próprio produto decidiu ignorar (por um motivo documentado, não por desconhecê-lo) confundia "a suíte está quebrada" com "a decisão de produto diverge da validação estatística" — dois eventos diferentes que pedem reações diferentes.

---
