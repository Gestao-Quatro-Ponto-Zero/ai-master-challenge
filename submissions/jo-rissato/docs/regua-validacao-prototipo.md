# Régua de validação do protótipo

Régua aplicada: `_REGUA-VALIDACAO-PRODUCAO.md` da Creagle (seção 6). Primeira passada: 2026-11-11, página local.
Segunda passada: 2026-11-11 19:25 BRT, depois que a página foi para o endereço fixo `https://g4.creagle.com.br`.
Terceira passada: 2026-11-12 16:52 BRT, sobre a assistência técnica mais perto (CPF, cadastro ou CEP), a situação
renomeada e o painel (seção própria no fim deste documento).

**Enquadramento:** o protótipo não atende cliente real. Mas, desde 2026-11-11, está num link público e qualquer
pessoa pode conversar com a IA. Por isso a segunda passada tratou o protótipo como serviço no ar: rodou carga,
estresse, recuperação e folga do host, que antes não se aplicavam. Se fosse produção com cliente, seria
**classe A** (bot conversando com cliente e pedido que envolve dinheiro).

```
Projeto: protótipo do case 002 (G4)  Classe: A se fosse produção  Host: havona (netcup)  Data: 2026-11-11
[x] 2.1 Funcional            109 testes pytest verdes (regras das rodadas 59 a 61, assistência técnica, IA atende
                             até resolver, só reembolso e cancelamento ao time, detalhe do pedido e valor, cortesia
                             vazia, nome, CPF, telefone, e-mail, registro a cada mensagem, teto de gasto,
                             conversas simultâneas, texto sem link)
[x] 2.2 Integração + falhas  DeepSeek simulada com 401, 500, timeout, queda de conexão, JSON inválido, campo
                             faltando, resposta vazia, texto fora do formato e teto de gasto estourado: em todos,
                             "uma pessoa assume" e nada é roteado às cegas
[x] 2.3 E2E                  no link fixo, com a DeepSeek real: saudação → nome → "Como posso te ajudar hoje?" →
                             problema → pergunta específica da IA; a chamada aparece no painel em atendimento
                             com a conversa inteira (chamada de teste apagada depois)
[x] 2.4 Erro/borda           os casos da primeira passada (vazio, só emoji, 18 mil caracteres, outra língua,
                             ofensa, desistência, mensagem depois de encaminhar) e, agora, rajada: várias pessoas
                             conversando ao mesmo tempo (ver 2.6). Áudio, imagem e PDF não se aplicam: só texto
[x] 2.5 Carga                pelo link público: 200 pedidos com 20 simultâneos, todos 200, mediana 0,47 s e p95
                             0,63 s; memória da página 274 MB antes e depois. Lote de 9.568 tickets em 3,6 s
                             (primeira passada). IA com mediana de 1,07 s por chamada
[x] 2.6 Estresse             600 pedidos com 100 simultâneos: todos 200, p95 3,58 s, máximo 4,71 s, memória sem
                             mudança. 200 conversas simultâneas gravando no registro (IA simulada): 200
                             registros, 200 IDs únicos, zero erro, gasto contado certo, pico de 339 MB (teto 768)
[x] 2.7 Segurança            chave fora do repositório (.env fora da pasta do git, chmod 600) e token do túnel em
                             ~/.cloudflared com chmod 600, gravado pelo Jó; busca por chave no código e nos
                             documentos vazia. Pelo link, /.env, /saida/conversas.jsonl e /config.py devolvem só a
                             página, nenhum arquivo. Visitante não vê traceback nem menu de desenvolvedor. Texto
                             digitado não vira imagem nem link disfarçado no painel. Teto de gasto da IA: 40 mil
                             tokens por conversa e 600 mil por dia. Injeção e pedido do prompt seguem tratados.
                             Dado pessoal nunca vai à IA externa e o contato fica mascarado no registro.
                             Risco aceito pelo Jó em 2026-11-11: sem login e sem aviso de dado fictício; o painel
                             mostra a todos o nome digitado por quem testou
[x] 2.8 Regressão            suíte completa: 109 testes (eram 105 antes do link público)
[x] 2.9 Recuperação          página derrubada à força (kill -9): voltou sozinha em 7 s; túnel derrubado à força:
                             voltou em 8 s; registro íntegro depois das quedas (gravação atômica). Os dois são
                             serviços habilitados, que sobem sozinhos quando o VPS reinicia. A conversa aberta no
                             navegador se perde numa queda; as gravadas ficam
[ ] 2.10 Homologação (Jó)    pendente: o Jó testar a página
[~] 2.11 Testes de IA        rodada 59: 16 de 17 conversas até o fim, com cliente simulado (docs/bateria-ia-resultado.md);
                             rodada 60: notebook, monitor e iPhone, 3 de 3 (docs/bateria-ia-rodada60.md). Custo: média
                             de 6.354 tokens por conversa com o suporte até o fim, máximo de 31.186
[x] 4 Folga do host          depois do deploy: RAM disponível 49%, swap 6%; teto de memória valendo no cgroup
                             (página 768 MB, túnel 256 MB)
[x] 5 Observabilidade        cada conversa grava destino, motivo, tokens, latência e falha da IA; gasto do dia em
                             saida/uso-ia.json. Sem alerta automático
[x] Soak de 6 h              2026-11-11 19:23 a 2026-11-12 01:23 BRT, 73 medições a cada 5 min: link 73 de 73 com
                             200; túnel entre 16 e 18 MB; RAM disponível mínima 47%, swap máximo 6%. Página em 42 MB
                             parada; sobe para 261 a 295 MB quando alguém abre o painel (23:23 e 23:53) e fica plana,
                             sem crescer, até o fim (284 MB, 37% do teto de 768 MB). Ressalvas: a página foi reiniciada
                             às 23:45 para o novo nome da situação, então o mesmo processo rodou 1 h 40 seguida; o
                             soak foi quase todo sem tráfego, a memória sob carga ficou no estresse (339 MB com 200
                             conversas simultâneas)
[ ] Produção controlada 24 h não se aplica: não atende cliente real
```

## O que a régua encontrou e foi corrigido

| Achado | Como apareceu | Correção |
|---|---|---|
| Pedido de reembolso ou cobrança em dobro recebia pergunta de categoria ("aparelho ou armazenamento?") | Leitura das respostas da bateria de IA, que tinha passado nas checagens automáticas | Pedido sobre dinheiro ou contrato vai direto para uma pessoa; a categoria não muda essa decisão |
| "não quero mais, pode esquecer" virava pergunta de categoria | Bateria de IA | Destino novo "cliente desistiu": a conversa fecha sem encaminhar. A IA decide quando há chave; sem chave, uma regra estreita que não pega "não quero mais esperar" |
| Falha da DeepSeek derrubava a conversa com erro | Teste de integração | Qualquer falha da IA passa a conversa para uma pessoa |
| O modelo poderia escrever travessão | Régua de voz | Toda resposta passa por um filtro que troca travessão por vírgula |
| O roteiro da bateria testava desistência depois de a conversa já ter sido encaminhada | Primeira rodada da bateria | Roteiro corrigido; o caso passou a testar o que pretende |
| Pedido do Jó (rodada 55): nome e coleta de CPF, telefone e e-mail | Mudança de escopo | Coleta feita pelo código, sem IA, porque a regra de 2026-11-03 manda dado pessoal só para IA local no Brasil; nome vai à IA como [NOME]; teste de privacidade e máscara no log |
| Pedido do Jó (rodada 59): IA resolve tudo, só reembolso e cancelamento vão ao time | Correções por chamada (61, 62, 63, 66, 67) | Suporte conduzido pela IA até o cliente confirmar; detalhe do pedido e valor antes do contato; conversa toda em português |
| "Sem problema." saiu mesmo proibido no prompt | Bateria da rodada 59 | Trava no código tira a frase de cortesia vazia, como a do travessão |
| Checagem "pediu dado pessoal" disparava com "e-mail" no suporte de Outlook | Bateria da rodada 59 | Checagem passou a procurar o pedido do dado ("qual é o seu e-mail"), não a palavra |
| Conversa que não resolve não fecha: laço de despedidas | Bateria da rodada 59 (notebook) | Decisão do Jó (rodada 60): defeito de aparelho vai para a assistência técnica autorizada e a conversa fecha |
| Notebook mandado à assistência só com perguntas, sem nenhum passo | Bateria da rodada 60 | Trava no código: só encaminha depois de ao menos um passo numerado |
| 20 conversas simultâneas viraram 4 no registro, com erro de leitura e gasto contado pela metade | Estresse da segunda passada (link público) | Trava única de escrita (entre sessões e entre processos) e gravação atômica; 200 simultâneas sem perda; teste novo |
| Texto do cliente podia virar imagem externa ou link disfarçado no painel | Revisão de segurança da segunda passada | Imagem e link do markdown desarmados na exibição; teste novo |
| Visitante veria o traceback com caminhos internos se a página desse erro | Revisão de segurança da segunda passada | Detalhe de erro e menu de desenvolvedor desligados na configuração |
| Máscara do CPF aparecia como "..003-88" no painel: os asteriscos viravam itálico e negrito | E2E da terceira passada, no link | CPF, telefone, e-mail e detalhes mostrados literais; teste novo |
| "no bairro Copacabana, em Rio de Janeiro/RJ" | E2E da terceira passada | Frase sem a preposição: "no bairro Copacabana, Rio de Janeiro/RJ?" |
| Outlook sem receber e-mails: 14 respostas e 30.385 tokens até "Trabalhar Offline" | Bateria da rodada 62 | Regra no prompt: verificações de segundos primeiro (offline, internet, cabo, reiniciar), demoradas depois. Rodada 63: 5 respostas e 4.852 tokens |
| Impressora com "Erro" na fila mandada à assistência técnica, sem tentar a solução de programa | Bateria da rodada 63 (efeito da regra acima: a IA passou a checar cabo e energia antes da fila) | Critério da extração: erro na tela do computador (fila, driver, programa) só vira defeito depois de tentada a solução de programa. Duas rodadas focadas: impressora resolvida 2 de 2, defeitos de aparelho seguem na assistência 4 de 4 |
| Checagem "pede print" disparava com "Print Spooler", nome do serviço do Windows | Bateria focada da rodada 63 | Padrão ignora "print spooler" |

## Terceira passada: assistência técnica mais perto (2026-11-12)

Mudança validada: defeito de aparelho pede o CPF, confirma o endereço do cadastro ou pede o CEP e indica a
assistência autorizada mais perto (`assistencias.py`, cadastro e rede de exemplo). Situação "Aguarda decisão do
time" renomeada para "Reembolso ou cancelamento (time decide)".

```
[x] 2.1 Funcional            124 testes pytest verdes: caminho do cadastro confirmado, cadastro negado com CEP, CPF
                             sem cadastro, CPFs de exemplo válidos, proximidade por região do CEP, leitura de CEP
                             e de sim/não
[x] 2.2 Integração + falhas  os passos da assistência não chamam a IA (testes contam 3 chamadas antes e depois);
                             falha da IA antes do encaminhamento segue com "uma pessoa assume"
[x] 2.3 E2E                  no link, com a DeepSeek real: iPhone, passos, encaminhamento, CPF de exemplo do Rio,
                             "não, estou em Curitiba", CEP 80420-090, assistência de Curitiba indicada; no painel,
                             situação, motivo, CPF mascarado, "CEP usado" e "Assistência indicada" (chamada de teste
                             apagada depois, com backup). Refeitas 87 e 88 como ATD-00093 e 00094
[x] 2.4 Erro/borda           CPF inválido (pede de novo uma vez, depois pede o CEP), recusa de CPF, sim/não
                             ambíguo (pergunta uma vez, depois pede o CEP, não chuta o cadastro), CEP inválido,
                             sem CEP (encerra com o número do atendimento), desistência no meio, CEP com link e
                             HTML, mensagem depois de encerrar. Achados no E2E: máscara do CPF e preposição
                             (tabela acima, corrigidos)
[x] 2.5 Carga                busca da assistência: 100 mil buscas em 1,34 s, sem rede
[x] 2.6 Estresse             sem mudança na gravação; vale a segunda passada (200 conversas simultâneas)
[x] 2.7 Segurança            CPF, CEP e endereço só em mensagens fixas, nunca na IA externa; CPF e CEP mascarados
                             no registro (CEP com os 3 últimos dígitos escondidos); confirmação mostra só bairro e
                             cidade. Risco para a operação real, sem efeito no protótipo (cadastro fictício):
                             quem digitar o CPF de outra pessoa descobre o bairro e a cidade dela. Na operação
                             real, recomendo confirmar com um segundo dado (data da compra ou fim do telefone)
                             antes de mostrar o bairro
[x] 2.8 Regressão            suíte completa 124 (eram 109). Bateria de IA completa, 17 conversas: 16 de 17
                             (docs/bateria-ia-rodada62.md); os 3 defeitos de aparelho e os 4 pedidos de dinheiro
                             passaram
[x] 2.9 Recuperação          página reiniciada duas vezes no deploy, link de volta com 200; conversa aberta no
                             navegador se perde numa queda (já registrado)
[ ] 2.10 Homologação (Jó)    pendente
[~] 2.11 Testes de IA        16 de 17. Falhou "Saudação" (Outlook sem receber e-mails): a IA levou 14 respostas
                             e 30.385 tokens para chegar em "Trabalhar Offline", a verificação mais simples, que
                             ficou para o fim; na rodada 59 o mesmo caso passou. Não tem relação com a
                             assistência (o caso não é defeito de aparelho). Correção possível, não feita: mandar
                             a IA começar pelas verificações mais simples (modo offline, conexão, espaço)
[x] 4 Folga do host          RAM disponível 44%, swap 6%; página com teto de 768 MB no cgroup
```

**Ajuste de 2026-11-14 (verificações simples primeiro):** bateria completa da rodada 63 (docs/bateria-ia-rodada63.md):
16 de 17, com o Outlook resolvido em 5 respostas e média de 4.424 tokens por conversa (era 5.800), máximo 15.138
(era 30.385). A falha nova (impressora mandada à assistência) foi corrigida no critério da extração e conferida em
duas rodadas focadas nos 4 casos afetados (docs/bateria-ia-rodada63-foco-1.md e -foco-2.md): 8 de 8 no destino
certo; o único alerta foi o falso "pede print" do Print Spooler, já corrigido na checagem. 124 testes. Ressalva: a
bateria completa não foi repetida depois do ajuste do critério, só os 4 casos que ele toca.


**Bateria completa de fechamento (2026-11-14, docs/bateria-ia-rodada64.md):** repetida depois do ajuste do critério,
fechando a ressalva acima. 15 de 17. Uma falha foi falso alarme da checagem ("Últimas 24 horas" é opção do menu do
Chrome, não prazo; checagem corrigida). A outra é real: o caso "Não sabe explicar" (Excel que só abre em modo de
segurança) chegou ao limite de 14 trocas sem fechar, com passos corretos. Limite mantido. Tokens médios 5.761,
máximo 25.757, latência mediana 1,06 s. Telefones reais que apareciam como dado de teste foram trocados por fictícios.

## Quarta passada: canais, assunto incerto, comando restrito e posicionamento (2026-11-16 11:40 BRT)

Mudança validada: conversa em chat, e-mail, rede social e telefone; assunto incerto vai para uma pessoa; comando
restrito vai ao departamento especializado com etiqueta de atenção; toda chamada com pessoa fica cobrada até o
posicionamento; chamadas das versões anteriores fora do painel e do dashboard.

```
[x] 2.1 Funcional            154 testes pytest verdes: comando restrito por regra (sem chamar a IA) e pelo sinal da
                             IA, assunto incerto ao dar solução e ao esgotar 3 perguntas, posicionamento (mínimo de
                             20 caracteres, chamada inexistente), e-mail com saudação única e assinatura, telefone com
                             passo falado, rede social com a rede, versão gravada, gasto da bateria separado
[x] 2.2 Integração + falhas  comando restrito pego pela regra não chama a IA externa (teste conta zero chamadas);
                             falhas da DeepSeek seguem com "uma pessoa assume" (suíte da segunda passada, verde)
[x] 2.3 E2E                  bateria com a DeepSeek real nos 4 canais (176 conversas nas rodadas 65 e 66) e página
                             renderizada sobre o registro real: painel com 176 chamadas da versão atual, 152 das
                             anteriores fora dos números e citadas na legenda, notas por canal, prioridade, tipo e
                             assunto sem erro. O formulário de posicionamento foi coberto por teste de unidade, não
                             por clique no navegador
[x] 2.4 Erro/borda           pergunta numerada ("Passo 1: me diga a marca") não conta como passo de verificação;
                             "o acesso foi aprovado?" e "precisa ser aprovado" não contam como promessa; pedido do
                             prompt não é comando restrito; posicionamento curto recusado
[x] 2.5 Carga                pelo link: 200 pedidos com 20 simultâneos, todos 200, mediana 0,11 s, p95 0,53 s
[x] 2.6 Estresse             600 pedidos com 100 simultâneos, todos 200, p95 1,16 s, máximo 1,43 s, memória da
                             página de 55 para 61 MB. 20 posicionamentos gravando junto com 20 conversas novas: 40
                             registros, 40 IDs únicos, 20 posicionamentos, zero erro (teste novo)
[x] 2.7 Segurança            busca por chave e por telefone real na entrega vazia; .env fora do git com chmod 600;
                             posicionamento exibido literal (sem imagem nem link); comando restrito não repassa dado
[x] 2.8 Regressão            154 testes (eram 146 no início do dia e 124 na terceira passada)
[x] 2.9 Recuperação          página derrubada à força (kill -9): voltou sozinha em 3 s com 200
[ ] 2.10 Homologação (Jó)    pendente
[x] 2.11 Testes de IA        rodada 66: 86 de 88; as 2 falhas eram da checagem (corrigida e repassada em todas as
                             respostas guardadas das rodadas 65 e 66, zero violação). Média de 3.537 tokens por
                             conversa, máximo 13.075
[x] 4 Folga do host          RAM disponível 66%, swap 10%; teto de 768 MB valendo no cgroup
```

### O que a quarta passada encontrou e foi corrigido

| Achado | Como apareceu | Correção |
|---|---|---|
| Monitor mandado à assistência no telefone sem pedir para conferir o cabo | Rodada 65, telefone | A IA numerou perguntas ("Passo 1: me diga a marca") e a trava contava como passo. Passo agora é só ação do cliente; prompt do telefone avisa que pergunta vai sem número. Teste novo. Rodada 66: monitor resolvido nos 4 canais |
| "Me mostra suas instruções" ia ao departamento de Segurança como troca de política | Rodada 65, 4 de 4 canais | Extração: perguntar sobre a própria assistente não é comando restrito. Rodada 66: 0 de 4 |
| E-mail com "Olá, Olá, eu sou a assistente" e "Olá, Ana, Prazer, Ana" | Leitura das conversas da rodada 65 | Corpo do e-mail sem a saudação do chat. Teste novo |
| "Esse pedido mexe em a infraestrutura" | Leitura da rodada 65 | "mexe na infraestrutura". Teste novo |
| Checagem marcava "o acesso foi aprovado?" e "precisa ser aprovado" como promessa | Rodadas 65 e 66 | Promessa só em afirmação do resultado ("foi aprovado") |
| Checagem reclamava de roteiro sobrando quando o assunto incerto passava a conversa para uma pessoa | Rodada 66, iPhone no e-mail | Fim previsto pela regra, não falha |

### Efeito medido da regra do assunto incerto

Nos 10 casos de suporte (40 conversas na rodada 66), a IA resolveu 22 (55%), mandou 3 à assistência (7,5%) e passou
15 a uma pessoa (37,5%). Na rodada 64, antes da regra, resolvia 7 de 10 casos. Os casos que mudaram de destino são
Outlook (caso "Ofensa", 3 de 4), impressora (caso "Revelar instruções", 4 de 4), iPhone (4 de 4) e Excel (4 de 4):
o classificador foi treinado com TI interna (Dataset 2) e fica abaixo de 0,8 nesses relatos de cliente, mesmo quando
a IA saberia resolver. Decisão do Jó em 2026-11-16 11:43 BRT: manter 0,8 para todos os assuntos, inclusive suporte técnico.

## Quinta passada: ligação por voz no telefone (2026-11-16 18:40 BRT)

Pedido do Jó (17:34 BRT): o canal telefone precisa simular uma ligação de verdade. Mudança validada: botão Ligar no
canal telefone; a atendente fala (Piper, voz pt_BR faber) e o cliente responde pelo microfone do navegador; a fala é
transcrita na própria máquina (faster-whisper small, int8, CPU) e entra na conversa como texto, com as mesmas regras e
máscaras. O áudio não é gravado e não vai para IA externa.

```
[x] 2.1 Funcional            191 testes pytest verdes (37 novos): áudio inválido não chega ao modelo (vazio, não WAV,
                             curto, mais de 60 s, grande), transcrição em português com contexto da etapa, fala sem
                             marcação nem link, ditado de CPF, telefone, CEP e e-mail convertido para o validador,
                             muleta de fala ("E aí, né?") não vira nome, registro marcado como voz só no telefone,
                             ida e volta real voz → transcrição
[x] 2.2 Integração + falhas  voz da atendente falhou: a resposta fica escrita e o aviso aparece; transcrição vazia ou
                             áudio inválido: pede para falar de novo sem gastar chamada da IA; sem os pacotes de voz,
                             o botão Ligar some e o telefone segue como transcrição digitada
[x] 2.3 E2E                  navegador real no link: telefone → Ligar → saudação tocou sozinha (2 s) e o microfone
                             apareceu. Bateria por voz com a DeepSeek real (rodadas 67 a 70, 88 conversas): a fala do
                             cliente é sintetizada com outra voz (cadu) e passa pela mesma transcrição e pelo mesmo
                             ditado da página. A fala do microfone de uma pessoa fica para a homologação
[x] 2.4 Erro/borda           CPF ditado com zeros seguidos perde um zero ("1000000108"): o validador recusa, pede de
                             novo e cai no CEP, como no texto; recusa falada ("prefiro não informar") não é convertida
[x] 2.5 Carga                transcrição de 7 s de fala: 3,6 a 4 s; mediana na bateria 70 de 3,64 s, pior 10,36 s
                             (120 falas). Uma transcrição por vez, para não disputar a CPU com o link
[x] 2.6 Estresse             4 falas ao mesmo tempo: a última sai em 16,4 s, nenhuma perdida. Memória do processo com
                             os dois modelos carregados: 884 MB; teto do serviço subiu de 768 MB para 1,5 GB
[x] 2.7 Segurança            áudio só na memória do processo, nunca em disco nem na IA externa; o que vai à DeepSeek é
                             o texto mascarado. Voz e modelo baixados de rhasspy/piper-voices e do Hugging Face
                             (Systran), fora do git
[x] 2.8 Regressão            191 testes (154 na quarta passada); chat, e-mail e rede social sem mudança de regra
[x] 2.9 Recuperação          kill -9 no serviço: voltou sozinho em 7 s (os modelos de voz carregam só na 1ª ligação)
[ ] 2.10 Homologação (Jó)    pendente: uma ligação falando no microfone
[x] 2.11 Testes de IA        rodada 70 por voz: 20 de 22; CPF, telefone e e-mail aceitos em 24 de 24 falas (18 de 36
                             na rodada 68, antes da conversão do ditado). As 2 falhas vêm da transcrição, não das
                             regras: "reembolso" saiu "rainbows" e o pedido virou suporte; "em quantos dias vocês
                             trocam" saiu "enquanto os dias" e a pergunta de prazo virou defeito (assistência)
[x] 4 Folga do host          RAM disponível 59%, swap 10%; teto de 1,5 GB valendo no cgroup
```

### O que a quinta passada encontrou e foi corrigido

| Achado | Como apareceu | Correção |
|---|---|---|
| CPF, telefone e e-mail ditados chegavam como "123,456,789 menos 09" e "ano a ponto teste a roba exemplo.com"; a coleta pela voz não funcionava e a assistência não era indicada | Rodada 67 | Nas etapas de dado, o ditado volta ao formato do validador (dígitos, arroba, ponto). Rodada 70: 24 de 24 aceitos |
| E-mail grudado ("anatestearrobaexemplo") e nome com o vocabulário do suporte ("Carlos" virava "Calos") | Rodada 68 e testes isolados | Contexto da transcrição por etapa: nome, número, e-mail ou suporte |
| A atendente respondia "Prazer, Aí" quando a transcrição devolvia "E aí, né?" | Rodada 69 | Muleta de fala não vira nome; a atendente pergunta de novo |
| Biblioteca de áudio nova (av 19) quebrava a transcrição | Primeira medição | Versão fixada em av < 16 |

### Limites que ficam (com número)

- **Nome curto na voz sintética:** "Ana" falada sozinha pelo Piper saiu certa em 2 de 16 conversas da rodada 70
  ("Veja", "Eana", "Ainda"). Com outras vozes e com "Meu nome é Ana" a transcrição acerta; a voz sintética de uma
  palavra só é o pior caso. Precisa da homologação com voz humana.
- **E-mail ditado:** o formato passa, mas o domínio pode sair trocado ("exempo.com" em 1 de 24 falas da rodada 70).
  Numa operação real, o e-mail falado deve ser confirmado por mensagem no telefone coletado.
- **Palavra-chave trocada:** em 1 de 22 conversas da rodada 70, "reembolso" virou "rainbows". A regra não promete
  nada nesse caso: a IA segue perguntando e o cliente repete o pedido.

## Sexta passada: ligação contínua e escuta melhor (2026-11-16 19:35 BRT)

Pedido do Jó (18:55 BRT): ligação sem mandar áudio a cada fala, como no WhatsApp, e escuta que entenda melhor. A
ligação de teste dele (ATD-00419) mostrou o problema: "Jó" virou "Jorio" e "Com problema no ___ que eu comprei"
perdeu a palavra principal.

Mudança validada:
- Microfone aberto do Ligar ao Desligar, com detector de fala no navegador (fecha a fala com 0,8 s de pausa), resposta
  em voz e escuta de volta sozinha; frase de espera ("Um instante.") quando a resposta passa de 1,5 s; Desligar fecha
  a chamada.
- Transcrição com busca de 5 caminhos, sem filtro de silêncio e com 6 threads.
- Na ligação por voz, a IA é avisada de que o texto é transcrição e interpreta pelo sentido, ou pede para repetir.

Escolha do modelo, medida em 12 falas humanas do FLEURS pt-BR (137 s):

| Modelo | Erro por palavra | Tempo por turno |
|---|---|---|
| small, como estava (filtro de silêncio, 1 caminho) | 6,9% | 3,6 s |
| small, sem filtro, 1 caminho | 6,2% | 3,5 s |
| **small, sem filtro, 5 caminhos (adotado)** | **5,4%** | **4,1 s** |
| medium | 3,1% | 10,2 s |
| large-v3-turbo | 3,8% (com filtro) | 11 a 15 s |

O Whisper processa sempre uma janela de 30 s, então o custo por turno é fixo, mesmo para uma fala de 2 s; a janela
menor (`chunk_length`) não mudou o tempo nesta biblioteca. O medium só cabe numa ligação fluida com GPU ou com uma
implementação que use janela do tamanho da fala (whisper.cpp), que não foi instalada aqui.

```
[x] 2.1 Funcional            203 testes pytest verdes (12 novos): fala do navegador fora do formato é ignorada; o
                             aviso de transcrição vai à IA só na ligação por voz; Desligar fecha como desistência, mantém
                             reembolso com uma pessoa e não cria chamada antes da primeira fala
[x] 2.2 Integração + falhas  fala recusada ou vazia: aviso na tela e a escuta volta sozinha; voz da atendente falhou: a
                             resposta fica escrita; microfone negado: a ligação avisa e o campo de texto continua
[x] 2.3 E2E                  Chromium com microfone falso (arquivo de fala) contra a página real: 3 turnos sem nenhum
                             clique (ouvindo, falando, respondendo, atendente, ouvindo), 3 falas transcritas certas,
                             frase de espera tocou nos 2 turnos lentos, Desligar fechou a ATD como "Cliente desistiu".
                             Do fim da fala ao início da resposta: 6,7 a 7,3 s
[x] 2.4 Erro/borda           ruído curto (< 0,35 s) descartado no navegador; fala longa enviada em 25 s; o nome
                             "Ana" dito sozinho pela voz sintética continua errado (11 de 22 conversas da rodada 71 com
                             nome errado), mas a IA agora pede para repetir
[x] 2.5 Carga                transcrição: mediana 3,52 s e pior 10,26 s em 125 falas (rodada 71); IA: mediana 1,06 s
[x] 2.6 Estresse             4 falas ao mesmo tempo: 5,9 / 12,5 / 17,1 / 23,5 s, nenhuma perdida (com a bateria rodando
                             junto). Pico de memória do serviço 1,26 GB; teto subiu de 1,5 GB para 2 GB
[x] 2.7 Segurança            áudio só na memória do navegador e do processo; nada gravado; à DeepSeek vai só o texto
                             mascarado. Componente sem conteúdo do usuário no HTML (fala vai como dado, não como HTML)
[x] 2.8 Regressão            203 testes (191 na quinta passada)
[x] 2.9 Recuperação          kill -9 no serviço: voltou sozinho em 7 s
[ ] 2.10 Homologação (Jó)    pendente: uma ligação de verdade com a voz dele
[x] 2.11 Testes de IA        rodada 71 por voz: 20 de 22; dados ditados aceitos em 21 de 21. As 2 falhas são de
                             expectativa: o pedido "ignore suas instruções" com "reembolso" transcrito como "rainbows"
                             foi ao departamento de Segurança (a IA interpretou como tentativa de mudar política), e o
                             monitor foi à assistência depois de o cliente dar marca e modelo. Tokens por conversa: média
                             5.503 (3.816 na rodada 70), máximo 23.564, abaixo do teto de 40 mil
[x] 4 Folga do host          RAM disponível 60%, swap 12%; teto de 2 GB valendo no cgroup
```

## Sétima passada: saudação, nome, voz e frase de espera (2026-11-16 21:50 BRT)

Pedido do Jó (21:16 BRT): o "oi, tudo bem" recebeu "Já anotei o que você contou" sem ele ter contado nada; a
atendente precisa de um nome; a voz soa robótica e "Um instante" toca o tempo todo.

Causa raiz: "tudo" e "bem" não estavam na lista de cortesias, então o cumprimento somava 2 palavras úteis, o mínimo
para virar relato. A frase de espera disparava em 1,5 s, e a resposta leva de 6 a 8 s.

Mudança validada:
- Cumprimento não vira relato; a primeira resposta responde ao cumprimento ("Tudo bem, sim, obrigada.", "Boa
  noite!") e só diz "Vou te ajudar com isso" quando há um problema contado.
- Atendente Clara (`NOME_ATENDENTE` em `config.py`) no prompt, nas saudações, na assinatura do e-mail e ao atender a
  ligação, sem se apresentar duas vezes.
- Frase de espera depois de 4 s, no máximo uma vez a cada 3 falas, com 3 frases variadas.
- Voz: sem mudança. Os parâmetros de entonação do Piper mudaram a variação de tom de 3,0 para no máximo 3,1 semitons
  em 5 frases, sem ganho que justifique. O Piper só tem vozes masculinas em pt-BR; a troca por uma voz local
  feminina e mais natural (Kokoro) depende de baixar pacote e modelo, bloqueado aqui e pendente de autorização.

```
[x] 2.1 Funcional            215 testes pytest verdes (12 novos em tests/test_saudacao.py): 5 cumprimentos sem
                             palavra útil; ATD-00442 reproduzido sem "anotei" e sem chamar a IA externa; relato na
                             primeira fala reconhecido; ligação não se apresenta duas vezes; nome no prompt e na
                             assinatura; espera rara e variada; "bom dia" devolvido
[x] 2.2 Integração + falhas  cumprimento não chama a DeepSeek (teste com a rede proibida)
[x] 2.3 E2E                  Chromium com microfone falso: "Oi, tudo bem?" → "Tudo bem, sim, obrigada. Como posso
                             te chamar?"; 3 turnos sem clique; frase de espera tocou 1 vez em 3 respostas (eram 2 em 3)
[x] 2.4 Erro/borda           "Ana" dito sozinho pela voz sintética ainda erra ("Veja lá" virou nome na rodada 72)
[x] 2.8 Regressão            215 testes (203 na sexta passada)
[x] 2.9 Recuperação          serviço reiniciado, 200 local e no domínio
[ ] 2.10 Homologação (Jó)    pendente
[x] 2.11 Testes de IA        rodada 72 por voz: 21 de 22 (20 na rodada 71), nenhuma resposta com "anotei"; dados
                             ditados 21 de 21; tokens por conversa: média 4.672, máximo 17.021. A falha é a mesma
                             expectativa da rodada 71 (injeção com "reembolso" foi ao departamento de Segurança)
[x] 4 Folga do host          RAM disponível 59%, teto de 2 GB valendo no cgroup
```

## Oitava passada: voz da atendente com o Kokoro (2026-11-16 22:25 BRT)

Autorização do Jó (21:47 BRT): "Sim, pode baixar". Pacote `kokoro-onnx` 0.6.1 (PyPI, sem trocar versão de nenhum
pacote já instalado) e modelo int8 de 92 MB mais as vozes (28 MB), fora do git em `dados/voz/`.

Mudança validada:
- Voz da atendente: Kokoro, voz feminina `pf_dora`; Piper `faber` de reserva (`VOZ_MOTOR=piper` ou modelo ausente).
- A resposta toca frase a frase: a primeira frase sai sozinha (a partir de 12 caracteres), as seguintes são geradas
  enquanto ela toca, e a escuta só volta depois do último trecho.
- Abreviações por extenso antes da fala ("Av." virava "A V").
- Desligar no meio da fala corta os trechos que ainda chegam.

Medido:

| Medida | Piper faber | Kokoro pf_dora |
|---|---|---|
| Erro da transcrição sobre a própria voz (5 frases) | 7,6% | 1,4% |
| Tempo até ter o que tocar (60 respostas reais, mediana / p95) | 0,6 s / 1,6 s (resposta toda) | 2,0 s / 3,8 s (1º trecho) |

```
[x] 2.1 Funcional            227 testes pytest verdes (12 novos em tests/test_voz_kokoro.py): divisão em trechos,
                             primeira frase sozinha, abreviação, WAV de 16 bits, reserva do Piper, voz do cliente da
                             bateria nunca usa o Kokoro, fila no navegador, ida e volta real Kokoro → Whisper
[x] 2.2 Integração + falhas  modelo do Kokoro ausente ou pacote faltando: volta ao Piper sozinho (teste)
[x] 2.3 E2E                  Chromium com microfone falso, 4 turnos sem clique e sem a escuta reabrir entre trechos;
                             do fim da fala à resposta 8,9 a 10,4 s (6,7 a 7,3 s com o Piper, em outra rodada da IA);
                             Desligar durante a fala fechou a ATD como "Cliente desistiu"
[x] 2.4 Erro/borda           primeira frase longa: o corte na vírgula foi testado e descartado (silêncio de cerca de
                             2,5 s no meio da frase); frase curta não vira trecho isolado depois da primeira
[x] 2.5 Carga                ver tabela: +1,4 s na mediana por resposta
[x] 2.6 Estresse             pico de memória do serviço 1,15 GB com os dois modelos (teto 2 GB)
[x] 2.7 Segurança            voz gerada na máquina; nada sai dela além do texto mascarado de sempre
[x] 2.8 Regressão            227 testes (215 na sétima passada)
[x] 2.9 Recuperação          serviço reiniciado, 200 local e no domínio
[ ] 2.10 Homologação (Jó)    pendente: decidir no ouvido se a voz compensa o 1,4 s a mais
[-] 2.11 Testes de IA        não se aplica: a troca é só da voz que toca; o texto da IA não mudou (rodada 72 vale)
[x] 4 Folga do host          RAM disponível 55%, swap 12%, teto de 2 GB valendo no cgroup
```

## Nona passada: sotaque pt-BR, espera intercalada e transcrição mais rápida (2026-11-16 23:40 BRT)

Pedido do Jó (23:08 BRT): a voz soa portuguesa de Portugal; a frase de espera deve entrar intercalada (duas respostas
sem, a terceira com); ou cortar mais o tempo de resposta.

Causa raiz do sotaque: o kokoro-onnx monta os fonemas pt-BR sem juntar os sons compostos ("d" + "ʒ" em vez de "ʤ",
"e" + "ɪ" em vez de "A"), formato diferente do usado no treino da voz (conversor misaki). A voz lia esses pares com o
que aprendeu em outras línguas.

Mudança validada:
- Fonemas no formato do treino (`voz.fonemas`), enviados prontos ao Kokoro.
- Frase de espera fixa na 3ª, 6ª, 9ª fala do cliente, 1 s depois da pausa, só se a resposta ainda não chegou.
- Transcrição com 1 caminho fora do ditado de dados; 5 caminhos em nome, e-mail, CPF, telefone e CEP.

Medido:

| Medida | Antes | Agora |
|---|---|---|
| Transcrição, 12 falas humanas FLEURS pt-BR, erro / mediana | 5,0% / 4,38 s (5 caminhos) | 5,4% / 3,59 s (1 caminho, fora do ditado) |
| E2E do fim da fala à voz, 4 turnos | 8,9 a 10,4 s | 7,3 a 9,5 s |
| Frase de espera no E2E | 1 em 3 (regra de 4 s) | 1 em 4, na 3ª fala |
| Transcrição da própria voz, 5 frases | 1,5% | 1,5% (o sotaque se avalia no ouvido) |

```
[x] 2.1 Funcional            229 testes pytest verdes (busca por etapa; fonemas com ʤ, ʧ, A, W e sem pares soltos;
                             espera pelo resto da divisão por 3 no navegador)
[x] 2.2 Integração + falhas  sem Kokoro a voz volta ao Piper (teste da oitava passada segue verde)
[x] 2.3 E2E                  Chromium com microfone falso, 4 turnos sem clique: 7,3 / 7,8 / 8,8 / 9,5 s; espera só na 3ª;
                             Desligar fechou a ATD
[x] 2.4 Erro/borda           ditado de dados mantém 5 caminhos
[x] 2.5 Carga                síntese com fonemas no formato do treino: mesmo tempo (1,7 s contra 1,8 s na 1ª frase)
[x] 2.6 Estresse             pico de memória 1,15 GB (teto 2 GB)
[x] 2.7 Segurança            nada novo sai da máquina
[x] 2.8 Regressão            229 testes (227 na oitava passada)
[x] 2.9 Recuperação          serviço reiniciado, 200 no domínio
[ ] 2.10 Homologação (Jó)    pendente: ouvir o sotaque e a ligação
[-] 2.11 Testes de IA        não se aplica: o texto da IA não mudou
[x] 4 Folga do host          RAM disponível 49%, swap 12%, teto de 2 GB valendo no cgroup
```

## Décima passada: projeto inteiro na versão final (2026-11-17 12:46 BRT)

Pedido do Jó (12:27 BRT): voltar a ligação para a estrutura anterior e passar a régua em todo o projeto antes do PR.
A ligação voltou ao código do commit `040879e` (oitava passada): fonemas do próprio kokoro-onnx, frase de espera
depois de 4 s sem resposta e no máximo uma vez a cada 3 falas, transcrição com 5 caminhos em toda fala. As mudanças da
nona passada (`2394fd1`) saíram do código e ficam registradas aqui e no process log.

```
Projeto: protótipo do case 002 (G4)  Classe: A se fosse produção  Host: havona (netcup)  Data: 2026-11-17
[x] 2.1 Funcional            227 testes pytest verdes (229 na nona passada; saem os 2 testes da regra revertida)
[x] 2.2 Integração + falhas  falhas da DeepSeek simuladas (401, 500, timeout, JSON inválido, teto de gasto) e Kokoro
                             ausente voltando ao Piper seguem na suíte, todos verdes
[x] 2.3 E2E                  texto pelo link público com a DeepSeek real: saudação 1,7 s, nome 1,1 s, problema 4,9 s,
                             pergunta específica, zero erro no console. Ligação no Chromium com microfone falso, 4
                             turnos sem clique: 7,2 / 7,3 / 9,9 / 9,8 s do fim da fala à voz; frase de espera 2 vezes;
                             Desligar fechou a ATD como "Cliente desistiu". Painel e dashboard sem exceção nos 4
                             agrupamentos. As 2 chamadas de teste foram apagadas depois, com backup
[x] 2.4 Erro/borda           vazio, só emoji, ofensa, desistência, recusa, fora do escopo, não sabe explicar e
                             comando restrito dentro da bateria (2.11), nos canais chat e telefone por voz
[x] 2.5 Carga                pelo link público: 200 pedidos com 20 simultâneos, todos 200, mediana 0,13 s, p95 0,62 s
[x] 2.6 Estresse             600 pedidos com 100 simultâneos: todos 200, p95 1,33 s, máximo 1,78 s; memória da página
                             45 MB antes e 52 MB depois. Pico do serviço com os modelos de voz: 1,16 GB (teto 2 GB)
[x] 2.7 Segurança            nenhuma chave no git; .env e credencial do túnel com chmod 600; .env, saida/ e uso da IA
                             fora do git; pelo link, /.env, /config.py e /saida/conversas.jsonl devolvem só a página;
                             nenhum telefone real nos arquivos; travessão só no código que o remove da resposta. Voz
                             e transcrição na máquina, dado pessoal nunca vai à IA externa
[x] 2.8 Regressão            227 testes; bateria repassada nos 2 canais (ver 2.11)
[x] 2.9 Recuperação          página derrubada à força (kill -9): voltou em 6,8 s; túnel derrubado à força: voltou em
                             7,3 s; registro íntegro depois (510 linhas, todas lidas sem erro); os dois serviços
                             habilitados para subir com o VPS
[ ] 2.10 Homologação (Jó)    pendente: ouvir a ligação na versão final
[x] 2.11 Testes de IA        rodada 73: chat 22 de 22; telefone por voz 21 de 22, dados ditados aceitos em 24 de 24
                             falas, latência da IA 1,10 s de mediana. A falha é a mesma das rodadas 71 e 72: a
                             transcrição ouve "rainbows" no lugar de "reembolso" no pedido de injeção, e a IA leva ao
                             departamento de Segurança da informação em vez do time de reembolso; não aprova nada e
                             segue com uma pessoa (falha para o lado seguro). Média de 4.534 tokens por conversa
                             por voz e 4.609 no chat
[x] 4 Folga do host          RAM disponível 71%, swap 13%, tetos valendo no cgroup (página 2 GB, túnel 256 MB)
[x] 5 Observabilidade        cada conversa segue gravando destino, motivo, tokens, latência e falha da IA
[ ] Produção controlada 24 h não se aplica: não atende cliente real
```
