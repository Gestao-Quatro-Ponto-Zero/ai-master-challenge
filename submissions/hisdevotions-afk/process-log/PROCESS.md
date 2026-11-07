# Process log: Challenge 003, Lead Scorer

Registro cronológico do trabalho. A ferramenta principal foi o Claude Code no terminal, com acesso ao repositório e aos meus projetos locais. As primeiras sessões usaram o Claude Opus 5.5 e várias das seguintes o Claude Sonnet 5; o modelo de cada commit está no `Co-Authored-By` do git.

Convenção: [EU] marca decisão ou correção minha, [IA] o que a IA propôs ou fez, e [DADO] o que os dados mostraram.

As seções com letra (6b e 9b) foram acrescentadas na auditoria da seção 17, a partir dos commits, para cobrir trabalho que tinha ficado sem registro. Elas entram na ordem em que aconteceram, sem renumerar as outras.

---

## 1. Escolha do desafio

- [IA] Leu os READMEs dos quatro challenges, o guia de submissão, o CONTRIBUTING e o template.
- [EU] Pedi para a IA varrer todos os meus projetos locais atrás de algo reaproveitável, com a instrução de não perder tempo se não houvesse nada.
- [IA] Encontrou no meu CRM de produção (Fadelito, rede de escolas) heurísticas de pipeline que eu já uso: limite de tempo parado por estágio, estado "morto" (o lead esfriou de vez e é arquivado, em vez de gerar alerta para sempre), comparação com pares usando taxa agregada e amostra mínima, e uma fila de ações ordenada por valor esperado. Recomendou não portar código, porque o domínio é outro e seria código de cliente num repositório público. Só o raciocínio veio.
- [EU] Escolhi o 003. É o problema que eu já resolvo no dia a dia (deal esfriando sem ninguém ver) e o único challenge em que software rodando é obrigatório.
- [EU] Mandei a IA salvar o brief (estrutura, requisitos, critérios, dicas) na memória persistente dela como referência primária para as decisões.

## 2. Exploração dos dados, antes de qualquer feature

A regra que impus foi olhar os dados antes de decidir o score, que é o que o próprio brief pede.

### Qualidade dos dados

| Problema | Impacto | Tratamento |
|---|---|---|
| `GTXPro` no pipeline e `GTX Pro` no catálogo | 1.480 deals perdem preço e série no join | normalizar o nome |
| `technolgy` (typo) em setor | setor duplicado em qualquer agrupamento | normalizar |
| 68% dos Engaging e 67% dos Prospecting sem conta | não dá para usar dado de conta nesses deals | virar tarefa de higiene na interface em vez de esconder |
| 5 vendedores sem nenhum deal | aparecem vazios nos filtros | mostrar mesmo assim |
| Os dados terminam em 2017-12-31 | é preciso fixar o "hoje" | data de referência 2017-12-31, configurável |

### O achado central: as features "óbvias" são ruído

Testei cada feature categórica contra uma simulação de acaso puro (2.000 sorteios binomiais com a taxa global de 63,2%):

| Feature | Win rate (mín. a máx.) | p vs. acaso |
|---|---|---|
| Vendedor | 55% a 70% | 0,29 |
| Conta | 53% a 75% | 0,96 |
| Produto | 60% a 65% | 0,49 |
| Setor, região, manager | cerca de 61% a 66% | 0,79 a 0,99 |
| Vendedor × série, vendedor × produto | | 0,21 a 0,24 |
| Idade do deal (até 15 dias ou mais) | 56% contra 68% | < 0,001 |
| Mês de fim de trimestre | cerca de 80% contra 52% | < 0,001 |

- [DADO] Só o tempo carrega sinal. Deals que sobrevivem ganham mais: P(ganho | idade > 90d) = 71%, e com mais de 120 dias, 76%.
- [DADO] O fechamento é bimodal: ou o deal morre rápido (até 15 dias) ou fecha entre 60 e 138 dias. Com idade entre 90 e 138 dias, 86% fechavam nos 30 dias seguintes. Esse número tinha viés de sobrevivência, porque só contava deals já fechados; a seção 7 explica e corrige.
- [DADO] Nenhum deal da história fechou depois de 138 dias. Com referência em 2017-12-31, 1.291 dos 1.589 Engaging (81%) já passaram disso, somando US$ 3,2 mi dos US$ 5,0 mi do pipeline a preço de lista. O pipeline está inflado de zumbis.
- [DADO] O `close_value` fica quase igual ao preço de lista (razão média 0,996), então o preço do produto é um proxy honesto do valor de um deal aberto.

### Onde a IA errou até aqui

- [IA] Na primeira resposta, antes de ver os dados, a IA sugeriu como diferencial frases como *"esse vendedor fecha 40% menos que os pares nessa série de produto"*. O teste de significância mostrou que as diferenças entre vendedor e série não se distinguem do ruído (p ≈ 0,22). Se eu tivesse aceitado, a ferramenta ranquearia deals, e exporia vendedores, com base no acaso. A correção virou regra: nenhuma feature entra no score sem passar no teste contra o acaso, e a interface mostra essas features como contexto, explicando por que não pesam.
- É o que um baseline de "colar o brief" faz: dá peso a setor, vendedor e produto porque parecem relevantes.

## 3. Desenho

- [IA] Propôs uma tela única de segunda de manhã, com três filas (fechar agora, decidir os zumbis, nutrir).
- [EU] Corrigi o escopo. A tela matinal é uma feature, e o produto precisava ser um app de vendas de verdade, com a priorização no centro. Pedi o mesmo que fiz no meu CRM: pegar o melhor do Salesforce e refinar. Uma tela que se abre uma vez na segunda de manhã fica fechada o resto da semana. O vendedor vive no pipeline e na ficha do deal, e é ali que a priorização precisa aparecer, não numa aba separada que ele visita e esquece.
- [IA] Mapeou sete features do Salesforce para uma versão refinada: Meu Dia, Pipeline, Ficha do deal com os "top factors" que passaram no teste, Forecast honesto, Conta 360, Time com intervalo de confiança e "Como o score funciona".
- [IA] Propôs Python com uma SPA estática. [EU] Questionei se não ficaria simples demais, e o resultado foi um motor Python testado, um app em React com TypeScript (Vite) e publicação no GitHub Pages. Não há backend porque os dados são um retrato e o score é calculado em lote, como no próprio Einstein. Também não há LLM em tempo de execução: as explicações são determinísticas, o que o vendedor lê não tem como ser alucinação, e o avaliador não precisa de chave de API.

## 4. Motor de scoring (`solution/engine/`)

- Métrica escolhida nesta primeira versão: score = percentil da receita esperada nos próximos 30 dias, ou seja, preço × P(ganhar em até 30 dias | idade). Juntava valor, chance e momento numa grandeza econômica explicável ("score 85 = entre os 15% com mais receita esperada no mês"). Zumbis iam a 0 e deals jovens caíam porque historicamente ainda não fecham. A seção 7 troca essa fórmula.
- Quatro filas derivadas dos dados, sem limites chutados: fechar (idade ≥ 58 dias, onde pelo menos metade fecha em 30 dias pelo cálculo da época), decidir (idade ≥ 138 dias, o maior ciclo já visto), avançar (jovem) e prospectar.
- Resultado com referência em 2017-12-31: de 2.089 deals abertos, só 236 estavam na janela de fechamento, e 1.301 eram zumbis (US$ 3,23 mi dos US$ 4,97 mi a preço de lista).
- Só biblioteca padrão do Python, sem dependências. 9 testes.

### Onde a IA errou nesta etapa

1. Bug de mutação. A IA serializou as datas para texto no mesmo objeto antes de o teste de significância usá-las. O teste ponta a ponta pegou (`TypeError`), e a correção foi serializar só no final.
2. Número frouxo da exploração. A EDA contou os zumbis como idade > 138 (1.291). O motor usa ≥ 138 (1.301), porque um deal ainda aberto aos 138 dias só fecharia com mais de 138, e isso nunca aconteceu. O teste foi atualizado com o número certo e a justificativa.
3. Comparações múltiplas, o mais importante. A primeira versão rotulou 2 vendedores como acima ou abaixo da média com IC de 95%. Comparando 35 pessoas a 95%, 1 ou 2 falsos positivos são esperados por acaso, e o teste global de vendedor já dava p ≈ 0,3. Rotular essas pessoas seria o ranking injusto que prometemos evitar. A correção usa intervalo com correção de Bonferroni, e um teste garante que nenhum vendedor recebe rótulo enquanto o teste global não mostrar sinal.

## 5. Frontend (`solution/app/`)

- [IA] Carregou a skill de design e fez um plano antes de codar. Como o único sinal real é o tempo, o elemento visual que se repete no app todo é a régua de idade (cedo, janela, além do histórico). A cor indica a fila de ação, e o zumbi ficou em lilás apagado, de "adormecido", em vez de vermelho de alarme. A IA evitou de propósito os clichês de página gerada por IA (fundo creme com terracota, eyebrow em caixa alta, "01/02/03").
- React com TypeScript (Vite), sem dependência além do React. Rotas em hash, que funcionam no GitHub Pages sem configuração. Decisões do vendedor em `localStorage`.
- Sete telas: Meu dia, Pipeline (lista ordenável e quadro), Ficha do deal, Forecast honesto, Contas e Conta 360, Time, Como o score funciona. Filtros de região, manager e vendedor em todas.

### Verificação visual (screenshots em `process-log/screenshots/`)

A extensão do Chrome travou na captura três vezes. Em vez de insistir, a IA passou para o Chrome headless por linha de comando, que também gerou as imagens deste log.

### O que a revisão das telas pegou e foi corrigido

1. Score comprimido, um bug de lógica que só apareceu no visual. Os seis primeiros deals tinham todos 100. A causa: os 1.301 zumbis empatados em 0 ocupavam 62% do ranking, então todo deal vivo caía entre 62 e 100. Correção: percentil só entre deals vivos, com um teste novo garantindo que a escala usa de 0 a 100.
2. Forecast inflado pela prospecção. A primeira versão contava os deals em Prospecting a 63% de chance, uma taxa que vem de deals que já engajaram, e não há dado de quantos prospects engajam. Correção: a prospecção saiu do "esperado" e aparece separada. O esperado caiu de US$ 1,2 mi para US$ 472 mil; a diferença era número inventado. Esse é o número que a liderança leva para a reunião de metas, então inflar em US$ 700 mil não é um detalhe de tela: é prometer uma receita que os dados não sustentam.
3. Um achado novo, que só apareceu no forecast por região: os 500 deals em prospecção são todos da Central, e todos os 408 Engaging da Central já passaram de 138 dias. A Central não tem nenhum deal vivo em negociação, com o topo do funil parado e o meio morto. O app passou a mostrar um alerta quando um grupo fica nessa situação, e o Meu dia muda a mensagem: a semana é de destravar o funil.
4. A curva despencava no fim, por ruído em idades com menos de 30 deals. Ela deixou de ser desenhada abaixo de 30.
5. Correções menores: régua quase invisível no modo escuro; colunas numéricas alinhadas à esquerda (conflito de especificidade no CSS); "1 que você já decidiu ficam" (concordância, e a contagem ignorava o filtro); "0 deals… Comece por eles"; p-valor com ponto em vez de vírgula.

### Teste funcional no navegador

A decisão "Encerrar" persiste e tira o zumbi da fila. O filtro Região=West com Vendedor=Hayden vira "Bom dia, Hayden." com 5 deals na janela. A busca e a contagem de decididos respeitam o recorte.

## 6. Documentação e verificação final

- README da submissão no template do desafio, com Setup, Lógica, Limitações, Recomendações e um resumo do Process Log.
- Cada número do README foi conferido contra o `data.json` antes de ficar no texto. Dois p-valores estavam arredondados diferente do que o app mostrava (0,96 virou 0,95 e 0,49 virou 0,48) e foram alinhados.
- Clone limpo da branch: testes do motor passando, o motor regenerando os dados e `npm ci` com build do app funcionando, que é o caminho que o avaliador vai seguir.
- [IA] Errou no git. O `.gitignore` da raiz do repositório ignora `submissions/`, o que contradiz o CONTRIBUTING, e a regra do PR não deixa alterar esse arquivo. O `git add -f` usado para contornar isso passou por cima também do `.gitignore` interno e colocou `node_modules/`, `dist/` e caches do Python no commit. A revisão do commit pegou antes de qualquer push, e a correção foi adicionar só a lista explícita de arquivos-fonte.

## 6b. Identidade G4, shell do sistema e bot de notificação (commit `513b767`)

Registrado na auditoria da seção 17, a partir do commit.

- Redesign do app com a identidade da G4: navy e ouro, Libre Caslon Text nos títulos e Manrope nos dados, com tema claro e escuro, mantendo a lógica e os dados.
- Shell de sistema: topbar com logo, busca global, contador de decisões pendentes e exportação em CSV; barra lateral com ícones e um rodapé que mostra o escopo do filtro.
- KPIs no Meu Dia (receita esperada, janela de fechamento, aguardando decisão), cada um com a proporção real que o sustenta.
- Na fila "Decida o destino", o score (sempre 0) e a régua (sempre no fim) não diferenciavam nada. A linha passou a mostrar os dias parado e o valor que o deal soma ao forecast.
- Largura do conteúdo de 1140 px para 1440 px, para não deixar metade de uma tela grande vazia, com o texto editorial mantendo a própria medida.
- O logo fornecido entrou no lugar do compasso desenhado à mão, e o favicon saiu dele.
- Motor: testei o tamanho da conta (receita anual e funcionários) com uma busca do melhor corte binário e significância por permutação. Não bate o acaso (p = 0,66 e 0,77), então não entrou no score.
- Primeira versão do bot de notificação (`notify.py`), que reformata as filas e ações do Meu Dia para terminal, Slack ou email, sem LLM.

## 7. Auditoria pós-entrega (achado grave no motor)

Antes de abrir o PR, pedi a uma segunda sessão do Claude Code (Claude Opus 5.5) que auditasse a submissão como um avaliador externo faria, sem o contexto de quem construiu: comparar o que estava pronto com o brief do challenge 003, rodar os testes e conferir os números do `data.json` à mão, sem se basear só no README.

[IA, auditoria] Achou dois problemas de lógica:

1. `fit_curve` só aprendia com deals fechados (Won e Lost). Um deal aberto há 90 dias que ainda não fechou é evidência de que 90 dias não garantem fechar em 30, e ele não entrava em nenhuma conta. Por isso a curva dizia que 91% dos deals com 95 dias fecham em 30 dias, um número otimista por construção (viés de sobrevivência), justo no texto que o README apresentava como "zero alucinação". Recalculando com os abertos como censura à direita (eles contam como "não fechou" só depois de observados pela janela inteira sem fechar), a mesma idade cai para cerca de 40%. Depois da correção, nenhuma idade chega perto de 50%, e a antiga janela de "≥ 58 dias, ≥ 50%" deixou de existir. Na prática, um funil que se pinta mais saudável do que é faz o gerente confiar num número que não vai se cumprir, e deixar de empurrar justamente os deals que estão travando.
2. O score como percentil da receita esperada tinha correlação de 0,90 (Spearman) com o preço do deal. Os 12 primeiros do ranking eram sempre os produtos mais caros. O brief pede explicitamente que não seja "só ordenar por valor", e na prática era quase isso.

[EU] Corrigi:

- `fit_curve` passou a receber as idades dos deals abertos e a contá-las no denominador de `close_soon` e `win_soon` (censura à direita). A janela de fechamento deixou de ser um limiar absoluto (≥ 50%) escolhido sobre uma curva que eu supunha crescente. Com a correção a curva sobe, tem um pico (75 dias, 44%) e cai. Passei então a achar o vale depois da mortalidade inicial e subir dali até a curva cruzar metade do pico. Os números continuam vindo dos dados; o algoritmo só passou a respeitar o formato real da curva.
- O score virou `P(ganhar em 30 dias | idade)`, uma probabilidade, e deixou de depender do preço (a correlação com o preço caiu de 0,90 para 0,18). Zumbi e prospecção ficam sem score, porque não têm histórico confiável de curto prazo; antes eles tinham um "0" que parecia dizer "chance zero". A prioridade das filas continua sendo a receita esperada (valor × chance), agora como um número separado do score na tela. Um ranking que no fundo é só o preço já existe em qualquer CRM, e o vendedor aprende a ignorar, porque sabe que o deal mais caro nem sempre é o que fecha esta semana. O que ajuda a decidir é a chance, e era exatamente ela que o preço estava escondendo.
- Efeito colateral bom: o `ev` e o `ev_soon` da prospecção agora são sempre 0, porque não se conhece a taxa de conversão de prospecção para Engaging. Com isso, o card "Receita esperada" do Meu Dia e o "Esperado" do Forecast, que antes divergiam porque um somava tudo e o outro só os Engaging, passaram a bater sem precisar sincronizar duas fórmulas.
- 2 testes novos no motor (`test_censoring_pulls_close_soon_down` e `test_prospecting_and_zombie_have_no_score`) para travar os dois problemas.

Isso não teria aparecido numa revisão visual das telas, que já tinha sido feita. Só apareceu comparando, de fora, os números do JSON com a definição matemática deles. É o exemplo mais forte deste log de desconfiar do próprio output: com os testes passando e as telas revisadas, o número que o vendedor lia estava errado.

## 8. Questionando o conserto

Depois que a IA corrigiu os dois problemas da seção 7, não aceitei a correção como pronta só porque os testes passaram. Rodei um segundo review adversarial com o Codex (`/codex:adversarial-review`), um modelo diferente do que fez a correção, pedindo explicitamente que questionasse se a implementação estava certa, além de procurar bugs. A ideia era não deixar a IA corrigir a própria lição de casa sem outro olhar conferindo.

[Codex] Achou 2 problemas no que a correção deixou:

1. O `PRODUCT.md`, o "manual" do produto, continuou descrevendo a fórmula antiga do score (percentil × preço, zumbi = 0) quando o código já usava a nova (chance de ganhar em %, zumbi e prospecção sem score). Quem lesse só o manual ia achar que o código estava errado.
2. A janela de fechamento pode estar apoiada num pico instável da curva. O código pega a idade com a maior chance histórica de fechar logo (o pico) e usa metade dela como fronteira da janela. Só que "o maior entre várias idades" é sensível a solavancos de amostra pequena, do mesmo jeito que tirar 7 caras em 10 jogadas não prova que a moeda é viciada. O corte de 30 deals por idade ajuda, mas não garante que o pico escolhido é real; com dados um pouco diferentes, a fronteira pode mudar de lugar sem aviso.

[EU] Entendi cada achado antes de mandar corrigir. Pedi para a IA explicar os dois em linguagem simples, sem termo técnico, antes de decidir o que fazer. Não bastava a IA dizer "achei 2 problemas, corrigindo": eu precisava entender o mecanismo de cada um para julgar se a correção proposta fazia sentido.

É o padrão que quero deixar registrado. A IA implementa, e a decisão de aceitar ou mandar de volta para revisão é minha. Passar a correção por um segundo review antes de considerá-la pronta faz parte do processo, na primeira versão e também na correção da correção.

Situação dos dois achados, atualizada na seção 17: o primeiro só foi corrigido na auditoria final, e o segundo continua aberto e está nas Limitações do README.

## 9. Questionei o bot também

Antes de dar o bot de notificação por pronto, perguntei se ele fazia sentido, já que só dispara com webhook ou email configurado. Não aceitei a resposta óbvia ("sim, é assim que bot funciona") e pedi para examinar o que acontece antes do envio: de onde vem o destino de cada um dos 35 vendedores. A resposta foi que de lugar nenhum. O `sales_teams.csv` não tem email nem Slack ID, então "mandar a fila para cada vendedor sem abrir o app" (a frase do resumo executivo) exigia rodar o comando 35 vezes à mão, digitando o destino certo em cada uma. Era um formatador de mensagem acionado uma vez de cada vez. Ninguém roda um comando 35 vezes na segunda de manhã, então na prática o bot não seria usado, e o resumo executivo prometia algo que a ferramenta não entregava.

[EU] Decidi fechar esse buraco com o menor código que resolvesse de verdade. `--all` roda o digest dos 35 vendedores do roster numa chamada só, e `--targets targets.json` (um arquivo opcional, documentado em `targets.example.json`) dá o destino de cada um. Sem o arquivo, o bot continua no modo seguro de sempre: só imprime e não envia nada. Esse arquivo é dado que eu criei, sem origem no CSV do Kaggle, e documentei isso como um artefato que a RevOps manteria na vida real.

## 9b. Auditoria da barra lateral e da topbar (commit `b659261`)

Registrado na auditoria da seção 17, a partir do commit.

- O contraste de "Workspace" e de "Dados até…" estava abaixo de 4,5:1 contra o navy e foi ajustado. O mesmo ajuste valeu para o placeholder da busca e para o nome do vendedor nos resultados.
- O chip de escopo sumia no celular. Passou a ficar fixo fora da área que rola, e com filtro ativo virou um botão que limpa os filtros.
- Bug na busca global: ela filtrava pelo recorte ativo (região, manager, vendedor), então um deal fora do recorte sumia da busca sem aviso. Passou a buscar na base inteira, e "Ver todos os N resultados" limpa o filtro antes de ir para o Pipeline, para não prometer N e mostrar menos. Verificado no navegador: com o filtro Central, a busca "Hayden" achava 0 e passou a achar 50.
- O contador da fila Decidir passou a respeitar o limite "99+" que o DESIGN.md já descrevia, mantendo o número exato no `aria-label` para leitor de tela. A contagem de resultados da busca passou a ser anunciada por `role="status"`.
- A página "Como o score funciona" ganhou o rótulo "Método" no menu. Ela sairia do produto logo depois (seção 10).
- CSS morto removido (`.topbar-scope`).

## 10. Tirei a explicação do produto de dentro do produto

Pedi um unslop nos textos do app (adjetivo sem dado atrás, como "Forecast honesto") e, na mesma conversa, perguntei se a tela "Como o score funciona" fazia sentido dentro do app ou se bastava documentar no GitHub. A primeira resposta da IA foi defender a tela, porque o brief pede explicabilidade e a tela linkava a ficha do deal. [EU] Corrigi: explicabilidade é mostrar o motivo de cada dado junto do dado. Uma aba separada explicando como o produto foi construído é outra coisa, e documentar as métricas por trás da inteligência é processo, fora do MVP.

Isso separou duas coisas que a resposta anterior misturava:

- Decisão, que fica no produto: por que este deal tem este score, a taxa do vendedor com a faixa de confiança e o histórico da conta. Boa parte já estava na ficha do deal. Faltava estar também nas listas (Meu dia, Contas), e o motivo virou uma linha visível em cada `DealRow`.
- Construção, que sai do produto: a tabela de significância completa, a curva genérica, as correções de dado e o motivo estatístico por trás de "ninguém foi ranqueado" no Time. Tudo isso já estava no README e no `scoring.py`. A tela `/metodo` repetia a mesma informação dentro do app com a moldura errada, como manual do produto, quando o papel dela era de prova de auditoria.

Removidos: a página inteira (`Method.tsx`), o item de menu, o link "Ver os testes" da ficha do deal (que levava a uma tela que ia sumir e citava um p-valor que o vendedor não precisa ler) e as citações de p-valor no Time e na ficha. Ficou só o veredito em português ("dentro da média do time"). O motor continua calculando tudo isso (`significance` no `data.json`); a tela é que parou de mostrar.

No mesmo commit (`e3b9a12`) entrou a decisão em lote na fila Decidir do Pipeline: checkbox por linha, "selecionar todos os visíveis" e requalificar ou encerrar em lote. Vale só nessa fila, porque são 1.301 deals que nenhuma característica distingue; nas outras, cada deal pede julgamento próprio.

## 11. Sugestão de ação na fila Decidir, e o limite que eu não ia deixar passar

Depois da decisão em lote, pediram uma sugestão de qual deal encerrar ou requalificar e por quê, com a observação de que podia ser Python ou ML em vez de LLM. Antes de escrever código, precisei resolver uma tensão que o pedido não via: o zumbi ainda está aberto. Não existe rótulo de ganho ou perda para um classificador aprender, e é justamente por isso que a fila se chama "decidir". Treinar qualquer coisa supervisionada em cima disso seria inventar um desfecho que os dados não têm, o mesmo tipo de alucinação que o projeto evita desde a seção 1.

[EU] Recusei a versão fácil, um modelo bonito sem dado para sustentar, e construí o que os dados respondem: uma função de triagem, que não faz previsão. São duas variáveis honestas: se há conta vinculada, e quanto o deal passou da mediana de "dias além do maior ciclo" (mediana calculada dos próprios 1.301 zumbis, sem escolha à mão, pelo mesmo princípio do `window_start`). Documentei isso no código e no README como o que é: uma forma de priorizar a revisão, sem prever resultado.

Reaproveitei a infraestrutura que já existia. A sugestão vira o `action` do deal, o mesmo campo que a ficha do deal, a tabela do Pipeline e o bot de Slack e email já leem, e com isso o `notify.py` passou a mandar a razão certa para cada zumbi sem eu mexer numa linha do bot. Os botões "Requalifiquei" e "Encerrar como perdido" passaram a destacar o sugerido, e o botão "selecionar sugeridos para encerrar" do Pipeline liga direto na decisão em lote. O motivo e a ação em lote acabaram se encaixando.

## 12. Fechando o ciclo da decisão em lote: confirmação, desfazer, nota e portabilidade

Numa sessão seguinte do Claude Code, levantei quatro furos que a mecânica original da decisão em lote tinha deixado e tratei como conserto e acabamento. A ordem reflete a prioridade: o primeiro era um risco de operação, e os outros são ergonomia de decisão.

12.1 Confirmação e desfazer em lote (`pages/Pipeline.tsx`, `styles.css`). A decisão em lote aplicava na hora e sem volta: clicar "Encerrar como perdido" com 42 deals selecionados encerrava os 42 sem como reverter. Agora o botão abre uma confirmação ("Confirma encerrar 42 deals?") que só aplica no "Sim, confirmar", e logo depois aparece um aviso de desfazer ("42 deals encerrados como perdido. Desfazer") que reverte o lote inteiro com um clique. Não há timer: o aviso fica até a próxima ação em lote ou até o desfazer, o mesmo padrão do "Desfazer" por deal na ficha, para o vendedor não perder a chance de corrigir por hesitar alguns segundos.

12.2 Nota por decisão (`components.tsx`, `data.ts`, `main.tsx`, `styles.css`). "Requalifiquei" e "Encerrar" marcavam o deal sem guardar o motivo. Entrou um campo de texto opcional ao lado da decisão ("falei com o cliente, a decisão sai em fevereiro"), gravado no mesmo `localStorage` da decisão (`note?` no tipo `Decisions`), sem backend novo. Quando o vendedor voltar ao deal daqui a três meses, o motivo está lá. Um detalhe: editar só a nota preserva o `at` original da decisão, para a nota não mudar a data em que o deal foi decidido e bagunçar o histórico.

12.3 Exportar e importar decisões (`main.tsx`, `styles.css`, README). A limitação documentada é real: a decisão só existe naquele navegador. A barra lateral ganhou "Baixar decisões (N)" e "Importar decisões", que geram um JSON com as decisões e importam de volta validando o formato, reaproveitando o `downloadBlob` do "Exportar CSV". Não resolve o uso em vários dispositivos (o README diz que isso não sincroniza nada), mas permite levar as decisões de um navegador para outro e fazer backup antes de limpar o cache.

12.4 Tooltip nos gráficos (`components.tsx`, `pages/Forecast.tsx`, `pages/Team.tsx`, `styles.css`). A curva e a barra empilhada eram SVG estático, sem valor exato ao passar o mouse. Na curva, o hover converte a posição do mouse numa idade e mostra um tooltip ("42 dias · Ganhar: 33% · Fechar em 30d: 41%"); o marcador muda de cor no hover para não se confundir com o marcador fixo do deal. Com isso a curva serve para consultar qualquer idade. Na barra do Forecast, cada segmento virou um link com `title` e `aria-label` ("Fechar: US$ X em N deals") que leva ao filtro `?fila=`. A faixa de taxa do Time também ganhou tooltip com a faixa de confiança.

Registro de processo: esta sessão rodou perto do limite de requisições da ferramenta e parou antes do fim, sem exportar a conversa. As quatro mudanças foram conferidas no código contra as funções auxiliares (`int`, `plural`, `moneyShort`, `sum`, `pct`) e os módulos importados (`BUCKETS`, `BUCKET_ORDER`), sem referência a símbolo inexistente. O `npm run build` não rodou nesta sessão porque o Node não estava disponível no ambiente; o build e o `dist/` foram refeitos na seção 13.

## 13. Topbar e filtros centralizados

Numa nova passada de design com o Impeccable (os playbooks de layout e de "craft floor", a parte que lista os vícios de interface gerada por IA), pedi para deixar o topo da tela e a faixa de filtros alinhados ao centro, em vez de tudo encostado na esquerda.

Por que estava torto: `main` e `.filters` não compartilhavam coluna, cada um tratava o próprio eixo, e o `.topbar-search` empurrava para a esquerda com `margin-left`. A identidade, a busca e as ações da topbar, e os campos de filtro, ficavam colados no canto, sem equilíbrio em tela larga.

O que mudou em `styles.css`:

- `main` e `.filters` passaram a compartilhar `max-width: 1440px; width: 100%; margin-inline: auto`, uma coluna centralizada. Filtros e conteúdo ficam no mesmo alinhamento, e em tela larga sobra espaço dos dois lados.
- `.topbar-search` trocou `flex: 1 1 22rem; margin-left: 1.25rem` por `flex: 0 1 42rem; min-width: 12rem; margin-inline: auto`, e a busca fica centralizada no espaço entre a identidade e as ações.
- A faixa de filtros era um vidro translúcido genérico (`blur(10px) saturate(1.05)`, o glassmorphism de template). Virou um papel quase sólido (`96%` de paper, `blur(6px)`, sem aumento de saturação) com um filete de 1 px embaixo.

No mesmo commit (`f0b190d`) entraram duas coisas no Pipeline: o desfazer em lote ficou flexível (dá para escolher à mão, por pesquisa com uma lista de nomes, ou todos) e surgiu a aba "Encerrados na última semana", uma revisão de higiene do funil que só aparece quando há encerramentos na semana.

[EU] Verifiquei pela geometria renderizada, sem screenshot, porque o modelo daquela sessão não lia imagem. O runtime mediu as caixas (`getBoundingClientRect`) de `main`, `.filters`, `select`, `pageHead`, `toolbar`, `search`, `brand` e `actions` em três telas (`#/pipeline`, `#/`, `#/forecast`) e no celular (390 px):

- Desktop, 1920 px: `main` e `.filters` ocupam exatamente a mesma faixa (l=357 a 1797, w=1440). `pageHead`, `toolbar` e o primeiro `select` começam no mesmo recuo interno (l=397). A busca fica centralizada entre a marca (l=20) e as ações (l=1563), com cx≈805.
- Celular, 390 px: `main` e `.filters` ocupam a largura toda e o `select` começa no padding certo (l=16). Essa medição só olhou a borda esquerda, e a seção 17 achou que a página inteira vazava pela direita no celular.
- O `detect.mjs --scope layout` do Impeccable voltou `[]`, sem defeito, no CSS final.

O `npm run build` passou limpo e o `dist/` foi reconstruído. O commit ficou local, sem push, para visualização em `http://127.0.0.1:8099`.

## 14. Cinco melhorias de decisão no Meu Dia

Depois da seção 13, a direção pedida foi melhorar o design e a inteligência de verdade: sair da aparência e olhar o momento em que a tela ajuda, ou deixa de ajudar, o vendedor a decidir. As mudanças vieram do que o motor já calculava e a tela não mostrava, e foram agrupadas em cinco itens.

14.1 Direção geral: expor o que já existe, sem criar score novo. O motor (`scoring.py`) já calcula o `ev_soon` (receita esperada em 30 dias), o `suggested_action` (encerrar ou confirmar na fila Decidir) e a curva `win_soon` (chance de ganhar por idade). As melhorias usam só esses três e nenhum número novo foi criado, mantendo a regra de nenhuma feature sem dado atrás. A inteligência nova está na navegação: o que eu faço agora, em quantos grupos a fila se divide, onde a semana trava.

14.2 Item 1, ação do momento. Um card no topo do Meu Dia mostra o deal de maior `ev_soon` da fila Fechar, com o texto do seu `action` e o link para a ficha. É o que o vendedor vê ao abrir a ferramenta na segunda de manhã, a cena que o challenge descreve. Antes isso era só a primeira linha de uma fila; agora é uma decisão com nome. Não há score novo: o card escolhe o topo de um ranking que `PRIORITY.fechar` já ordena.

14.3 Item 2, agregado da fila Decidir. A fila tem 1.301 deals. O `decide-split` mostra "1.102 para encerrar | 199 para confirmar antes", com os dados reais do `suggested_action`, e um link "Ver todos". A fila vira uma decisão de gestão com dois números, e o detalhe de cada deal continua a um clique.

14.4 Item 3, saúde do funil. Uma faixa discreta com os sinais do que trava a semana: deals parados além do ciclo (em % do aberto), prospecção sem negociação viva (gargalo de engajamento) e deals sem conta vinculada. Os dois últimos só aparecem quando o recorte tem mesmo esse desequilíbrio, para não virar alarme falso.

14.5 Item 4, destaque do deal mais quente na fila Fechar. O pico da curva (`win_soon` máximo, calculado a partir dos dados por `peakAge`) marca o deal mais próximo dele com o selo "no pico" e destaque na régua, e o primeiro da fila recebe uma faixa lateral. A cor continua indicando a fila e só marca a urgência relativa dentro dela. Na seção 15 a fila virou tabela: o selo foi para a coluna Dias e a faixa lateral ficou na linha do deal da ação do momento.

14.6 Item 5, fim do glassmorphism. A última superfície translúcida (`.filters`, com `backdrop-filter: blur`) virou papel sólido (`var(--paper)`, com a hierarquia dada por borda e sombra). No modo escuro vira uma faixa navy coerente. Confirmado por CDP: `backdropFilter: "none"`.

[EU] Verifiquei pela geometria renderizada e pela contagem de nós no runtime, já que o modelo daquela sessão não lia imagem. No Meu Dia (`#/`) com 1680 px, `razor`, `health-strip` e `decide-split` ficaram alinhados à coluna central (l=284, r=1630, off=122); `hotRows=1`, `peakedRows=1`, `peakBadges=1`; o texto do agregado era "1.102 para encerrar | 199 para confirmar antes | Ver todos"; `filtersBg: "none"`. No celular (390 px) os três alinharam à largura (l=18). O `detect.mjs --scope layout` voltou `[]`, o `npm run build` passou limpo e o `dist/` foi reconstruído.

Os commits das seções 13 e 14 (`f0b190d` e `e0892ff`) ficaram locais, sem push, para a análise visual em `http://127.0.0.1:8099`.

## 15. O visual do Meu Dia a partir de um mockup do Claude Design

[EU] Trouxe um mockup do Claude Design ("Lead Scorer Dashboard") e pedi para deixar o design igual a ele, mantendo os dados e a inteligência atuais: copiar só a aparência.

[IA] O link é privado e não abre por WebFetch, então a IA abriu pela extensão Claude in Chrome, na minha sessão logada. O mockup tinha as mesmas telas e a mesma estrutura do app, e a IA concluiu que a diferença principal era o tema: o app só ficava escuro com o sistema operacional em modo escuro, e o mockup é escuro. Ela trocou o padrão para o tema escuro e deixou o claro disponível por `data-theme="light"`, que hoje não tem controle na interface.

[EU] Pedi uma auditoria da prévia contra o resultado, com nota de 0 a 10, e correções até chegar a 9 de semelhança. [IA] A comparação lado a lado deu cerca de 6 para a parte de baixo da página. A maior diferença era "Feche esta semana": no mockup é uma tabela (Deal, Score, Probabilidade, Dias, Próxima ação), e no app era uma lista de cards com a régua de idade. Enquanto a IA comparava, [EU] restringi o escopo: copiar só dos KPIs para baixo, e manter como estava tudo o que fica acima, os KPIs inclusive.

[IA] Reescreveu "Feche esta semana" como tabela, reaproveitando os estilos da tabela do Pipeline. As colunas usam campos que o motor já calculava (score, `win_prob`, idade e `action`). A linha do deal da ação do momento ganhou a mesma faixa dourada que a fila Fechar tem no Pipeline, e o selo "no pico" foi para a coluna Dias. Depois disso, a IA deu nota 9.

[IA] Não copiou as cores da coluna Dias. No mockup, 42 e 95 dias aparecem em verde, 61 e 74 em amarelo e 118 em vermelho, sem nenhuma regra que se derive da idade ou do score. Colorir por enfeite contradiz o princípio de que a cor indica a fila. Essa coluna continua diferente do mockup.

[EU] Olhei no navegador e disse que ainda não estava igual. Pedi a cor de fundo e tudo a partir de "Ação do momento" exatamente como na referência.

[IA] Refez a comparação com zoom na referência e achou o que tinha deixado passar:

- o fundo da página é mais escuro e mais neutro;
- os dois avisos de saúde do funil ficam em caixas separadas, e no app estavam na mesma caixa;
- o card "Ação do momento" é plano, sem tinta dourada e sem faixa de cabeçalho, e "Abrir ficha" é um botão com borda;
- o score fica dentro de um anel de progresso com arco proporcional ao valor (91 quase fecha o círculo, 76 deixa um vão maior).

O anel foi feito com `conic-gradient` a partir do próprio score. Como o componente `Score` é compartilhado, ele vale também no Pipeline, no quadro, na ficha do deal e nos resultados da busca do topo. Deal sem score continua com um círculo sem anel, para não sugerir 0%. [IA] Conferiu o Pipeline e a ficha do deal no navegador depois da troca, justamente por ser um componente compartilhado, e verificou que o miolo do anel acompanha o fundo navy do cabeçalho da ficha.

[IA] O detector do Impeccable apontou a borda esquerda de 4 px do painel "O que fazer" da ficha. A IA classificou como intencional e silenciou a regra para o `styles.css` inteiro. Foi um exagero, porque um ignore desse tamanho esconderia qualquer ocorrência futura no arquivo. A seção 17 desfaz.

## 16. As outras abas, o nome da primeira aba e uma sessão em paralelo

[EU] Pedi para melhorar e alinhar o design das outras abas. [IA] Rodou o detector do Impeccable (sem achados) e revisou cada aba no navegador. O desalinhamento vinha de um lugar só: com o fundo mais escuro da seção 15, os cards e as tabelas ficaram claros demais em relação à página, um salto de brilho que o mockup não tem e que aparecia em todas as abas. A IA aproximou `--surface` e `--surface-2` do fundo e ajustou as bordas, que passaram a fazer a separação. O contraste do texto foi recalculado e ficou entre 6,1:1 e 14,8:1, acima dos 4,5:1 que a WCAG pede.

[EU] Pedi para trocar "Meu dia" por "Overview" ou outro nome que coubesse melhor. [IA] Manteve "Overview", que combina com Pipeline e Forecast, e trocou o rótulo na navegação e no link da página 404. O arquivo e o componente continuam se chamando `MyDay`.

Durante essas duas seções, outra sessão do Claude Code (Claude Sonnet 5) trabalhou no mesmo repositório e fez o commit `35bee14`. Nele, "Ação do momento" virou um `h2` (o DESIGN.md já tratava o rótulo em caixa alta acima de um título como defeito), o painel "O que fazer" perdeu a borda esquerda de 4 px, a paginação do Pipeline trocou as setas unicode por SVG, e o `DealRow` perdeu as props `hot` e `peakGap`, que tinham ficado sem uso depois da tabela da seção 15. O commit também levou as mudanças das seções 15 e 16 que estavam na árvore de trabalho, menos a troca do nome da aba, que veio depois. [IA] Percebeu os arquivos mudando no disco, conferiu que as mudanças eram coerentes (nenhum chamador usava mais `hot` ou `peakGap`) e continuou a partir delas, sem reverter.

## 17. Auditoria final contra o brief

[EU] Pedi uma vistoria do que está feito contra os requisitos do challenge e a atualização dos arquivos, com o texto escrito usando a skill humanizer.

### Requisitos do challenge

| Requisito | Situação | Como foi conferido |
|---|---|---|
| A solução roda | Sim | `npm run build` limpo; 14 testes do motor e 8 do bot passando |
| Usa os dados reais | Sim | Os quatro CSVs do Kaggle, 8.800 oportunidades, com as correções da seção 2 |
| Tem lógica de scoring além de ordenar por valor | Sim | O score é a chance de ganhar em 30 dias pela idade, sem o preço; a ordem das filas usa a receita esperada, como número separado |
| O vendedor entende o porquê | Sim | Motivo em cada linha das listas e na ficha, e uma ação recomendada por deal |
| Documentação: setup, lógica e limitações | Sim, com as correções abaixo | README |
| Process log | Sim | Este arquivo, os screenshots e o histórico do git |
| Bônus: filtro por vendedor, manager e região | Sim | Em todas as telas, em cascata |

### O que a auditoria achou e corrigiu

1. O layout vazava no celular. Numa tela de 390 px, a página inteira ficava com 712 px, e as ações do topo, os filtros, os títulos, os cards e as tabelas saíam pela direita. O Chrome headless não aceita janela menor que 500 px, então a primeira captura "de celular" era um layout de 500 px cortado em 390; para medir de verdade, a IA renderizou o app dentro de um iframe de 390 px servido pela mesma origem. A causa estava no grid: com `1fr`, a coluna não encolhe abaixo do conteúdo mínimo do item mais largo, que era a fila de links da navegação (sem quebra de linha) somada ao chip de escopo. A correção foi `minmax(0, 1fr)`. Medido depois: em 390 px, Overview, Pipeline, Forecast e Time ficam exatamente da largura da tela, a navegação e as tabelas rolam dentro de si, e o desktop não mudou (244 px de barra lateral mais o conteúdo). A versão antiga cabia na tela (`08-mobile.png`), então a regressão entrou em algum ponto depois, e a medição da seção 13 não pegou porque só olhou a borda esquerda.
2. O README tinha números e textos que o código já não produzia:
   - o exemplo de saída do bot mostrava o texto antigo da fila Decidir, de antes da sugestão por deal da seção 11;
   - "os que sobrevivem ganham de 68% a 83%": o máximo da curva é 77%, aos 125 dias;
   - "a janela de fechamento (44 a 138 dias) é onde essa chance está em pelo menos metade do pico": a chance cai abaixo da metade do pico aos 114 dias, e a janela vai até 138 porque esse é o maior ciclo já fechado;
   - a tabela de significância não trazia o tamanho da conta (p = 0,66 e 0,77), que o motor testa desde a seção 6b e que o brief cita como feature óbvia;
   - "existiu uma sexta tela": era a sétima.
3. O `PRODUCT.md` ainda descrevia a fórmula antiga do score (o achado 1 do Codex, seção 8), listava "Meu dia" e "Como o score funciona" entre as telas, dava as superfícies em marfim como padrão e apontava para um registro de marca que fica fora da submissão. Foi corrigido.
4. O achado 2 do Codex (a janela apoiada num único máximo da curva) continua aberto e entrou nas Limitações do README.
5. O ignore amplo do detector, da seção 15, foi removido. A borda que ele silenciava já tinha saído no commit `35bee14`, então o ignore só servia para esconder achados futuros.
6. Screenshots novos da versão atual: `12-overview.png`, `13-deal.png`, `14-forecast.png`, `15-pipeline.png` e `16-mobile.png`. Os de 01 a 11 ficam como registro das versões anteriores.

Cada número citado no README foi recalculado nesta auditoria a partir do `data.json` e dos CSVs: 65% do pipeline declarado parado (US$ 3.227.151 de US$ 4.966.215), 1.301 zumbis, 259 deals na janela, a divisão de 1.102 e 199 na fila Decidir, a Central com 408 parados, 500 em prospecção e nenhum deal vivo, 56% de ganho para quem fecha em até 15 dias contra 68,5% depois disso, o pico aos 75 dias (44%) e os 5 deals na janela do Hayden.

### O que ficou pendente, depois desta auditoria

- O README ainda tem os campos do template para preencher: nome, LinkedIn e data de envio.
- O PR não foi aberto. O título precisa seguir o formato `[Submission] Nome — Challenge 003`.
- O `DESIGN.md` ficou desatualizado: descreve o tema claro como principal, traz as cores do tema claro nos tokens e a régua de idade na fila Fechar. Ele não foi reescrito à mão porque o caminho previsto é o `/impeccable document`, que regenera o arquivo a partir do código.

## 18. Commit, branch no GitHub e publicação

Com as correções da seção 17 prontas, pedi para aplicá-las, garantir que a pasta `.impeccable/` da raiz não fosse commitada, remover a exigência de chat export e publicar a branch e o app.

[EU] Antes de mexer no git, chequei três coisas: se o `.impeccable/` da raiz estava rastreado (não estava), se algum arquivo fora de `submissions/hisdevotions-afk/` tinha mudado desde `origin/main` (nenhum) e se as branches locais e remotas batiam com o que o CONTRIBUTING espera. Achei que a branch `main` local tinha 5 commits de submissão que nunca foram enviados ao GitHub, provavelmente porque o trabalho começou direto em `main` antes de a branch `submission/hisdevotions-afk` existir. Como o `origin/main` do fork ainda está limpo (na mesma versão do template), decidi não empurrar `main`: só a branch de submissão foi enviada, para não levar commits de submissão para dentro de `main` no GitHub.

O que fiz:

1. Adicionei `.impeccable/` ao `.git/info/exclude` (arquivo local, nunca versionado) como rede de segurança extra contra um `git add -A` por engano.
2. `git add` explícito dos cinco arquivos alterados e `git add -f` dos cinco screenshots novos, um por um. Conferi a lista de arquivos staged antes de commitar: nenhum tocava fora de `submissions/hisdevotions-afk/`, e nada de `dist/`, `node_modules/`, cache do Python ou `.impeccable/`.
3. Rodei de novo o build e as duas suítes de teste (14 do motor, 8 do bot) antes do commit.
4. Commit na branch `submission/hisdevotions-afk` e `git push -u origin submission/hisdevotions-afk`. A branch existe agora em `github.com/hisdevotions-afk/ai-master-challenge`.
5. Para o GitHub Pages, criei uma branch `gh-pages` numa worktree separada (órfã, sem histórico da submissão), copiei o `dist/` do build para a raiz dela, adicionei um `.nojekyll` e fiz o push. Essa branch é só hospedagem: não entra no PR e não compartilha histórico com `submission/hisdevotions-afk`.
6. Ativei o GitHub Pages pela API (`gh api`) apontando para `gh-pages` na raiz, e acompanhei o build até o status virar `built`.
7. [EU] Verifiquei o site publicado no navegador, não só o status da API: a Overview carrega com os dados reais, o `data.json` responde 200, não há erro no console, e a navegação por hash (`#/pipeline`) funciona sem configuração de servidor, porque o Pages serve arquivo estático puro.
8. Atualizei o README com a URL publicada: `https://hisdevotions-afk.github.io/ai-master-challenge/`.

Não abri o PR. Faltam os campos do template (nome, LinkedIn, data), e abrir o PR é o passo que efetivamente inscreve a submissão. Isso fica para quem vai preencher esses campos e revisar o resultado antes do envio.

## 19. Tipografia, hierarquia e centralização

[EU] Pedi correções de tipografia, hierarquia, centralização e espaçamento: os textos pareciam agrupados à esquerda da tela, com pouco respiro.

[IA] Antes de mexer em CSS, mediu a página renderizada em vez de supor o problema pelo código. Num viewport de 1920px, o cabeçalho de cada tela (h1 e o parágrafo de resumo) ficava limitado a 72ch de largura (cerca de 660px) e colado na borda esquerda do canvas, enquanto os cards de KPI e as tabelas logo abaixo ocupavam a largura inteira (por volta de 1360px). Isso deixava um vão vazio de mais de 700px ao lado do título, exatamente o efeito de "texto grudado à esquerda" descrito no pedido.

A segunda medição, num viewport de 1440px (o tamanho mais comum de notebook, e bem mais realista que um monitor ultrawide), mostrou uma causa adicional: o `main` e a faixa de filtros já tinham `max-width: 1440px` com `margin-inline: auto`, mas esse auto-centering só existe quando a tela sobra além de 244px de barra lateral mais 1440px de conteúdo, ou seja, acima de 1680px de largura. Abaixo disso, que é a maioria das telas reais, a única folga nas bordas vinha de um padding fixo de 2,5rem (40px), então o conteúdo ficava colado na borda direita da janela, sem nenhuma margem correspondente.

[EU] Corrigi as duas causas em `styles.css`, sem mudar a identidade visual documentada no DESIGN.md nem a decisão anterior de manter tabelas em largura cheia:

- O `max-width: 72ch` saiu do `.page-head` (o contêiner) e passou só para o `.lede` (o parágrafo). Um título de uma linha como "Pipeline" ou "Forecast" não precisa de limite de medida de leitura; quem precisa é o parágrafo de várias linhas.
- O `.lede` ganhou mais peso visual: de 1,25rem para 1,3125rem de tamanho, de 1,5 para 1,6 de entrelinha, e a largura máxima passou de 72ch (medido na fonte sans do body, por herança, o que já era impreciso) para 46rem fixos, medidos na própria fonte serifada do parágrafo.
- O espaçamento do `.page-head` aumentou: o vão entre título e parágrafo foi de 0,6rem para 0,85rem, e a margem antes do conteúdo seguinte, de 2,25rem para 3rem.
- O padding lateral de `main` e `.filters` trocou o valor fixo de 2,5rem por `clamp(1,75rem, 3,5vw, 4rem)`, que cresce com a largura da tela em vez de ficar travado. Isso dá uma margem real em qualquer notebook comum, não só em monitores ultrawide.
- No celular (abaixo de 860px), adicionei um ajuste equivalente para `.page-head` (de volta a 0,6rem de vão e 2rem de margem) e tirei o limite de largura do `.lede`, porque numa tela de 390px de largura o parágrafo já ocupa a coluna inteira e o corte de medida de leitura não faz sentido.

Como essas classes (`.page-head`, `.lede`) são compartilhadas por todas as telas com cabeçalho de página (Overview, Pipeline, Forecast, Contas, Time), a correção vale para o app inteiro num commit só, sem repetir a mudança tela por tela.

[EU] Verifiquei sem depender de screenshot: rodei o `detect.mjs` do Impeccable nos escopos `layout` e `type` (voltou `[]` nos dois, sem achado), remedi a página num iframe da mesma origem em 1440px e 1920px para confirmar os números (o padding lateral de `main` foi de 40px para cerca de 50px em 1440px; o `.lede` foi de 659px para 736px de largura, com fonte e entrelinha maiores), rodei `tsc --noEmit` e `npm run build`, que passaram limpos.

## 20. Review crítico com o olhar de quem avalia

[EU] Pedi à IA que subisse o app local, limpo como um avaliador o encontraria, e fizesse um review crítico com o olhar de um diretor do G4: o que melhorar e por quê.

[IA] Antes de opinar, reproduziu o caminho do avaliador: um clone limpo, `npm install`, build, os testes do motor e do bot, e `scoring.py` gerando de novo o `data.json` (que saiu idêntico ao versionado). Depois navegou por todas as telas, na visão da empresa e na de um vendedor. Os achados que importavam:

- A ficha do deal mostrava três probabilidades para o mesmo deal (28, 40 e 71%), e o texto dizia "28% de chance de **fechar**" quando o 28 é a chance de **ganhar** em 30 dias. A mesma métrica tinha três nomes: "Score", "Chance (30d)" e "Probabilidade".
- Um score de 0 a 31 lê como nota baixa, e a fila era ordenada por outro número (receita esperada), que não aparecia. O deal com score 13 vinha antes do de score 18, e parecia erro.
- Os 259 deals da fila Fechar tinham a mesma frase de ação.
- O topo da Overview mostrava US$ 116,8 mil e US$ 120,5 mil como "receita esperada em 30 dias": um somava só a fila Fechar, o outro todo o aberto.
- Deal sem conta era sugerido para "encerrar como perdido". Como 68% dos abertos não têm conta, a regra misturava higiene de cadastro com previsão de resultado.
- A tela Time não mostrava receita nem volume, que variam muito e são o que um gestor olha primeiro, e cinco vendedores apareciam zerados sem explicação.
- Os achados "a Central não tem deal em negociação" e "todos os prospects são da Central" foram apresentados como fato, quando têm cara de artefato de uma base sintética.

[EU] Decidi corrigir quase tudo. O que eu defini em cada ponto:

- **Um número, um nome.** O score continua sendo a chance de ganhar em 30 dias, agora mostrado como "28%", com o mesmo nome em todas as telas, no CSV exportado e na curva da ficha, que passou a desenhar essa mesma chance. "Chance de fechar em 30 dias" saiu da tela: continua no motor, só para calcular a janela.
- **Faixa contra o melhor possível.** Uma faixa alta, média ou baixa compara o score com o máximo da base (31%, aos 85 dias), e o anel enche contra esse máximo. Um 28% virou "alta", que é o que ele é.
- **A ordem à vista.** A tabela "Feche esta semana" trocou a coluna de probabilidade sem prazo pela receita esperada em 30 dias, que é o que ordena, e diz isso numa linha. O Pipeline abre na mesma ordem.
- **Ação por fase.** Antes do pico, "envie a proposta"; no pico, "peça a decisão"; depois, "feche antes de esfriar"; abaixo de metade do pico (115 dias), "peça um sim ou não", com os dias que faltam para o limite. O pico e a reta final saem da curva, não de constantes.
- **Contexto da conta.** Conta não muda a chance de ganhar (p = 0,95), então não entra no score. Mas quantas vezes o cliente já comprou e quantos outros deals ele tem abertos mudam a conversa. Isso entra como motivo e como complemento da ação.
- **Sem conta não encerra.** A sugestão da fila Decidir usa só quanto o deal passou do limite, contra a mediana dos parados. A divisão foi de 1.102 encerrar e 199 confirmar para 653 e 648. A falta de conta virou uma tarefa de cadastro dentro da própria ação.
- **Time com receita.** Receita ganha, participação no time e ticket médio, ordenados por receita, que é um fato e não uma estimativa. A taxa de ganho continua sem comparação. Quem não tem nenhum deal sai da tabela e ganha uma nota pedindo para confirmar com o manager.
- **Artefatos como hipótese.** O Forecast e o README avisam que o padrão da Central pode vir de como a base foi gerada.

[IA] Também testou o que o review sugeria para ir além da idade: a duração do ciclo muda por produto? O mesmo teste contra o acaso deu p = 0,10, então não justifica uma curva por produto. O teste entrou na tabela de significância como "não usado".

[EU] Também cortei o README pela metade (o guia do desafio pede 5 páginas, não 40), refiz as screenshots com Chrome headless num perfil limpo, movi as de versões antigas para `screenshots/old/` e tirei `.impeccable/design.json` do versionamento (o commit anterior dizia que tinha tirado, mas o arquivo continuava lá).

Verificação: 18 testes do motor (cinco novos: sugestão sem conta, ações por fase, faixa, contexto da conta e o teste de ciclo), os testes do bot, `tsc --noEmit`, `npm run build`, e as telas conferidas no navegador. A 390 px, nenhuma tela passa da largura.

Texto deste log revisado com a skill humanizer.
