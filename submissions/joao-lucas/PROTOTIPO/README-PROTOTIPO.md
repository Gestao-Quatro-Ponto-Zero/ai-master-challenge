# Mesa Viva — Protótipo de Automação de Suporte
### Challenge 002 · Redesign de Suporte · João Lucas

> **Para o avaliador:** este documento é autossuficiente. Ele explica o que o protótipo faz, o que ele deliberadamente **não** faz, e como colocá-lo para rodar em uma instância n8n limpa em cerca de 20 minutos. Se você tiver 5 minutos, leia as seções 1, 3 e 7.

---

## 1. Resumo em um parágrafo

O diagnóstico mostrou que a operação de suporte não tem um problema de volume — tem um problema de **cegueira**. Não existe data de abertura de ticket, então não existe tempo de atendimento calculável. O campo de prioridade tem ~25% em cada nível, então não prioriza nada. 67% dos casos não têm resolução, tempo, nem nota. O **Mesa Viva** é um fluxo de 21 etapas que ataca a cegueira antes de atacar o volume: ele carimba o tempo, classifica com confiança declarada, recalcula a urgência a partir do texto, tenta resolver dentro de limites escritos por humanos, audita a própria resposta com um segundo modelo, e registra **cada decisão** em uma tabela de eventos. A regra de ouro é: *se não está na tabela `mv_evento`, não aconteceu.*

**Este arquivo JSON contém a Fase 2 (etapas 9 a 15): a tentativa de resolução.** É o núcleo da automação — onde a IA decide se resolve ou entrega para um humano.

---

## 2. Escopo honesto — o que está e o que não está neste arquivo

Esta seção existe porque a proposta se comprometeu a não inventar nada. Leia antes de avaliar.

### 2.1 O que ESTÁ no arquivo `Mesa_Viva___WF2_Fase_2__Resolução_.json`

| Item | Status |
|---|---|
| Etapas 9 a 15 completas | ✅ 43 nodes |
| 5 pontos de decisão (IF) | ✅ Todos implementados |
| 2 agentes de IA com modelos diferentes | ✅ Executor (gpt-5-mini) e Auditor (gpt-5) |
| Log em `mv_evento` em toda etapa | ✅ 8 inserts (etapas 9,10,11,12,13,14,15 + erro) |
| Trava dura por valor e por retenção | ✅ Code node, não depende da IA |
| Dossiê para a mesa humana | ✅ 7 campos em JSON |
| Trigger manual para teste | ✅ Roda sem precisar de webhook |
| Trigger de sub-workflow | ✅ Aceita ser chamado pelo WF1 |

### 2.2 O que NÃO está neste arquivo

| Item | Onde está | Impacto na avaliação |
|---|---|---|
| **WF1 (etapas 1–8)** — chegada, registro, classificação | Workflow separado, não incluído | O WF2 tem um trigger manual próprio que **lê direto da tabela** e simula a saída do WF1. Roda sozinho. |
| **WF3 (etapas 16–21)** — confirmação, fechamento, curador | Workflow separado, não incluído | O node `Chamar WF3` referencia o ID `OayIRNaENFANFZBk`, que **não existirá** na sua instância. Está com `onError: continueRegularOutput`, então **falha silenciosamente sem quebrar o fluxo**. Ver §9.2. |
| **WF4/WF5/WF6** — sentinela, retomada, curador | Não implementados | Declarado como escopo futuro. |

**Por que só o WF2?** Porque é a fase onde as decisões difíceis acontecem. As etapas 1–8 são registro e classificação (importantes, mas mecânicas). As etapas 16–21 são follow-up. A etapa que decide **"a IA resolve ou o humano decide?"** é esta.

### 2.3 Mocks declarados — nenhum disfarçado

| O que | Por que é mock | Como está marcado no código |
|---|---|---|
| **Política (etapa 9)** | Não existe documento de política nos datasets do desafio | Node `Get politica` monta as regras em JS. Todo registro sai com `fonte: 'FICTICIO_DEMO'` |
| **Similaridade do precedente (etapa 10)** | **Não há embedding.** O código fixa `similaridade = 0.85` sempre que acha qualquer linha da mesma categoria | `const sim = best ? 0.85 : 0;` — a arquitetura de corte está pronta e correta; o cálculo real de similaridade é substituição direta |
| **Execução da ação (etapa 11)** | Não existe sistema de billing/CRM | `status_acao: "SIMULADO"`. Nenhuma chamada HTTP externa acontece |
| **Envio da resposta (etapa 14)** | Não existe integração de e-mail/chat | `status_envio: "SIMULADO"`. Node nomeado `Send resolvido (SIMULADO)` |

> **Declaração de acurácia:** a proposta cita 84,1% de acurácia medida no Dataset 2 (TI interna, 8 categorias). Esse número **valida o método** (embedding + zero-shot), não este classificador. A acurácia na taxonomia operacional do Dataset 1 não foi medida, porque o campo `Ticket Type` é o próprio rótulo que o modelo tentaria prever — não existe validação independente. Os cortes 0,50 / 0,70 / 0,80 são política inicial transportada, sujeita a recalibração.

---

## 3. Como o fluxo funciona — a lógica em linguagem simples

Imagine um ticket chegando. O WF2 pergunta **cinco coisas, em ordem**, e para no primeiro "não":

```
1. "Esse caso é válido?"          → se não, loga erro e pula
2. "A política deixa a IA agir?"  → se não, humano (RETENCAO ou OUTROS)
3. "Existe caso igual resolvido?" → se não, humano (SEM_PRECEDENTE)
4. "A ação cabe no limite?"       → se não, humano (LIMITE)
5. "Um segundo modelo aprova?"    → se não, humano (AUDITORIA)

Passou nas cinco → IA responde sozinha.
Falhou em qualquer uma → mesa humana, com dossiê pronto.
```

**O ponto central:** o humano nunca faz triagem. Quando o caso chega nele, já vem com histórico, categoria, confiança, urgência, o que a IA tentou e exatamente em que ponto parou. Ele **decide**, não investiga.

### 3.1 Os 5 motivos de escalonamento — e só estes 5

| Código | Quando dispara | Node que decide |
|---|---|---|
| `RETENCAO` | Cancelamento — sempre exige gente | `Avalia politica` |
| `OUTROS` | Categoria sem padrão conhecido | `Avalia politica` |
| `SEM_PRECEDENTE` | Nenhum caso similar acima do corte 0,80 | `Avalia precedente` |
| `LIMITE` | Valor proposto acima do teto da política | `Trava dura` |
| `AUDITORIA` | Segundo modelo reprovou a resposta | `Registra auditoria` |

Motivos fechados e codificados existem por um motivo: permitem contar. Depois de 1.000 casos, você sabe *por que* a IA não resolveu — e isso vira roadmap.

### 3.2 Por que dois modelos diferentes

O node `Executor de acao` usa **gpt-5-mini**. O node `Auditor` usa **gpt-5**. Isso é deliberado.

Se o mesmo modelo propõe e audita, ele tende a aprovar a própria resposta — o erro dele é invisível para ele mesmo. Modelos diferentes quebram essa correlação. O prompt do auditor é explícito: *"Na dúvida, reprove. Reprovar custa barato; resposta errada com tom confiante custa caro."*

---

## 4. As três tabelas

O protótipo usa **Data Tables nativas do n8n** (não Postgres externo). Isso foi escolha consciente: um avaliador consegue rodar sem provisionar banco.

### 4.1 `mv_tickets` — entrada (leitura)

Contém os casos a processar. **É aqui que o avaliador pode plugar dados reais.**

| Coluna | Tipo | Obrigatória | Usada para |
|---|---|---|---|
| `id_ticket` | number/string | ✅ | Vira `caso_id` |
| `tipo_ticket` | string | ✅ | Categoria — decide a política (etapa 9) e filtra precedentes (etapa 10) |
| `assunto` | string | ✅ | Concatenado no texto enviado à IA |
| `descricao` | string | ✅ | Texto principal do cliente |
| `canal` | string | ⬜ | Default `email` se ausente |
| `email_cliente` | string | ⬜ | Default vazio |
| `confianca_classificacao` | number | ⬜ | Default 0 |
| `urgencia_calculada` | number | ⬜ | Default 0 — vai no dossiê |
| `irritacao_nivel` | number | ⬜ | Default 0 — vai no dossiê |
| `prioridade_declarada` | string | ⬜ | Default `normal` — guardado só para comparação |
| `resolucao_texto` | string | ⬜ | **Serve como base de precedentes na etapa 10** |

> **Nota de design:** o node `Preparar casos` tem defaults para toda coluna opcional. Um CSV com apenas `id_ticket`, `tipo_ticket`, `assunto` e `descricao` já roda.

### 4.2 `mv_evento` — rastreabilidade (escrita)

O coração do protótipo. Toda etapa escreve aqui.

| Coluna | Tipo | Conteúdo |
|---|---|---|
| `caso_id` | string | Liga o evento ao caso |
| `etapa` | number | 9 a 15 |
| `nome_etapa` | string | Ex.: "Consulta a politica" |
| `ator` | string | `IA` \| `SISTEMA` \| `HUMANO` |
| `decisao` | string | Ex.: `IA_PODE`, `SEM_PRECEDENTE`, `APROVADO` |
| `saida` | string | JSON com os detalhes técnicos da etapa |

### 4.3 `mv_auditoria` — auditoria (escrita)

Só recebe registro quando o auditor **reprova**.

| Coluna | Tipo | Conteúdo |
|---|---|---|
| `caso_id` | string | Caso reprovado |
| `resposta_proposta` | string | O que a IA queria enviar |
| `aprovado` | boolean | Sempre `false` neste caminho |
| `motivo_reprovacao` | string | Justificativa do auditor |
| `checks` | string | JSON: `{base_verificavel, dentro_politica, tom_ok}` |

---

## 5. Setup passo a passo — para o avaliador

**Tempo estimado: 20 minutos.** Testado em n8n Cloud e self-hosted.

### Passo 1 — Importar o workflow

1. No n8n: **Workflows → Import from File**
2. Selecione `Mesa_Viva___WF2_Fase_2__Resolução_.json`
3. O workflow abre com 43 nodes. Alguns nodes de Data Table aparecerão com aviso — isso é esperado, resolvemos no Passo 3.

### Passo 2 — Criar as três Data Tables

No menu lateral: **Data Tables → Create**.

**Tabela 1 — `mv_tickets`**

Crie com estas colunas (nomes exatos, minúsculo):
```
id_ticket                 (String)
tipo_ticket               (String)
assunto                   (String)
descricao                 (String)
canal                     (String)
email_cliente             (String)
confianca_classificacao   (Number)
urgencia_calculada        (Number)
irritacao_nivel           (Number)
prioridade_declarada      (String)
resolucao_texto           (String)
```

**Tabela 2 — `mv_evento`**
```
caso_id      (String)
etapa        (Number)
nome_etapa   (String)
ator         (String)
decisao      (String)
saida        (String)
```

**Tabela 3 — `mv_auditoria`**
```
caso_id             (String)
resposta_proposta   (String)
aprovado            (Boolean)
motivo_reprovacao   (String)
checks              (String)
```

### Passo 3 — Re-apontar os nodes para as suas tabelas

> ⚠️ **Este passo é obrigatório.** Os IDs de Data Table (`0GD38j7AJRl8nfMB`, `QXSalxwMmxqsM3MR`, `uQ2qHMpeVd0KKa76`) são específicos da instância onde o protótipo foi construído. Na sua instância eles não existem.

Abra cada node do tipo Data Table e selecione a tabela correta no dropdown:

| Node | Aponte para |
|---|---|
| `Buscar tickets` | `mv_tickets` |
| `Buscar precedente` | `mv_tickets` |
| `Log evento erro` | `mv_evento` |
| `Log evento 9` | `mv_evento` |
| `Log evento 10` | `mv_evento` |
| `Log evento 11` | `mv_evento` |
| `Log evento 12` | `mv_evento` |
| `Log evento 13 (dossie)` | `mv_evento` |
| `Log evento 14` | `mv_evento` |
| `Log evento 15` | `mv_evento` |
| `Insert auditoria` | `mv_auditoria` |

São 11 nodes. O mapeamento de colunas já está definido dentro de cada um — você só troca a tabela.

### Passo 4 — Configurar as credenciais de IA

Dois nodes precisam de credencial OpenAI:
- `Modelo Executor` (gpt-5-mini)
- `Modelo Auditor` (gpt-5)

Se estiver no n8n Cloud com AI Gateway ativo, eles já vêm configurados. Se não, aponte para sua credencial OpenAI.

> **Trocar de modelo é permitido.** Se sua instância não tem gpt-5, use qualquer par de modelos — **contanto que sejam diferentes entre si**. Essa separação é parte do design, não detalhe de implementação.

### Passo 5 — Desabilitar o node `Chamar WF3`

O node `Chamar WF3` referencia um workflow que não está neste pacote.

**Duas opções:**
- **(a) Deixar como está.** Ele tem `onError: continueRegularOutput` — vai falhar, registrar o erro e o fluxo continua. Nada quebra.
- **(b) Desabilitar o node** (clique direito → Deactivate). Mais limpo para leitura da execução.

Recomendo **(b)** para a primeira execução.

### Passo 6 — Carregar dados

**Opção A — usar o CSV que acompanha esta submissão**

Importe `support_tickets_completo.csv` na tabela `mv_tickets`. Os nomes de coluna já batem.

**Opção B — usar sua própria base**

Qualquer CSV serve, desde que tenha no mínimo `id_ticket`, `tipo_ticket`, `assunto`, `descricao`. As demais colunas têm default no node `Preparar casos`.

Se os nomes das suas colunas forem diferentes, edite **um único node** — `Preparar casos` — e ajuste o mapeamento:

```javascript
return $input.all().map(i => {
  const t = i.json;
  return { json: {
    caso_id: String(t.id_ticket),        // ← troque aqui
    categoria: t.tipo_ticket || 'OUTROS', // ← e aqui
    texto: (t.assunto ? t.assunto + ' - ' : '') + (t.descricao || ''),
    // ...
  }};
});
```

Todo o resto do fluxo trabalha com os nomes internos (`caso_id`, `categoria`, `texto`) — não precisa tocar em mais nada.

### Passo 7 — Executar

Clique em **Execute Workflow** no node `Iniciar teste (exemplos)`.

O node `Buscar tickets` está com `limit: 12` — processa 12 casos por execução. Aumente se quiser volume.

---

## 6. O que esperar na primeira execução

### 6.1 Comportamento correto (não é bug)

**A maioria dos casos vai cair em `SEM_PRECEDENTE` ou passar direto.** Isso depende do que tem em `resolucao_texto`.

- Se a tabela tem `resolucao_texto` preenchido → o node acha "precedente" e segue.
- Se está vazio → `SEM_PRECEDENTE` → mesa humana.

**Cancelamentos SEMPRE vão para mesa humana.** Está na política: `Cancelamentos exigem retencao humana`. Se um cancelamento for resolvido pela IA, é bug.

**Reembolsos acima de R$200 SEMPRE param na trava.** Teto escrito na política.

### 6.2 Os 4 caminhos que você deve ver

Rode com uma amostra que tenha tipos variados e confira:

| Caminho | Como forçar | Resultado esperado em `mv_evento` |
|---|---|---|
| **IA resolve** | Ticket `Technical issue` com `resolucao_texto` preenchido | Etapas 9→10→11→12→14→15, decisão final `RESOLVIDO_SEM_HUMANO` |
| **Bloqueio por política** | Ticket `Cancellation request` | Etapa 9 com decisão `ESCALAR:RETENCAO`, depois etapa 13 |
| **Sem precedente** | Ticket com `resolucao_texto` vazio | Etapa 10 com decisão `SEM_PRECEDENTE`, depois etapa 13 |
| **Trava de valor** | `Refund request` onde a IA propõe > R$200 | Etapa 11 registra, `Trava dura` marca `LIMITE`, depois etapa 13 |

---

## 7. Como auditar o resultado

Esta é a parte que mais importa na avaliação. **Todo o comportamento do sistema é reconstruível sem abrir o n8n.**

### 7.1 O teste de rastreabilidade

Abra a tabela `mv_evento` e filtre por um `caso_id`. Você deve conseguir responder, **só olhando as linhas**:

- [ ] Qual regra de política foi aplicada, e que era fictícia
- [ ] Se havia precedente e com que similaridade
- [ ] Que ação a IA propôs e com que valor
- [ ] Se a auditoria aprovou, e quais dos 3 checks passaram
- [ ] Se foi para humano, por qual dos 5 motivos
- [ ] Qual foi o desfecho final

Se algum item não é respondível pela tabela, **falta um node de log** — e isso é uma falha legítima a apontar.

### 7.2 Exemplo de trilha completa

Um caso resolvido pela IA gera esta sequência:

```
etapa  nome_etapa                      ator      decisao
-----  ------------------------------  --------  --------------------------
9      Consulta a politica             SISTEMA   IA_PODE
10     Busca de precedente             IA        PRECEDENTE_OK
11     Execucao da acao (SIMULADO)     IA        REEMBOLSO
12     Auditoria da resposta           IA        APROVADO
14     Resposta enviada (SIMULADO)     SISTEMA   RESPONDIDO_IA
15     Carimbo T2 e tempos             SISTEMA   RESOLVIDO_SEM_HUMANO
```

Um caso escalado por cancelamento gera:

```
etapa  nome_etapa                      ator      decisao
-----  ------------------------------  --------  --------------------------
9      Consulta a politica             SISTEMA   ESCALAR:RETENCAO
13     Mesa humana                     HUMANO    RETENCAO
15     Carimbo T2 e tempos             SISTEMA   ENVIADO_MESA_HUMANA
```

Note que a etapa 13 traz o **dossiê completo** no campo `saida`:
```json
{
  "categoria": "Cancellation request",
  "confianca": 0.93,
  "urgencia_calculada": 4,
  "prioridade_declarada": "Low",
  "irritacao": 4,
  "politica_aplicada": "Cancelamentos exigem retencao humana.",
  "motivo": "RETENCAO"
}
```

> Repare no contraste `urgencia_calculada: 4` vs `prioridade_declarada: "Low"`. Esse par lado a lado é a prova visual de que o campo de prioridade original era ruído — o texto do cliente indica urgência 4, mas o campo declarado dizia "Low".

---

## 8. Decisões de design que merecem escrutínio

Coloco aqui as escolhas que um avaliador rigoroso deveria questionar — e a defesa de cada uma.

**"Por que a trava de valor está em Code node e não no prompt?"**
Porque prompt não é garantia. O agente executor recebe o teto no contexto e é instruído a respeitá-lo, mas a verificação real acontece em JavaScript, depois da resposta. Se o modelo alucinar um valor de R$5.000 em um teto de R$200, o Code node barra. Instrução em prompt é pedido; Code node é lei.

**"Por que o auditor pode reprovar mesmo depois da trava passar?"**
Porque trava e auditoria checam coisas diferentes. A trava verifica **números** (valor ≤ teto). O auditor verifica **fundamento** (essa afirmação tem lastro na política ou no precedente?) e **tom**. Uma resposta pode estar dentro do limite financeiro e ainda assim prometer algo que a empresa não pode cumprir.

**"Por que a nota do cliente não influencia nada?"**
Porque testes formais no Dataset 1 mostraram que nenhuma variável explica a nota: canal p=0,467, prioridade p=0,400, tipo p=0,257, idade r=−0,004. A distribuição é uniforme. Automatizar em cima disso seria aprender com aleatoriedade. A nota é coletada e armazenada — mas **nenhum node a lê para decidir**. Essa abstenção é deliberada.

**"Por que não usar o campo `Ticket Priority` que já existe?"**
Porque ele tem ~25% em cada nível (Medium 2.192, Critical 2.129, High 2.085, Low 2.063). Um campo em que um quarto de tudo é "crítico" deixou de ser filtro e virou ruído. O protótipo guarda o campo antigo lado a lado com a urgência recalculada — não para usar, mas para provar a diferença.

**"Por que a base de precedentes não usa o campo `Resolution` original?"**
Porque no Dataset 1 ele é texto gerado aleatoriamente. Alimentar um gerador de resposta com isso produziria texto sem sentido em tom confiante — o pior erro possível em suporte. No CSV que acompanha esta submissão, `resolucao_texto` foi reconstruído com templates coerentes por categoria (declarado como inventado). Em produção, a base cresceria pela curadoria da etapa 20.

---

## 9. Limitações conhecidas

Listadas por ordem de impacto.

### 9.1 A similaridade do precedente é fixa

```javascript
const sim = best ? 0.85 : 0;
```

O node não calcula similaridade semântica — ele retorna 0,85 se encontrou qualquer linha da mesma categoria com `resolucao_texto` não vazio. **A arquitetura de corte está correta e pronta** (o limiar de 0,80, o roteamento para `SEM_PRECEDENTE`, o log da similaridade), mas o cálculo é placeholder.

**Substituição em produção:** trocar o node `Buscar precedente` por embedding + busca vetorial (pgvector no Supabase, ou o Vector Store nativo do n8n). O resto do fluxo não muda — só o valor de `sim` passa a ser real.

### 9.2 O node `Chamar WF3` falha nesta instância

Referencia o workflow `OayIRNaENFANFZBk`, que não acompanha este pacote. Configurado com `onError: continueRegularOutput`, então não interrompe o fluxo. Ver Passo 5 do setup.

### 9.3 Não há WF1 neste arquivo

As etapas 1–8 (carimbo T0, reconhecimento de cliente, detecção de continuação, classificação, cálculo de urgência, sentinela de incidente, resposta imediata) não estão aqui. O WF2 compensa lendo os campos já calculados da tabela `mv_tickets`.

**Consequência prática:** a classificação e o cálculo de urgência que aparecem no dossiê vêm da tabela, não de uma execução ao vivo do classificador.

### 9.4 Canal telefone não implementado

Exigiria transcrição de áudio. O contrato aceita `canal='phone'` apenas com texto já transcrito. Não implementei um STT que não testei.

### 9.5 O loop processa 12 casos por execução

`limit: 12` no node `Buscar tickets`. Escolha para manter a execução legível durante avaliação. Ajustável.

---

## 10. Perguntas frequentes

**Funciona com uma base de dados real diferente da que acompanha?**
Sim, com uma ressalva: os nomes de coluna precisam bater, ou você ajusta o node `Preparar casos` (um único node). O fluxo depois disso é agnóstico aos dados — as decisões operam sobre `categoria`, `texto` e `valor`, não sobre nomes de coluna do CSV original.

**Preciso de Supabase ou Postgres?**
Não. O protótipo usa Data Tables nativas do n8n. Foi escolha consciente para reduzir atrito de setup na avaliação. A migração para Postgres + pgvector é direta (o schema SQL está na especificação técnica), mas não é pré-requisito para rodar.

**Posso trocar os modelos de IA?**
Sim. A única exigência de design é que **executor e auditor sejam modelos diferentes**. Qualquer par serve.

**Quanto custa rodar?**
Duas chamadas de LLM por caso que chega até a etapa 11 (executor + auditor). Casos bloqueados nas etapas 9 ou 10 não fazem nenhuma chamada — o corte barato acontece antes do gasto. Com temperatura 0 e prompts curtos, o custo por caso resolvido é baixo.

**Por que o nome "Mesa Viva"?**
Porque a mesa do agente humano deixa de ser uma fila de tickets crus e passa a ser uma fila de **decisões preparadas**. O trabalho que sobra para a pessoa é o que exige julgamento — o resto chega mastigado ou não chega.

---

## 11. Arquivos desta submissão

| Arquivo | O que é |
|---|---|
| `Mesa_Viva___WF2_Fase_2__Resolução_.json` | O workflow n8n (43 nodes, etapas 9–15) |
| `support_tickets_completo.csv` | 8.469 tickets, 23 colunas, pronto para carregar em `mv_tickets` |
| `README-PROTOTIPO.md` | Este documento |
| `Proposta_de_automação.pdf` | Diagnóstico, o que automatizar / o que não automatizar, fluxo das 21 etapas |

---

## 12. Critério de avaliação sugerido

Se você tiver pouco tempo, sugiro avaliar por estes três testes:

1. **Teste de rastreabilidade.** Pegue um `caso_id` qualquer em `mv_evento` e tente reconstruir a história dele sem abrir o n8n. Se conseguir, o log está correto.

2. **Teste da trava.** Force um `Refund request` onde a IA proponha valor acima de R$200. Confirme que o caso vai para mesa humana com motivo `LIMITE`, e que o registro em `mv_evento` mostra a ação proposta antes do bloqueio.

3. **Teste do cancelamento.** Envie um `Cancellation request`. Ele deve parar na etapa 9, nunca chegar ao executor, e nunca gastar chamada de LLM. Se um cancelamento for resolvido automaticamente, é falha grave.

---

*Protótipo construído para o Challenge 002 — G4 AI Master. Todo dado fictício está marcado como tal no código e nesta documentação.*
