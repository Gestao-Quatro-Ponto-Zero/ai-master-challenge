# CLAUDE.md — Contexto do Projeto (v3)

## O que é este projeto

Desafio técnico para a posição de AI Master no G4 Educação. Challenge 003 — Lead Scorer (Vendas / RevOps).

Ferramenta funcional que um vendedor abre, vê seu pipeline, e sabe imediatamente onde focar — com score de priorização explicável e transparente.

## Quem é o usuário

- 35 vendedores não-técnicos distribuídos em escritórios regionais
- Rotina: abre na segunda-feira de manhã e precisa saber em 10 segundos quais 5 deals atacar
- Precisa entender POR QUE cada deal tem aquele score — com pontuação detalhada por fator
- Precisa marcar o status de cada deal (contatado, em negociação, etc.) e a lista atualiza

## Princípios de design

1. **Funcional > bonito.** Algo simples que funcione vale mais que algo ambicioso que quebre.
2. **Explicável > complexo.** Pontuação detalhada por fator. Nada de caixa preta.
3. **O vendedor não é julgado.** O fator "vendedor" foi excluído do scoring por decisão de design.
4. **O score mede POTENCIAL, não progresso.** Stage (Prospecting/Engaging) NÃO entra no cálculo do score. Um deal em Prospecting com alto potencial aparece no topo — porque precisa de primeiro contato urgente.
5. **Top 5 dinâmico.** Quando o vendedor marca um deal como contatado/em negociação/concluído, ele sai do Top 5 e o próximo da fila entra.
6. **Dados reais.** Usa os 4 CSVs do dataset CRM na pasta data/.
7. **Data de referência.** Os dados são de 2016-2017. Toda a aplicação usa a engage_date mais recente dos deals abertos como "hoje" (2017-12-22). NÃO usar datetime.now().
8. **Interface em português do Brasil.**

## Estrutura do projeto

```
solution/
├── app.py                 ← Aplicação Streamlit (principal)
├── requirements.txt       ← Dependências (streamlit, pandas)
├── CLAUDE.md              ← Este arquivo
├── INSTRUCTIONS.md        ← Especificação técnica detalhada
├── CONTEXT1.md            ← Resultado da Etapa 1
├── CONTEXT2.md            ← Correções de scoring v2
├── CONTEXT3.md            ← Melhorias de interface
├── CONTEXT4.md            ← Scoring v3 + Top 5 dinâmico
└── data/
    ├── accounts.csv       ← 85 contas
    ├── products.csv       ← 7 produtos
    ├── sales_teams.csv    ← 35 vendedores
    ├── sales_pipeline.csv ← ~8800 oportunidades
    └── deal_status.csv    ← Status dos deals (gerado pela app, persistente)
```

## Stack técnica

- **Python 3.9** (já instalado)
- **Streamlit 1.50.0** (já instalado)
- **Pandas** (já instalado)
- Nenhuma outra dependência. Não instale pacotes extras.

## Regras para o código

- Código limpo e comentado em português
- Funções bem separadas (carregamento, scoring, interface, status)
- Caminhos relativos (data/arquivo.csv)
- Tratar dados faltantes (engage_date vazia em Prospecting, contas sem match no accounts)
- Não modificar os CSVs originais (exceto deal_status.csv que a app gera)
- Rodar com: `streamlit run app.py`

## O que NÃO fazer

- Não usar Machine Learning (sklearn, XGBoost, etc.)
- Não usar datetime.now() — usar data de referência do dataset
- Não incluir "vendedor" no cálculo do score
- Não incluir "stage" no cálculo numérico do score (stage é badge visual)
- Não instalar dependências extras
- Não criar múltiplos arquivos Python sem necessidade

## Referência

A especificação técnica completa está em INSTRUCTIONS.md. Para o histórico de decisões e iterações, consulte CONTEXT1.md → CONTEXT2.md → CONTEXT3.md → CONTEXT4.md nessa ordem.
