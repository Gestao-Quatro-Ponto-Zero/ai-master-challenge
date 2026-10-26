# Etapa 4 — A tela e o teste automático

Ferramenta: Claude Code. Código em [`solution/app/`](../solution/app/) (HTML + CSS + JavaScript, sem dependências) e [`solution/testes/teste_tela.mjs`](../solution/testes/teste_tela.mjs).

## Decisões

- **Página estática que lê `dados.js`.** Abre com dois cliques ou por link, sem servidor.
- **Três abas:** Vendedor, Chefe de vendas e Como a nota funciona.
- **Vendedor: as 5 da semana em primeiro lugar.** A queixa é "tempo demais em vendas que não fecham": a tela mostra primeiro só 5 vendas. O resto fica em blocos fechados (outras vendas, paradas, sem cliente).
- **Motivo e próxima ação sempre visíveis.** O vendedor entende a nota sem clicar.
- **Chefe de vendas: o pipeline de verdade.** CRM × previsão × parado × sem cliente, com filtro por região e gerente, e o próximo passo de cada vendedor.
- **Primeira visita abre num exemplo completo:** um vendedor com negociação em andamento e 5 vendas na semana. A primeira versão abria no primeiro nome da lista (Anna Snelling), que só tem prospecções, e a primeira coisa que aparecia era um aviso amarelo.

## Teste automático

O script abre a página num Chrome sem janela e confere 33 pontos, entre eles:

- as vendas da semana (1 a 5) aparecem em ordem de valor esperado, cada uma com motivo e ação, e nenhuma com nota baixa;
- os 27 vendedores com vendas abertas abrem sem erro e sem texto quebrado;
- o aviso aparece para quem não tem negociação em andamento e não aparece para quem tem;
- Feito, Desfazer, Ainda viva, Encerrar e Cadastrado funcionam e continuam salvos depois de recarregar;
- os filtros de região e gerente da chefe mostram só a equipe certa e os números mudam;
- as abas, o gráfico e as tabelas do teste aparecem;
- no celular (390 px), nada passa da borda;
- nenhum erro no console.

Ele também tira as fotos de [`docs/screenshots/`](../docs/screenshots/).

## Erros encontrados

| Erro | Como foi pego | Correção |
|---|---|---|
| Na tela da chefe, o "próximo passo" era o mesmo para todos ("Limpar a carteira") | Olhando a foto gerada pelo teste: a regra valia para todos os vendedores | Próximo passo específico: quantas paradas revisar (e quanto vale), quantos clientes cadastrar, e aviso quando não há negociação |
| "1 vendas" | Olhando a foto | Plural certo |
| O teste do filtro de gerente falhou | O teste lia os valores em dinheiro da tabela como se fossem o nome do gerente | Erro do teste, não da tela: o teste passou a ler só a primeira coluna |

## Revisão final (pedido do José)

Revisando a ferramenta pronta, José não aceitou nada que pudesse parecer estranho para o vendedor ou para o avaliador, mesmo estando certo nos dados:

| O que parecia estranho | Por que acontecia | Ajuste |
|---|---|---|
| Uma venda de US$ 16 (MG Special) entre as 5 da semana de uma vendedora | Ela tem poucas vendas vivas, e a lista pegava as 5 maiores mesmo que valessem quase nada | Só entram na semana vendas com nota 20 ou mais (fora os 20% de menor valor). Saíram 10 vendas; os 27 vendedores continuam com vendas na semana |
| A chefe via US$ 5,0 mi no CRM e US$ 0,2 mi de previsão, sem explicação | Em 31/12/2017, quase todo o pipeline está parado ou sem cliente | A tela explica: US$ 3,2 mi parados + US$ 1,2 mi sem cliente; sobram US$ 0,6 mi em 252 vendas vivas, e a previsão é a parte delas que deve fechar |
| A tela abria num vendedor sem negociação (aviso amarelo logo de cara) | O exemplo inicial era escolhido só pelo valor | Abre num vendedor com negociação em andamento e 5 vendas na semana |

