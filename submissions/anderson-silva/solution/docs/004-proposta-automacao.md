# Proposta de automação do suporte

- **Status:** versão final da submissão, 2026-11-03.
- **Origem:** diagnóstico e testes registrados no [audit trail](../../process-log/002-audit-trail.md), principalmente os itens 95, 100, 107, 130, 133, 143, 145, 151 e 158. Estrutura aprovada nos itens 146 a 148; grupos de problema acrescentados no item 153; sinais no texto do Dataset 1 no item 161; duplicatas, exemplos e fluxo visual no item 171; limiar por categoria no item 183.
- **Autoria:**
  - Direção, decisões e ajustes da pessoa candidata: as três perguntas do Diretor, a premissa do item 95, o teste do zero-shot com Jev e embeddings, a fórmula com uma única premissa, a IA generativa sempre com revisão humana, a confirmação automática fora da métrica de primeira resposta e o formato curto.
  - Redação, estrutura e cálculos: IA, com aprovação da pessoa candidata. Todos os números vêm de scripts do projeto.

## Resumo executivo

Dois terços dos tickets (67,3%) estão parados: 33,3% sem nenhuma resposta e 34,0% aguardando o cliente. O acúmulo é igual em todos os canais, prioridades, tipos e produtos, e há indício de que a fila não respeita a prioridade. Os dados atuais não explicam o CSAT e não têm rótulo confiável nem tempo real. O que o cliente escreve também não é usado: quem diz que é urgente ou que já contatou o suporte não recebe prioridade maior, e o problema descrito não bate com o assunto registrado.

Por isso, a proposta começa pelo processo, sem IA: formulário de abertura, fila por prioridade, cobrança automática do cliente e registro de cada etapa. Esses registros criam o histórico de que a IA precisa. Onde esse histórico existe (Dataset 2), um classificador supervisionado encaminha 70,8% dos tickets sozinho com 95% de acerto. Sem histórico, o zero-shot acerta 43%, o que não basta para decidir sozinho.

Lidos pelo texto, sem rótulo, os problemas se concentram em acesso, equipamentos e um único sistema, o Oracle: juntos, cerca de 58% dos tickets. Entre 3,7% e 12,5% são mensagens padronizadas, resolvíveis por regra.

A IA generativa entra para ajudar o atendente, sempre com revisão humana: resumo do ticket, rascunho de resposta e, quando houver soluções validadas, uma base de conhecimento.

Ganho de referência na triagem: **11,79 × m horas a cada 1.000 tickets**, em que m é o número de minutos de triagem manual por ticket (35,4 horas com m = 3). A taxa de 70,8% foi medida em outro domínio e precisa ser medida de novo no histórico da empresa.

## 1. O que os dados mostram

| Achado | Base | Item | Consequência |
|---|---|---|---|
| 67,3% parados: 33,3% sem resposta e 34,0% aguardando o cliente | Dataset 1 | 143 | Atacar a entrada e a espera do cliente |
| Acúmulo igual em todos os segmentos (V ≤ 0,067) | Dataset 1 | 143 | Gargalo estrutural, não de um canal |
| Indício de que a fila ignora a prioridade: 32,5% dos críticos sem resposta, contra 33,7% dos de prioridade baixa. É uma foto, sem datas | Dataset 1 | 143, 145 | Fila por prioridade, com alerta de prazo |
| CSAT sem explicação; todos os fechados têm nota | Dataset 1 | 143 | Registrar o que explica o CSAT |
| Tipo e assunto não batem com o texto; a resolução não traz informação, nem por palavras nem por sentido (semelhança com a descrição igual à de pares sorteados, p = 0,498) | Dataset 1 | 100, 101, 158 | Hoje não há base para treinar nem para a base de conhecimento |
| 60,9% das descrições não trazem problema específico; as demais trazem um de 7 problemas (de 3,7% a 5,7% cada), que não bate com o assunto registrado (V = 0,040) | Dataset 1 | 158 | Problema escolhido no formulário e confirmado pelo atendente |
| 87,9% trazem algum sinal do cliente: tentativa prévia 34,1%, após atualização 11,3%, urgência 8,4%, contato repetido 5,4%. Nenhum sinal se relaciona com prioridade, status ou CSAT; a urgência não eleva a prioridade (V = 0,023) | Dataset 1 | 158 | Usar os sinais na prioridade e no formulário |
| Supervisionado: 85,3% de acerto; 70,8% encaminhados sozinhos com 95% de acerto | Dataset 2 | 107 | Encaminhamento automático depois do histórico |
| No teste do protótipo, Administrative rights teve 76,3% de acerto entre os tickets encaminhados sozinhos, contra 94,9% no geral: um limiar único esconde a categoria fraca | Dataset 2 | 173 | Limiar por categoria |
| Zero-shot: 43,0% (Jev) e 41,9% (embeddings); o Jev discorda do rótulo com 90% de confiança ou mais em 21,2% dos tickets | Dataset 2 | 130 | Zero-shot só como sugestão |
| O rótulo segue o dono do sistema ou do processo | Dataset 2 | 133 | Tabela de encaminhamento antes da automação |
| Mensagens padronizadas: entre 3,7% (abertura idêntica) e 12,5% (grupos inteiros de mensagens padronizadas e formulários). Nem todo ticket desses grupos é padronizado | Dataset 2 | 107, 151 | Regras e fluxos, sem IA |
| Pelo texto, sem rótulo: acesso, contas e senhas cerca de 24%; equipamentos e espaço físico cerca de 18%; Oracle cerca de 17%. Percentuais aproximados (Anexo A.4) | Dataset 2 | 151 | Autoatendimento de acesso; primeira base de conhecimento no Oracle |
| Cerca de 14% dos tickets não descrevem um problema claro, e cerca de 2% estão em outra língua | Dataset 2 | 151 | Formulário com conteúdo mínimo |
| Nenhuma ligação entre os datasets | Ambos | 125, 132 | Medir no histórico da própria empresa |

**O que o cruzamento mostra.**
- **Dataset 2:** prova o método. Com histórico rotulado, o encaminhamento automático chega a 70,8% com 95% de acerto; sem histórico, o zero-shot fica em 43%.
- **Dataset 1:** mostra a operação, que não tem esse histórico. O modelo do Dataset 2 aplicado a ele põe 90,9% dos tickets em Hardware e não se relaciona com nenhuma variável (item 132).
- **Conclusão:** o modelo não se transfere, e o rótulo precisa nascer na operação da própria empresa. Daí a fase 0, que registra cada etapa e a categoria confirmada.

## 2. Princípios

- Automatizar só o que foi medido ou o que segue uma regra simples.
- Toda decisão automática tem um limiar de confiança e uma saída para uma pessoa.
- Toda automação registra dados que alimentam o histórico.
- Corrigir o processo antes de pôr IA.

## 3. O que automatizar

| # | Automação | Problema que ataca | Tipo | Fase | Revisão humana |
|---|---|---|---|---|---|
| 1 | Formulário de abertura com campos estruturados e conteúdo mínimo, incluindo o problema e opções marcáveis para "já tentei…", "é urgente" e "já contatei antes" | Tickets curtos demais (6 de 20 na leitura do item 133); cerca de 14% sem problema claro no texto (Dataset 2) e 60,9% sem problema específico (Dataset 1) | Regra | 0 | Não se aplica |
| 2 | Confirmação automática de recebimento, **que não conta como primeira resposta** | Expectativa do cliente | Regra | 0 | Não se aplica |
| 3 | Fila por prioridade, alertas de prazo e escalonamento de redes sociais. A prioridade sugerida considera as frases de urgência e de contato repetido | Indício de prioridade ignorada; urgência (8,4%) e contato repetido (5,4%) não mudam a prioridade; risco de exposição | Regra | 0 | Uma pessoa responde pelos críticos e confirma a prioridade sugerida |
| 4 | Lembretes ao cliente e encerramento após N dias sem resposta, com reabertura fácil | 34,0% aguardando o cliente | Regra; N é decisão de negócio | 0 | Não se aplica |
| 5 | Regras e fluxos para mensagens padronizadas e formulários (avisos de compra, admissão, desligamento, pedidos automáticos de acesso, alertas) | Entre 3,7% e 12,5% dos tickets | Regra | 0 | Não se aplica |
| 6 | Registro automático de cada etapa (docs/003) e pesquisa de CSAT com taxa de resposta | Falta de tempo real; CSAT sem explicação | Regra | 0 | Não se aplica |
| 7 | Resumo do ticket para o atendente | Leitura de tickets longos, com várias mensagens | IA generativa | 1 | O atendente decide com o original à mão |
| 8 | Rascunho de pedido de informação que faltou | Tickets curtos demais | IA generativa | 1 | O atendente aprova antes do envio |
| 9 | Sugestão da intenção: cobrança, reembolso, cancelamento, problema técnico ou dúvida | Rótulos do Dataset 1 que não batem com o texto | IA, zero-shot | 1 | O atendente confirma; a confirmação vira rótulo |
| 10 | Tickets parecidos para o atendente: os casos mais próximos do histórico, com a categoria e, quando houver, a solução validada | Apoio à decisão; base da resposta sugerida | IA, por semelhança | 1 | O atendente decide se usa |
| 11 | Detecção de quase duplicatas e de contato repetido: sugere juntar ao ticket já aberto | Dataset 2: fora das mensagens padronizadas, de 1,2% a 2,6% dos tickets têm um vizinho quase idêntico (Anexo A.6). Dataset 1: 5,4% relatam contato repetido | IA, por semelhança, e regra | 1 | Uma pessoa confirma a junção |
| 12 | Classificador supervisionado de encaminhamento, com limiar definido por categoria | Triagem manual; categoria fraca escondida pelo limiar único (Administrative rights, 76,3%) | IA preditiva | 2 sugere; 3 encaminha acima do limiar da categoria | Uma pessoa decide abaixo do limiar |
| 13 | Rascunho de resposta com base de conhecimento (RAG) | Resposta mais rápida e consistente | IA generativa | 3 | O atendente revisa e edita |

**Por que não há modelo de prioridade:** no Dataset 1, a prioridade não se relaciona com o estágio, o CSAT, o problema descrito nem a urgência relatada (itens 143 e 158). Não há o que aprender. A prioridade vem de regra e das frases do cliente, e uma pessoa confirma.

## 4. O que não automatizar

**Tipos de ticket que exigem julgamento humano:**

| Tipo de ticket | Por quê | Exemplo dos dados |
|---|---|---|
| Curto ou sem problema claro | Não há o que classificar | Dataset 2, linha 7246: "it si si hi please log queue". Cerca de 14% do Dataset 2 não descreve um problema claro (item 151) |
| Cabe em duas categorias | A escolha depende de contexto | Dataset 2, linha 1807: pedido de compra de cabos e hubs, rotulado Hardware; o modelo disse Purchase (item 107) |
| Segue uma regra não escrita da organização | O rótulo segue o dono do sistema | Dataset 2, linha 18162: acesso ao sistema de desenvolvimento de carreira, rotulado HR Support (item 133) |
| Fora do escopo de TI | O modelo força uma categoria | Dataset 2, linha 39429: problema elétrico na cafeteria, que o zero-shot chamou de Hardware (item 133) |
| Abaixo do limiar de confiança | O acerto cai fora dos 70,8% mais confiantes | Dataset 2: os tickets que o classificador não encaminha sozinho (item 107) |
| Segurança dos dados | Risco para o cliente | Dataset 1: 445 tickets. Ticket 5297, ainda aberto: "I'm concerned about the security of my {product_purchased} and would like to ensure that my data is safe." |
| Perda de dados | Risco alto e recuperação delicada | Dataset 1: 474 tickets. Ticket 7773: "I've encountered a data loss issue with my {product_purchased}." |
| Contato repetido | Pede escalonamento, não resposta automática | Dataset 1: 460 tickets. Ticket 2227, com prioridade baixa: "I've already contacted customer support multiple times, but the issue remains unresolved." |
| Reembolso e cancelamento | Julgamento financeiro e de retenção. É um princípio, não algo medido | Dataset 1: 1.752 pedidos de reembolso e 1.695 de cancelamento |
| Críticos e reclamações públicas | Risco de exposição; a automação só alerta | Dataset 1: 2.129 críticos e 2.121 em redes sociais |

**Decisões que não se automatizam:**

| Decisão | Por quê | Item |
|---|---|---|
| Encaminhar por zero-shot | 43% de acerto; o Jev discorda do rótulo com 90% de confiança ou mais em 21,2% dos tickets | 130 |
| Encaminhar antes de existir a tabela de regras | O rótulo segue o dono do sistema, e isso não está escrito em lugar nenhum | 133 |
| Encaminhar sozinho uma categoria abaixo da meta de acerto | O limiar geral esconde a categoria fraca: Administrative rights teve 76,3% no teste do protótipo. A categoria fica com uma pessoa até ter um limiar próprio, medido no histórico | 173 |
| Enviar resposta gerada sem revisão | Ainda não há base de soluções validadas; a resolução do Dataset 1 não tem sentido | 100, 158 |
| Contar a confirmação automática como primeira resposta | Esconderia o gargalo dos 33,3% sem resposta | 143 |

## 5. Como funcionaria na prática

```
TICKET ENTRA ── formulário: problema, conteúdo mínimo, "já tentei", "é urgente", "já contatei"
   │            confirmação automática (auto_ack_at; não conta como resposta)
   ▼
REGRAS ──────── mensagem padronizada → fluxo próprio
   │            conteúdo insuficiente → pede informação (rascunho da IA, pessoa aprova)
   │            quase duplicata ou contato repetido → sugere juntar (pessoa confirma)
   ▼
PRIORIDADE ──── regra + frases de urgência e contato repetido (pessoa confirma os críticos)
   ▼
CLASSIFICADOR ─ confiança ≥ limiar → encaminha sozinho │ abaixo → fila humana com 3 sugestões
   ▼
ATENDENTE ───── IA oferece resumo, tickets parecidos e rascunho → PESSOA decide e responde
   ▼
RESOLUÇÃO ───── PESSOA confirma a categoria (vira rótulo) e valida a solução (alimenta a base)
   ▼
FECHAMENTO → PESQUISA → HISTÓRICO → retreino do classificador
```

| Etapa (docs/003) | O que acontece | Onde a IA atua | Onde a pessoa decide | Registro |
|---|---|---|---|---|
| 1. Abertura | Formulário com conteúdo mínimo; confirmação automática | Rascunho de pedido de informação que faltou (fase 1) | Aprova o rascunho | `opened_at`, `auto_ack_at` |
| 2. Triagem e atribuição | Regras para mensagens de sistema; fila por prioridade | Sugestão de intenção (fase 1); classificador sugere (fase 2) e encaminha acima do limiar (fase 3) | Confirma as sugestões; decide abaixo do limiar | `assigned_at`, fila, categoria sugerida, confiança, quem decidiu |
| 3. Primeira resposta | Uma pessoa responde | Resumo do ticket (fase 1); rascunho com RAG (fase 3) | Escreve ou aprova a resposta | `first_response_at`, só para resposta humana |
| 4. Tentativas | Atendimento; lembretes quando aguarda o cliente | Resumo da conversa (fase 1) | Conduz o caso | Tentativas, interações e histórico de status |
| 5. Resolução | Categoria confirmada; solução registrada | Não atua | Confirma a categoria, que vira rótulo, e marca a solução como validada | `resolved_at`, código, categoria confirmada, solução validada |
| 6. Fechamento | Confirmado pelo cliente ou prazo esgotado | Não atua | Não decide | `closed_at`, motivo |
| 7. Pesquisa | Enviada a todos os fechados | Não atua | Não decide | `survey_sent_at`, `survey_answered_at`, nota |
| 8. Reabertura | Volta para as tentativas | Não atua | Conduz o caso | `reopened_at`, motivo |
| Contínuo | Soluções validadas alimentam a base; o classificador é retreinado | Busca na base (RAG) | Cuida da qualidade da base | Versão do modelo e da base |

## 6. IA generativa: fase e o que falta para funcionar

| Uso | Fase | Revisão humana | O que falta hoje |
|---|---|---|---|
| Resumo do ticket | 1 | O atendente decide com o original à mão | Interações registradas; hoje só existe a descrição |
| Rascunho de pedido de informação que faltou | 1 | O atendente aprova antes do envio | Campos mínimos definidos no formulário |
| Base de conhecimento (RAG) | Construída desde a fase 0, usada na fase 3. Começar pelo Oracle, que concentra cerca de 17% dos problemas | Curadoria por uma pessoa | Registros do docs/003: problema com categoria confirmada, tentativas com resultado e solução validada. Só entra solução confirmada pelo cliente ou sem reabertura |
| Rascunho de resposta com RAG | 3 | O atendente revisa, edita e vê a fonte usada | A base acima. As resoluções do Dataset 1 não servem: têm com a descrição 6,3% de palavras em comum, contra 6,1% ao acaso (item 100), e o sentido delas também não se relaciona com a descrição (item 158) |

Como acompanhar: taxa de aceitação dos rascunhos, quanto o atendente edita e reaberturas dos casos respondidos com rascunho.

## 7. Implantação em fases

| Fase | O que entra | Pré-requisito | Libera a próxima quando |
|---|---|---|---|
| 0 | Automações 1 a 6, só regras | Sistema de tickets com os campos do docs/003 | Etapas e categoria confirmada registradas em todos os tickets |
| 1 | Resumo, rascunho de pedido de informação, sugestão de intenção, tickets parecidos e detecção de quase duplicatas (automações 7 a 11) | Interações registradas; fornecedor de IA dentro da LGPD | Houver histórico rotulado em volume definido com a equipe |
| 2 | Classificador só sugerindo; taxa e limiar medidos por categoria no histórico da empresa | Categoria confirmada por uma pessoa | A taxa medida em cada categoria justificar o encaminhamento automático dela (referência: 70,8% no geral) |
| 3 | Encaminhamento automático acima do limiar; rascunho de resposta com RAG | Base de soluções validadas | Monitoramento contínuo |

## 8. Métricas

| Métrica | Definição |
|---|---|
| Tickets sem resposta humana | Parcela sem `first_response_at`. A confirmação automática não conta |
| Tempo até a primeira resposta humana, por prioridade | `minutes_to_first_response`, separado por prioridade |
| Prioridade coerente com o relato | Parcela dos tickets com urgência ou contato repetido relatados que receberam prioridade alta ou crítica |
| Tickets aguardando o cliente | Parcela no status de espera e tempo nele, pelo histórico de status |
| Encaminhamento automático | Parcela encaminhada sozinha e parcela reencaminhada depois, por categoria |
| Rascunhos | Taxa de aceitação e quanto o atendente edita |
| CSAT | Nota e taxa de resposta, por canal, prioridade e tempo de espera |
| Reabertura | `reopen_count` por categoria |

## 9. Ganho e riscos

**Ganho na triagem:** 11,79 × m horas a cada 1.000 tickets. Para o volume da empresa: (volume mensal ÷ 1.000) × 11,79 × m. As ressalvas estão no Anexo A.1.

| Risco | Mitigação |
|---|---|
| Confiança descalibrada | Começar só sugerindo e definir o limiar medindo no histórico da empresa |
| Desvio do modelo com o tempo | Acompanhar o acerto e retreinar |
| Encaminhamento errado | Reencaminhar com facilidade e medir a taxa |
| Confirmação automática vista como descaso | Mensagem clara sobre o prazo; ela não substitui a resposta |
| Rascunho com informação inventada | Revisão obrigatória; base só com soluções validadas; fonte visível |
| Dados pessoais (LGPD) | Enviar o mínimo de dados, anonimizar e ter contrato com o fornecedor |

## 10. Próximo passo: protótipo

O protótipo está no [docs/006](006-prototipo.md): uma página local que demonstra a etapa de triagem, com as regras, o classificador com limiar, a saída para uma pessoa, os tickets parecidos, o registro do docs/003 e a IA generativa com revisão. Em 9.568 tickets de teste que o modelo nunca viu, encaminhou sozinho 67,5% com 94,9% de acerto.

## Anexo A: detalhes

### A.1 Fórmula do ganho e ressalvas

> Horas de triagem economizadas a cada 1.000 tickets = 1.000 × 70,8% × m ÷ 60 = 11,79 × m

- **m:** minutos de triagem manual por ticket. É a única premissa. Os 3 minutos do exemplo são ilustrativos; o Diretor pode trocar pelo valor dele.
- **70,8%:** 33.852 de 47.837 tickets do Dataset 2 encaminhados sozinhos com pelo menos 95% de acerto (item 107).

Ressalvas:
1. **Os 70,8% são uma referência, não uma garantia.** Foram medidos no Dataset 2, com outro domínio e outras categorias. No Dataset 1, a taxa precisa ser medida de novo quando existir histórico rotulado.
2. **É economia bruta.** O tempo para corrigir os encaminhamentos errados não entra.
3. **O resto continua com triagem humana:** tickets de baixa confiança, curtos ou ambíguos.

### A.2 Supervisionado contra zero-shot no Dataset 2 (item 130)

| Método | Acerto | F1 macro | Acerto nos 25% mais confiantes | Cobertura com acerto ≥ 95% |
|---|---|---|---|---|
| TF-IDF supervisionado | 85,3% | 84,6% | 99,7% | 70,8% |
| Jev 1.14, zero-shot | 43,0% | 40,4% | 57,4% | 0% |
| Embeddings OpenAI large, zero-shot | 41,9% | 38,8% | 63,1% | 0% |

Sem viés de ordem no Jev: 94,5% das respostas iguais com a ordem das opções invertida. Custo total dos testes: US$ 1,5585.

### A.3 Por que o zero-shot erra: o rótulo segue o dono (item 133)

Em 13.514 tickets (28,3%), os dois modelos zero-shot concordam entre si e discordam do rótulo. Nesses casos, o supervisionado escolhe o rótulo em 79,7% das vezes, sinal de uma regra consistente.

| Rótulo → resposta dos zero-shot | Palavras típicas | Leitura |
|---|---|---|
| HR Support → Access | starter, enabling, secure, officer, oracle | Acesso de funcionário novo fica com o RH |
| HR Support → Miscellaneous | time, submit, week, error, oracle | Folha de horas no Oracle fica com o RH |
| Hardware → Access | connection, server, address, connect | Conexão fica com hardware e infraestrutura |
| Hardware → Miscellaneous | room, meeting e palavras em outra língua | Salas de reunião ficam com hardware |

### A.4 Grupos de problema pelo texto, sem rótulo (item 151)

Os 47.837 tickets do Dataset 2 foram agrupados só pelo texto, com os embeddings da OpenAI (text-embedding-3-large) e KMeans, sem usar o Topic_group. Saíram 40 grupos, reunidos em 10 famílias por leitura da IA. O grupo de cada ticket está em `results/004-it-problem-groups.csv`.

| Família | Parcela aproximada |
|---|---|
| Acesso, contas e senhas | cerca de 24% |
| Equipamentos e espaço físico | cerca de 18% |
| Oracle: horas, ausências, aprovações, relatórios, projetos e acessos | cerca de 17% |
| Acompanhamento e conversas sem problema claro | cerca de 14% |
| Erros e conexão | cerca de 8% |
| Entrada e saída de funcionários | cerca de 5% |
| Software e e-mail | cerca de 5% |
| Compras e entregas | cerca de 4% |
| Mudanças cadastrais | cerca de 3% |
| Outra língua (romeno) | cerca de 2% |

**Por que aproximados:**
- **Grupos com fronteiras difusas:** a silhueta ficou baixa para qualquer número de grupos testado, de 0,0519 a 0,0779.
- **Número de grupos não fixado:** 40 venceu, no limite da faixa testada, e a curva é quase plana de 20 a 40.
- **Encaixe forçado:** todo ticket entra em algum grupo.
- **Leitura humana:** os nomes e as famílias são leitura da IA.

**Mensagens padronizadas, entre 3,7% e 12,5%:**
- **3,7%** são tickets com as mesmas 5 primeiras palavras em pelo menos 20 tickets (item 107).
- **12,5%** é a soma dos grupos inteiros de mensagem padronizada ou formulário: avisos de compra, entregas, admissão em geral, em Bucareste e em Bogotá, desligamento, pedidos automáticos de acesso e alertas.
- **A faixa existe porque nem todo ticket desses grupos é padronizado.**

### A.5 Sinais no texto do Dataset 1 (item 158)

**Resolução: sem sentido.** Embeddings da descrição, da resolução e do assunto dos 2.769 tickets fechados.

| Teste | Resultado | Ao acaso |
|---|---|---|
| Semelhança média entre a descrição e a própria resolução | 0,0826 | 0,0826 (p = 0,498) |
| Posição da própria descrição entre as 2.769, para cada resolução | mediana 1.403 | 1.385 |
| O assunto mais parecido com a resolução é o do próprio ticket | 5,5% | 6,2% |

**Descrição: frases padrão.** 95 frases se repetem em pelo menos 20 tickets. Foram procuradas no texto inteiro, porque muitas vêm coladas a um trecho sem relação com o problema, e rotuladas em duas dimensões. Os 7 rótulos de problema e os 13 de sinal são proposta da IA.

| Problema relatado | Tickets |
|---|---|
| Sem problema específico (só a abertura genérica) | 60,9% |
| Falha de software | 5,7% |
| Rede e conexão | 5,5% |
| Acesso à conta | 5,5% |
| Hardware | 5,3% |
| Perda de dados | 5,0% |
| Bateria e carga | 4,6% |
| Mensagem de erro | 3,7% |
| Mais de um | 3,7% |

| Sinal do cliente | Tickets |
|---|---|
| Tentativa prévia (reset, cabos, manual, configurações) | 34,1% |
| Após atualização | 11,3% |
| Urgência ou impacto no trabalho | 8,4% |
| Contato repetido | 5,4% |
| Outros 9 sinais | de 2,9% a 5,9% cada |

**Cruzamentos:**
- **Problema × assunto:** V = 0,040.
- **Problema e sinais × tipo, prioridade, canal, status e CSAT:** todos os p com Bonferroni entre 0,103 e 1.
- **Urgência × prioridade:** V = 0,023.

**O que medir de novo com dados reais:** as diferenças pequenas no CSAT, como "vários aparelhos" com 2,65 contra 3,00 e "contato repetido" com 2,83 contra 3,00, não passam do acaso depois da correção.

### A.6 Quase duplicatas no Dataset 2 (item 170)

Para cada ticket, o vizinho mais parecido pelos embeddings da OpenAI (semelhança de cosseno). Os grupos de mensagem padronizada são os do Anexo A.4.

| Vizinho com semelhança | Tickets | Fora das mensagens padronizadas |
|---|---|---|
| 0,99 ou mais | 457 (1,0%) | 95 (0,2%) |
| 0,97 ou mais | 1.906 (4,0%) | 572 (1,2%) |
| 0,95 ou mais | 3.267 (6,8%) | 1.226 (2,6%) |
| 0,90 ou mais | 6.933 (14,5%) | 3.419 (7,1%) |

**Leitura de 2 exemplos por faixa, fora das mensagens padronizadas** (leitura da IA):
- **0,99 ou mais:** duplicatas de fato, como o mesmo pedido de férias duas vezes (linhas 5724 e 4988) e o mesmo aviso mensal de atualização (linhas 31069 e 13620).
- **0,97 a 0,99:** a mesma conversa aberta em mais de um ticket, como as linhas vizinhas 22044 e 22045, e tarefas recorrentes.
- **0,95 a 0,97:** casos relacionados ao mesmo assunto, como a migração de sites (linhas 29096 e 29092).
- **0,90 a 0,95:** pedidos parecidos de pessoas e casos diferentes. Não são duplicatas.

Por isso, a faixa de quase duplicatas fica entre 1,2% (0,97 ou mais) e 2,6% (0,95 ou mais) dos tickets, fora das mensagens padronizadas. **Limite:** o Dataset 2 não tem solicitante nem data, então não dá para confirmar se dois tickets parecidos são do mesmo caso. O e-mail do Dataset 1 não foi usado.

### A.7 Limites do diagnóstico

- **Os estágios são uma foto de um momento.** Sem data de abertura, não dá para saber há quanto tempo cada ticket está parado, e parte dos abertos pode ter acabado de chegar.
- **As colunas de tempo marcam etapas, não medem duração** (premissa do item 95).
- **O CSAT só existe para os tickets fechados.** Os clientes que mais esperam não avaliam.
