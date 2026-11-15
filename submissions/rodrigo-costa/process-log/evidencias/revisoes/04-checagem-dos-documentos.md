# Checagem dos documentos da entrega (3 leitores, 37 achados)

> O README, o process log e o documento de contribuição foram lidos por três checadores independentes: números, fatos do processo e privacidade, e uma leitura de avaliador cético. Saída bruta de agentes de IA, sem edição além da remoção de caminhos locais.


## Revisor: numeros

**Resumo do revisor.** Conferi cerca de 110 números e afirmações quantitativas distintas nos 5 documentos. Muitos se repetem entre README, process-log e contribuição. As fontes foram três: `verify.py --json` (189 de 189 batem), a API em 8077 (seller, time-machine, proof, team, pipeline, score-model, login) e a saída de todos os 16 scripts de análise, que rodei de novo. Também li `conferencia-independente/saida.txt`. Quase tudo bate com o dado: base (8.800, 4.238, 2.473, 1.589, 500, 85, 30), 4 dez (2.078, 779, 37%, US$ 5.006.104, US$ 2.060.421), Daniell (85, 47, US$ 146.909, US$ 253.368, 59,5%, 46,8%, #LFI3BGEE score 98, 391/196, US$ 2.748, 2%), Rocco (US$ 824.840, US$ 438.104, 53%) e a prova (659 listas, as quatro linhas da tabela, +22%, +42%, +30%, +10%, -1%, 20 de 22, 30 out e 6 nov). Também batem a máquina do tempo (5 vendas e US$ 25.687 contra 0; 3, 6 e 4,3), 1.185, 1.425 e 68%, 32% e 95%, 549, 750 e 404, 3.438, 81% e 52%, medianas de 39 a 52, GTK 500 com 69 dias e 9 vendas, 22,3% e 3,6%, 59,5% e 60,9%, 118 vivos (Darcel Schlecht em 4 dez) e 13 contra 7 deals (Mathtouch). Comandos que rodam: `python3 server.py` (subi com PORT=8091; /health e / deram 200; depois parei), `python3 -m unittest discover -s tests -t .` (184 testes, OK), `verify.py`, o controle negativo de 31 dias (reproduzi: 35 não batem, código 1) e os 16 scripts com `-I` (15 com só a pasta dos dados; `mock.py` precisa da data). Todos os caminhos de código citados existem: classe Snapshot, campo rate_with_stale, sources() com o comentário "manter a redação", messages e signals na API, as 12 PNGs e o PDF. Os problemas: o 68% (fim da base) aparece como se fosse de 4 dez; o "30 dias" da máquina do tempo na data padrão são 27; pranchas embutidas no README mostram +11% e "quase nunca"; a soma 36 achados = 32 correções + 6 mantidos não fecha; vários números do processo não têm evidência na pasta; o checkbox de git history não corresponde ao estado do repositório.

**Achados: 11**

### 1. [alto] 68% de abertos sem cliente é do fim da base, mas aparece colado a 4 dez 2017

- **onde:** README.md, linha 13 (Executive Summary); linha 59; linha 124 (Recomendação 2); também a prancha docs/ux/02 embutida no README
- **detalhe:** 68% = 1.425 de 2.089 abertos no fim da base (31 dez, contando os 500 Prospecting; cal.py). Na data simulada de 4 dez, que o Executive Summary cita na mesma frase, leak.py mostra que 1.078 dos 2.078 abertos não têm cliente (52%). Entre os vivos, 549 de 1.299 (42%). A prancha 02, datada de 4 dez e embutida no README, diz 'está vazio em 68% dos deals abertos'. O mesmo vale para 'um em cada três tem cliente' (664/2.089 = 31,8%, fim da base): em 4 dez, 48% dos abertos e 58% dos vivos têm cliente. A nota da Máquina do tempo na API em 4 dez também diz 'deal aberto, só um em cada três'.
- **correção sugerida:** Dizer 'no fim da base (31 dez 2017)' sempre que usar 68% ou 'um em cada três', ou trocar pelo número de 4 dez (52% dos abertos sem cliente).

### 2. [medio] Máquina do tempo em 4 dez cobre 27 dias, não 30

- **onde:** README.md, linha 31 (passo 3 do 'Para ver em um minuto'); docs/contribuicao-do-rodrigo.md, linha 33
- **detalhe:** O README diz que a Máquina do tempo revela 'o que aconteceu nos 30 dias seguintes'. Na data padrão, a API (/api/time-machine) responde window.days = 27 e truncated = true: o desfecho real vai só até 31 dez 2017. As 5 vendas e os US$ 25.687 do Daniell, citados no README (linha 94) e na contribuição, são de 27 dias. A prova de 22 segundas (até 27 nov) não tem esse problema.
- **correção sugerida:** Escrever 'nos 30 dias seguintes (27 em 4 dez, porque a base acaba em 31 dez)' ou citar a janela junto do número.

### 3. [medio] A prancha 04 embutida no README contradiz o texto: +11% e 'quase nunca'

- **onde:** README.md, linhas 115-117 (pranchas embutidas); docs/ux/04-maquina-do-tempo.png
- **detalhe:** A prancha 04, mostrada no corpo do README, diz '+30% no 3º trimestre e +11% em outubro e novembro'. O README, o app e o verify dizem +10% (0,1044). O +11% bate com a conferência independente (C/B = 1,109), não com o app. A mesma prancha diz 'deal aberto quase nunca', o erro que o process-log descreve como corrigido. O aviso de que algumas pranchas estão desatualizadas existe só em docs/README.md; o README principal mostra as imagens sem esse aviso.
- **correção sugerida:** Pôr uma legenda de uma linha sob as imagens ('desenho de referência; números do app prevalecem') ou trocar a prancha 04 por outra sem divergência.

### 4. [medio] '36 achados, 32 correções, 6 mantidos' não fecha (32 + 6 = 38)

- **onde:** README.md, linha 167; process-log/README.md, linha 43 (passo 9)
- **detalhe:** Pela aritmética, 36 achados não se dividem em 32 correções mais 6 itens mantidos. Pode haver achado com mais de uma correção, ou uma contagem errada, mas o texto não explica. A pasta da entrega não tem nenhum arquivo que permita conferir essa contagem.
- **correção sugerida:** Explicar a relação (por exemplo, 'alguns achados geraram mais de uma correção') ou corrigir a contagem a partir do registro da revisão.

### 5. [medio] Números do processo sem evidência na pasta da entrega

- **onde:** README.md, linha 167; process-log/README.md, linhas 43, 81, 82; docs/contribuicao-do-rodrigo.md, linha 78
- **detalhe:** Não há na pasta arquivo que sustente: 33.505 de 33.507 comparações da recontagem às cegas; 'respostas idênticas' no teste de vazamento em bases truncadas; 36, 32 e 6 achados; '7 agentes, 6 falhas'. Os 184 testes conferem (rodei: Ran 184 tests, OK). Os outros números são afirmados sem arquivo de saída. Para uma banca cética, sem saída na pasta estes números não podem ser conferidos.
- **correção sugerida:** Salvar em process-log/evidencias as saídas da recontagem e do teste de vazamento (ou um resumo dos achados), ou marcar no texto que são relatos dos agentes, sem arquivo.

### 6. [medio] Checkbox 'Git history: commits da entrega' marcado, mas os commits não são desta entrega

- **onde:** README.md, linha 198 (Evidências)
- **detalhe:** git log em submissions/rodrigo-costa mostra só 4 commits, todos da primeira tentativa descartada ('app local com plano da semana', 'curva de idade, score por fila...', 'exploração inicial', dataset). O trabalho atual está todo fora de commit (git status: 15 entradas, entre elas arquivos da tentativa antiga apagados). Do jeito que está, o checkbox afirma algo que o repositório não mostra. Os commits visíveis são justamente da tentativa que o texto diz ter sido descartada.
- **correção sugerida:** Fazer os commits da entrega antes de enviar, ou desmarcar o item até lá.

### 7. [baixo] 'Chegou aos mesmos números' e 'as razões coincidem' é um pouco mais forte que o dado

- **onde:** README.md, linha 95; process-log/README.md, linha 80; docs/contribuicao-do-rodrigo.md, linha 76
- **detalhe:** A conferência (saida.txt) dá C/A = 1,421 e C/B = 1,225; o app dá 1,418 e 1,222. Os totais também diferem um pouco: valor 4.924.037 contra 4.932.579; sem parados 5.711.177 contra 5.723.131; score 6.996.785 contra 6.994.434. Em outubro e novembro, a conferência dá +11% (1,109) e o app +10%. O process-log explica a diferença de desempate, mas o README diz 'chegou aos mesmos números'. Além disso, o '1% abaixo da regra mais novo primeiro' não está em saida.txt: vem de check2.py (0,993) e do app (-1,06%). A contribuição atribui esse número à segunda implementação.
- **correção sugerida:** Escrever 'chegou a números muito próximos (diferença abaixo de 0,3%, por causa do desempate)' e atribuir o -1% ao app e ao check2.py.

### 8. [baixo] Comando genérico dos scripts falha com mock.py

- **onde:** README.md, linha 199 (Evidências)
- **detalhe:** 'python3 -I script.py <pasta dos dados>' funciona para 15 dos 16 scripts. mock.py exige a data como segundo argumento: sem ela dá IndexError em sys.argv[2]. O process-log mostra o comando certo (com data e vendedor); o README não.
- **correção sugerida:** Acrescentar no README: 'mock.py também pede a data (AAAA-MM-DD) e, opcional, o vendedor'.

### 9. [baixo] Taxa por terço de faturamento (63,2%, 63,0%, 63,2%) não aparece nos scripts de evidência

- **onde:** docs/contribuicao-do-rodrigo.md, linha 67 (tabela da seção 9)
- **detalhe:** O número vem só do app (/api/score-model, signals.revenue, calculado em engine/model_page.py). hyp.py, o script da conversa, usa quartis (64,4%, 61,2%, 64,6%, 62,5%), não terços. O número é verificável pela API, mas não pelo script que o texto apresenta como o teste da hipótese.
- **correção sugerida:** Citar a fonte ('Como o score funciona' ou /api/score-model) ou usar os quartis de hyp.py.

### 10. [baixo] 'Entre os abertos parecia forte (22,3% contra 3,6%)': o grupo não é 'os abertos'

- **onde:** docs/contribuicao-do-rodrigo.md, linha 68
- **detalhe:** Em hist2.py e no app, 22,3% e 3,6% são a parcela que ficou sem desfecho entre deals com cliente que entraram de 1 abr a 14 ago 2017 (n = 938 e 2.391). É um grupo que mistura fechados e abertos, não 'os abertos'. Os números batem; a descrição do grupo, não.
- **correção sugerida:** Trocar por 'entre os deals com cliente que entraram de abr a meados de ago, 22,3% ficaram sem desfecho quando...'.

### 11. [baixo] '14 meses (out 2016 a dez 2017)'

- **onde:** README.md, linha 131
- **detalhe:** A base vai de 20 out 2016 (primeira entrada) a 31 dez 2017 (último fechamento): 14 meses e 11 dias, cobrindo 15 meses do calendário. Aceitável; apontado só para a banca não ler como erro de conta.
- **correção sugerida:** Opcional: 'de 20 out 2016 a 31 dez 2017'.


## Revisor: processo

**Resumo do revisor.** Li os cinco documentos: README.md, process-log/README.md, process-log/prompts-do-rodrigo.md, docs/contribuicao-do-rodrigo.md e docs/README.md. Comparei com os FATOS DO PROCESSO e com as evidências em process-log/evidencias. As citações do Rodrigo em prompts-do-rodrigo.md batem literalmente com os fatos, incluindo grafia e ordem. Os recortes citados em contribuicao-do-rodrigo.md também são literais, marcados com "[...]" ou cortados no fim. Os dez erros da IA (a a j) e todas as contribuições do Rodrigo aparecem nos dois READMEs. Não achei e-mail, empregador, caminho /Users/ nem nome de outro candidato. Conferi fora dos fatos e confirmei: os números da conferência independente (4.924.037; 1,421 e 1,225; 20 repetições; top 5 e top 20; sementes; retirada de um vendedor ou de uma data) estão em saida.txt. O 189 de 189 e o controle negativo com 35 diferenças estão em saida-verify.txt. Os 1.425 abertos sem cliente batem com o CSV (de 2.089 abertos). O alerta mantido com o comentário "manter a redação" está em solution/engine/quality.py. regmatch, trunc, hyp e leak terminaram sem erro. Os problemas reais são três. O primeiro e mais grave: o README marca "Git history: commits da entrega", mas os únicos commits da pasta são da tentativa descartada. O segundo: a interface aparece como pronta em vários trechos, embora esteja em andamento. O terceiro: há pequenos acréscimos não presentes nos fatos (o Rodrigo "acompanhou e aceitou", o título "como corrigi", a contagem de rodadas). Há também alguns termos técnicos sem explicação.

**Achados: 14**

### 1. [critico] "Git history: commits da entrega" marcado como feito, mas os commits são da tentativa descartada

- **onde:** README.md, seção Evidências, linha 198
- **detalhe:** O git log da pasta submissions/rodrigo-costa mostra só 4 commits: 069da76 (dataset), 8014913 (exploração inicial), 4a31e62 ("curva de idade, score por fila e backtest fora da amostra") e ab211ef ("app local com plano da semana..."). Todos são da primeira tentativa, que os fatos dizem ter sido descartada. A entrega atual não tem commit; o git status mostra os arquivos antigos como apagados e não registrados. Um avaliador que abrir o histórico vai ver só a tentativa descartada. Isso também choca com "Pasta zerada" (process-log/README.md, linha do tempo, passo 1), já que o histórico dela continua visível.
- **correção sugerida:** Desmarcar o item até haver commits da entrega, ou dizer com todas as letras que os commits atuais são da tentativa descartada e citar os novos quando existirem.

### 2. [alto] Interface descrita como pronta; os fatos dizem que está em andamento

- **onde:** README.md linha 168 (Workflow, passo 10); linha 50 (Abordagem, item 7); docs/contribuicao-do-rodrigo.md linha 78
- **detalhe:** README linha 168: "Interface construída por outro fluxo de agentes". contribuicao linha 78: "o motor, a API e a interface, feitos por fluxos de vários agentes". O item 10 dos fatos diz "em andamento: descreva o método, não invente resultado". O process-log/README.md trata o tema certo ("Em andamento quando este texto foi escrito"), então os documentos se contradizem.
- **correção sugerida:** Usar o mesmo tempo verbal do process log ("em construção quando este texto foi escrito") ou atualizar quando a interface estiver pronta.

### 3. [alto] Telas e elementos de interface citados como existentes antes de a interface ficar pronta

- **onde:** README.md linhas 29-31 (Para ver em um minuto) e 97-111 (O que o app tem); docs/contribuicao-do-rodrigo.md seções 1, 3, 4 e 7 ("Onde ver")
- **detalhe:** O roteiro "abra o primeiro deal... Abra a Máquina do tempo", a tabela de telas e trechos como "aba Sem desfecho e cartão 'Indicador'", "bloco 'As duas leituras, por vendedor'", "bloco 'Para quem não abre o sistema'" e "selo 'Conceito' sempre visível" descrevem a interface final. Nos fatos, ela ainda está sendo construída. Se um nome de bloco, aba ou cartão mudar, o avaliador encontra uma afirmação falsa. Os nomes que vêm da API (campos messages, signals, a função sources) podem ser conferidos hoje; os nomes de tela, não.
- **correção sugerida:** Conferir cada nome de tela, aba e bloco na interface final antes do envio, ou citar só a rota da API até lá.

### 4. [medio] Mérito pelas correções atribuído ao Rodrigo

- **onde:** README.md linha 170 (título "Onde a IA errou e como corrigi")
- **detalhe:** Pelos fatos, quase todos os erros foram pegos pela própria IA (conferência de datas, segunda implementação feita por outro agente, revisores independentes). O próprio contribuicao-do-rodrigo.md (linha 77) diz "A maior parte dos erros foi pega pela própria IA". O título em primeira pessoa contradiz isso.
- **correção sugerida:** Trocar para "Onde a IA errou e como foi corrigido", como no process-log/README.md.

### 5. [medio] Os três erros do estudo de UX colapsados num só jeito de pegar

- **onde:** README.md linha 177
- **detalhe:** O texto diz "Pegos ao recalcular cada frase a partir do dado" para os três. Pelos fatos, só o (f) foi pego assim. O (g) foi pego "ao revisar tela por tela" e o (h) "ao consultar o dado antes de escrever o texto final". O process-log/README.md está certo.
- **correção sugerida:** Separar os três jeitos ou usar uma frase genérica que não afirme um mecanismo único.

### 6. [medio] Ações do Rodrigo que não estão nos fatos

- **onde:** process-log/README.md, linha do tempo, passo 8 (linha 42) e passo 10 (linha 44)
- **detalhe:** Passo 8: "Acompanhou e aceitou as duas mudanças". Passo 10: "Acompanhou". Os fatos não registram aceite nem acompanhamento nesses passos; dizem só que "A manchete do app passou a ser o +22%" e que o campo ficou fora. É um acréscimo pequeno, mas atribui ao Rodrigo uma ação não documentada.
- **correção sugerida:** Deixar a célula com "—" ou escrever só o que consta nos fatos.

### 7. [medio] Contagem de rodadas montada pelo redator, não presente nos fatos

- **onde:** process-log/README.md, seção Iterações (linhas 86-95)
- **detalhe:** "Análise 4", "Score 2", "Prova 3", "Desenho 3", "Motor e API 3". Os fatos não trazem número de iterações; as contagens foram reconstruídas a partir da linha do tempo. A maior parte é defensável, mas "Score: 2" conta como rodada a criação de uma regra ("o campo cliente nunca entra..."), não uma nova versão do score. Em "Análise", "Um fluxo de 7 agentes falhou" exagera: os fatos falam em 6 falhas de 7.
- **correção sugerida:** Apresentar como resumo das etapas, sem número de rodadas, ou ajustar "Score" e trocar por "6 de 7 agentes falharam".

### 8. [baixo] Recursos de produto datados como nascidos em 13 nov

- **onde:** process-log/README.md, linha do tempo, passo 2 (linha 36)
- **detalhe:** "Nasceram a faixa 'Sem desfecho', a mensagem pronta por vendedor para o gestor e a máquina do tempo" aparece na linha de 13 nov. Os fatos dizem que as respostas viraram a espinha do produto, mas esses recursos foram definidos e desenhados depois (14 nov). A ligação de causa está certa; a data sugere que foram criados naquele momento.
- **correção sugerida:** Escrever "Daí vieram depois..." ou mover para a coluna de consequência sem implicar a data.

### 9. [baixo] "Recusou" é mais forte que os fatos

- **onde:** process-log/README.md passo 3 ("Recusou a primeira análise") e Iterações ("primeira análise (recusada)")
- **detalhe:** Os fatos dizem "Rodrigo não aceita de primeira: pede antes o inventário". A mensagem literal é "quero saber antes de te responder essa analise": ele adiou a resposta, não recusou. O README principal usa "Não aceitei a primeira análise", que é mais fiel.
- **correção sugerida:** Trocar para "Adiou a resposta à primeira análise e pediu o inventário".

### 10. [baixo] Omissão: o pedido de revisar as regras de entrega

- **onde:** process-log/README.md passo 7 (linha 41)
- **detalhe:** A mensagem dele de 14 nov inclui "Revisa no repositoria os termos de entrega... e veja se nosso design atende". A linha do tempo lista os outros pedidos da mesma mensagem, mas não este, e a coluna da IA diz só "Redesenhou o estudo". É uma contribuição de método dele que ficou de fora.
- **correção sugerida:** Acrescentar ao passo 7 o pedido de checar o design contra as regras do desafio.

### 11. [baixo] Afirmações e hipóteses do redator que vão além dos fatos

- **onde:** docs/contribuicao-do-rodrigo.md seção 1 (linha 9), seção 4 (linha 27) e seção 6 (linhas 38-39)
- **detalhe:** Seção 1: "A frase dele também definiu o tom: o texto do app diz 'sem desfecho' e pede uma decisão, sem acusar ninguém" não está nos fatos. Seção 4: "a pergunta da IA seguia essa premissa" é deduzida da resposta dele; o texto da pergunta da IA não está nos fatos. Seção 6: "o inventário é a base da tela Qualidade dos dados" e "a conversa seguiria sobre a primeira análise da IA, aceita como veio" são hipóteses do redator. Nada disso está errado com certeza, mas o leitor cético pode tomar como fato.
- **correção sugerida:** Tirar a frase sobre o tom ou dizer que é leitura do redator; trocar "aceita como veio" por algo que não suponha o que teria acontecido.

### 12. [baixo] Privacidade: nome de um projeto pessoal no Paper

- **onde:** process-log/prompts-do-rodrigo.md linha 88
- **detalhe:** A citação literal revela o nome de um projeto pessoal do Rodrigo no Paper [nome omitido]. Não é e-mail, empregador nem caminho local, e a regra pede manter a grafia original. Fica como ponto para ele decidir: confirmar que o projeto não é ligado ao empregador nem confidencial. O link do GitHub (rodrigopiffer) foi citado por ele mesmo e é permitido.
- **correção sugerida:** Pedir ao Rodrigo que confirme se pode publicar o nome do projeto; se não puder, marcar o trecho como [nome de projeto omitido].

### 13. [baixo] Termos técnicos sem explicação

- **onde:** process-log/README.md seção "Como a IA foi verificada" (linhas 80, 82, 84) e Ferramentas; README.md linha 153
- **detalhe:** "as razões coincidem: 1,421 ... 1,225" (o leitor não técnico não sabe que é receita do score dividida pela da outra regra); "outras sementes" (sementes de sorteio, sem explicação); "desempata ... por expectativa exata"; "bases truncadas"; "MCP" nunca explicado; o campo "auc.score" citado sem dizer o que é AUC. "Controle negativo" e "vazamento" já vêm explicados.
- **correção sugerida:** Explicar em meia frase: razão = quantas vezes a receita do score é maior; sementes = sorteios diferentes do desempate; MCP = conexão que deixa a IA usar o aplicativo.

### 14. [baixo] Tom de autoelogio leve

- **onde:** docs/contribuicao-do-rodrigo.md linha 55 ("Um limite honesto"); README.md linha 91 ("Limites, com todas as letras"); process-log/README.md linha 9 ("O resultado mais importante do processo foi um número menor")
- **detalhe:** Chamar o próprio limite de "honesto" e anunciar "com todas as letras" chama atenção para a franqueza em vez de só mostrá-la. A frase do "número menor" é retórica. Não há adjetivo de venda nem emoji nos cinco documentos.
- **correção sugerida:** Trocar por "Um limite:" e "Limites:"; reescrever a frase do resumo de forma descritiva ("A conferência independente reduziu a manchete de +42% para +22%").


## Revisor: banca

**Resumo do revisor.** Leitura de banca cética. Li as cinco regras do desafio e depois a entrega, começando pelo README.

O que conferi contra a API viva (porta 8077) e contra os arquivos: todos os números do README que testei batem.
- Daniell Hammack: 85 abertos, 47 sem desfecho, US$ 146.909 de US$ 253.368, taxa de ganho 59,5% e 46,8%.
- Deal #LFI3BGEE: score 98, 391 casos, 196 vendas, chance de 50%, US$ 2.748 esperados.
- Máquina do tempo: 5 vendas e US$ 25.687 pelo score, contra 0 só por valor; regra simples de 3 a 6 vendas, 4,3 em média.
- Prova: 659 listas; os quatro totais da tabela; +22% e +42%; vitória em 20 de 22 segundas (perdeu em 30 out e 6 nov); +30% de julho a setembro, +10% em outubro e novembro, 1% abaixo da regra do mais novo nesses dois meses.
- Time de Rocco Neubert: US$ 824.840 declarados e US$ 438.104 vivos.
- Qualidade dos dados: as 5 particularidades. Fontes de dados: o alerta com o texto do Rodrigo.
- `verify.py`: 189 de 189, com o controle negativo (35 diferenças com o horizonte trocado). `saida.txt`: razões 1,421 e 1,225.
- Testes: há 184 `def test_` em `solution/tests`.

O que está bom e não deve ser mexido:
- A seção "Para ver em um minuto": um comando e três cliques com resultado conferível.
- A história do +42% que virou +22%, contada com os limites "com todas as letras". É o que mais diferencia esta entrega do baseline.
- `verify.py` com controle negativo e a conferência independente com a saída anexada.
- A tabela "O que a base esconde", com o que o app faz em cada caso.
- `prompts-do-rodrigo.md` com a linha "O que isso mudou" depois de cada mensagem.
- Em `contribuicao-do-rodrigo.md`, a seção "O que foi da IA" e o trecho "Um limite honesto".
- As Limitações, que admitem as escolhas feitas olhando a base inteira.
- Zero dependências.

Contra cada critério do desafio 003:
- Roda: sim, pela API. A interface não foi avaliada.
- Scoring além do óbvio: sim. Idade, ritmo do trimestre e corte de 138 dias, com as hipóteses descartadas por número.
- Não técnico entende: parcialmente (ver achados).
- Ajuda a decidir: sim, há ação sugerida por deal.
- Código mantível: o motor tem 4.231 linhas com testes, aceitável.
- Documentação mínima (setup, lógica, limitações): presente.
- Process log: presente, mas sem o lado da IA.

Veredito: é uma entrega acima da média, honesta sobre os próprios limites e conferível. O que mais ameaça a nota é a distância entre o que o process log afirma (13 agentes, recontagem às cegas, teste de vazamento) e o que a pasta prova, somada ao histórico git que hoje mostra só a tentativa descartada.

Os 3 ajustes que mais aumentariam a nota:
1. Anexar a evidência bruta do processo: trechos exportados ou capturas da conversa com a IA nos 3 ou 4 momentos decisivos, e as saídas dos revisores (recontagem, vazamento, achados). Onde não houver arquivo, suavizar a afirmação. Corrigir também a conta 36 = 32 + 6.
2. Fazer commits da entrega atual em etapas e citar no process log que os commits 069da76 a ab211ef são a primeira tentativa descartada.
3. Enxugar o README e tirar a repetição entre os documentos. Ao mesmo tempo, pôr uma linha clara sobre a marca ("conceito inspirado no G4 OS, não é produto oficial do G4; a Gabi é por regras, não um modelo de linguagem") e dizer que os 500 deals em Prospecção ficam sem score.

**Achados: 12**

### 1. [alto] Process log sem o lado da IA: só as mensagens do Rodrigo e uma narrativa escrita depois

- **onde:** README.md, seção Evidências; process-log/
- **detalhe:** As regras dizem: 'Sem evidência de processo = desclassificado'. O guia também cita 'zero evidência de verificação'. Hoje a pasta tem as mensagens do Rodrigo (sem as respostas da IA, como o próprio arquivo admite), uma narrativa em terceira pessoa escrita depois e scripts. Os itens 'Screenshots das conversas com IA' e 'Screen recording' estão desmarcados. Um avaliador cético pode ler a narrativa como reconstrução feita pela própria IA. Faltam as respostas da IA, a primeira análise recusada e o momento em que o +42% caiu.
- **correção sugerida:** Exportar a conversa principal (sem dados pessoais) ou anexar de 4 a 6 capturas dos momentos decisivos: as três perguntas, a primeira análise recusada, o resultado das hipóteses, a descoberta do vazamento do campo cliente e a troca de +42% por +22%. Colocar em process-log/screenshots ou chat-exports, que são os nomes sugeridos no guia de submissão.

### 2. [alto] Afirmações de verificação sem arquivo na pasta, e uma conta que não fecha

- **onde:** README.md, Workflow item 9; process-log/README.md, 'Como a IA foi verificada'; docs/contribuicao-do-rodrigo.md
- **detalhe:** Não há artefato para: a recontagem às cegas '33.505 de 33.507 comparações', o 'teste de vazamento em bases truncadas: respostas idênticas', os '36 achados, 32 correções, 6 itens mantidos', as 'três revisões de usabilidade' e a 'auditoria contra as regras' do estudo de UX. Só a conferência independente da prova (saida.txt) e o verify.py (saida-verify.txt) têm saída anexada. Além disso, 32 correções mais 6 itens mantidos dão 38, não 36. Um leitor atento nota na hora e passa a desconfiar dos outros números.
- **correção sugerida:** Anexar em process-log/evidencias os relatórios ou as saídas dos quatro revisores e do teste de vazamento (mesmo resumidos). Onde não houver arquivo, dizer 'relatado pelo agente revisor; saída não anexada'. Explicar a conta 36 contra 32 + 6 (por exemplo, um achado que gerou duas correções) ou corrigir os números.

### 3. [alto] O histórico git mostra a tentativa descartada, não a entrega

- **onde:** README.md, Evidências ('[x] Git history: commits da entrega neste repositório'); git log de submissions/rodrigo-costa
- **detalhe:** O git log da pasta tem 4 commits: 069da76 (dataset), 8014913, 4a31e62 ('backtest fora da amostra') e ab211ef ('app local com plano da semana'). É a primeira tentativa que o process log diz ter descartado. O trabalho atual não está commitado: o git status mostra app.py, leadscorer/ e docs/0x apagados. A banca vai abrir o PR e ver esse histórico. Do jeito que está, a caixa marcada é falsa, ou o histórico contradiz a narrativa de 'pasta zerada'.
- **correção sugerida:** Fazer commits da entrega atual em etapas que sigam a linha do tempo (análise, estudo de UX, motor e API, interface, docs). No process log, citar que os commits 069da76 a ab211ef são a primeira tentativa e por que foi descartada. Isso vira evidência de julgamento em vez de contradição.

### 4. [medio] Aviso de marca só aparece numa prancha; a 'Gabi' não é explicada no README

- **onde:** README.md (nenhuma menção); docs/contribuicao-do-rodrigo.md linha 52; docs/ux/01-acesso-simulado.png; API
- **detalhe:** O README não diz que o visual foi inspirado no G4 OS nem que o app não é produto oficial do G4. O aviso 'Conceito criado para o AI Master Challenge. Não é um produto oficial do G4.' existe só no rodapé da prancha 01. Nenhuma rota da API devolve esse texto, e não consegui confirmar que a interface o mostra em todas as telas. O README cita 'Insights da Gabi' três vezes sem dizer quem é a Gabi. Pela mensagem do Rodrigo, é 'a IA da G4', ou seja, o nome de um produto real da empresa que avalia. Só a contribuição explica que os cartões são regras, não um modelo de linguagem. Um leitor pode entender que há um modelo de linguagem no app ou que o candidato está usando um produto da G4 como se fosse dele.
- **correção sugerida:** Uma linha no topo do README: 'Módulo conceito, com visual inspirado no G4 OS, feito para o desafio; não é produto oficial do G4. Os Insights da Gabi são cartões calculados por regra, não um modelo de linguagem.' Garantir o mesmo rodapé em todas as telas da interface. Se possível, pôr o texto num campo de /api/meta para a interface não depender de texto fixo.

### 5. [medio] O mesmo conteúdo repetido em três ou quatro lugares

- **onde:** README.md; process-log/README.md; docs/contribuicao-do-rodrigo.md
- **detalhe:** A lista 'Onde a IA errou' aparece no README, no process-log/README e (segundo o README) na tela Como chegamos aqui. 'O que eu adicionei' aparece no README, no process-log/README e em docs/contribuicao-do-rodrigo.md. Este último ainda termina com 'Contribuição em uma olhada', que repete as próprias seções 1 a 9. A linha do tempo aparece no Workflow do README e na tabela do process log. São cerca de 550 linhas de texto. Não chega a ser 'documento de 40 páginas', mas o leitor relê a mesma coisa três vezes e o README perde força.
- **correção sugerida:** No README, deixar de 3 a 4 linhas por seção de process log com links. Manter os detalhes só no process log e a contribuição só no documento próprio. Tirar a tabela final de contribuicao-do-rodrigo.md ou trocar as seções por ela.

### 6. [medio] Contagem de agentes e de comparações soa como tentativa de impressionar

- **onde:** README.md, Abordagem item 7 e Workflow item 9
- **detalhe:** 'Fluxo de 13 agentes', '4 revisores independentes', '33.505 de 33.507', '12 pranchas', '3 críticos de IA'. O desafio pede de 4 a 6 horas e diz que horas a mais não valem ponto. A entrega não informa quanto tempo levou. Para um cético, o volume de agentes pode parecer foco em parecer sofisticado. O que de fato pesa é a decisão (o corte de 138 dias, o campo cliente fora, o +22%).
- **correção sugerida:** Informar o tempo real gasto. No README, falar do resultado de cada verificação (o que ela mudou) em vez do número de agentes, e deixar a mecânica dos fluxos no process log.

### 7. [medio] Limite da prova não dito: as 22 segundas não são 22 testes independentes

- **onde:** README.md, seção 3 'A prova (e os limites dela)'
- **detalhe:** Com horizonte de 30 dias e listas semanais, a mesma carteira e muitos dos mesmos deals se repetem em segundas vizinhas. 'Venceu em 20 de 22 segundas' soa como 20 confirmações separadas. Na prática são poucas janelas de cerca de 30 dias, quase todas dentro de dois trimestres. Os limites citam a queda em out/nov e as escolhas feitas olhando a base inteira, mas não essa sobreposição. A saída da conferência mostra ainda que o score captura cerca de metade do máximo possível (US$ 6,99 mi contra US$ 13,04 mi do oráculo), referência que ajudaria a calibrar a expectativa e não aparece no README.
- **correção sugerida:** Acrescentar um item aos limites: 'As segundas se sobrepõem (horizonte de 30 dias); o resultado equivale a poucos meses de teste, não a 22 testes separados.' Se quiser, citar o teto (oráculo) da própria saida.txt.

### 8. [medio] Os 500 deals em Prospecção ficam sem score, e o README não diz

- **onde:** README.md, seções 2 e Limitações
- **detalhe:** Pelo modelo, deal em Prospecting não tem data de entrada e não entra no retrato nem no score. São 500 dos 8.800 deals. Na prancha 01, Darcel Schlecht aparece com '111 em prospecção'. Um 'Lead Scorer' que não pontua os leads em prospecção é a primeira pergunta de um avaliador de RevOps. O README não menciona isso na Lógica nem nas Limitações (a API.md só cita a coluna Prospecção do kanban).
- **correção sugerida:** Uma linha na Lógica e nas Limitações: 'Deals em Prospecção (500) não têm data de entrada na base, então ficam fora do score e aparecem só no kanban; numa integração real, a data de criação resolveria.'

### 9. [medio] Pontos onde o leitor não técnico se perde

- **onde:** README.md, Executive Summary e seções 2 e 3
- **detalhe:** (1) O Executive Summary tem 7 números num parágrafo, e 'deals sem desfecho' aparece antes de ser definido. (2) A tabela da prova mostra vendas fracionárias (1.437,6, 879,7) sem explicar que vêm do desempate por média. (3) O parágrafo 'Empates contam' ('acima da média e abaixo do melhor desempate') é difícil de seguir. (4) A chance não cresce de forma contínua com a idade: 17% de 0 a 14 dias, 6% de 15 a 30, 10% de 31 a 45, 50% de 61 a 75, conforme /api/score-model. O README não explica que isso vem do ritmo do trimestre na data; um vendedor vai perguntar por que um deal de 20 dias vale menos que um de 73. (5) Termos como 'retratos', 'célula' e 'expectativa exata' aparecem na API e nas definições.
- **correção sugerida:** Reduzir o Executive Summary a 3 números (138 dias, +22%, +10% em out/nov). Arredondar as vendas na tabela ou dizer 'média, por causa dos empates'. Acrescentar uma frase: 'em dezembro, deals de 2 a 3 meses são os que costumam fechar no fim do trimestre; por isso pesam mais que os recentes.'

### 10. [baixo] O README embute uma prancha que a própria entrega diz conter frase errada

- **onde:** README.md (imagem 04 embutida); docs/README.md; docs/ux/04-maquina-do-tempo.png e 08
- **detalhe:** O docs/README admite que as pranchas 04 e 08 ainda dizem 'deal aberto quase nunca tem cliente', frase corrigida para 'um em cada três'. O README principal embute a prancha 04. Quem olha a imagem sem ler docs/README vê uma afirmação que a entrega já sabe que é falsa.
- **correção sugerida:** Reexportar 04 e 08 com a frase corrigida, ou trocar a imagem embutida no README por uma captura do app pronto.

### 11. [baixo] Afirmações sobre a interface que a API não sustenta

- **onde:** README.md, seções 4 e Limitações
- **detalhe:** Não dá para conferir pela API: 'As ações marcadas ficam só no navegador' (não há rota de escrita), 'A data simulada troca no menu lateral', 'selo Conceito sempre visível' (na contribuição) e a ação sugerida exibida por deal. Pela API existem os dados de suporte (why.action, bands com e sem cliente, filtros de /api/team), mas as ações marcadas e o selo dependem só da interface.
- **correção sugerida:** Quando a interface estiver pronta, conferir tela por tela que essas quatro afirmações valem. Se alguma não entrar, tirar do README.

### 12. [baixo] Pendências de forma: placeholders e arquivo do sistema

- **onde:** README.md; submissions/rodrigo-costa/.DS_Store
- **detalhe:** Três itens a preencher: LinkedIn, link do deploy e data de envio. Há um .DS_Store na raiz da pasta da entrega (o .dockerignore cobre só solution/). O PR precisa do título '[Submission] Rodrigo Costa — Challenge 003'.
- **correção sugerida:** Preencher os três itens antes do PR, apagar o .DS_Store e conferir o título do PR.


## O que foi feito com os achados

### Corrigidos (31)

1. **68% de abertos sem cliente colado a 4 dez 2017**: Conferido no leak.py: em 4 dez, 1.078 de 2.078 abertos (52%) estão sem cliente; os 68% (1.425) são do fim da base. Em README.md, o número saiu do Executive Summary. Na tabela de particularidades e na Recomendação 2 ficou 'No fim da base (31 dez 2017), 68% ... (em 4 dez, 52%)'. Em process-log/README.md e em docs/contribuicao-do-rodrigo.md entrou o mesmo qualificador. 'Um em cada três' passou a dizer 'no fim da base' no README, no process-log e em docs/README.md.
2. **Máquina do tempo em 4 dez cobre 27 dias**: A API confirma window.days = 27 e truncated = true. No passo 3 do README: 'nos 30 dias seguintes (27 em 4 dez, porque a base acaba em 31 dez)'. O limite do Daniell no README e a seção 5 da contribuição agora citam a janela de 27 dias junto das 5 vendas e dos US$ 25.687.
3. **Prancha 04 embutida contradiz o texto (+11%, 'quase nunca')**: Conferido na imagem. Abaixo das pranchas, no README, entrou uma legenda: são desenho de referência e valem os números do app. Ela cita os dois pontos da prancha 04 (+11% contra +10% do app; 'quase nunca' contra um em cada três no fim da base). O +11% também foi acrescentado ao aviso de docs/README.md.
4. **36 achados contra 32 correções + 6 mantidos**: Nenhum arquivo explica a conta. O detalhamento saiu do README. Em process-log/README.md (passo 9), os números estão atribuídos ao relato dos agentes, com a frase de que 32 + 6 passa de 36 e de que o registro da revisão não foi anexado, então a conta não pode ser conferida.
5. **Números do processo sem evidência na pasta (recontagem, vazamento, achados)**: README, process-log e contribuição agora marcam a recontagem às cegas e o teste de vazamento como 'relato do agente revisor; saída não anexada'. No resumo do process log entrou uma linha dizendo o que está e o que não está anexado. Os 184 testes foram mantidos sem ressalva, porque o revisor os rodou.
6. **Checkbox de Git history marcado com commits da tentativa descartada**: Conferido com git log (só leitura): há 4 commits, de 069da76 a ab211ef, todos da primeira tentativa. O item foi desmarcado e explica que esses commits são da tentativa descartada e que os desta entrega ainda não foram feitos. No passo 1 do process log, 'Pasta zerada' ganhou a mesma ressalva.
7. **'Mesmos números' e atribuição do -1%**: No README: 'números muito próximos: diferença abaixo de 0,3% nos totais, porque ela desempata por sorteio'. No process-log, a conferência e o app aparecem lado a lado (1,421/1,225 contra 1,418/1,222; +11% contra +10%). O -1% passou a ser atribuído ao app e ao check2.py, no README, no process-log e na contribuição.
8. **mock.py precisa da data**: Nas Evidências do README entrou: 'mock.py também pede a data, AAAA-MM-DD, e opcionalmente o vendedor'.
9. **Terços de faturamento sem script de evidência**: Na contribuição, a fonte agora aparece (Como o score funciona, /api/score-model), com a observação de que hyp.py faz o teste em quatro faixas: 64,4%, 61,2%, 64,6% e 62,5%, conferido rodando hyp.py.
10. **Grupo do 22,3% contra 3,6% descrito como 'os abertos'**: Trocado por 'entre os deals com cliente que entraram de 1 abr a 14 ago 2017, 22,3% ficaram sem desfecho...', conforme os signals de /api/score-model.
11. **'14 meses (out 2016 a dez 2017)'**: Conferido nos CSVs: a primeira entrada é de 2016-10-20 e o último fechamento de 2017-12-31. O texto agora diz 'de 20 out 2016 a 31 dez 2017'.
12. **Interface descrita como pronta**: No README (Abordagem 7 e Workflow 10) e na contribuição ('O que foi da IA'), a interface aparece 'em construção quando este texto foi escrito', no mesmo tempo verbal do process log.
13. **Nomes de tela e bloco citados antes da interface pronta**: Uma busca em solution/web, só leitura, não encontrou 'As duas leituras', 'Para quem não abre', 'Indicador' nem 'Pauta da Gabi'. Na contribuição, esses nomes saíram de 'Onde ver' e foram trocados pelo nome da tela mais a rota da API (/api/seller, /api/team). Entrou uma nota no topo dizendo que os nomes seguem o estudo de UX. O README ganhou uma nota parecida no 'Para ver em um minuto'. 'Conceito' e localStorage existem na web e foram mantidos.
14. **Título 'Onde a IA errou e como corrigi'**: Trocado para 'Onde a IA errou e como foi corrigido'.
15. **Três erros do estudo de UX com um só mecanismo**: Agora cada um diz como foi pego: (f) pelo recálculo do app, (g) na revisão tela por tela, (h) na consulta ao dado antes do texto final.
16. **Ações do Rodrigo não documentadas (passos 8 e 10)**: As células 'Acompanhou e aceitou' e 'Acompanhou' foram trocadas por '—'.
17. **Contagem de rodadas montada pelo redator**: A seção Iterações virou um 'Resumo das etapas', sem números de rodadas. O texto de Score foi ajustado e ficou 'num fluxo de 7 agentes de análise, 6 falharam'.
18. **Recursos datados como nascidos em 13 nov**: Passo 2 reescrito: 'As respostas viraram a espinha do produto. Delas vieram depois a faixa...'.
19. **'Recusou' a primeira análise**: Trocado por 'Adiou a resposta à primeira análise e pediu o inventário', na linha do tempo, na decomposição e em Iterações.
20. **Omissão do pedido de revisar as regras de entrega**: No passo 7 entrou: 'Pediu também que a IA conferisse o desenho contra as regras de entrega do desafio'.
21. **Afirmações do redator além dos fatos na contribuição**: Saíram a frase sobre o tom ('sem acusar ninguém'), 'a pergunta da IA seguia essa premissa' e 'aceita como veio'. A seção 6 foi reescrita só com o que os fatos sustentam.
22. **Termos técnicos sem explicação**: MCP explicado no README e no process-log. Explicados também: a razão (receita do score dividida pela da outra regra), as sementes (pontos de partida do sorteio), 'expectativa exata' (média exata de todos os desempates), bases truncadas (cortadas na data simulada) e AUC (nota de 0 a 1, em que 0,5 é o acaso).
23. **Tom de autoelogio**: 'Limites, com todas as letras' virou 'Limites:'. 'Um limite honesto' virou 'Um limite:'. A frase do 'número menor' foi reescrita de forma descritiva.
24. **Process log sem o lado da IA (parcial)**: No resumo do process log entrou o que existe e o que falta (respostas da IA e saídas dos revisores não anexadas). Não há como produzir capturas ou export da conversa a partir desta tarefa; ver notes.
25. **Aviso de marca e Gabi não explicados no README**: Linha no topo do README: módulo conceito com visual inspirado no G4 OS, não é produto oficial do G4; os Insights da Gabi são cartões calculados por regra, não um modelo de linguagem.
26. **Conteúdo repetido em vários documentos (parcial)**: A tabela final 'Contribuição em uma olhada', que repetia as seções 1 a 9, saiu da contribuição. No README, a seção de verificação do Workflow foi enxugada.
27. **Contagem de agentes soa como tentativa de impressionar (parcial)**: Na Abordagem 7 e no Workflow 9 do README, a contagem de agentes e de comparações deu lugar ao que cada verificação mudou. A mecânica dos fluxos ficou só no process log.
28. **As 22 segundas não são 22 testes independentes**: Novo limite no README: segundas vizinhas repetem deals (horizonte de 30 dias), então o resultado equivale a poucos meses de teste. Também entrou o teto: escolhendo já sabendo o desfecho, as listas somariam US$ 13.039.226 (/api/proof e saida.txt), e o score pega pouco mais da metade.
29. **500 deals em Prospecção sem score**: Uma linha na Lógica e outra nas Limitações do README: os 500 deals não têm data de entrada, ficam fora do score e aparecem só no kanban; numa integração real, a data de criação resolveria.
30. **Pontos onde o leitor não técnico se perde**: O Executive Summary ficou com 138 dias, +22% e +10%, e define 'sem desfecho' na primeira menção. Abaixo da tabela da prova entrou uma frase sobre as vendas fracionárias (média dos desempates). O parágrafo de empates foi reescrito. Na Lógica entrou a explicação de por que a chance não cresce com a idade, com números de /api/score-model: 17%, 6%, 50%, e a janela de 61 a 105 dias.
31. **README embute prancha com frase que a entrega sabe ser falsa**: Resolvido com a legenda abaixo das imagens, que cita a frase e o número errados da prancha 04.

### Mantidos como estavam, com justificativa (7)

1. **Privacidade: nome de um projeto pessoal em prompts-do-rodrigo.md**: É citação literal e a regra pede manter a grafia original. Não é e-mail, empregador nem caminho local. O Rodrigo precisa decidir se o nome do projeto pode ser publicado; não alterei.
2. **Informar o tempo real gasto (achado da contagem de agentes)**: Os fatos só dizem 'dias 13 e 14 de novembro', sem horas. Escrever um número seria inventar.
3. **Exportar a conversa ou anexar capturas (process log sem o lado da IA)**: Exige o export da conversa ou capturas, que esta tarefa não tem como produzir sem inventar conteúdo. Fica para o Rodrigo: anexar em process-log/screenshots ou chat-exports.
4. **Fazer commits da entrega**: A tarefa proíbe comandos git que alteram estado. O item foi desmarcado e explicado; os commits ficam para o Rodrigo antes do envio.
5. **Placeholders, .DS_Store e título do PR**: LinkedIn, link do deploy e data de envio têm de ficar como estão, por instrução da tarefa. Apagar o .DS_Store é mudança de arquivo fora dos documentos, e o título do PR não está nesta pasta. Ficam para o Rodrigo.
6. **Reexportar as pranchas 04 e 08**: Exigiria editar no Paper e mexer em docs/ux, fora do escopo de ajuste de texto. A legenda no README e o aviso em docs/README.md cobrem o problema.
7. **Redução maior das seções repetidas do README**: O template do desafio exige as seções 'Onde a IA errou' e 'O que eu adicionei' no README, e elas já estão curtas. Tirei só a tabela redundante da contribuição.

### Notas de quem corrigiu

Todos os achados foram conferidos na fonte: API em 127.0.0.1:8077, scripts leak.py e hyp.py, saida.txt, CSVs, git log só leitura e busca em solution/web só leitura.

Defeitos do app, não corrigidos porque não são texto da documentação:
(1) /api/time-machine em 4 dez, hidden_account_note: 'deal aberto, só um em cada três' é o número do fim da base. Em 4 dez, 48% dos abertos e 58% dos vivos têm cliente. O texto deveria citar a data ou usar o número da data simulada.
(2) Nomes de bloco citados no estudo de UX ('As duas leituras, por vendedor', 'Para quem não abre o sistema', 'Indicador', 'Pauta da Gabi') ainda não existem em solution/web. Quando a interface terminar, conferir os nomes de tela e o seletor de data no menu lateral contra o README e a contribuição.
(3) O aviso 'Não é um produto oficial do G4' só aparece na tela de acesso (views/login.js). Se a banca quiser o aviso em todas as telas, a interface precisa mostrá-lo. Nenhuma rota da API devolve esse texto.

Pendências do Rodrigo antes do envio:
- fazer os commits da entrega e atualizar o item de Git history;
- confirmar se o nome do projeto pessoal pode aparecer;
- anexar o export ou as capturas da conversa;
- se houver, anexar as saídas da recontagem às cegas, do teste de vazamento e o registro dos 36 achados, para explicar 32 + 6;
- preencher LinkedIn, link do deploy e data;
- apagar o .DS_Store da raiz da pasta da entrega.

Tamanhos finais: README.md com 215 linhas (limite 220), process-log/README.md com 134 (limite 200), docs/contribuicao-do-rodrigo.md com 80 (limite 110).

Arquivos editados: README.md, process-log/README.md, docs/contribuicao-do-rodrigo.md e docs/README.md, todos dentro de submissions/rodrigo-costa.
