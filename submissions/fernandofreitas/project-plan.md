# Plano de execucao - Challenge 002

## Objetivo da entrega

Construir uma solucao end-to-end para uma operacao de suporte assistida por IA.

A entrega deve responder ao Diretor de Operacoes:

1. Onde estamos perdendo tempo?
2. O que pode ser automatizado com IA?
3. O que nao deve ser automatizado?
4. Como isso funcionaria na pratica?
5. Qual impacto operacional esperado?

Para isso, a solucao sera dividida em tres experiencias conectadas:

- **Assistente do cliente:** o usuario descreve sua duvida em linguagem natural; a IA tenta resolver rapidamente com base em FAQ, tickets similares e conhecimento existente.
- **Abertura inteligente de ticket:** se a IA nao tiver informacao suficiente ou o caso exigir humano, ela coleta contexto, classifica e abre o ticket ja enriquecido.
- **Painel admin/operacoes:** visualizacao dos gargalos, KPIs, fila de tickets, oportunidades de automacao e indicadores para decisao executiva.
- **Loop de aprendizado:** quando o humano resolve um ticket, essa resolucao entra na base de conhecimento para melhorar respostas futuras.

---

## Principio de produto

O objetivo nao e criar apenas um classificador de tickets.

O objetivo e demonstrar como uma operacao de suporte poderia funcionar com IA no fluxo real:

```text
Cliente tem uma duvida/problema
|
|-- Descreve em um input livre
|-- IA tenta responder com base em conhecimento interno e casos similares
|-- Se faltar informacao ou risco for alto, IA pede abertura de ticket
|-- Ticket ja nasce classificado, priorizado e com contexto coletado
|-- Humano resolve quando necessario
|-- Resolucao entra na base da IA
|-- Admin acompanha gargalos, backlog, satisfacao e oportunidades de automacao
```

---

## O que faz sentido da ideia

### 1. Assistente do cliente antes do ticket

Faz bastante sentido porque mostra uma automacao antes do ticket virar custo operacional.

A pergunta central deixa de ser:

```text
Como abrir ticket mais rapido?
```

e passa a ser:

```text
Como evitar que um ticket simples precise ser aberto?
```

Funcionalidades propostas:

- Input principal: "Descreva sua duvida ou problema".
- Base interna com problemas recorrentes, sem expor FAQ como tela principal.
- Assistente que tenta responder com base em conhecimento existente.
- Busca de tickets/assuntos semelhantes.
- Indicador de confianca da resposta.
- Botao "isso resolveu" ou "preciso abrir um ticket".
- Se nao resolver, formulario de ticket ja preenchido com o contexto da conversa.

Ao abrir ticket, o sistema classifica automaticamente:

  - categoria provavel;
  - prioridade sugerida;
  - nivel de confianca;
  - rota recomendada;
  - se pode ser automatizado ou precisa de humano.

### 2. Abertura inteligente de ticket

Faz sentido porque reduz retrabalho do agente.

Em vez de o cliente abrir um ticket cru, a IA coleta:

- resumo do problema;
- produto envolvido;
- assunto provavel;
- urgencia percebida;
- tentativas ja realizadas;
- dados faltantes;
- sugestao de rota;
- motivo de escalacao para humano.

Isso melhora a vida de quem abre o ticket e tambem a vida de quem atende.

### 3. Loop de aprendizado com resolucao humana

Essa e a parte menos comum e mais forte da ideia.

Quando o humano resolve o ticket, o sistema registra:

- problema original;
- categoria final;
- rota usada;
- resolucao aplicada;
- se a resposta da IA ajudou;
- satisfacao, quando existir.

Essa resolucao vira um novo item da base de conhecimento.

No prototipo, isso pode ser demonstrado sem treinamento real continuo:

- salvando resolucoes em memoria ou arquivo local;
- incluindo a resolucao em uma "base de conhecimento";
- permitindo que tickets futuros recuperem essa resolucao como caso similar.

Em uma versao de producao, isso viraria:

- base vetorial/RAG;
- revisao humana das novas respostas;
- avaliacao de qualidade;
- retreinamento periodico do classificador;
- monitoramento de respostas ruins.

### 4. Assistente de IA

Faz sentido como demonstracao, mas com limite claro.

O assistente deve:

- responder duvidas frequentes;
- pedir informacoes adicionais;
- sugerir passos basicos;
- indicar quando o caso precisa de humano;
- evitar prometer resolucao para casos sensiveis.

Casos que devem escalar:

- prioridade critica;
- pedido de reembolso;
- cancelamento;
- baixa confianca da IA;
- cliente insatisfeito;
- problema que envolve excecao de politica.

### 5. Painel admin

Faz muito sentido porque conversa diretamente com o desafio.

KPIs minimos:

- total de tickets;
- tickets abertos, pendentes e fechados;
- tempo mediano de resolucao;
- p90 de resolucao;
- CSAT medio;
- backlog;
- tickets por canal;
- tickets por tipo;
- tickets por prioridade;
- principais gargalos por combinacao canal + tipo + prioridade;
- horas acima da mediana;
- candidatos a automacao;
- estimativa de horas economizaveis.

KPIs adicionais que podem impressionar:

- taxa de tickets que poderiam passar por auto-triagem;
- percentual de tickets que devem ir para humano;
- top assuntos recorrentes para FAQ;
- risco operacional por fila;
- ranking de oportunidades de automacao por impacto x esforco;
- simulacao de ROI com custo/hora ajustavel.
- taxa de deflexao: quantas duvidas foram resolvidas antes de virar ticket;
- taxa de escalacao: quantos atendimentos precisaram de humano;
- novos artigos sugeridos para a base de conhecimento;
- categorias onde a IA mais pede ajuda humana;
- taxa de reaproveitamento de resolucoes humanas.

---

## O que eu evitaria

### 1. Prometer automacao total

Isso seria uma red flag. A propria vaga valoriza saber o que nao automatizar.

### 2. Criar um chatbot generico demais

Um chatbot que responde qualquer coisa parece demo superficial. Melhor um assistente focado em suporte, FAQ, triagem e coleta de contexto.

### 3. Chamar isso de "treinamento automatico" sem controle

Em producao, nao e seguro deixar qualquer resolucao humana treinar a IA automaticamente sem revisao. O melhor termo para o prototipo e:

```text
base de conhecimento retroalimentada por resolucoes humanas
```

Isso mostra aprendizado operacional sem prometer fine-tuning continuo irresponsavel.

### 4. Depender de API paga para a entrega funcionar

Se usarmos LLM externo, pode falhar por chave/API. Para o desafio, o nucleo deve funcionar localmente com modelo simples, regras e dados reais.

Podemos simular a resposta da IA usando:

- FAQ baseado nos assuntos recorrentes;
- tickets similares;
- templates de resposta;
- classificador treinado no Dataset 2.

### 5. Fazer uma interface grande demais

Melhor entregar um prototipo enxuto e bem amarrado do que tentar construir um Zendesk completo.

---

## Etapas do trabalho

## Etapa 1 - Auditoria dos dados

Objetivo: entender a confiabilidade dos datasets antes de concluir qualquer coisa.

Tarefas:

- Auditar Dataset 1:
  - quantidade de linhas e colunas;
  - nulos;
  - duplicados;
  - consistencia de status;
  - validade de datas;
  - problemas em timestamps;
  - distribuicao de canal, tipo, prioridade e satisfacao;
  - qualidade dos textos.
- Auditar Dataset 2:
  - quantidade de registros;
  - distribuicao das categorias;
  - textos vazios ou repetidos;
  - balanceamento das classes;
  - utilidade para treino de classificador.

Saida esperada:

- Secao de confiabilidade dos dados.
- Decisoes metodologicas documentadas.
- Lista do que podemos afirmar com seguranca e do que deve entrar como limitacao.

Status: concluido.

---

## Etapa 2 - Perguntas de negocio e hipoteses

Objetivo: transformar o briefing em perguntas testaveis.

Perguntas principais:

- Onde o fluxo trava?
- Quais canais tem pior desempenho?
- Quais tipos de ticket demoram mais?
- Quais combinacoes canal + tipo + prioridade sao mais criticas?
- O que parece impactar satisfacao?
- Onde existe desperdicio recuperavel?
- Quais assuntos sao bons candidatos para FAQ?
- Quais problemas podem ser resolvidos antes de virar ticket?
- Quais casos devem ser humanos?
- Quais resolucoes humanas deveriam virar conhecimento reutilizavel?

Saida esperada:

- Lista de hipoteses.
- Mapa de analises necessarias.

Status: concluido.

---

## Etapa 3 - Diagnostico operacional

Objetivo: responder ao Diretor com numeros concretos.

Analises:

- backlog por status;
- tempo de resolucao por canal;
- tempo de resolucao por tipo;
- tempo de resolucao por prioridade;
- combinacoes mais criticas;
- CSAT por canal/tipo/prioridade;
- assuntos mais frequentes;
- estimativa de desperdicio em horas;
- oportunidades de automacao.

Saida esperada:

- Findings executivos.
- Tabelas e graficos para o painel admin.
- Recomendacoes priorizadas.

Status: concluido.

---

## Etapa 4 - Estrategia de automacao

Objetivo: definir onde IA entra e onde humano continua indispensavel.

Automatizar:

- FAQ dinamico para problemas recorrentes;
- resposta inicial para duvidas simples;
- classificacao inicial do ticket;
- roteamento;
- sugestao de prioridade;
- resposta sugerida para baixa complexidade;
- recuperacao de tickets similares;
- coleta de contexto antes de escalar para humano.
- sugestao de novo artigo de conhecimento apos resolucao humana.

Nao automatizar:

- casos criticos;
- refund sensivel;
- cancelamento;
- baixa confianca;
- cliente muito insatisfeito;
- casos com excecao de politica;
- qualquer decisao com impacto financeiro sem revisao.

Saida esperada:

- Blueprint do fluxo operacional.
- Matriz automatizar vs revisar vs escalar.

Status: concluido.

---

## Etapa 5 - Modelo de classificacao

Objetivo: provar tecnicamente que a triagem automatizada e viavel.

Tarefas:

- Treinar classificador com Dataset 2.
- Medir accuracy, macro F1 e desempenho por categoria.
- Aplicar classificador nos tickets do Dataset 1.
- Definir thresholds de confianca:
  - alta confianca: auto-roteamento;
  - media confianca: revisao rapida;
  - baixa confianca: triagem humana.

Saida esperada:

- Modelo funcional no prototipo.
- Metricas de validacao.
- Justificativa para limites de automacao.

Status: pendente.

---

## Etapa 6 - Prototipo funcional

Objetivo: mostrar o sistema funcionando.

Formato escolhido: Flask com HTML/CSS customizado.

Telas:

### 1. Assistente do cliente

- Input livre para duvida/problema.
- Resposta rapida baseada em FAQ/casos similares.
- Perguntas de esclarecimento quando faltar contexto.
- Indicador de confianca.
- Botao "resolveu" e botao "abrir ticket".

### 2. Abertura inteligente de ticket

- Ticket pre-preenchido com resumo da conversa.
- Classificacao automatica:
  - categoria;
  - prioridade sugerida;
  - confianca;
  - proximo passo.
- Decisao operacional:
  - resolver via IA;
  - revisar;
  - escalar para humano.

### 3. Admin / Operacoes

- dashboard executivo;
- KPIs operacionais;
- gargalos;
- backlog;
- ranking de automacoes;
- fila de tickets priorizada.
- base de conhecimento alimentada por resolucoes humanas.
- metricas de deflexao e aprendizado.

### 4. Simulador de aprendizado

- humano registra uma resolucao;
- sistema adiciona essa resolucao na base de conhecimento;
- uma duvida futura consegue recuperar essa resolucao como caso similar.

Saida esperada:

- Aplicacao local rodando.
- Instrucoes de setup.
- Screenshots ou video curto.

Status: concluido.

---

## Etapa 7 - ROI e impacto

Objetivo: traduzir a solucao para linguagem executiva.

Estimativas:

- horas acima da mediana;
- percentual de tickets roteaveis;
- taxa de deflexao estimada;
- economia se a IA reduzir X minutos por ticket;
- economia se parte das duvidas for resolvida antes de virar ticket;
- custo/hora do agente como parametro ajustavel;
- economia mensal/anual;
- impacto esperado em backlog e primeira resposta.

Saida esperada:

- Simulador simples de ROI.
- Recomendacao de piloto.

Status: concluido no prototipo, com simulacao parametrica documentada.

---

## Etapa 8 - Documentacao final

Objetivo: transformar a execucao em uma submissao clara.

Arquivos finais:

- `README.md`: narrativa executiva da entrega.
- `solution/README.md`: como rodar.
- `solution/docs/operational-diagnosis.md`: diagnostico.
- `solution/docs/automation-blueprint.md`: fluxo de automacao.
- `process-log/ai-workflow.md`: evidencia do uso de IA.
- `project-plan.md`: plano e raciocinio de execucao.

Saida esperada:

- Entrega compreensivel para avaliador tecnico e executivo.
- Processo documentado.

Status: concluido.

---

## Etapa 9 - Revisao e submissao

Objetivo: preparar para GitHub/PR.

Checklist:

- validar se o app roda;
- revisar README com nome, LinkedIn e data;
- conferir se nada fora de `submissions/fernandofreitas/` foi alterado;
- adicionar arquivos com `git add -f`, porque `submissions/` esta no `.gitignore`;
- criar commit;
- fazer push;
- abrir PR.

Status: pendente para o momento de PR.

---

## Decisoes em aberto

Estas decisoes devem ser tomadas conversando antes de implementar:

1. Preencher LinkedIn e data de submissao.
2. Definir senhas finais de deploy.
3. Configurar ou nao `OPENAI_API_KEY` na demo publica.
4. Incluir screenshots/video como evidencia final.

---

## Minha recomendacao inicial

Versao implementada: Flask com tres areas:

- **Cliente:** input livre + resposta rapida + abrir ticket quando necessario.
- **Atendimento:** resolucao humana alimentando a base de conhecimento.
- **Admin:** dashboard + fila priorizada + ROI + metricas de deflexao/aprendizado.

Isso entrega a ideia completa sem aumentar demais o escopo.

---

## Stack escolhida para o MVP

### Aplicacao

- **Python + Flask**
  - Motivo: sobe rapido, permite front mais limpo que Streamlit e mantem backend simples.
  - Bom para demo publica e para avaliador testar sem setup complexo.

### Dados e IA local

- **pandas**
  - leitura e analise dos datasets.
- **scikit-learn**
  - classificador com TF-IDF + regressao logistica.
- **SQLite local**
  - base simples para salvar resolucoes humanas e demonstrar aprendizado operacional.

### IA generativa

- **OpenAI API opcional**
  - usada para melhorar a resposta do assistente quando `OPENAI_API_KEY` estiver configurada.
  - se nao houver token, o app funciona com fallback local baseado em FAQ/casos similares.

### Autenticacao

- Autenticacao simples por senha:
  - `CLIENT_PASSWORD`
  - `ADMIN_PASSWORD`
- Para o desafio, isso e suficiente para proteger a demo publica.
- Em producao, seria substituido por login real, SSO ou provedor como Supabase/Auth0.

### Guardrails de custo e seguranca

- limite de caracteres por input;
- limite de chamadas de IA por sessao;
- limite de tokens de saida;
- bloqueio basico de prompt injection;
- respostas apenas com base em FAQ/casos similares;
- casos criticos, refund, cancelamento, perda de dados e baixa confianca escalam para humano.

Status: implementado no app Flask.
