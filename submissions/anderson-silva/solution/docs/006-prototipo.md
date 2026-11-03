# Protótipo: triagem de tickets

- **Status:** versão final da submissão, 2026-11-03.
- **Origem:** escopo proposto no item 154 do [audit trail](../../process-log/002-audit-trail.md) e aprovado no item 172, com as recomendações da IA para as 5 decisões. Construção e testes nos itens 173 e 174; troca do modelo de IA generativa no item 181; exemplos reais no item 183; ajuste dos prompts no item 185; página sem os datasets no item 197.
- **Autoria:**
  - Direção e decisões da pessoa candidata: demonstrar a triagem da proposta, com limiar de confiança e saída para uma pessoa; IA generativa só com revisão humana; seguir as recomendações da IA.
  - Código, medições, testes e redação: IA, com aprovação da pessoa candidata.

## O que é

Uma página local que demonstra a etapa de triagem do [docs/004](004-proposta-automacao.md): o ticket entra, passa pelas regras, recebe a sugestão do classificador com a confiança, é encaminhado sozinho ou vai para uma pessoa, e tudo fica registrado com os campos do [docs/003](003-arquitetura-fluxo-atendimento.md).

**Ressalva:** o modelo é treinado com o Dataset 2, um suporte interno de TI. O protótipo demonstra o mecanismo; na empresa, ele seria treinado de novo com o histórico dela (fase 2 da proposta).

## Como rodar

A página não precisa dos datasets do Kaggle. Com Python 3.12:

```
pip install -r requirements.txt
streamlit run scripts/008-triage-app.py --server.address 127.0.0.1
```

Ao abrir, a página treina o modelo com os 38.269 tickets de treino guardados em `results/011` (7,7 s no teste desta máquina) e sorteia tickets dos 9.568 de teste guardados em `results/012`. O modelo é o mesmo que foi avaliado: o script 010 confere que as 9.568 previsões de teste saem idênticas às do modelo do script 007.

Para refazer tudo a partir do Dataset 2, baixado do Kaggle em `datasets/002-it-service-tickets.csv`:

```
# 1. Treinar e avaliar o modelo (cerca de 1 minuto, sem API)
uv run --no-project --python 3.12 --with pandas --with scikit-learn python -I \
  scripts/007-triage-model.py datasets/002-it-service-tickets.csv

# 2. Exportar os arquivos que a página usa (results/011 a 013) e conferir o modelo remontado
uv run --no-project --python 3.12 --with pandas --with scikit-learn python -I \
  scripts/010-triage-demo-data.py datasets/002-it-service-tickets.csv
```

O `--server.address 127.0.0.1` impede que a página apareça na rede local. Isso importa porque ela lê a chave do `.env` e pode gastar o saldo do OpenRouter.

O módulo de IA generativa só liga com `OPENROUTER_API_KEY` no `.env`. O modelo padrão é `z-ai/glm-5.3-flash`, escolhido pelo custo (US$ 0,0285 por milhão de tokens de entrada e US$ 0,0923 de saída). Ele substituiu o `anthropic/claude-opus-5.5`, que era superdimensionado para resumos e pedidos de informação. Para trocar, acrescente `OPENROUTER_MODEL=` no `.env`.

## O que a página faz

| Parte | O que mostra | Base |
|---|---|---|
| Entrada | Texto do ticket, canal e prioridade; botão para sortear um ticket do teste e conferir o rótulo real | Formulário da fase 0 |
| Regra: mensagem padronizada | Abertura igual às de 20 ou mais tickets do treino vai para um fluxo próprio | Itens 107 e 151 |
| Regra: conteúdo mínimo | Abaixo de 5 palavras, pede mais informação | Medição no treino (abaixo) |
| Classificador | Categoria, confiança e as 3 mais prováveis. Acima do limiar, encaminha sozinho; abaixo, vai para a fila humana com as sugestões | TF-IDF e regressão logística (item 107) |
| Tickets parecidos | Os 3 mais parecidos do histórico de treino, com a categoria que receberam | Semelhança de palavras, sem API |
| Decisão da pessoa | Confirmar ou corrigir a categoria; o registro passa a "decidido por pessoa" e marca se houve correção | docs/004, seção 5 |
| IA generativa (opcional) | Resumo para o atendente e pedido de informação ao solicitante; o rascunho é editável e só entra no registro depois de aprovado | docs/004, seção 6 |
| Registro | `opened_at`, `auto_ack_at`, `first_response_at` vazio (só resposta humana), regras, sugestão, confiança, decisão, motivo, quem decidiu, fila e rascunhos aprovados. Gravado em `cache/004-triage-decisions.jsonl` | docs/003 |
| Avaliação | Os números do teste, por categoria, e as horas a cada 1.000 tickets com o m escolhido na tela | Abaixo |

O limiar e o conteúdo mínimo podem ser ajustados na barra lateral.

## Como foi medido

- **Separação:** 80% do Dataset 2 para treino e 20% para teste (9.568 tickets), estratificada por categoria, semente 42.
- **Limiar:** definido só com o treino, por validação cruzada: 0,606, que deu 95% de acerto em 68,6% dos tickets de treino.
- **Conteúdo mínimo:** medido no treino. A suposição inicial de 8 palavras não se confirmou:

| Palavras | Tickets do treino | Acerto nos curtos | Acerto nos demais |
|---|---|---|---|
| Menos de 3 | 13 | 61,5% | 84,6% |
| Menos de 5 | 105 | 79,0% | 84,6% |
| Menos de 8 | 777 | 86,2% | 84,5% |
| Menos de 10 | 1.816 | 86,8% | 84,4% |

  O acerto só cai abaixo de 5 palavras. De 5 a 19 palavras, o classificador acerta tanto quanto nos textos longos, e o que é ambíguo cai abaixo do limiar de confiança e vai para uma pessoa.

## Resultado no teste (tickets que o modelo nunca viu)

| Medida | Valor |
|---|---|
| Acerto geral do classificador | 85,5% |
| Encaminhados sozinhos | 67,5% |
| Acerto nos encaminhados sozinhos | 94,9% |
| Fila humana com sugestões | 29,1% |
| Fluxo de mensagem padronizada | 3,1% |
| Pedido de mais informação | 0,3% |
| Horas de triagem economizadas a cada 1.000 tickets | 11,24 × m (33,7 horas com m = 3) |

**As horas economizadas consideram só os 67,5% encaminhados sozinhos.** Elas não incluem os 3,1% de mensagens padronizadas, que também dispensam a triagem humana porque vão direto para um fluxo próprio. O ganho real de triagem é, portanto, um pouco maior que o da fórmula.

| Categoria | Encaminhados sozinhos | Acerto nos encaminhados |
|---|---|---|
| Access | 73,9% | 95,3% |
| Hardware | 71,9% | 96,6% |
| HR Support | 69,6% | 95,7% |
| Storage | 67,4% | 93,6% |
| Miscellaneous | 61,7% | 94,7% |
| Internal Project | 57,8% | 93,5% |
| Administrative rights | 55,1% | **76,3%** |
| Purchase | 48,7% | 93,8% |

**Dois achados do teste:**
- **Administrative rights fica muito abaixo dos 95%.** Um limiar único esconde uma categoria fraca. Na empresa, o limiar deveria ser definido por categoria, ou essa categoria não seria encaminhada sozinha até o acerto dela ser medido. A recomendação entrou no docs/004.
- **Purchase tem a menor parcela encaminhada sozinha** porque parte dos tickets vai antes para o fluxo de mensagem padronizada, que é a regra fazendo o seu papel.

## Testes da página

A página foi testada sem navegador, com o testador do próprio Streamlit (`streamlit.testing`). O teste sorteou um ticket do teste, fez a triagem, confirmou a categoria, testou um ticket de 3 palavras e abriu a aba de avaliação, sem erro. Uma chamada real ao módulo de IA generativa gerou o resumo em português, que foi editado e aprovado, e o registro marcou o rascunho como editado. O teste foi feito com o Claude Opus 5.5 e repetido com o GLM 5.3 Flash, no mesmo ticket (linha 5050); os dois resumos ficaram fiéis ao texto.

Depois da mudança para rodar sem os datasets, o mesmo testador abriu a página numa cópia com só `scripts/`, `results/` e `requirements.txt`, sem `datasets/`, sem `cache/` e sem `.env`: os 6 primeiros sorteios saíram iguais aos da pasta do projeto, a aba de avaliação mostrou 85,5%, 67,5% e 94,9%, e a IA generativa ficou desligada por falta de chave.

## Exemplos reais da IA generativa

Para quem avaliar sem chave: 3 tickets sorteados do teste (semente 42), com o resumo e o pedido de informação gerados pelo `z-ai/glm-5.3-flash` em 2026-11-02, em duas versões de prompt.
- **Versão 1:** o primeiro prompt da página.
- **Versão 2:** o prompt ajustado depois da revisão, que é o que a página usa hoje.

Os textos das duas versões estão no Anexo A, com os prompts. Os arquivos são `results/008-genai-examples.json` (versão 1), `results/010-genai-examples-v2.json` (versão 2) e `results/009-genai-prompts-v1.json`. Para gerar de novo: `scripts/009-genai-examples.py`.

**O que mudou no prompt:**
- **Pedido de informação:** agora é escrito em inglês, o que ancora a língua da resposta. Ele manda conferir antes o que o ticket já informa, perguntar só o que falta e resumir o que foi entendido.
- **Resumo:** proíbe acrescentar datas, nomes, números, sistemas ou fatos e completar datas parciais. Também manda dizer que uma frase está ambígua quando o texto sem pontuação, e sem palavras como "not", puder ser lido de dois jeitos.

**O que a revisão encontrou, antes e depois do ajuste** (leitura da IA; a aprovação é de uma pessoa):

| Problema | Versão 1 | Versão 2 |
|---|---|---|
| Pedido de informação na língua errada | 2 de 3 em português (linhas 5050 e 47824) | Os 3 em inglês |
| Data inventada | "(11/07)" no resumo da linha 47824 | Nenhuma; o resumo escreve só "sexta-feira" |
| Sentido invertido pela falta do "not" | O resumo da linha 47824 diz que o site "está acessível novamente" | Os 3 resumos apontam o trecho ambíguo em vez de escolher uma leitura |
| Leitura duvidosa | "Já enviou versões corrigidas" (linha 5050) | "Solicita versões corrigidas" |
| Perguntas sobre o que o ticket já informa | Os 3 pedidos perguntam sistema e erro | Nenhuma; as perguntas ficaram específicas de cada caso |

**O que ainda resta na versão 2:**
- **O pedido da linha 47824 assume que o site funciona,** embora o resumo tenha marcado esse trecho como ambíguo.
- **O pedido da linha 40919 põe entre aspas uma mensagem de erro levemente alterada** ("scheduled hours", no texto "schedules hours") e um caminho com uma palavra a mais ("Manage Time Cards", no texto "manage cards").
- **O resumo da linha 47824 saiu em lista, e não em frases,** e os resumos ficaram mais longos.

A linha 47824 também mostra um erro do encaminhamento automático: foi para Hardware com confiança 0,65, e o rótulo é HR Support. É a regra do dono do sistema (item 133): o Oracle Fusion fica com o RH.

O ajuste do prompt resolveu os problemas principais, e os resíduos são o motivo de a proposta exigir revisão humana antes de qualquer envio.

**Aprovação (itens 186 e 188):** a pessoa candidata aprovou a versão 2 dos 6 textos.
- **Dois sem alteração:** o resumo e o pedido da linha 5050.
- **Quatro com correções apontadas pela IA e aprovadas por ela:**
  - o pedido da linha 47824 deixou de assumir que o site funciona e passou a perguntar se ele funciona;
  - o pedido e o resumo da linha 40919 passaram a reproduzir entre aspas exatamente o texto do ticket;
  - o resumo da linha 47824 perdeu as aspas nas traduções para o português.

**Regra da revisão, definida pela pessoa candidata:** aspas só para texto literal do ticket; tradução fica sem aspas. Uma conferência por script mostrou que todas as aspas dos 6 textos aprovados aparecem, literalmente, no ticket. Os textos aprovados estão no Anexo A e em `results/010-genai-examples-v2.json`.

## Limites

- **O modelo é do Dataset 2:** não se aplica ao Dataset 1 sem histórico rotulado da própria empresa.
- **Tickets parecidos só mostram a categoria:** o Dataset 2 não tem soluções. Com a base de soluções validadas (fase 3), passariam a mostrar a solução.
- **Sem integração com um sistema de tickets real,** sem login e sem banco de dados.
- **Os 94,9% de acerto ficam um pouco abaixo dos 95% buscados no treino,** o que é esperado ao passar para tickets novos.

## Anexo A: rascunhos gerados e textos aprovados

Textos copiados dos arquivos de resultado sem edição manual. Os 6 textos aprovados são da versão 2 do prompt: 2 sem alteração e 4 com correções apontadas pela IA e aprovadas pela pessoa candidata (itens 186 e 188). Regra das aspas: só para texto literal do ticket; tradução fica sem aspas.

### A.0 Prompts

**Resumo para o atendente, versão 1:**

```text
Você ajuda um atendente de suporte de TI. Resuma o ticket em português, em até 3 frases: o que a pessoa pede, o que ela já tentou e o que ainda falta saber. Use só o que está no texto; não invente informação.
```

**Resumo para o atendente, versão 2:**

```text
Você ajuda um atendente de suporte de TI. Resuma o ticket em português, em até 3 frases: o que a pessoa pede, o que ela já tentou e o que ainda falta saber. Regras: use só o que está escrito no texto; não acrescente datas, nomes, números, sistemas ou fatos que não apareçam nele; não complete datas parciais (se o texto diz só 'sexta-feira', escreva só 'sexta-feira'). O texto pode vir sem pontuação e sem palavras como 'not'; quando uma frase puder ser lida de dois jeitos, diga que ela está ambígua em vez de escolher uma leitura.
```

**Pedido de informação ao solicitante, versão 1:**

```text
Você ajuda um atendente de suporte de TI. Escreva, na língua do ticket, uma mensagem curta e educada ao solicitante pedindo só as informações que faltam para resolver o caso: o sistema ou equipamento, o que aconteceu, a mensagem de erro e desde quando. Não prometa prazo nem solução.
```

**Pedido de informação ao solicitante, versão 2:**

```text
You help an IT support agent. Write a short, polite message to the requester in the same language as the ticket text (if the ticket is in English, write in English). Before writing, check which of these the ticket already states: the system or equipment, what happened, the exact error message, and since when. Ask only for the items that are missing; never ask for something the ticket already states, and briefly restate what you understood. If nothing essential is missing, say what you understood and that the team will follow up. Do not promise deadlines or solutions, and do not invent names, dates or facts.
```

### A.1 Linha 40919 (rótulo real: HR Support)

- **Decisão da triagem:** Encaminhado automaticamente, sugestão HR Support com confiança 1,00.
- **Trecho do ticket:** "public holiday leave cannot submit time card sent monday public holiday leave can submit week public holiday leave fig thursday steps go manage cards add row below complete info code location hours click save close error received hours entered below your schedules hours regards…"

**Resumo para o atendente, gerado (versão 1):**

```text
O usuário relata erro ao tentar registrar um cartão de ponto na segunda-feira, que é feriado público: ao adicionar uma linha com código, local e horas e clicar em salvar, aparece uma mensagem de erro sobre "horas inseridas abaixo das horas do seu cronograma". Ele consegue registrar normalmente o restante da semana, apenas a entrada do feriado falha. Falta saber o motivo exato do erro (se o sistema bloqueia horas em feriado ou exige valor específico) e como o usuário deseja lançar as horas do feriado.
```

**Resumo para o atendente, gerado (versão 2):**

```text
Resumo do ticket: A pessoa relata que não consegue enviar o cartão de ponto referente à folga em feriado, recebendo um erro de que as horas inseridas ficam abaixo das horas do horário dela. Ela já tentou ir em "Manage Cards", adicionar uma linha abaixo, preencher código, local e horas, e clicar em "Save Close". Não está claro se a mensagem "cannot submit" refere-se ao envio na segunda-feira ou à folga em si, e o ticket está ambíguo sobre se a frase "can submit week" significa que a folga de feriado na semana pode ser enviada ou não.
```

**Resumo para o atendente, aprovado:** aprovado pela pessoa candidata (versão 2 com correção). Correção apontada por: IA (item 187), ao aplicar a regra das aspas aprovada para a linha 40919. Aprovação: pessoa candidata (item 188). As aspas passam a reproduzir exatamente o texto do ticket.

```text
Resumo do ticket: A pessoa relata que não consegue enviar o cartão de ponto referente à folga em feriado, recebendo um erro de que as horas inseridas ficam abaixo das horas do horário dela. Ela já tentou ir em "manage cards", adicionar uma linha abaixo, preencher código, local e horas, e clicar em "save close". Não está claro se a mensagem "cannot submit" refere-se ao envio na segunda-feira ou à folga em si, e o ticket está ambíguo sobre se a frase "can submit week" significa que a folga de feriado na semana pode ser enviada ou não.
```

**Pedido de informação ao solicitante, gerado (versão 1):**

```text
Hello,

Thank you for reaching out, and sorry to hear about the trouble submitting your time card for the public holiday.

To help investigate, could you please provide the following details:

1. Which system or application are you using to submit the time card (e.g., portal name or website)?
2. What exactly happens when you click "Save & Close"?
3. The exact error message you receive (a screenshot would be very helpful).
4. Since when have you been experiencing this issue?

With this information we can look into it further.

Best regards,
IT Support
```

**Pedido de informação ao solicitante, gerado (versão 2):**

```text
Hello,

Thank you for your message. If I understand correctly: you are trying to submit your time card including leave for a public holiday (via Manage Time Cards > Add Row Below, entering code, location, and hours), and when you click "Save & Close" you receive the error "Hours entered below your scheduled hours". You also mentioned this was sent on Monday.

To help us investigate further, could you please provide:
1. Since when has this issue been occurring (did it only start this week)?
2. Which specific leave code and hours you are entering when the error appears?

Thank you, and our team will follow up once we have this information.

Best regards,
IT Support
```

**Pedido de informação ao solicitante, aprovado:** aprovado pela pessoa candidata (versão 2 com correção). Correção apontada por: IA (item 185). Aprovação: pessoa candidata (item 186). As aspas passam a reproduzir exatamente o texto do ticket.

```text
Hello,

Thank you for your message. If I understand correctly: you are trying to submit your time card including leave for a public holiday (via "manage cards" and "add row below", entering code, location, and hours), and when you click "save close" you receive the error "hours entered below your schedules hours". You also mentioned this was sent on Monday.

To help us investigate further, could you please provide:
1. Since when has this issue been occurring (did it only start this week)?
2. Which specific leave code and hours you are entering when the error appears?

Thank you, and our team will follow up once we have this information.

Best regards,
IT Support
```

### A.2 Linha 5050 (rótulo real: Internal Project)

- **Decisão da triagem:** Fila humana com sugestões, sugestão Internal Project com confiança 0,54.
- **Trecho do ticket:** "new project oracle only oracle replacement replacement hi please ask create additional attached form part tech refresh efforts related replacement version out please booked report efforts related item tech refresh costs labour costs total spent remaining budget item total markup total spent date tot…"

**Resumo para o atendente, gerado (versão 1):**

```text
**Resumo do ticket:**
O usuário pede ajuda para criar/preencher um formulário anexo, relacionado a esforços de substituição de sistema Oracle ("tech refresh"), incluindo dados como custos de mão de obra, orçamento restante, margem e gastos totais. Ele já enviou versões corrigidas dos arquivos e aguarda confirmação de detalhes da solicitante sobre como preencher o formulário. Falta confirmar as informações necessárias com a solicitante antes de prosseguir e atribuir o atendimento apropriado.
```

**Resumo para o atendente, gerado (versão 2):**

```text
**Resumo do ticket:**

A pessoa pede ajuda para criar um formulário anexo, relacionado a esforços de tech refresh / substituição (replacement), incluindo custos de mão de obra, total gasto, orçamento restante e markup, e também solicita versões corrigidas dos arquivos com margem, além de detalhes sobre como preencher o formulário de setup. Ela menciona que vai preencher os detalhes e, após confirmação, pede que se processe a atribuição apropriada conforme o usual. O texto contém trechos ambíguos (por exemplo, as repetidas frases sobre "program upcoming leave thursday" e datas como "thursday pm" sem contexto claro), então não é possível determinar com precisão o que ainda falta saber — aparentemente restam detalhes sobre o preenchimento do formulário e a confirmação final, conforme mencionado no texto.
```

**Resumo para o atendente, aprovado:** aprovado pela pessoa candidata (versão 2 sem alteração)

```text
**Resumo do ticket:**

A pessoa pede ajuda para criar um formulário anexo, relacionado a esforços de tech refresh / substituição (replacement), incluindo custos de mão de obra, total gasto, orçamento restante e markup, e também solicita versões corrigidas dos arquivos com margem, além de detalhes sobre como preencher o formulário de setup. Ela menciona que vai preencher os detalhes e, após confirmação, pede que se processe a atribuição apropriada conforme o usual. O texto contém trechos ambíguos (por exemplo, as repetidas frases sobre "program upcoming leave thursday" e datas como "thursday pm" sem contexto claro), então não é possível determinar com precisão o que ainda falta saber — aparentemente restam detalhes sobre o preenchimento do formulário e a confirmação final, conforme mencionado no texto.
```

**Pedido de informação ao solicitante, gerado (versão 1):**

```text
Olá,

Obrigado pelo seu contato. Para podermos ajudar com a criação do formulário anexado, precisamos de algumas informações adicionais:

1. Em qual sistema ou equipamento o formulário deve ser criado?
2. O que exatamente acontece ao tentar criar/preencher o formulário?
3. Aparece alguma mensagem de erro? Se sim, qual?
4. Desde quando esse problema ocorre?

Com esses dados poderemos analisar o caso e encaminhar para o responsável adequado.

Atenciosamente,
Suporte de TI
```

**Pedido de informação ao solicitante, gerado (versão 2):**

```text
Hello,

Thank you for your message. If I understand correctly, you are asking us to help create an additional attached form as part of the tech refresh efforts related to the Oracle replacement, and you would like details on how to fill in the setup form so the request can be assigned appropriately.

To help us process this, could you please clarify a few points:

- The attached form or template is not clearly identifiable on our side — could you confirm which specific form/file you are referring to, or re-send it?
- Which exact fields or sections you need guidance on when filling in the setup form?
- Which project or cost item this should be booked against (e.g., the specific Oracle replacement workstream), if applicable?

Once you confirm these details, we will proceed as usual and assign the request to the appropriate team.

Best regards,
IT Support
```

**Pedido de informação ao solicitante, aprovado:** aprovado pela pessoa candidata (versão 2 sem alteração)

```text
Hello,

Thank you for your message. If I understand correctly, you are asking us to help create an additional attached form as part of the tech refresh efforts related to the Oracle replacement, and you would like details on how to fill in the setup form so the request can be assigned appropriately.

To help us process this, could you please clarify a few points:

- The attached form or template is not clearly identifiable on our side — could you confirm which specific form/file you are referring to, or re-send it?
- Which exact fields or sections you need guidance on when filling in the setup form?
- Which project or cost item this should be booked against (e.g., the specific Oracle replacement workstream), if applicable?

Once you confirm these details, we will proceed as usual and assign the request to the appropriate team.

Best regards,
IT Support
```

### A.3 Linha 47824 (rótulo real: HR Support)

- **Decisão da triagem:** Encaminhado automaticamente, sugestão Hardware com confiança 0,65.
- **Trecho do ticket:** "oracle fusion is not working message unplanned outage sent friday july fusion working message unplanned outage please attached image fusion site working cannot fill manager en…"

**Resumo para o atendente, gerado (versão 1):**

```text
**Resumo do ticket:** A usuária relata que o Oracle Fusion não está funcionando, exibindo a mensagem "unplanned outage" desde sexta-feira (11/07), e anexou uma imagem como evidência. Ela informa que agora o site do Fusion está acessível novamente, mas não consegue preencher/cadastrar o gestor. Falta saber se o problema de preencher o gestor é um erro específico ou relacionado à instabilidade anterior, e se a mensagem de outage ainda aparece em algum momento.
```

**Resumo para o atendente, gerado (versão 2):**

```text
Resumo do ticket:

1. O usuário relata que o Oracle Fusion apresentaria uma mensagem de "unplanned outage", e menciona uma imagem anexada, mas o texto é ambíguo: não está claro se o sistema "não está funcionando" ou "está funcionando", pois as duas leituras aparecem no texto sem separação clara.
2. Também é ambíguo se o usuário "não consegue preencher o gestor" (cannot fill manager) ou se consegue, já que o texto pode ser lido de dois jeitos.
3. Falta esclarecer: qual é o estado atual do sistema, em que momento (o texto menciona apenas "sexta-feira") a mensagem apareceu, e o que exatamente a imagem anexada mostra.
```

**Resumo para o atendente, aprovado:** aprovado pela pessoa candidata (versão 2 com correção). Correção apontada por: IA (item 187), como observação. Aprovação: pessoa candidata (item 188). Aspas só para texto literal do ticket; as traduções ficaram sem aspas.

```text
Resumo do ticket:

1. O usuário relata que o Oracle Fusion apresentaria uma mensagem de "unplanned outage", e menciona uma imagem anexada, mas o texto é ambíguo: não está claro se o sistema não está funcionando ou está funcionando, pois as duas leituras aparecem no texto sem separação clara.
2. Também é ambíguo se o usuário não consegue preencher o gestor (cannot fill manager) ou se consegue, já que o texto pode ser lido de dois jeitos.
3. Falta esclarecer: qual é o estado atual do sistema, em que momento (o texto menciona apenas sexta-feira) a mensagem apareceu, e o que exatamente a imagem anexada mostra.
```

**Pedido de informação ao solicitante, gerado (versão 1):**

```text
Olá,

Obrigado pelo contato. Para que possamos analisar o caso, preciso de algumas informações adicionais:

1. Qual sistema ou equipamento exatamente está apresentando o problema?
2. O que aconteceu? Descreva o comportamento observado.
3. Qual é a mensagem de erro exibida? (a imagem em anexo foi mencionada, mas confirme se foi enviada)
4. Desde quando o problema ocorre?

Fico no aguardo para prosseguir com a análise.

Atenciosamente,
Suporte de TI
```

**Pedido de informação ao solicitante, gerado (versão 2):**

```text
Hello,

Thank you for your message. I understand that you are experiencing an issue with Oracle Fusion, which shows an "unplanned outage" message, and that you have attached an image. I also noted that the site appears to work, but you cannot fill in the manager field.

To help us investigate, could you please provide the following details:

1. Since exactly when have you been experiencing this issue (date and time)?
2. Does the outage message appear on all Oracle Fusion pages, or only where you try to fill in the manager field?
3. Could you confirm whether the attached image shows the "unplanned outage" message, so we can make sure we received it correctly?

Thank you in advance, and we will follow up as soon as we have more information.

Best regards,
IT Support
```

**Pedido de informação ao solicitante, aprovado:** aprovado pela pessoa candidata (versão 2 com correção). Correção apontada por: IA (item 185). Aprovação: pessoa candidata (item 186). O pedido deixa de assumir que o site funciona e pergunta se ele funciona.

```text
Hello,

Thank you for your message. I understand that you are experiencing an issue with Oracle Fusion, which shows an "unplanned outage" message, and that you have attached an image. From your message, it is not clear to us whether the site is working at the moment, or whether you are able to fill in the manager field.

To help us investigate, could you please provide the following details:

1. Is the Oracle Fusion site working for you right now? If so, are you able to fill in the manager field?
2. Since exactly when have you been experiencing this issue (date and time)?
3. Could you confirm whether the attached image shows the "unplanned outage" message, so we can make sure we received it correctly?

Thank you in advance, and we will follow up as soon as we have more information.

Best regards,
IT Support
```
