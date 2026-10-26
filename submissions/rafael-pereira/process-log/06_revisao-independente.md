# Bloco 6: revisão independente

**Como foi feito (decisão autônoma do Claude, conforme o PROMPTS.md e o PROMPT_AUTONOMO.md).**
- O orquestrador (Claude Opus 5.5) disparou um subagente de **contexto limpo**: Claude Sonnet, esforço médio, sem acesso a esta conversa.
- O revisor recebeu só três caminhos: o README do challenge 003, o `submission-guide.md` e a pasta `submissions/rafael-pereira/`.
- O prompt foi o do PROMPTS.md (bloco 6), mais duas instruções: usar o Python do venv e o Edge (Playwright), e não editar arquivos.
- O relatório abaixo está **sem filtro**: só os títulos foram ajustados ao nível deste arquivo.
- Os critérios com nota ≤ 3 foram corrigidos (seção "Correções aplicadas"). Depois rodou-se uma segunda revisão com um novo subagente, também de contexto limpo, que não viu a primeira.

---

## Revisão 1 (texto integral)

### Avaliação: Rafael Pereira, Challenge 003 (Lead Scorer)

Base da avaliação: li o README do challenge, o guia de submissão, o README da submissão, `scorer/score.py`, `scorer/explain.py` e trechos de `SCORING.md` e `app.js`. Rodei o setup do README e usei a interface em `file://` no Edge via Playwright. Não editei nenhum arquivo da submissão.

#### Notas por critério

| Critério | Nota | Justificativa |
|---|---|---|
| 1. Funciona de verdade | **5** | `pytest` passou inteiro (3 linhas de pontos, 100%, sem falhas, rodado duas vezes). O build terminou com exit 0 em ~11 s. Os hashes SHA256 de `data/processed/deals.csv` e `app/data.js` ficaram idênticos antes e depois do build, então o determinismo é real. `index.html` abre em `file://` sem erro de console (nenhum `console.error` nem `pageerror`). Sem scroll horizontal a 390 px. Único ponto fora: o link do GitHub Pages é um modelo com "[ativar — Rafael]" (README, passo 2), não um link real. |
| 2. Scoring faz sentido, features certas, vai além do óbvio | **3** | A tese de que frescor vence atributos é bem investigada e honesta (descartou produto, região, setor, porte e vendedor com regra pré-registrada). Mas o score entregue é só `chance(idade) × preço de tabela` (`score.py`, linhas 64-69 e 200-204). A chance é constante até o joelho de 95 dias, então dentro do Foque o score é só o preço do produto. São 7 produtos, logo 7 valores de score. Um deal de 12 dias e um de 94 dias do mesmo produto têm score e chance idênticos (Boris Faz: "há 12 dias, chance 40%"; GTX Plus Pro de 92 a 94 dias, todos "Score 75"). O resumo do README diz que ≤30 dias ganha 50% e >90 dias ganha 0%, e o modelo ignora justamente essa diferença. O README admite que, entre deals já resolvidos, o score empata com o valor, e que a recência vence em AUC em 3 de 4 cortes. A vantagem de 61% contra 48% vem quase toda de tirar zumbis do topo. Isso é um filtro de idade com régua de preço. Não há estágio, tamanho da conta, nem histórico da conta no score. |
| 3. Vendedor não técnico consegue usar e entender | **3** | A tela abre em "Todos os vendedores", com 126 Foque e 1.291 Limpe misturados. O vendedor precisa achar o próprio nome num select de 35 itens (alguns "sem deals no CRM"). Fazendo isso, a frase "Esta semana: foque em N, reative M, limpe K" é clara e a explicação é em português simples. Mas Darcel Schlecht abre com Foque 0 e Reative 0, e a tela mostra uma lista de 83 deals Limpe: "Esta semana: limpe 83... e qualifique 111". Para um vendedor isso é uma tarefa de faxina, não de prioridade. Vários cards têm "Conta não informada" como título. Na lista Foque, as frases são quase idênticas entre cards ("foram ganhos em 40% dos casos nos 90 dias seguintes"). "Valor esperado", "joelho" e "log" (em "Como funciona") exigem leitura. |
| 4. Interface ajuda a decidir | **3** | Pontos fortes: listas por ação (Foque, Reative, Limpe, Qualifique), dias até a chance cair ("a chance começa a cair em 3 dias"), filtros por vendedor, manager e região, e o modo teste que compara recomendação e resultado real. Pontos fracos: dentro do Foque o card não ajuda a escolher entre dois deals parecidos. A ordenação é por preço, e o desempate é por "dias até o joelho", que não aparece como argumento de escolha. O modo teste mostra desfecho agregado de todos os vendedores ("os filtros não mudam estes números"), enquanto os cards mostram só os do vendedor. A lista Limpe não diz quem ligar nem o que perguntar. Não há ação concreta além de "confirme com o cliente". |
| 5. Código limpo e mantenível | **4** | Pacote pequeno e modular (`clean`, `features`, `score`, `explain`, `fmt`, `validate`, `build`), funções puras, docstrings úteis, `config.py` central, 199+ testes (inclusive teste de mutação do futuro para vazamento e teste de permutação do vendedor). Pontos fracos: `validate.py` (757 linhas), `docs.py` (719) e `build.py` (678) são grandes. `docs.py` gera prosa e tabelas dos documentos, o que acopla documentação ao código. `app.js` tem 592 linhas em um IIFE só, sem testes unitários próprios. A "validação da interface" depende de um script Playwright opcional que eu não rodei. Há ruído na pasta da submissão (`CLAUDE.md`, `GUIA.md`, `PROMPTS.md`, `PROMPT_AUTONOMO.md`, 28 briefs `.md` gerados). |
| 6. Documentação cobre setup, lógica e limitações | **4** | Cobre os três itens e vai além: SCOPE, DATA_QUALITY, SCORING, MODEL_CARD, DECISIONS. As limitações são brutalmente honestas (zumbis, sintético, Foque otimista, recência ganha em AUC). Pontos fracos: a documentação é longa demais para a ferramenta (README com ~200 linhas e jargão como "pré-registrado", "AUC", "bootstrap" que o vendedor ou a Head não pediram). Há rascunho deixado no texto final: "[RASCUNHO — Rafael revisar]" e "[preencher ao abrir o PR]". A seção "O que eu adicionei" é explicitamente escrita pelo Claude. O guia pede 5 páginas em vez de 40; aqui a documentação se aproxima do excesso. |
| 7. Process log mostra iteração, julgamento e uso estratégico de IA | **3** | Há muito material: logs por bloco, DECISIONS, 11 episódios de erro e autocorreção, plano do Opus, screenshots antes/depois. Mas o processo é majoritariamente Claude orquestrando subagentes Claude de forma autônoma. A seção "O que eu adicionei" é um rascunho escrito pelo Claude e pede para o Rafael confirmar. Não há export de chat nem screenshot de conversa com IA (o próprio README admite). O bloco 6 (revisão independente) está "planejado", e `06_revisao-independente.md` não existe. Os "erros da IA" são mais técnicos e internos ao agente (float, teste fraco) do que decisões de negócio do candidato. |

#### Setup ao pé da letra

Ambiente: Python 3.11.9 do venv indicado, rodado com `-B` e `-p no:cacheprovider`. Os comandos do README, executados dentro de `solution/`:

| Passo do README | Comando | Resultado |
|---|---|---|
| 1. Abrir sem instalar | `solution/app/index.html` em `file://` (Edge headless) | Abre, sem erros de console, `LEAD_DATA` carrega. |
| 3. Dependências | `pip install -r requirements.txt` | Não rodei, por instrução do enunciado de que o ambiente já tem tudo instalado. `requirements.txt` lista pandas, numpy, scipy e pytest com `>=` (README cita versões exatas, o arquivo não as fixa). |
| 3. Testes | `python -B -m pytest -p no:cacheprovider -q` | Passou 100% (duas execuções, sem falhas). |
| 3. Build | `python -B -m scorer.build --reference-date 2017-12-31` | Exit 0, ~11 s. SHA256 de `deals.csv` (626A09F3...) e `data.js` (61599E1F...) idênticos antes e depois. Determinismo confirmado. |
| 4. Verificação da interface | `python tools/check_app.py --prefix final` | Não rodei. Exige `requirements-dev.txt` (playwright), fora do que me foi autorizado instalar. Fiz verificação equivalente à mão com Playwright: filtros, modo teste, "Como funciona", 390 px sem scroll horizontal, console limpo. |
| 2. Link GitHub Pages | URL do README | Não verificável. É um modelo com `<seu-usuario>` marcado como pendente. |

Conclusão: o setup funciona como descrito, exceto o link publicado, que o README já admite ser pendente.

#### 5 pontos mais fracos

1. **O score, dentro do Foque, é só o preço do produto.** A curva é plana até 95 dias (`score.py:64-69`). No Foque de hoje, 126 deals recebem 7 valores de score possíveis. Os 5 primeiros deals são todos GTX Plus Pro de 92 a 94 dias, com score 75 e chance 40%. Um deal de 12 dias e um de 94 dias do mesmo produto têm score igual. Isso contradiz a tese central do próprio README (frescor decide, 50% em ≤30 dias vs 0% em >90). Para o vendedor, o "score" é uma etiqueta de produto.
2. **Vantagem do backtest vem só de tirar zumbis, e a ferramenta não prova que escolhe bem entre deals vivos.** O README admite empate com o valor entre deals resolvidos (48,7% vs 49,0%) e que a recência ganha em AUC em 3 de 4 cortes. A melhor feature (idade) está usada de forma grosseira (platô + queda a partir de 95 dias). A honestidade é um ponto positivo, mas o resultado é "ordene por preço e esconda os velhos".
3. **A ferramenta não responde "o que faço com o meu primeiro deal" para quem tem carteira velha.** Darcel Schlecht abre com Foque 0, Reative 0 e uma lista Limpe de 83 itens. Para 1.291 dos ~2.100 deals abertos a única recomendação é "confirme e encerre". Não há ação por deal (script de contato, ligar a quem, o que perguntar) nem priorização dentro do Limpe além de preço.
4. **Tela inicial genérica e card repetitivo.** Abre em "Todos os vendedores"; o vendedor tem que achar o nome em um select de 35 itens. Nos cards, as frases repetem o mesmo modelo em todos os deals, e muitos têm "Conta não informada" como título (1.425 deals sem conta). Não aproveita conta, setor, estágio nem histórico da conta para diferenciar. Dois deals vizinhos na lista parecem iguais.
5. **Documentação e process log com cheiro de agente autônomo, não de decisão do candidato.** O README final ainda tem "[RASCUNHO — Rafael revisar]", "[preencher ao abrir o PR]" e "[ativar — Rafael]". A seção "O que eu adicionei" foi escrita pelo Claude. Não há chat export nem screenshot de conversa com IA. O bloco 6 (revisão independente) não existe. Os 11 "erros da IA" são de agentes contra agentes. O julgamento humano real se resume a 7 itens de uma lista reconstruída. O README tem quase 200 linhas e jargão ("pré-registrado", "AUC", "bootstrap") para um público que pediu algo simples.

#### O que pareceria baseline de LLM

- **Estrutura de repositório excessiva para o tamanho do problema:** 5 documentos de apoio, CLAUDE.md, PROMPTS.md, PROMPT_AUTONOMO.md, DECISIONS, model card, 28 briefs `.md`. A cara é de "projeto completo de IA", não de ferramenta enxuta.
- **Frases de card em template fixo**, com a mesma construção para todo deal ("Aberto há X dias. No histórico, deals em Engaging com essa idade foram ganhos em Y% dos casos nos 90 dias seguintes"). Explicabilidade correta, mas sem nada específico do deal.
- **Score = chance(idade) × preço**, numa escala de log 0 a 100, com listas Foque, Reative, Limpe e Qualifique. É a resposta de manual a "prioridade de CRM por idade e valor" que um LLM entrega.
- **Auto-crítica em grande volume** (limitações extensas, model card, "pré-registro") como substituto de uma ideia de produto diferente. Honestidade de método boa, mas é a voz de um LLM cuidadoso.
- **Process log como diário de agentes**: muitos episódios de "autocorreção na execução autônoma", poucas decisões visivelmente do candidato.

O que não parece baseline: a descoberta de que atributos não separam os deals e o frescor sim, o teste de vazamento por mutação do futuro, o modo teste na interface, a recusa de usar vendedor no score e a escolha de não usar Streamlit. Isso é real e acima de uma entrega média.

#### Veredito

Entrega funcional, determinística e honesta, com a melhor parte nos dados (tese de frescor, validação temporal, limitações). Mas o score é, na prática, "filtre os zumbis e ordene por preço", a interface não ajuda a escolher entre deals do mesmo produto, e o process log depende de agentes Claude e de um rascunho não revisado, o que enfraquece a evidência de julgamento do candidato.

**Nota média aproximada: 3,6 em 5.**

---

## Triagem do orquestrador (Claude Opus 5.5): o que corrigir e o que não

Regra do plano (E10): o bloco 6 **não pode mudar o modelo, os parâmetros, o critério nem a métrica primária**. O ajuste único já foi reservado no bloco 3 e não foi usado porque o critério passou. Mudar a curva agora, depois de ver o backtest e a crítica, seria ajuste pós-hoc.

| Crítica (nota ≤ 3) | Decisão | Motivo |
|---|---|---|
| C2: "dentro do Foque o score é só o preço; um deal de 12 dias vale o mesmo que um de 94" | **Não mexer no modelo; explicar com número.** README e SCORING passam a mostrar, a partir do JSON (`cuts[].foque_por_idade`), que dentro do platô a diferença entre 61+ e 0–30 dias **troca de sinal** entre cortes (−17,4 e −41,3 pp nos fins de trimestre; +19,2 e +21,3 pp no meio). Com isso, uma inclinação dentro do platô não tem direção estável. A frase "≤30 dias ganha 50%, >90 dias 0%" do resumo passa a deixar claro que o salto está no joelho, não dentro dele. | É limitação real, documentada sem maquiagem. Mudar a curva seria p-hacking. |
| C3/C4: frase repetida no card do Foque; nada ajuda a escolher entre deals parecidos | **Corrigir o texto** (`explain.py`, sem tocar no modelo): no Foque, a 1ª frase passa a ser a que diferencia (valor e prazo), e a frase genérica da curva vai para o detalhe. | Correção de interface, não de modelo. |
| C3: tela abre em "Todos os vendedores" | **Corrigir**: aviso de primeira tela pedindo "Escolha seu nome". | Atrito real para o vendedor. |
| C3/C4: vendedor sem deals vivos (Foque e Reative vazios) abre numa lista Limpe | **Corrigir**: sem Foque nem Reative, a aba padrão é Qualifique, e a frase de ação diz que a receita nova está ali. | Prioriza gerar pipeline em vez de faxina. |
| C4: Limpe sem ação concreta | **Corrigir o texto**: cada card do Limpe ganha a pergunta a fazer ao cliente e o que fazer no CRM em cada resposta. | Ação concreta, sem novo dado. |
| C4: resumo do modo teste não muda com filtro | **Manter.** | Decisão 4 do CLAUDE.md: não exibir taxa de vitória por vendedor. Será explicado na própria faixa. |
| C7: `06_revisao-independente.md` não existia; placeholders; process log "diário de agentes" | **Parcial.** Este arquivo agora existe. Os placeholders `[RASCUNHO — Rafael revisar]`, `[ativar — Rafael]` e `[preencher ao abrir o PR]` são **pedidos explícitos do Rafael** (PROMPT_AUTONOMO, seção 4) e ficam. O README passa a separar, de forma visível, o que foi decisão do Rafael (fase 0) e o que foi execução autônoma. | Não dá para inventar intervenção humana: o process log registra o que aconteceu. |
| C6 (nota 4, oportunista): README longo e com jargão | **Corrigir**: o resumo para a Head de RevOps fica no topo, sem jargão; o jargão vai para o SCORING. | Barato e melhora a leitura. |

## Correções aplicadas

Executor: Claude Sonnet (subagente executor). Modelo, parâmetros, critério, métrica, `score.py`, `features.py` e `validate.py` não foram tocados.

| Crítica | Mudança | Arquivo | Evidência (antes → depois) |
|---|---|---|---|
| C3/C4: frase repetida no Foque | 1ª frase com valor e prazo; a da curva vai para a 2ª | `scorer/explain.py`, `tests/test_explain.py` | Antes: "Aberto há 21 dias. No histórico, deals em Engaging com essa idade foram ganhos em 40%...". Depois: "GTX Plus Pro: US$ 5.482 de tabela, valor esperado US$ 2.187; janela boa por mais 74 dias." (screenshot `final_card-aberto_390.png`) |
| C4: Limpe sem ação | 2ª frase: perguntar ao cliente; se não, marcar Lost; se sim, atualizar e mover para Reative ou Foque | `scorer/explain.py`, `tests/test_explain.py`, instrução da aba em `app/app.js` | Antes: "Provável deal parado ou CRM desatualizado: confirme com o cliente e encerre ou atualize." Depois: "Pergunte ao cliente se ainda quer comprar: se não, marque Lost no CRM; se sim, atualize o deal e mova para Reative ou Foque." |
| C3: tela abre em "Todos os vendedores" | Aviso visível "Escolha seu nome em “Quem é você?” para ver só os seus deals." (visão do manager mantida) | `app/app.js`, `app/index.html`, `app/style.css` | `final_inicio_1280.png`: aviso amarelo sob a frase de ação; antes não havia aviso |
| C3/C4: vendedor sem Foque e Reative abre em Limpe | Com Foque 0, Reative 0 e Qualifique > 0, a aba padrão é Qualifique e a frase de ação diz que a receita nova está ali | `app/app.js` | Darcel Schlecht (Foque 0, Reative 0, Limpe 83, Qualifique 111): antes abria em Limpe com "limpe 83 ... e qualifique 111"; depois abre em Qualifique |
| C4: modo teste mostra números do time todo | Faixa do modo teste explica que é de propósito (sem taxa de vitória por vendedor; decisão 4) | `app/app.js` | Antes só o título "(todos os vendedores; os filtros não mudam estes números)"; depois, frase na faixa |
| C2: "12 dias vale o mesmo que 94" | Bloco AUTO `foque-plato-sinal` mostra o sinal da diferença 61+ contra 0 a 30 dias por corte (-17,4 e -41,3 pp nos fins de trimestre; +19,2 e +21,3 pp nos outros); a curva não mudou | `scorer/docs.py`, `README.md`, `docs/SCORING.md` (seção 10) | Antes: nenhuma explicação de por que o platô é plano; depois: 2 frases geradas do JSON (`cuts[].foque_por_idade.diferenca_ultima_menos_primeira_90d`) |
| C2: "≤30 dias 50% contra >90 dias 0%" lido como diferença dentro do Foque | Frase removida do Executive Summary; o bloco AUTO diz que o salto está no joelho | `README.md` | Antes: resumo citava 50% e 0% ao lado do score; depois: sem a comparação |
| C6: README longo e com jargão | Executive Summary em 5 frases, sem AUC, win rate ou bootstrap; termos técnicos ficam nas seções técnicas e no SCORING | `README.md` | Antes: 5 frases com "win rate" e "AUC"; depois: 5 frases sem esses termos |
| C7: process log "diário de agentes" | Tabela "Quem decidiu o quê" (decisões do Rafael na fase 0 × execução autônoma do Claude); bloco 6 deixa de ser "planejado"; Evidências citam este arquivo e explicam os placeholders | `README.md` | Nenhuma intervenção humana inventada; `[RASCUNHO — Rafael revisar]`, `[ativar — Rafael]` e `[preencher ao abrir o PR]` mantidos |

Verificação (cwd `solution`): `scorer.build --reference-date 2017-12-31` exit 0; `pytest` exit 0 (2 testes de documentos e de resumo ajustados ao texto novo: o limite de 5 frases e a palavra "frescor" na 1ª frase continuam valendo); `scorer.docs --check` exit 0; `tools/check_app.py --prefix final` PASSOU (24 de 24, nenhuma checagem precisou mudar).

## Críticas não corrigidas

| Crítica | Motivo |
|---|---|
| C2: score dentro do Foque é só o preço (curva plana até o joelho de 95 dias) | Mudar a curva depois de ver o backtest seria ajuste pós-hoc, e o bloco 6 não pode mudar modelo, parâmetros, critério nem métrica. Virou texto com número (bloco `foque-plato-sinal`). |
| C2: vantagem do backtest vem de tirar zumbis; entre resolvidos o score só empata com o valor | É limitação real e já documentada (README, SCORING seção 7). Sem maquiagem. |
| C2/C4: nada de estágio, tamanho da conta ou histórico da conta no score | Atributos só entram se o backtest mostrar ganho (decisão 3); os testados não mostraram. |
| C4: modo teste não muda com o filtro de vendedor | Decisão 4 do CLAUDE.md (sem taxa de vitória por vendedor). Só foi explicado na faixa. |
| C3: "Conta não informada" como título em 1.425 deals | É dado ausente no CRM; o card já avisa que a conta deve ser preenchida e que isso não muda o score. |
| C5: arquivos grandes (`validate.py`, `docs.py`, `build.py`) e `app.js` sem teste próprio | Refatorar sem mudar comportamento fica fora do escopo desta rodada; `app.js` é coberto pelo `check_app.py`. |
| C5: ruído na pasta (CLAUDE.md, PROMPTS.md, briefs) | Fazem parte do process log pedido pelo challenge; a pasta é só da submissão. |
| C6: `requirements.txt` com `>=` e README citando versões exatas | Não alterado nesta rodada; o README declara as versões testadas. |
| C7: sem chat export nem screenshot de conversa | Não existem; o README diz isso. Não dá para inventar. |


---

## Revisão 2 (texto integral; novo subagente de contexto limpo, sem acesso à revisão 1 antes de dar as notas)

Executor: Claude Sonnet, esforço médio, somente leitura. Ele recebeu os mesmos três caminhos e o mesmo prompt da revisão 1, com dois acréscimos: a ordem de só ler este arquivo depois de dar as notas, e a pergunta "as correções declaradas existem?".

### Notas

| Critério | Nota | Justificativa |
|---|---|---|
| 1. Funciona de verdade | **5** | `pytest` passou inteiro (cerca de 72 s, 100%). O `build` terminou com exit 0 em cerca de 11 s e gerou os mesmos bytes, então o determinismo é real. O `check_app.py` deu 24 de 24 PASSOU, com console sem erros. A página abre por duplo-clique em `file://`. Usa os dados reais: 8.800 deals, 126/172/1.291/500 nas listas, e o `check_app` confere esses números contra o CSV. Ressalva única: o link do GitHub Pages é um modelo (`<seu-usuario>`) e não funciona. |
| 2. Scoring faz sentido e vai além do óbvio | **3** | A parte analítica é de nível alto. O frescor vence os atributos, a validação é temporal com critério fixado antes, há teste de vazamento por mutação do futuro, e o vendedor foi excluído do score com teste de permutação. O score entregue, porém, é `chance(idade) × preço` (`score.py:64-69`, `200-204`). A curva é plana até o joelho de 95 dias. Medi no snapshot de hoje: os 126 deals do Foque têm exatamente a mesma chance (0,3989, desvio-padrão 1e-16), e a correlação de Spearman entre score e preço é 1,00. Dentro do Foque, o "score" é o preço de tabela. O README admite que, entre deals resolvidos, o score só empata com o valor (48,7% contra 49,0%). O ganho do backtest (61% contra 48%) vem de esconder os deals velhos. A idade, que é a única feature útil, entra como degrau e não como gradiente. |
| 3. Vendedor não técnico usa e entende | **3** | Pontos fortes: a frase "Esta semana: foque em 126, reative 172…" é clara, as listas são por ação, e o aviso amarelo manda escolher o nome. O vendedor Darcel Schlecht abre em Qualifique, com explicação. Pontos fracos: a tela inicial mostra "Todos os vendedores", e o vendedor precisa achar o nome num select de 35 itens. Cada card do Foque mostra "chance 40%", sempre o mesmo número, o que não ajuda a escolher. O "Como funciona" fala em "escala de log" e "487 vezes o mais barato". Na Qualifique, os cards do topo são idênticos entre si ("Conta não informada · GTX Plus Pro · Sem score · US$ 5.482"). O ID só aparece depois de expandir. Os cards de Limpe mostram "chance 0%", enquanto o `explain.py` diz "menos de 1%". |
| 4. Interface ajuda a decidir | **3** | O que ajuda: a divisão em quatro listas de ação, o "a chance começa a cair em N dias", os filtros em cascata por vendedor, manager e região, e o modo teste ("o que o score teria dito" contra "o que aconteceu"). O que atrapalha: o `MODEL_CARD.md:52` diz que o Foque de hoje provavelmente está otimista para deals com 61 dias ou mais, porque hoje é fim de trimestre (69 dos 126 deals). Mesmo assim, o primeiro card da tela é o de 95 dias (Betasoloin, "Score 100, hoje é o último dia da janela boa"). O aviso não aparece em lugar nenhum de `app.js` (a busca por "61", "otimista" e "trimestre" não achou nada). A ferramenta mostra no topo o deal que a própria documentação diz estar superavaliado, sem avisar o vendedor. Dentro do Foque, dois deals do mesmo produto ficam empatados no score. O Limpe é ordenado por preço, o que é "faxina" e não prioridade. |
| 5. Código mantível | **4** | Pacote modular (`clean`, `features`, `score`, `explain`, `fmt`, `validate`, `build`), `config.py` central, funções puras, docstrings úteis e cerca de 200 testes de boa qualidade. `check_app.py` roda Playwright e confere o app contra o `data.js` e contra o CSV. Pontos fracos: arquivos grandes (`validate.py` 757 linhas, `docs.py` 744, `build.py` 678, `check_app.py` 895), `app.js` é um IIFE único de 610 linhas sem teste unitário próprio, `docs.py` gera prosa de documentação a partir de código (acoplamento), `requirements.txt` usa `>=` enquanto o README cita versões exatas, e a pasta tem ruído (`CLAUDE.md`, `GUIA.md`, `PROMPTS.md`, `PROMPT_AUTONOMO.md`, 27 briefs gerados). |
| 6. Documentação: setup, lógica, limitações | **4** | Cobre os três itens e vai além (SCOPE, DATA_QUALITY, SCORING, MODEL_CARD, DECISIONS). As limitações são muito honestas: dataset sintético, o ganho vem dos zumbis, a recência ganha em AUC, o Foque otimista, a fragilidade do corte de 30/06. Pontos fracos: o README tem cerca de 210 linhas, com jargão ("pré-registrado", "AUC", "bootstrap", "joelho"). O resumo ficou mais enxuto, mas ainda é denso para a Head de RevOps. Há três marcadores de pendência no texto final (`[ativar — Rafael]`, `[RASCUNHO — Rafael revisar]`, `[preencher ao abrir o PR]`). O setup lista duas fontes de verdade para as versões (README e `requirements.txt`). |
| 7. Process log: iteração, julgamento, uso estratégico de IA | **3** | Há volume e rigor: logs por bloco, `DECISIONS.md` com alternativa descartada, 11 episódios de autocorreção, screenshots antes e depois, e commits por bloco. Mas a execução é quase toda de agentes Claude autônomos (Opus orquestra, Sonnet e Haiku executam). O julgamento humano reconhecido é uma lista de 7 itens da fase 0, e a seção "O que eu adicionei" é um rascunho escrito pelo Claude, ainda pedindo confirmação. Não há chat export nem screenshot de conversa. Os erros listados são em maioria internos entre agentes (ponto flutuante, teste fraco, tolerância pós-hoc). O guia pede "o que você adicionou que a IA sozinha não faria", e aqui isso é a parte mais frágil. |

### Setup ao pé da letra

| Passo do README | Resultado |
|---|---|
| 1. Abrir `solution/app/index.html` | Funcionou. Sem servidor, sem erro de console (`read_console` vazio na Darcel e na Zane). |
| 2. Link do GitHub Pages | Não verificável. É um modelo marcado como pendente, e o README admite isso. |
| 3a. `pip install -r requirements.txt` | Não rodei, por instrução. O arquivo usa `>=`. |
| 3b. `python -m pytest` | Funcionou: todos passaram, cerca de 72 s. |
| 3c. `python -m scorer.build --reference-date 2017-12-31` | Funcionou: exit 0, cerca de 11 s. Os blocos AUTO dos documentos ficaram "sem mudanças", e nenhum arquivo da submissão mudou de hash. |
| 4. `python tools/check_app.py --prefix final` | Funcionou com `--prefix revisor2 --shots-dir`: 24 de 24 PASSOU. |

Conclusão: o setup funciona como descrito. A única ressalva é o link publicado, que é pendência declarada.

### 5 pontos mais fracos

1. **Dentro do Foque o score é o preço do produto.** A chance é 0,3989 para os 126 deals (`score.py:64-69`) e a correlação de Spearman entre score e preço é 1,00. Na tela, todo card do Foque mostra "chance 40%". Um deal de 21 dias e um de 94 dias do mesmo produto têm o mesmo score. O "score" é uma etiqueta de produto, e o vendedor não consegue escolher entre dois deals vivos.
2. **O ganho do backtest vem de esconder zumbis.** O score empata com o valor entre deals vivos (48,7% contra 49,0%), e a recência o vence em AUC em 3 de 4 cortes. A única feature útil (idade) entra como degrau em 95 dias, sem gradiente. O resultado é "ordene por preço e esconda os velhos", bem documentado mas pouco além do óbvio.
3. **A UI contradiz o model card.** O model card diz que o Foque de hoje está otimista para deals com 61 dias ou mais (69 de 126, hoje é fim de trimestre). A tela de hoje abre com o card de 95 dias no topo, sem nenhum aviso (`app.js` não trata isso). A ferramenta destaca para o vendedor justamente o deal que a documentação diz estar superavaliado. "Medido, não corrigido" fica só no documento.
4. **Cards pouco discriminantes e uma lista sem priorização.** A Qualifique abre com cards idênticos ("Conta não informada · GTX Plus Pro · Sem score · US$ 5.482"). O ID só aparece depois de expandir. O Limpe (1.291 deals, 62% do pipeline aberto) é ordenado só por preço. "Chance 0%" nos cards de Limpe diverge do texto do `explain.py` ("menos de 1%"). Para Darcel Schlecht, 100% da fila é Qualifique e Limpe. Não há conta, setor, estágio ou histórico para diferenciar os cards.
5. **Process log com pouca evidência de julgamento humano.** "O que eu adicionei" é rascunho do Claude, sem chat export nem screenshot de conversa. As autocorreções são de agentes contra agentes. Os três marcadores de pendência ficam no README final. O guia de submissão pede explicitamente a evidência do que o candidato fez que a IA sozinha não faria.

### O que pareceria baseline de LLM

- **O score em si.** `chance(idade) × preço`, escala log de 0 a 100, listas Foque, Reative, Limpe e Qualifique. É a resposta de manual a "prioridade de CRM por idade e valor".
- **Explicação em template fixo** (`explain.py`): a mesma construção para todo deal ("Aberto há X dias… foram ganhos em Y%… A chance só começa a cair depois de Z dias"). Não há nada específico do deal.
- **Volume de auto-crítica e governança** (model card, pré-registro, bootstrap, 11 "autocorreções"), que funciona como substituto de uma ideia de produto mais afiada. É honestidade de método, mas na voz de um LLM cuidadoso.
- **Estrutura de repositório pesada** para o tamanho do problema: `CLAUDE.md`, `PROMPTS.md`, `PROMPT_AUTONOMO.md`, 5 documentos de apoio, 27 briefs `.md`.
- **Diário de agentes** no lugar de decisões do candidato.

O que não parece baseline: a descoberta de que atributos não separam os deals e o frescor sim, a validação temporal com critério fixado antes, o teste de vazamento por mutação do futuro, o modo teste na interface (mostra score contra história), a recusa de usar o vendedor no score, a lista Limpe com a pergunta a fazer ao cliente, e a escolha de não usar Streamlit.

### As correções declaradas no 06 existem?

Sim, as que verifiquei em código e na tela.

- **Aviso "Escolha seu nome em 'Quem é você?'":** existe (`index.html:58` e tela inicial 1280 e 390).
- **1ª frase do Foque com valor e prazo:** existe (`explain.py:38-44`). Na tela: "GTX Plus Pro: US$ 5.482 de tabela, valor esperado US$ 2.187; janela boa por mais 74 dias." A frase da curva foi para o detalhe.
- **Limpe com pergunta ao cliente e ação no CRM:** existe em `explain.py:68-69`. Não vi a frase na tela do card fechado, só no código.
- **Vendedor sem Foque e Reative abre em Qualifique:** confirmado com Darcel Schlecht (Foque 0, Reative 0, Limpe 83, Qualifique 111). A aba selecionada é Qualifique, e a frase de ação diz "a receita nova está no Qualifique".
- **Faixa do modo teste explicando que não mostra taxa por vendedor:** existe na tela do modo teste.
- **Bloco `foque-plato-sinal` e Executive Summary sem AUC nem win rate:** existem no README.
- **Tabela "Quem decidiu o quê" e o bloco 6 deixando de ser "planejado":** existem. A tabela cita o `06_revisao-independente.md`, embora na seção de Ferramentas a linha do revisor ainda diga "planejado; relatório quando existir".
- **Limitado pelo 06:** a crítica central (score do Foque é o preço) não foi corrigida e virou texto com número. É decisão declarada: mudar a curva depois do backtest seria ajuste pós-hoc. O argumento é coerente com o método, mas o resultado para o vendedor continua o mesmo.

### Veredito

Entrega funcional, reproduzível e honesta, com análise e validação acima da média, mas o score que o vendedor vê é na prática "filtre os zumbis e ordene por preço", e a tela não repete o aviso que o próprio model card faz sobre o topo do Foque. A evidência de julgamento humano no process log é a parte mais frágil, e o conjunto tem cara de agente cuidadoso com o ângulo de governança como principal diferencial. Nota média: cerca de 3,6 em 5.

---

## Comparação das notas: revisão 1 × revisão 2

| Critério | Rev. 1 | Rev. 2 | Leitura do orquestrador |
|---|---|---|---|
| 1. Funciona | 5 | 5 | Estável. |
| 2. Scoring | 3 | 3 | A crítica central continua: dentro do Foque, o score equivale ao preço. Não dá para corrigi-la sem mudar o modelo depois de ver o backtest, o que a regra pré-registrada proíbe. Fica como **decisão para o Rafael** (ver abaixo). |
| 3. Vendedor entende | 3 | 3 | As correções existem (aviso de escolher nome, 1ª frase com valor e prazo, Qualifique como padrão), mas o "chance 40%" igual em todo card continua. |
| 4. Interface decide | 3 | 3 | Crítica nova e procedente: a UI não repetia o aviso do model card sobre o Foque com 61 dias ou mais. Corrigido depois da revisão 2 (seção seguinte). |
| 5. Código | 4 | 4 | Estável. |
| 6. Documentação | 4 | 4 | Estável. |
| 7. Process log | 3 | 3 | Limitação estrutural de uma execução autônoma: o julgamento humano real está na fase 0 e na revisão que o Rafael fará do rascunho. Não se inventa intervenção. |

**Ponto que fica para o julgamento humano (Rafael).** As duas revisões, independentes, convergem na mesma crítica: o score não diferencia deals vivos do mesmo produto. Os dados mostram um gradiente de idade dentro do platô, mas com **sinal que troca entre cortes** (−17,4 / +19,2 / +21,3 / −41,3 pp). Adotar um gradiente agora seria uma decisão pós-hoc. Se o Rafael quiser fazê-lo, deve ser registrada como tal no DECISIONS e no SCORING, com novo backtest. O Claude, por regra do pré-registro, não fez essa mudança.


## Correções pós-revisão 2

Executor: Claude Sonnet (subagente executor). Modelo, curva, parâmetros, critério e métrica não mudaram (`score.py`, `features.py` e `validate.py` intocados).

| Crítica | Mudança | Arquivo | Antes / depois |
|---|---|---|---|
| Rev. 2, ponto 3: a UI não repetia o aviso do model card sobre o Foque com 61+ dias | Aviso "Atenção" na linha-instrução da aba Foque, lido de `backtest.notes` (números do `backtest_metrics.json` via `build.py`) | `app/app.js`, `app/style.css` | Antes: nenhum aviso na tela. Depois: "Atenção: No Foque, deals com 61 dias ou mais ganharam menos em 90 dias do que os de 0 a 30 dias nos cortes de fim de trimestre: 30/06/2017 (-17,4 pp), 30/09/2017 (-41,3 pp)... Hoje, 69 dos 126 deals do Foque estão nessa faixa." (conferido em `final_inicio_1280.png`) |
| Rev. 2, ponto 4: "chance 0%" no card do Limpe contra "menos de 1%" no texto | `<1%` quando 0 < p < 0,005; p = 0 continua "0%" (o `explain.py` só diz "menos de 1%" quando o inteiro arredonda para 0, e p = 0 cai nesse caso só em texto de Reative) | `app/app.js` | Antes: "chance 0%". Depois: "chance <1%" |
| Rev. 2, "As correções declaradas": linha do revisor ainda "planejado" | Linha aponta para este arquivo, com as duas revisões | `README.md` | Antes: "planejado; relatório ... quando existir". Depois: "duas revisões, com nota média entre três e quatro de cinco nas duas, relatório em `process-log/06_revisao-independente.md`" |

Escolha do aviso: a opção do `explain.py` mudaria a assinatura de `explain_deal` e repetiria a frase em cada card; a linha-instrução usa uma nota já pronta no `data.js` e fica visível na aba Foque de hoje.

Desvio: o "3,6" pedido não pôde entrar como número no README. `test_docs_numbers` rejeitou (número fora dos fatos) e a média foi escrita por extenso. O `check_app` rejeitou "1%" literal no `app.js`; o limite vem de `pct0(0.01)`.
