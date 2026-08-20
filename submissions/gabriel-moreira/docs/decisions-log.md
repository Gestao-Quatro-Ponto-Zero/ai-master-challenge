# Decisions Log

Registro cronológico das decisões de produto/técnicas tomadas durante o challenge, e por quê. Diferente do [`process-log/narrative.md`](../process-log/narrative.md) — que documenta *como a IA foi usada* — este arquivo documenta *o que foi decidido e a lógica por trás*, para servir de base ao `architecture.md` e ao README final.

Regra deste arquivo: nenhuma entrada é escrita sem a decisão ter vindo de mim (Gabriel). O Claude Code pode propor opções, mas quem decide e assina a entrada sou eu.

---

## 2026-08-18 — Escolha do challenge

**Decisão:** Challenge 003 — Lead Scorer.

**Por quê:** _TODO — registrar o motivo real da escolha (perfil técnico, interesse na área de vendas/RevOps, etc.)._

---

## 2026-08-18 — Estrutura da submissão

**Decisão:** seguir à risca a estrutura de pastas do `CONTRIBUTING.md` (`solution/`, `process-log/`, `docs/`), sem desvios, e manter um log de decisões separado do log de processo de IA.

**Por quê:** o guia de submissão penaliza explicitamente "process log mostra 1 prompt → 1 resposta → submissão" e valoriza "iteração e julgamento". Separar *decisão* de *uso de IA* deixa isso auditável — dá pra ver exatamente onde o julgamento humano entrou.

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

## Próximas decisões (se houver continuação)

- [ ] A/B test: metade dos vendedores prioriza pelo score, metade não. Métrica: receita por vendedor por trimestre.
- [ ] Recalibração trimestral: `k`, curvas de aging e limiares de idade gravados como percentis recalculados dos últimos 4 trimestres, não como as constantes fixas derivadas de 2016–2017.
- [ ] Coletar dados comportamentais (§6 do analise): speed-to-lead mata qualquer modelo de probability.
- [ ] Validar, assim que a implementação rodar sobre os dados carregados, se o corte de SCORE=50 na tabela de ESTADO produz uma distribuição operacionalmente razoável entre os cinco estados (ex.: Foco urgente não pode virar uma fila vazia nem uma fila do tamanho do funil inteiro) — o corte é principiado (mediana da referência), mas vale conferir na prática antes de considerar definitivo.
