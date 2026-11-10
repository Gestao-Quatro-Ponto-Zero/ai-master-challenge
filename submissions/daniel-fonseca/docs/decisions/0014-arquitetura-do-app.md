# 0014 — Arquitetura do app: três áreas com toggles, dados do Supabase, construção em frentes paralelas

- **Status:** Proposta (aguarda a validação do PRD v1.1)
- **Data:** 2026-11-10
- **Origem:** Daniel (estrutura de navegação, enxugamento do dashboard, fonte de dados, sessões paralelas) · IA (questionário, desenho da navegação e da camada de dados)
- **Referência:** [`docs/prd/01-prd.md`](../prd/01-prd.md)

## Decisão
1. **Três áreas** no lugar de oito páginas:
   - **Painel** (Diagnóstico · ROI · Operação);
   - **Console** (Triagem · Fila · Caixa);
   - **Como foi feito** (Proposta · Decisões · Condução).
   Cada área tem um toggle interno, e o estado fica na URL.
2. **Navegação:** top bar com controle segmentado no desktop; barra flutuante centralizada no rodapé no mobile.
3. **Dashboard enxuto:** um gráfico de barras com seletor de métrica e dimensão e um forest plot de CSAT. A significância vem escrita em linguagem simples. Sem filtros globais e sem painel de confiabilidade.
4. **ROI sem "níveis":** a frase de resultado fala dos casos em que a IA teria autonomia. Na interface, os caminhos se chamam Resposta automática · Revisão humana · Somente humano.
5. **Todos os dados do app vêm do Supabase.** Os resultados estatísticos continuam calculados pelos scripts Python e são carregados em tabelas `analysis_*`. O app lê só no servidor, com a service role.
6. **Construção:** uma sessão base (shell, tokens, camada de dados) e depois duas frentes paralelas, Painel/Como foi feito e Console/APIs, sem arquivos em comum.

## Consequências
- O número de telas cai, o que ajuda no vídeo de 5 minutos e no critério "comunicação clara".
- A proposta de automação (questão 2 do challenge) aparece em "Como foi feito › Proposta" e no README.
- **Sem login** (Daniel, 10/11): o app é público, com limites de uso nas rotas do servidor e uma rotina de monitoramento que **só alerta**. Ações contra abuso dependem de instrução do Daniel (PRD 8.1).
