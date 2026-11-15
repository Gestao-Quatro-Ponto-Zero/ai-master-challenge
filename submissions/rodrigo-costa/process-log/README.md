# Process log: como o trabalho foi feito

## Em resumo

- Rodrigo Costa (desenvolvedor, com vivência de CRM comercial) trabalhou em dupla com uma IA nos dias 13 e 14 de novembro de 2026.
- Ele definiu o problema, o jeito de trabalhar e as decisões de produto. A IA analisou os dados, testou hipóteses, desenhou as telas e escreveu o código.
- Antes de qualquer código houve três perguntas sobre o uso real de CRM, um inventário da base e o teste das hipóteses dele.
- A IA errou várias vezes (lista abaixo). Os erros foram pegos por conferência de dado, por uma segunda implementação feita às cegas e por revisores independentes.
- A conferência independente reduziu a manchete da prova de "+42%" para "+22%", e o app mostra o +22%.
- O que este log tem: as mensagens do Rodrigo na íntegra, os scripts de análise, as saídas da conferência da prova e do `verify.py`, e as saídas brutas das seis rodadas de revisão por agentes (`evidencias/revisoes/`). As respostas da IA na conversa principal não foram anexadas.

## Ferramentas

| Ferramenta | Para que foi usada |
|---|---|
| Claude Code (aplicativo desktop), modelo Claude Fable 5.2 na conversa principal | Conversa de produto, análise dos dados em Python, testes de hipótese, coordenação dos fluxos de agentes |
| Claude Opus nos subagentes | Construção do motor, da API e da interface por fluxos de vários agentes; revisões independentes; segunda implementação da prova |
| Paper (aplicativo de design, controlado pela IA via MCP, a conexão que deixa a IA usar o aplicativo) | Estudo de UX com 12 pranchas, exportado em `docs/ux` |
| Documentação do Railway, consultada via MCP | Preparar o deploy (`solution/Dockerfile` e `solution/railway.json`). O deploy ainda não foi feito |
| Python 3.9, só biblioteca padrão | Scripts de análise, motor, servidor e testes |

## Como o problema foi decomposto

O que ficou decidido antes de pedir código:

1. **Método.** Recomeçar do zero (uma primeira tentativa do mesmo dia, em outra conversa, foi descartada), não olhar soluções de outros candidatos, discutir antes de construir, e entregar algo fácil e rápido de validar.
2. **Uso real.** Três perguntas da IA sobre como vendedor e gestor usam CRM. As respostas do Rodrigo viraram a espinha do produto: nem todo vendedor abre o sistema; vendedor deixa deal aberto para não registrar a perda ("Esfriou é menos pior que Perdeu"); e a validação tem de ser simples.
3. **Dados antes de conclusão.** Ele adiou a resposta à primeira análise e pediu antes o inventário do que a base tem sobre clientes e oportunidades.
4. **Hipóteses dele, testadas com número.** Tempo de fechamento por produto, faturamento do cliente e histórico de compras.
5. **Forma da entrega.** Um score por deal, priorização por score, duas leituras para o gestor (pipeline declarado e real), UX desenhada antes no Paper, um painel "Insights da Gabi" e um documento sobre a contribuição dele.

## Linha do tempo

| # | Quando | O que o Rodrigo pediu ou decidiu | O que a IA fez | O que mudou |
|---|---|---|---|---|
| 1 | 13 nov, tarde | Apresentou o repositório, pediu a explicação de cada desafio e escolheu o 003. Decidiu descartar a primeira tentativa e recomeçar do zero | Explicou os desafios | Pasta zerada (o histórico git ainda mostra os 4 commits da tentativa descartada, 069da76 a ab211ef); regras de trabalho definidas (sem olhar outros candidatos, discutir antes, entrega fácil de validar) |
| 2 | 13 nov | Respondeu às três perguntas da IA sobre uso de CRM | Fez as perguntas antes de qualquer código | As respostas viraram a espinha do produto. Delas vieram depois a faixa "Sem desfecho", a mensagem pronta por vendedor para o gestor e a máquina do tempo |
| 3 | 13 nov | Adiou a resposta à primeira análise e pediu o inventário da base | Apresentou a análise; depois, o inventário (`profile.py`) | A discussão passou a partir do que a base de fato tem |
| 4 | 13 para 14 nov | Questionou a análise e propôs hipóteses: ciclo por produto, faturamento do cliente, histórico de compras. Definiu score por deal, duas leituras para o gestor, formas de mascarar deal parado, UX no Paper, Insights da Gabi e o documento de contribuição | Registrou as decisões | Lista de hipóteses a testar e escopo do produto |
| 5 | 14 nov | Aceitou a proposta de score depois de ver os números | Testou cada hipótese (`hyp.py`, `acct.py`, `hist2.py`, `rel.py`, `regmatch.py`) e propôs o score: chance por idade e ponto do trimestre, vezes preço de tabela | Produto não muda o ciclo (medianas de 39 a 52 dias; só o GTK 500 foge, com 9 vendas). Faturamento e histórico não mudam a taxa de ganho entre os fechados. O sinal entre os abertos levou à armadilha do cliente (abaixo). As três hipóteses ficaram fora do score |
| 6 | 14 nov | Pediu um app que suba no Railway, com acesso simulado (vendedor ou gestor, escolhendo a pessoa) e identidade visual inspirada no G4 OS | Desenhou 5 telas no Paper; submeteu o estudo a três revisores de IA independentes (usabilidade) e a uma auditoria contra as regras do desafio | A auditoria apontou risco de escopo, a prova ainda sem conferência e o risco de a tela de integrações parecer mockup |
| 7 | 14 nov | Pediu mais telas: fontes de dados com lista de CRMs e um alerta com texto dele, kanban, filtro com e sem cliente, clientes com painel de três abas, explicação na Transparência, qualidade dos dados. Pediu também que a IA conferisse o desenho contra as regras de entrega do desafio | Redesenhou o estudo | O estudo passou a 12 pranchas |
| 8 | 14 nov | — | Durante o redesenho, achou dois problemas: o campo cliente adianta o futuro, e o "+42%" era contra um adversário fraco | O cliente saiu do score e da prova e a máquina do tempo o esconde. A manchete virou +22% |
| 9 | 14 nov | Autorizou o desenvolvimento | Fluxo de 13 agentes: 1 núcleo, 6 módulos de tela em paralelo, 1 integração no servidor, 4 revisores independentes, 1 reprodução e correção dos achados | 184 testes automatizados passando. Os revisores registraram 36 achados; o agente de correção listou 32 correções e 6 itens mantidos com justificativa (a soma passa de 36 porque um achado pode gerar mais de uma correção). Saída bruta em `evidencias/revisoes/03-revisao-do-motor-e-da-api.md` |
| 10 | 14 nov | — | Outro fluxo de agentes construiu a interface a partir das pranchas do Paper e da API real: a moldura, 9 telas em paralelo, a integração, 3 revisores independentes (contrato com a API, segurança e acessibilidade, fidelidade ao estudo) e 1 agente de correção | 10 telas, sem etapa de build. 38 achados, 31 correções e 8 itens mantidos com justificativa (há achado repetido entre revisores e achado corrigido só em parte, por isso a soma não fecha em 38). Saída bruta em `evidencias/revisoes/05-revisao-da-interface.md` |
| 11 | 14 nov | — | Teste final: cada tela aberta no Chrome sem interface gráfica, como vendedor e como gestor, em 1440 px; as principais também em 1280 px e em largura de celular (375 px); fluxos principais no navegador (entrar por link, marcar deal como tratado, revelar o desfecho, trocar data e pessoa) | Nenhum erro de console. Quatro ajustes: a Máquina do tempo passou a abrir com o desfecho escondido; o link direto de entrada passou a valer também numa aba já aberta; saiu o contorno de foco de um título; o score de três dígitos ganhou espaço no celular. Capturas em `docs/app/` |
| 12 | 14 nov | — | Revisão final por cinco agentes independentes (regras do desafio, fatos e números, instalação do zero, avaliador cético no navegador, privacidade e texto) e um sexto que tentou refutar cada achado | 31 achados brutos, 26 confirmados, nenhum que quebrasse o app. Uma segunda conferência, por três agentes, confirmou que as 26 correções entraram e pegou mais 5 pontos pequenos, também corrigidos. Exemplos: "Ver a conta" abria uma tela sem a conta; a diferença em pontos não batia com as taxas arredondadas na tela; o README chamava de "3.438 deals" uma soma em que o mesmo deal conta mais de uma vez. O que foi feito com cada um está em `evidencias/revisoes/06-revisao-final-da-entrega.md` |

**A armadilha do cliente (passos 5 e 8).** Todo deal fechado tem cliente; entre os abertos no fim da base (31 dez 2017), o campo está vazio em 68% (1.425 deals; em 4 dez 2017, 1.078 de 2.078, 52%). Onde está preenchido, a regional do vendedor bate com a do cliente em 32% dos deals abertos, contra 95% nos fechados (`regmatch.py`). Ou seja, o cliente dos deals abertos não é confiável. E numa data simulada, "ter cliente" adianta quem vai fechar: em 4 dez 2017, dos 549 deals vivos sem cliente, 0 fecharam até o fim da base; dos 750 com cliente, 404 viraram venda (`leak.py`). Usar esse campo daria um score ótimo no teste e inútil na vida real.

**A prova (passo 8).** A primeira versão dizia "+42% de receita contra ordenar por valor". Outro agente escreveu a prova do zero, só a partir da regra, sem ver o código nem os números (`evidencias/conferencia-independente`). Chegou a resultados muito próximos (diferença abaixo de 0,3% nos totais, por causa do desempate), mas mostrou que boa parte do ganho vem só de tirar os deals sem desfecho da frente. O número justo é +22% contra "ordenar por valor já sem os sem desfecho"; o score vence em 20 das 22 segundas e perde em 30 out e 6 nov. Em outubro e novembro o ganho cai para +10% no app (+11% na conferência), e contra a regra simples "sem os sem desfecho, o mais novo primeiro" o score fica 1% abaixo nesses dois meses (app e `check2.py`). Isso está dito no app.

## Onde a IA errou e como foi corrigido

| Erro da IA | Como foi pego | O que mudou |
|---|---|---|
| A primeira tabela de tempo de fechamento estava enviesada: a base não tem fechamentos antes de 1 mar 2017, então deals antigos só aparecem se demoraram | Conferência das datas (`trunc.py`) | Tabela refeita com a janela limpa |
| Um ranking de vendedores por deals parados parecia mostrar quem acumula deal velho | Ao abrir por regional: era diferença entre regionais (a Central só tem deals abertos recentes), não entre pessoas | Ranking retirado |
| "9 dos 10 maiores deals estão parados" soava como achado | Comparado com a taxa média da base: era só a média | Frase reescrita |
| "Cliente pequeno fecha menos" e "vendedor que nunca vendeu para o cliente perde mais" | Investigação do campo cliente (`rel.py`, `regmatch.py`): sinais criados pelo cliente trocado nos deals abertos | Descartados |
| "+42%" verdadeiro, mas contra um adversário fraco | Segunda implementação às cegas, por outro agente | Manchete passou a +22%, com os limites da prova à vista |
| O estudo de UX dizia "deal aberto quase nunca tem cliente"; no fim da base, um em cada três tem | Quando o app passou a recalcular cada frase a partir do dado | Corrigido nas duas telas |
| O estudo misturava duas datas: a tela de acesso usava 31 dez 2017 e as outras, 4 dez. A aba de deals em aberto de um cliente mostrava 7 deals (fim da base) em vez de 13 (data simulada) | Revisão tela por tela | Todas as telas na mesma data simulada |
| Uma sugestão da tela de acesso descrevia a carteira de um vendedor como "só prospecção"; ele tinha 118 deals vivos | Consulta ao dado antes de escrever o texto final | Texto corrigido |
| Na revisão do motor: um campo "auc.score" (AUC: nota de 0 a 1, em que 0,5 é o acaso, para quão bem uma ordem separa quem fechou de quem não fechou) media a chance, não a ordem do app; a etiqueta "Maior carteira" era falsa em algumas datas; "é mês de fechar" aparecia com 6 dias para o fim do trimestre; a validação de data mudava entre versões do Python | Revisores independentes do fluxo de 13 agentes | Todos corrigidos, cada um com teste de regressão |
| Na interface: um link da pauta do gestor dizia "Ver os 153 deals" (o time) e abria os 60 de um vendedor; o front refazia datas e limites que a API já entregava prontos; abaixo de 900 px o menu aberto deixava o foco do teclado ir para trás do fundo escuro | Três revisores independentes do fluxo da interface | Corrigidos (31 correções ao todo; 8 itens mantidos com justificativa) |
| A Máquina do tempo abria já com o desfecho revelado, o que tirava o sentido do botão "Revelar o desfecho" | Teste final, tela por tela, no navegador | Abre escondido; a escolha de cada pessoa fica salva no navegador |
| Um primeiro fluxo de 7 agentes de análise teve 6 falhas por limite de uso do modelo | As falhas apareceram na execução | Refeito com outro modelo; os testes mais importantes foram rodados diretamente |

## O que o Rodrigo adicionou que a IA sozinha não faria

- **"Esfriou é menos pior que Perdeu".** O vendedor deixa o deal aberto para não registrar a perda. Virou a faixa "Sem desfecho" e a taxa de ganho que conta esses deals.
- **Como se mascara um deal parado:** empurrar a data de fechamento e registrar atividade. Por isso o score usa só a data de entrada, que ninguém atualiza, e a tela de fontes de dados lista esses dois históricos como requisitos de uma integração real.
- **Duas leituras lado a lado para o gestor** (declarado e real), não um número no lugar do outro.
- **Nem todo vendedor abre o sistema.** Para quem só reage ao cliente, o gestor recebe uma mensagem pronta por vendedor.
- **"Fácil e rápido de validar".** Daí a máquina do tempo, o acesso simulado e um app que roda com um comando, sem instalar nada.
- **Inventário antes da análise e as hipóteses de produto, faturamento e histórico.** Nenhuma entrou no score, mas o teste delas revelou a armadilha do cliente.
- **Decisões de produto:** score por deal, Insights da Gabi, pipeline em kanban, filtro com e sem cliente, painel do cliente com três abas, tela de fontes de dados com o alerta escrito por ele, identidade visual.
- **Decisões de método:** recomeçar do zero em vez de remendar a primeira tentativa, não olhar outros candidatos, discutir antes de construir.

O que foi da IA: as perguntas iniciais, a análise e os scripts, a proposta do modelo de score, a descoberta de que o cliente adianta o futuro, a revisão da prova, o desenho das pranchas e todo o código.

## Como a IA foi verificada

- **Conferência independente da prova.** Outro agente recebeu só a regra e escreveu a prova do zero (`evidencias/conferencia-independente/backtest.py`). Ele desempata por sorteio (20 repetições) e o app pela média exata de todos os desempates, então os totais diferem um pouco (ordenar por valor: US$ 4.924.037 na conferência, US$ 4.932.579 no app). A receita do score dividida pela da outra regra dá 1,421 contra valor e 1,225 contra valor sem os sem desfecho na conferência; 1,418 e 1,222 no app. A saída inclui o teste com top 5 e top 20, sorteios com outras sementes (pontos de partida diferentes do sorteio) e a retirada de um vendedor ou de uma data por vez.
- **Recontagem às cegas** (`evidencias/revisoes/03-revisao-do-motor-e-da-api.md`). Um revisor recontou os números a partir dos CSVs, sem ler o código: 33.505 de 33.507 comparações bateram. As 2 diferenças eram nomes de campo enganosos, corrigidos.
- **Teste de vazamento** (mesmo arquivo). Um revisor procurou uso de informação do futuro e rodou o motor em bases cortadas na data simulada (sem nada depois dela): as respostas foram idênticas, salvo o total de 8.800 oportunidades da tela de acesso, que descreve a base inteira e passou a dizer isso.
- **Testes automatizados.** 190 testes (`unittest`) em `solution/tests`, todos passando: 185 do motor e da API e 5 da interface.
- **Teste da interface no navegador.** Cada tela aberta como vendedor e como gestor, sem erro de console; os valores de referência deste texto conferidos na tela (por exemplo #LFI3BGEE com score 98, US$ 438.104 vivos no time de Rocco Neubert e 5 vendas, US$ 25.687, na Máquina do tempo de Daniell Hammack).
- **`solution/verify.py`.** Uma segunda implementação curta das regras, que lê os CSVs e compara com o motor linha a linha: 189 conferências, 189 bateram (`evidencias/saida-verify.txt`). Como controle negativo, a mesma conferência com o horizonte trocado de 30 para 31 dias, só na segunda implementação, aponta 35 diferenças. Ou seja, o script de fato detecta divergência.

## Iterações

Resumo das etapas de cada frente, a partir da linha do tempo:

| Frente | Etapas |
|---|---|
| Análise | Primeira análise (resposta adiada pelo Rodrigo); inventário; teste das hipóteses do Rodrigo; investigação do campo cliente. Num fluxo de 7 agentes de análise, 6 falharam por limite de uso; foi refeito |
| Score | Proposta da IA (idade e ponto do trimestre, vezes preço), aceita depois do teste das hipóteses. Depois veio a regra de que o campo cliente nunca entra em chance, score, ordem ou prova |
| Prova | Protótipo (`backtest.py`) com "+42%"; conferência independente; versão final com +22% e os limites por período (`check2.py`) |
| Desenho | 5 telas, revisão por 3 revisores mais auditoria; 12 pranchas com as telas pedidas pelo Rodrigo; correção das frases e datas quando o app recalculou cada número |
| Motor e API | Construção (núcleo, 6 módulos, integração); 4 revisões independentes; reprodução e correção dos achados |
| Interface | Moldura; 9 telas em paralelo; integração; 3 revisões independentes; correção dos achados; teste final no navegador com mais 4 ajustes; revisão final da entrega |

## Evidências nesta pasta

Mensagens do Rodrigo na íntegra: `prompts-do-rodrigo.md`.

`evidencias/analise/`, scripts usados na conversa:

- `profile.py`: inventário dos arquivos (colunas, vazios, distintos, faixas, cobertura por estágio, integridade).
- `trunc.py`: mostra que a falta de fechamentos antes de 1 mar 2017 distorce a curva por idade.
- `hyp.py`: testa as hipóteses do Rodrigo (ciclo por produto, faturamento, histórico) e a estrutura de calendário.
- `acct.py`: porte do cliente contra deals sem desfecho.
- `hist2.py`: histórico de compras contra ficar sem desfecho.
- `rel.py`: relação vendedor-cliente; sinal real ou efeito do preenchimento do campo cliente.
- `regmatch.py`: o cliente pertence à regional do vendedor? Fechados contra abertos.
- `honest.py`: testa "deal parado = perda escondida" no CSV bruto.
- `honest2.py`: segunda rodada (estrutura por time, maiores deals, deals parados no top 10 por vendedor).
- `backtest.py`: protótipo da máquina do tempo e da prova (versão do "+42%").
- `check2.py`: refaz, com o código da IA, os achados da conferência independente (série por data, por trimestre, top 5/10/20).
- `leak.py`: mostra que o campo cliente adianta o futuro numa data simulada.
- `cal.py`: números das telas de Transparência e Qualidade dos dados.
- `mock.py`: retrato da base numa data, para as pranchas (argumentos extras: data e vendedor).
- `mock2.py`: dados das telas de kanban, clientes e comparação justa.
- `tm.py`: listas da máquina do tempo de um vendedor em 4 dez 2017.

`evidencias/conferencia-independente/`: `backtest.py` (a segunda implementação da prova), `extra.py` (verificações extras), `horizonte.py` (horizonte de 30, 60 e 90 dias) e `saida.txt` (a saída).

`evidencias/saida-verify.txt`: saída de `solution/verify.py`, com o controle negativo no fim.

`evidencias/revisoes/`: saídas brutas dos agentes revisores, sem edição além da remoção de caminhos locais.

- `01-critica-das-telas.md`: três revisores criticam as primeiras telas do estudo, antes do código.
- `02-auditoria-contra-as-regras-do-desafio.md`: dois revisores conferem o plano contra os termos de entrega.
- `03-revisao-do-motor-e-da-api.md`: recontagem às cegas, teste de vazamento, robustez e textos; 36 achados e o que foi feito com cada um.
- `04-checagem-dos-documentos.md`: três leitores conferem README, process log e contribuição; 37 achados.
- `05-revisao-da-interface.md`: três revisores da interface; 38 achados e o que foi feito com cada um.
- `06-revisao-final-da-entrega.md`: cinco revisores e um verificador sobre a entrega pronta; 31 achados, 26 confirmados, e o que foi feito com cada um.

**Como rodar um script de análise.** Precisa só de Python 3.9 ou mais novo. Da pasta `process-log/evidencias/analise`:

```
python3 -I hyp.py ../../../solution/data
python3 -I mock.py ../../../solution/data 2017-12-04 "Daniell Hammack"
```

`-I` roda o Python isolado (não carrega módulos da pasta atual). `regmatch.py`, `trunc.py`, `hyp.py`, `mock.py` e `leak.py` foram rodados assim ao escrever este texto e terminaram sem erro.
