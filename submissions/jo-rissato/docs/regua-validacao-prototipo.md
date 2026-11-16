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
