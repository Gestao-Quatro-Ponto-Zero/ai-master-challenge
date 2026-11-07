# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

Vendedores e o sales manager que precisam decidir, numa segunda de manhã, onde focar a semana num pipeline de vendas B2B. Com um vendedor selecionado no filtro, a tela se dirige a ele diretamente ("Bom dia, Hayden."). Sem filtro, ela fala com um manager ou com a Head de RevOps olhando a operação inteira.

## Product Purpose

Pipeline em Foco é um app de vendas que traduz um motor de scoring (Python, sem LLM em tempo de execução) em quatro filas de ação priorizadas: Fechar, Decidir, Avançar e Prospectar. Cada prioridade vem com o motivo em português. O app substitui o ranking arbitrário do forecast por um baseado no único sinal que passou em teste estatístico contra o acaso nesta base, a idade do deal.

## Positioning

Cada score e cada fila vêm de testes de significância sobre os dados. Vendedor, conta, tamanho da conta, produto, setor, região e manager foram testados e descartados; só a idade do deal muda a chance de ganhar. Um concorrente não copia a interface sem copiar a disciplina estatística que está por trás dela, e isso inclui o Time, que mostra receita e volume como são, mas não compara vendedores por taxa de ganho, porque ali a diferença é ruído (p = 0,30).

## Operating Context

- O dado é um retrato estático (`data.json` gerado pelo motor Python a partir dos CSVs); não há CRM ao vivo.
- As decisões do vendedor ("requalifiquei", "encerrar como perdido") ficam só no `localStorage` do navegador e não voltam para um CRM. Dá para baixar e importar um JSON com elas.
- Os filtros de Região, Manager e Vendedor aparecem em todas as telas, em cascata.
- O roteamento é por hash, no cliente, sem backend.

## Capabilities and Constraints

- Seis telas: Overview (a primeira aba, que antes se chamava Meu dia), Pipeline (lista e quadro kanban), Ficha do deal, Forecast, Contas e Time. A tela "Como o score funciona" saiu do produto; a auditoria estatística fica no README da submissão.
- Motor de scoring: `score = P(ganhar em 30 dias | idade)`, em %, sem o preço do deal, e com o mesmo nome em todas as telas. Ao lado dele vai uma faixa (alta, média, baixa) contra o melhor score possível na base (31%). Zumbis (parados além do maior ciclo já fechado) e prospecção ficam sem score. A ordem das filas usa a receita esperada em 30 dias (valor × score), mostrada na mesma tabela.
- A ação recomendada muda com a fase da curva (antes do pico, no pico, depois dele, reta final) e com o histórico da conta. Conta vazia nunca é motivo para sugerir encerrar.
- A prospecção fica fora do forecast esperado por falta de histórico de conversão para "Engaging".
- Stack: React 19, TypeScript e Vite, sem biblioteca de UI de terceiros; todo o visual é CSS próprio.
- Não há atividade de CRM (emails, reuniões) nos dados. A idade é o melhor sinal disponível, mas não é o ideal.

## Brand Commitments

Identidade visual definida pelo usuário a partir da marca G4 (G4 Educação, g4.business), extraída do perfil no Instagram: navy profundo como estrutura, ouro reservado a dados de dinheiro e ações primárias, bordô como acento secundário, serifada editorial nos títulos (Libre Caslon Text) sobre uma sans limpa nos dados (Manrope), e a marca com estrela-bússola. O tema padrão é escuro, em navy quase preto, seguindo o mockup de referência "Lead Scorer Dashboard" feito no Claude Design. O tema claro, com superfícies em marfim, existe por `data-theme="light"` e não tem controle na interface. O registro da direção de marca fica em `.impeccable/surfaces/` na raiz do repositório local, fora da submissão.

## Evidence on Hand

- Dados sintéticos de demonstração (empresas fictícias), num retrato de referência em 31/12/2017. Não são clientes reais e não devem ser tratados como tal em nenhuma cópia futura.
- `solution/data/*.csv`: pipeline de vendas, contas, times e produtos.
- `solution/engine/scoring.py` e `test_scoring.py`: o motor determinístico e sua suíte de testes.
- Screenshots em `process-log/screenshots/`: de 12 a 16 é a versão atual; de 01 a 11, versões anteriores.

## Product Principles

1. Nenhuma feature entra no score sem passar em teste de significância contra o acaso, e a interface nunca sugere uma causa que os dados não sustentam.
2. Zumbi pede decisão. Um deal sem histórico comparável sai do forecast até ser requalificado ou encerrado, e não fica gerando alerta para o vendedor indefinidamente.
3. Pessoas não são ranqueadas por ruído estatístico. Diferenças sem significância aparecem como higiene de pipeline, nunca como desempenho.
4. A cor indica a fila de ação. A paleta mostra em que fila cada deal está, em toda tela onde ele aparece, e não é usada como enfeite.
