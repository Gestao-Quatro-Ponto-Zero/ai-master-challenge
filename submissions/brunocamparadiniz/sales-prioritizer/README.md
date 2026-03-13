Process Log 

SalesMaster AI

Narrativa escrita:
clonei o git e iniciei /init no claude code; fiz DL dos arquivos de DB
abri o gemini para iniciar o processo de lógica
Prompt criado no gemini
/init no claude code
CD na pasta certa e npm install
Claude code trabalhando com o prompt inicial
Primeiro prototipo feito pelo Claude e funcionando em http://localhost:5173/
Filtros funcionando, emojis caracterizando a prioridades
Farei um segundo prompt com o gemini para melhorar o design
 Funcionalidade perfeita com todos os filtros e scores funcionando
 Eu não gostei muito do design (screenshot disponível)
 Vou deixar a visualização inicial proposta pelo claude, mas vou incluir mais possibilidades para facilitar navegação de não técnicos
 Segundo prompt enviado -> resposta recebida
 De volta ao claude code
 Ajuste de lógica implementado no scoringEngine.ts (penalidade de lead parado)
 Melhorias na interface e na exibição de dados
 Adicionando novas vizualizações
 Adicionando manutenção estratégica no código, evitando desorganização a longo prazo.
 Prototipo 2 finalizado e melhorias muito visíveis
 Ainda estou insatisfeito com o design e farei novo prompt ao gemini 
 Refazendo todo o design com os prompts criados pelo gemini
 Design refeito e prototipo 3 feito.
 Último prompt de aperfeiçoamento enviado ao gemini
 Corrigindo algumas coisas e aperfeiçoando outra no claude
 Versão final pronta para deploy

Ponderação final da narrativa: 
Projeto realizado em menos de 2 horas, sendo utilizado a combinação entre Gemini e Claude Code (fiz os sistemas das minhas empresas usando uma combinação entre lovable e gemini, mas nesse projeto resolvi usar o Claude para uma condução mais técnica).

Utilizei 4 prompts no gemini e 9% do meu limite semanal do Claude. Fiquei insatisfeito com o sistema de scoring, mas ele se baseou nas tabelas que foram enviadas, mas acredito que as datas dos leads no .csv são muito antigas, o que dificulta um melhor sistema de scoring, pois o sistema se baseia muito em soluções temporais.


Documentação Técnica

Setup & Execução:
Esta solução foi construída como uma PWA (Progressive Web App) de alta performance, utilizando processamento Client-Side para garantir latência zero ao lidar com o pipeline de ~8.800 oportunidades.

a) Pré-requisitos:
Node.js (v18 ou superior)
Gerenciador de pacotes: NPM ou Yarn

b) Comandos para rodar localmente:
1. Instalar dependências
npm install
2. Iniciar o servidor de desenvolvimento
npm run dev
3. Build para produção (PWA)
npm run build

c) Ingestão de Dados
A aplicação processa automaticamente os arquivos CSV localizados em /data. No primeiro acesso, os dados são migrados para o IndexedDB através da biblioteca Dexie.js, garantindo que a ferramenta funcione offline e com buscas instantâneas após o carregamento inicial.

Lógica de Scoring (Heurística de Priorização)
A ferramenta não é um modelo de "caixa-preta", mas uma Heurística de Negócio Explicável, focada em converter "feeling" em dados acionáveis.

O Score (0-100) é calculado com base em quatro pilares principais:

Critério: Recência (peso 35%) = O maior preditor de fechamento é o contato recente. Aplicamos um decay logarítmico: deals sem interação há mais de 7 dias perdem pontuação drasticamente. 
Critério: Win Rate Histórico (peso 25%) = Cruzo-se account_id com o histórico de Won/Lost. Contas com fidelidade alta recebem prioridade automática.
Critério: Tempo no Estágio (peso 20%) = Se um deal ultrapassa o tempo médio de fechamento da região/manager, ele é marcado como "Risco de Estagnação”.
Critério: Eficiência de Valor (peso 20%) = Deals com ticket médio superior ao quartil 75% da empresa ganham bônus, priorizando o impacto financeiro (Revenue Operations). 

Limitações & Escalabilidade

O que a solução não faz hoje:
Sincronização Bidirecional: Atualmente, a ferramenta lê os CSVs. Para produção, precisaria de uma API via Webhooks para atualizar o CRM em tempo real.
Análise de Sentimento: Não analisa o conteúdo das interações (e-mails/transcrições), apenas as datas e estágios.
O que seria necessário para escalar:
Backend Distribuído: Substituir o Dexie.js (IndexedDB) por um banco PostgreSQL ou BigQuery para consolidar dados de todos os 35 vendedores em um único dashboard de Manager.
Machine Learning (MLOps): Substituir a heurística manual por um modelo de Propensity to Buy (XGBoost) treinado nos dados históricos reais, rodando inferências via AWS Lambda ou similar.
Integração de Calendário: Feature de agendamento direto na interface (ex: integração com Google Calendar/Outlook) para reduzir o context switching do vendedor.