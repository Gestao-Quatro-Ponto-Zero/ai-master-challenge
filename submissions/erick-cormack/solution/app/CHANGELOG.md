# Changelog

## 2026-11-05 (10)
- Meu pipeline e Visão do gestor: botões "Exportar PDF" e "Exportar XLSX" que respeitam os filtros ativos, nas cores G4 (azul-marinho e dourado). PDF do pipeline traz resumo do recorte e as três filas completas; XLSX traz abas Resumo, Focar agora, Requalificar ou encerrar e Prospectar. Exportação do gestor traz a tabela por vendedor com destaque para mais de 70% parado.

## 2026-11-05 (9)
- Meu pipeline: gráfico "Valor esperado em foco por manager" (barras horizontais) logo abaixo dos cartões de resumo, respeitando os filtros do recorte.

## 2026-11-05 (8)
- Página inicial: botão "Detalhar mais" ao lado de "Resumo executivo" abre modal com a análise completa (em 30 segundos, descobertas, onde está o problema, recomendações e ressalvas).

## 2026-11-05 (7)
- Resumo executivo da página inicial em card destacado (fundo de destaque, borda e sombra) com fonte maior, para leitura rápida do panorama do pipeline.

## 2026-11-05 (6)
- Números dos cartões e scores usam Archivo sem serifa, com peso semibold e algarismos tabulares para facilitar leitura e comparação; títulos mantêm a identidade G4.
- Meu pipeline: paginação de 25 oportunidades nas três abas, com primeira/anterior/próxima/última página e indicação de intervalo e total. Alterar os filtros reinicia a paginação.
- Teste de paginação cobre tamanho de página, continuidade dos registros e última página parcial; banco permanece sem alterações.

## 2026-11-05
- Estrutura base do Lead Scorer: página inicial com título e subtítulo, barra lateral com navegação para "Meu pipeline" e "Visão do gestor" (páginas vazias), identidade visual (Instrument Serif + Geist, tons grafite e verde).

## 2026-11-05 (2)
- Conexão somente leitura com o banco (views v_deals_score, v_resumo_vendedor, v_curva_ganho e tabela parametros); tipos regenerados.
- Filtros Região → Manager → Vendedor em cascata, salvos no link; aviso "Retrato do CRM em 31/12/2017".
- Meu pipeline: cartões de resumo, abas Focar agora / Requalificar ou encerrar / Prospectar, painel "Por que este score" com motivos, conta do valor esperado, curva de ganho e contexto.
- Visão do gestor: cartões do recorte e tabela por vendedor ordenável, com total, destaque âmbar acima de 70% parado e link para o pipeline do vendedor.
- Página inicial: "Como o score funciona" e gráfico da curva de ganho.

## 2026-11-05 (3)
- Curva de ganho: ignora pontos sem dado, linha sólida só com amostra mínima e tracejada no último valor confiável até o ciclo máximo; eixo de 50% a 90%; marcador do deal usa a chance do próprio deal.
- Ciclo máximo, fase de risco e reta final lidos de `parametros` (sem valores fixos no código).
- Aba Focar agora: estado vazio com atalhos para Requalificar ou encerrar e Prospectar.

## 2026-11-05 (4)
- Identidade visual G4 (g4business.com): azul-marinho + dourado, Playfair Display (itálica) nos títulos e Archivo no texto.
- Login por e-mail e senha: usuário recrutamentog4@g4club.com.br criado com confirmação automática; cadastros públicos bloqueados.
- Acesso com validade de 15 dias (até 20/11/2026), verificado no login e na proteção das rotas; tela /login e botão Sair na barra lateral.

## 2026-11-05 (5)
- Página inicial: seção "Resumo executivo" com texto dinâmico e 4 cartões (deals abertos, foco imediato, parados além do limite, sem conta).
- Novos gráficos na inicial: deals abertos por fila, valor esperado em foco por região e distribuição do score nos deals em foco (agregações em `src/lib/homeStats.ts`, com testes).
