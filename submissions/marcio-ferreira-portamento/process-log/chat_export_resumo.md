# Process Log: AI Master Challenge - Lead Scorer

Este documento serve como backup e registro das interações entre o Usuário (Marcio Ferreira) e a IA (Antigravity), comprovando o uso estratégico de inteligência artificial durante a construção da solução.

## Resumo das Decisões e Interações (Até FASE 2)

1. **Definição da Stack Tecnológica:**
   - O usuário propôs a stack: `Frontend Next.js`, `Backend FastAPI`, `Deploy Docker`. A IA validou a arquitetura como sendo de nível "Premium" e alinhada às expectativas do desafio de entregar algo funcional.

2. **Auditoria de Percepção de Mercado (Pesquisa Externa):**
   - O usuário paralisou a execução do código (FASE 3) exigindo que a IA realizasse uma pesquisa de mercado sobre Benchmarks B2B para não ficarmos apenas nas respostas rasas.
   - A IA utilizou busca web e retornou dados reais de 2026: Ciclos de vendas Enterprise demoram até 18 meses devido ao comitê de compras (6.8 pessoas em média), enquanto SMB fecha entre 14-45 dias.
   - O usuário validou a tese de que a **burocracia corporativa** gera atrasos maiores, e isso foi integrado à inteligência de negócio.

3. **Análise Exploratória de Dados (EDA):**
   - A IA rodou scripts Pandas nos arquivos CSV fornecidos (`accounts`, `sales_pipeline`, `products`).
   - Descobrimos que o win-rate geral é ~63%, produtos como `MG Special` convertem mais (65%), e empresas de receita média convertem mais (66%) do que as muito grandes (61%).

4. **Descoberta do Padrão Oculto do Dataset:**
   - O usuário perguntou qual o prazo ideal no dataset vs. o mercado.
   - A IA rodou um novo script EDA e descobriu um comportamento atípico do dataset fornecido: nele, empresas de todos os tamanhos (SMB, Mid, Enterprise) levam em média ~51 dias para fechar, e o limite de estagnação é de ~85 dias para todas.
   - **Estratégia acordada:** Penalizar duramente (Score reduzido) qualquer deal acima de 85 dias, pois foge do padrão de sucesso *deste banco de dados específico*.

5. **Engenharia de Interface e Explainability (Automação):**
   - O usuário sugeriu usar AI para respostas abaixo de 5 minutos.
   - Decidimos que a interface do vendedor terá botões "Acionar AI Auto-Responder" para leads em `Prospecting` recentes (< 1 dia), aumentando o "Speed-to-Lead".
   - O vendedor também terá a tag **HOT SIGNAL** para leads que entraram recentemente na fase `Engaging` (Signal-based selling).

## Status Atual
As fases 1 (Configuração do Fork) e 2 (Data Intelligence) estão completas. Este log e os datasets originais estão sendo comitados no Git como backup.
