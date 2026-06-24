# Process Log — Priorizador de Leads com ML.NET

## Objetivo

Evoluir o projeto `Challenge 003 — Lead Scorer` para incluir uma camada real de machine learning, mantendo a aplicação funcional em Visual Studio 2022, C# .NET 8 WinForms e CSVs em português do Brasil.

## Uso de IA no processo

A IA foi usada como par de desenvolvimento para:

1. Identificar que a versão anterior tinha score heurístico, mas não um modelo supervisionado treinado.
2. Definir corretamente o problema de ML como classificação binária: `Ganha` contra `Perdida`.
3. Evitar vazamento de informação removendo a etapa do negócio das features do modelo.
4. Implementar `MachineLearningLeadScorer.cs` com ML.NET.
5. Atualizar `CrmModels.cs` para incluir probabilidade ML, score híbrido e resumo de treinamento.
6. Atualizar a interface WinForms para exibir:
   - probabilidade ML;
   - score híbrido;
   - explicação ML;
   - aba `Modelo ML.NET` com métricas.
7. Atualizar exportação CSV para incluir colunas de ML.
8. Criar documentação técnica do modelo.
9. Gerar uma validação exploratória em Python para conferir a estratégia, já que o ambiente de geração não possui SDK do .NET instalado.

## Ferramentas usadas

| Ferramenta | Para que foi usada |
|---|---|
| ChatGPT | Arquitetura da solução, geração de código C#, revisão metodológica, documentação e process log |
| ML.NET | Modelo supervisionado integrado ao projeto C# WinForms |
| Python / scikit-learn | Validação exploratória da estratégia de classificação e geração de CSV de saída com probabilidade ML |
| Visual Studio 2022 | Ambiente alvo do projeto |

## Workflow

1. Partida a partir do projeto em português com CSVs anonimizados.
2. Revisão do motor de scoring existente.
3. Definição do alvo supervisionado: oportunidades fechadas como `Ganha` ou `Perdida`.
4. Seleção de features úteis e disponíveis no dataset.
5. Exclusão deliberada da etapa do negócio para evitar vazamento.
6. Criação do serviço `MachineLearningLeadScorer.cs`.
7. Inclusão dos pacotes NuGet `Microsoft.ML` e `Microsoft.ML.FastTree`.
8. Atualização da UI para exibir score híbrido e métricas.
9. Atualização da exportação CSV.
10. Geração de documentação e validação exploratória.

## Onde a IA errou e como foi corrigido

A solução anterior poderia ser apresentada como “inteligente”, mas tecnicamente não treinava um modelo de machine learning. Isso foi corrigido com a inclusão de um modelo supervisionado.

Outro ponto crítico: usar a coluna de etapa como feature pareceria natural, mas estaria errado. Como `Ganha` e `Perdida` são o resultado final, incluir essa variável como entrada causaria vazamento de informação. A correção foi excluir essa coluna do treinamento e usar apenas dados de conta, produto, vendedor, região, porte e ciclo.

## O que foi adicionado que a IA sozinha poderia não priorizar

- Preservação do score explicável em vez de substituir tudo por ML.
- Score híbrido para equilibrar confiança estatística e interpretabilidade comercial.
- Registro explícito das limitações do dataset.
- Métricas interpretadas com cautela, sem vender o modelo como perfeito.
- Arquivo `ML_MODEL.md` documentando decisões metodológicas.

## Evidências

- Código-fonte alterado:
  - `Services/MachineLearningLeadScorer.cs`
  - `Models/CrmModels.cs`
  - `Forms/MainForm.cs`
  - `Services/ReportExporter.cs`
  - `PriorizadorLeads.WinForms.csproj`
- Saídas geradas:
  - `outputs/prioridades_oportunidades_abertas_ptbr_ml.csv`
  - `outputs/modelo_ml_validacao.txt`
- Documentação:
  - `README.md`
  - `docs/ML_MODEL.md`
  - `docs/PROCESS_LOG.md`

## Limitação do processo

O ambiente onde esta versão foi montada não possui o SDK do .NET instalado. Por isso, a compilação final deve ser validada no Visual Studio 2022. A validação exploratória do modelo foi feita com Python para confirmar a estratégia estatística e produzir métricas iniciais.
