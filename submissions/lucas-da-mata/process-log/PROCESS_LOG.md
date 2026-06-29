# Process Log - Pipeline Focus Console

## 1. Entendimento do problema

Primeiro eu li o Challenge 003 e separei o pedido em linguagem operacional:

> O cliente não pediu um modelo perfeito. Pediu uma ferramenta funcional que o vendedor abre para saber onde focar.

Essa interpretação guiou as decisões seguintes:

- primeira tela precisa ser a fila de ação;
- score precisa ser explicável;
- interface precisa parecer ferramenta real de trabalho;
- documentação e process log são parte da entrega, não detalhe opcional.

## 2. Decomposição com IA

Usei IA para quebrar o problema em frentes:

1. dados e relacionamentos;
2. fórmula de scoring;
3. experiência do vendedor;
4. visão de manager/RevOps;
5. documentação e submissão;
6. validação local e publicada.

A IA ajudou a transformar o README do desafio em critérios de aceitação práticos.

## 3. Decisões de produto

### Tabela priorizada em vez de kanban

Um kanban seria familiar, mas não responde tão diretamente à pergunta do desafio. A tabela priorizada responde melhor:

> Qual deal atacar agora?

### Score rule-based em vez de ML

Escolhi regras ponderadas porque:

- o time precisa confiar no score;
- o dataset é pequeno para um modelo sofisticado;
- o desafio valoriza utilidade e explicabilidade;
- uma heurística boa e transparente supera um modelo caixa-preta sem adoção.

### Dados reais direto no app

Removi a experiência de upload como primeira tela. O vendedor não deve começar carregando CSV. Ele deve abrir a ferramenta e ver o pipeline.

## 4. Onde a IA errou e como corrigi

### Erro 1 - Tela de upload como experiência principal

A primeira direção gerava uma tela para carregar CSVs. Tecnicamente funcionava, mas parecia sistema de teste. Corrigi para abrir direto com os dados do CRM embutidos.

### Erro 2 - Confundir validação local com validação publicada

Em alguns momentos o build local estava correto, mas o preview/publicação do Lovable ainda servia versão antiga. Corrigi o fluxo:

1. validar build local;
2. validar commit no GitHub;
3. validar preview Lovable;
4. validar URL pública.

### Erro 3 - Export/copy dependentes de permissão do navegador

O botão de copiar podia ser bloqueado pelo browser e o download podia não ser capturado em alguns ambientes de preview. Corrigi com fallback:

- textarea manual para copiar lista de ações;
- link `Baixar CSV pronto` depois de preparar o arquivo.

## 5. Iterações principais

### Iteração 1 - Produto base

- carregamento dos quatro CSVs;
- joins entre pipeline, contas, produtos e vendedores;
- score explicável;
- tabela priorizada;
- painel lateral.

### Iteração 2 - Experiência real

- remoção do fluxo de upload inicial;
- app abre direto em português;
- seletor PT/EN;
- filtros persistentes;
- responsivo mobile.

### Iteração 3 - Confiança e ação

- confiança do score por deal;
- dados usados;
- limitações;
- export CSV;
- cópia da lista de ações.

### Iteração 4 - Camada que impressiona

- brief de segunda-feira;
- visão RevOps para managers;
- resumo global de confiança e limitações;
- documentação de setup, scoring e limitações.

## 6. O que eu adicionei além da IA

- Priorizei o pedido da Head de RevOps acima da tentação de fazer uma UI genérica.
- Cortei features que pareciam sofisticadas, mas não ajudavam o vendedor a decidir.
- Mantive a fórmula simples e auditável.
- Expus limitações em vez de esconder incerteza.
- Transformei o processo em documentação reutilizável para avaliação.

## 7. Evidências técnicas

Repositorio da solução:

```text
https://github.com/olucasdamata/pipeline-focus
```

App publicado:

```text
https://pipeline-focus-buddy.lovable.app/
```

Comandos usados na validação:

```bash
npm run build
npm run lint
```

Resultado esperado:

- build sem erro;
- lint sem erro, apenas warnings já existentes de `react-refresh`;
- aplicação pública sem tela de upload;
- fila com dados reais do CRM;
- export/copy funcionais com fallback.

Screenshots finais anexados:

- `screenshots/01-public-dashboard-desktop.jpg`
- `screenshots/02-scoring-logic-modal.jpg`
- `screenshots/03-public-dashboard-mobile.jpg`

Código fonte incluído na submissão:

```text
solution/pipeline-focus-console/
```

## 8. Checklist de submissão

- [x] Challenge escolhido: 003 - Lead Scorer
- [x] Solução funcional publicada
- [x] Dados reais do dataset
- [x] Scoring/priorização explicável
- [x] Setup documentado
- [x] Lógica documentada
- [x] Limitações documentadas
- [x] Process log escrito
- [x] Screenshots finais anexados
- [x] Código fonte incluído no pacote de submissão
- [ ] PR final aberto no repo do desafio
