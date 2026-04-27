# Sales Priority OS 🎯

**Prioridade comercial explicável para vendedores e RevOps.**

Esta aplicação foi desenvolvida para o challenge G4 AI Master, focando na priorização inteligente e transparente de oportunidades de vendas.

## 🧠 Tese Central
"O problema do time não é falta de leads. É desperdício de atenção. Deals com alta probabilidade e alto valor estão sendo ignorados enquanto o time trabalha oportunidades com baixa chance de fechamento. Esta solução não é apenas um modelo de previsão; é um **sistema de correção de comportamento comercial**. O foco é reduzir o desperdício e maximizar a execução onde o ROI é real."

## 🚀 Executive Summary (Resumo Executivo)
O **Sales Priority OS** é uma solução de Revenue Operations de alta performance. Através de um motor de scoring estatisticamente rigoroso (Bayesian Smoothing), a ferramenta quantifica o **ROI Potencial** e identifica a **Realidade do Pipeline** — onde o dinheiro está parado por falta de execução. O resultado é um aumento imediato na conversão de deals estratégicos e uma gestão executiva baseada em impacto financeiro real.

## 🔴 O Problema
Vendedores gastam tempo demais em deals que não vão fechar ("feeling" impreciso) e deixam oportunidades boas esfriar por falta de um plano de ação claro. A ausência de visibilidade executiva para o manager impede intervenções de coaching precisas em deals de alto valor.

## 🟢 A Solução
Uma aplicação Streamlit que atua como o "Sistema Operacional" da segunda-feira de manhã. Ela integra 4 bases de dados do CRM para gerar scores de 0-100, classificações operacionais, mensagens sugeridas e planos de ação automáticos.

## 🧠 Abordagem (Como o problema foi atacado)
1.  **Integração de Dados**: Relacionamento centralizado no `sales_pipeline.csv` cruzando com contas, produtos e times.
2.  **Análise Histórica**: Cálculo de taxas de ganho (Win Rate) reais para fundamentar o score em fatos, não apenas suposições.
3.  **Design focado na Persona**: Criação de abas distintas para Vendedor (Rotina) e Manager (Controle).
4.  **Explicabilidade**: Cada score é acompanhado de um "AI Decision Memo", garantindo adoção rápida pelo time.

## 💡 Recomendações
- **Vendedores**: Iniciar a semana pela aba "Monday Morning Plan", focando nos top 3 deals e utilizando as mensagens sugeridas para ganhar agilidade.
- **Managers**: Utilizar o "Manager Command Center" para identificar vendedores com baixa média de score e realizar sessões de coaching focadas em qualificação.
- **RevOps**: Monitorar os deals penalizados por estagnação (>90 dias) para realizar limpezas periódicas no pipeline (Pipeline Hygiene).

## 🌟 Diferenciais da Solução
- **Monday Morning Plan**: Aba de execução tática com insights de pipeline por vendedor.
- **Realidade do Pipeline**: Bloco executivo que quantifica a receita pronta para fechamento e deals ignorados.
- **Loss Analysis**: Cálculo automático de "Onde estamos perdendo dinheiro" devido a falhas de execução.
- **Rigor Estatístico (Bayesian Smoothing)**: Win rates calibrados (k=30) para evitar vieses.
- **Dead Zone Detection**: Sinalização de Zombie Deals para higiene de pipeline.
- **AI Decision Memo (Natural Language)**: Narrativa decisional executiva para cada oportunidade.
- **Strategic Insights**: Detecção de anomalias e gaps de execução (ex: Gap de Execução, Tração Setorial).

## 🧠 Lógica de Scoring (0-100)
| Critério | Peso | Racional de Negócio |
| :--- | :--- | :--- |
| **Estágio (Stage)** | 20% | Prioriza deals avançados (`Engaging`). |
| **Win Rate Histórico** | 30% | Baseado na performance real por vendedor, produto e setor. |
| **Perfil da Conta** | 15% | Foco em contas de alta receita e grande porte. |
| **Valor Potencial** | 15% | Priorização pelo ticket médio do produto. |
| **Momentum/Risco** | 20% | Penalização drástica por estagnação (>90 dias). |

## 🛠️ Setup e Como Rodar
### Instalação
```bash
pip install -r requirements.txt
```
### Execução
```bash
streamlit run app.py
```

## ⚠️ Limitações e Próximos Passos
- **Limitação**: O valor potencial é baseado no preço de tabela; negociações específicas de desconto não são capturadas.
- **Próximo Passo**: Evoluir para um modelo de ML (XGBoost) para capturar padrões não-lineares de perda.
