# Process log

Como cheguei na solução, em ordem, com o que foi meu e o que foi da IA em cada passo. Ferramenta principal: Claude Code com o modelo Claude Opus 5.5, num terminal no meu computador, com subagentes para leitura longa e pesquisa. Os números citados aqui saem dos arquivos em `solution/analysis/outputs/`.

## Linha do tempo

| # | Etapa | Meu | IA | Resultado |
|---|---|---|---|---|
| 1 | Entender o teste | Pedi uma leitura profissional do teste e do repositório antes de escolher | Leu README, guia e os 4 enunciados; leu as 197 reviews públicas do avaliador e sintetizou a régua | Uso de IA vale 30%; process log em Markdown; screenshots são a primeira evidência; avaliação assistida por IA |
| 2 | Escolher o desafio | Escolhi o 002 | Mediu os 4 datasets: o 004 é ruído puro (engajamento 0,199 em todo recorte), o 002 tem texto real | 002 pede diagnóstico, automação e algo rodando |
| 3 | Auditoria | Não decidi nesta etapa; revisei o resultado no fim | Script de auditoria com testes estatísticos | Dataset 1 sintético (6 sinais); Dataset 2 limpo |
| 4 | Laboratório | Não decidi nesta etapa; revisei o resultado no fim | 5 modelos, divisão 70/15/15, limiar escolhido na validação | Regressão logística: 85,6% de acerto, ECE 0,011 |
| 5 | Estresse | Exigi cenários reais em 4 severidades, com evidência | 9 cenários; cada falha virou trava, medida de novo | Ver "Iterações" abaixo |
| 6 | Boas práticas | Pedi estudo de livros e práticas de mercado | Subagente pesquisou e conferiu fontes | Auditoria cega de 2% (viés de automação) entrou no desenho |
| 7 | Marca | Defini a identidade da G4, à risca | Mediu logo, cores, fontes e contraste nas páginas atuais | Dourado só sobre marinho; destaque em marinho no claro |
| 8 | Console | Defini a régua: profissional, rápido, seguro, validado visualmente | Construiu o app estático, teste de paridade, prints de cada tela | Lighthouse 98 a 100 em performance, 100 em acessibilidade |
| 9 | Revisão contra o enunciado | Pedi prints e a conferência de que é isso que o desafio pede | Comparou cada tela com o enunciado e a régua; viu que o diagnóstico não respondia as três perguntas pelo nome | Teste de permutação por canal × prioridade × tipo; bloco com as três respostas |
| 10 | UX | Pedi troca de página rápida e skeleton | Mediu a troca (20 a 64 ms, com 4G lento); skeleton no teste ao vivo e na rota; detalhe do ticket em folha inferior no celular | Sem salto de layout (CLS 0) |
| 11 | Segurança | Pedi pentest e estresse de segurança | Atacou o modelo (palavras coladas e intercaladas) e o console (10 ataques num Chrome real); auditou dependências e procurou segredo e dado pessoal | Falha real no modelo corrigida; 10 de 10 no console |
| 12 | Publicação | Liberei o deploy no Vercel e pedi o deck com a identidade da G4, as imagens para o PR e prints animados | Publicou no meu escopo pessoal, refez pentest e Lighthouse em produção, montou o deck de 8 slides (fundos gerados por IA) e as 5 animações | Pentest 10 de 10 e Lighthouse 99 a 100 na URL publicada |
| 13 | Console de operação | Pedi colunas ordenáveis e um ícone de explicação em cada seção | Ordenação acessível (aria-sort, seletor no celular) e explicações por hover, foco e toque | Acessibilidade continua 100 |

## Iterações que mudaram a solução

Cada linha é uma falha real encontrada por teste, não por revisão de texto.

| Versão | O que estava errado | Como apareceu | Correção | Efeito medido |
|---|---|---|---|---|
| v1 → v2 | Faixa assistida escolhida pela precisão acumulada: 27% dos tickets com 60% de acerto | Leitura do resultado do laboratório | Faixa definida pelo acerto das duas sugestões | Assistido com a fila certa entre as duas em 91% |
| v2 → v3 | Só o limiar: texto de outro domínio seguia sozinho | Estresse E1, 8.469 tickets do Dataset 1 | Trava de histórico parecido + disjuntor de distribuição | 51% → 15% automático; pausa em 159 tickets |
| v3 → v4 | Português passava pela trava de histórico | Estresse M2, 24 sondas | Trava de vocabulário conhecido | 62% automático com 20% de acerto → 0% |
| v4 → v5 | Trava de vocabulário calibrada em texto limpo barrava digitação | Estresse C2 | Piso entre o máximo do português (0,50) e o texto com 5% de erro (0,63) | Com 5% de erro: 77% humano → 8% humano |
| v5 → v6 | Tickets de RH seguiam sozinhos para outra fila | Estresse E3 | Trava de conteúdo sensível, com a tabela de custo | 54 → 26 de RH; 19 → 8 de administrador; custo de 5 pontos de automação |
| v6 → v7 | Disjuntor com alarme falso em tráfego normal | Simulação de fluxo | Suavização na contagem da janela | 0 alarme falso em 20 simulações |
| v7 → v8 | Laboratório e estresse com modelos de tamanhos diferentes | O subagente de pesquisa notou limiares diferentes (0,78 e 0,79) | Um modelo só, de 10 mil termos | Números consistentes em todo o material |
| v8 → v9 | As travas olhavam só o ticket inteiro: palavras coladas diluíam o sinal de RH e de administrador | Pentest S1: 5 palavras comuns no fim de 264 tickets de administrador e 1.638 de RH | Trava de trecho: o ticket também é lido em janelas de 8 palavras (parâmetros escolhidos na validação) | Escape de 42% para 10% a 16%; custo de 6,5 pontos de automação |
| v9 → v10 | A trava de trecho não pegava palavra intercalada entre cada palavra | Pentest S1, variante intercalada | Trava de sequência: pares de palavras conhecidos abaixo do percentil 2 da validação vão para humano | Escape de 96% a 100% para 2% a 7%; rejeição indevida de 2,2% para 4,1% |
| v10 → v11 | Modelo com cache imutável de um ano sob nome fixo | Leitura dos cabeçalhos durante o pentest | Nome do arquivo com o hash do conteúdo, conferido pelo console antes do uso | Retreino nunca fica preso no cache; arquivo adulterado é recusado |

## Onde a IA errou

1. Todas as falhas da tabela acima foram desenhos da IA que não resistiram ao teste.
2. O script de captura de tela montou a URL da home com barra dupla, e o print mostrou um erro que parecia do app. A investigação mostrou que era o script.
3. A primeira versão do README atribuía a mim decisões que a IA tinha tomado. Corrigi a coluna "meu" para conter só o que decidi.
4. A ferramenta de pentest entrou numa versão que puxava dependências com falha alta conhecida, e o pytest fixado tinha alerta. Trocados por versões sem alerta; `npm audit` e `pip-audit` limpos.
5. O primeiro teste de injeção acusou que `eval` rodava. Era o teste: a avaliação pelo DevTools ignora a CSP por padrão. Refeito sem essa exceção, o `eval` aparece bloqueado.
6. A exportação rodou em paralelo com o estresse e podia copiar número velho; a taxa de rejeição indevida não contava a trava nova. Rodado em sequência e métrica corrigida.
7. A primeira varredura de segredos não rodou de verdade (o zsh não separou os argumentos). Refeita em bash, com um controle positivo que prova que os padrões detectam o que foi plantado.

## Verificação

- `solution/analysis/tests/`: 11 testes da política de roteamento (`pytest`)
- `solution/app/tests/`: 22 testes, incluindo paridade Python × navegador em 300 tickets (mesma fila em 100%, diferença de probabilidade abaixo de 0,001, mesmos sinais das travas de trecho e de sequência) e a integridade do modelo
- `security/`: relatório do pentest do console (10 de 10) e [`../docs/seguranca.md`](../docs/seguranca.md)
- `lighthouse.md`: resultado por página, mobile e desktop
- `screenshots/`: todas as páginas, desktop e mobile

## Conversa

A conversa com a IA, curada, está em [`chat-exports/conversa-curada.md`](chat-exports/conversa-curada.md): as minhas mensagens como escrevi e o resumo de cada resposta, com os erros da IA no lugar em que aconteceram.
