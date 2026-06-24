# Priorizador de Leads — Visual Studio 2022 com ML.NET

Versão em **português do Brasil** do projeto `Challenge 003 — Lead Scorer`, implementada em **C# .NET 8 WinForms** e agora com uma camada real de **machine learning supervisionado com ML.NET**.

Esta versão lê as cinco planilhas traduzidas e anonimizadas em português, treina um modelo binário com oportunidades fechadas e aplica a probabilidade de ganho às oportunidades abertas.

## O que mudou nesta versão

Além do score heurístico explicável, a aplicação agora calcula:

| Campo | Significado |
|---|---|
| `Score regras` | score explicável baseado em regras, histórico e heurísticas comerciais |
| `Prob. ML` | probabilidade de ganho estimada pelo modelo supervisionado |
| `Score híbrido` | combinação de 55% score explicável + 45% probabilidade ML |
| `Valor pond. híbrido` | valor potencial ponderado pelo score híbrido |
| `Explicação ML` | interpretação textual do resultado do modelo para o vendedor |

O ranking principal da tela passou a usar o **score híbrido**.

## Como abrir e executar

1. Instale o **Visual Studio 2022** com a carga de trabalho:
   - Desenvolvimento para desktop com .NET
   - .NET 8 SDK
2. Abra o arquivo:

```text
PriorizadorLeads.sln
```

3. Aguarde o Visual Studio restaurar os pacotes NuGet.
4. Execute com `F5` ou `Ctrl + F5`.

Também é possível abrir pelo arquivo:

```text
run_visual_studio.bat
```

## Pacotes NuGet adicionados

```xml
<PackageReference Include="Microsoft.ML" Version="5.0.0" />
<PackageReference Include="Microsoft.ML.FastTree" Version="5.0.0" />
```

## CSVs usados pela aplicação

A pasta de dados do projeto é:

```text
src/PriorizadorLeads.WinForms/Data/
```

Arquivos esperados:

| Arquivo | Conteúdo |
|---|---|
| `contas.csv` | contas clientes, setor, receita, funcionários e localização |
| `produtos.csv` | catálogo de produtos e preço sugerido |
| `equipes_vendas.csv` | vendedores, gerentes e escritórios regionais |
| `funil_vendas.csv` | oportunidades do pipeline comercial |
| `metadata.csv` | dicionário de campos em português |

Os CSVs estão em padrão amigável para Excel em português:

```text
Separador: ;
Decimal: ,
Codificação: UTF-8 com BOM
```

## Estrutura da solução

```text
PriorizadorLeads.sln
src/
  PriorizadorLeads.WinForms/
    Data/
      contas.csv
      produtos.csv
      funil_vendas.csv
      equipes_vendas.csv
      metadata.csv
    Forms/
      MainForm.cs
    Models/
      CrmModels.cs
    Services/
      CsvLoader.cs
      ScoringEngine.cs
      MachineLearningLeadScorer.cs
      ReportExporter.cs
    Program.cs
    PriorizadorLeads.WinForms.csproj
docs/
  PROCESS_LOG.md
  ML_MODEL.md
outputs/
  prioridades_oportunidades_abertas_ptbr.csv
  prioridades_oportunidades_abertas_ptbr_ml.csv
  modelo_ml_validacao.txt
```

## Lógica do modelo de machine learning

### Alvo

O modelo é uma classificação binária:

```text
Ganha   -> true
Perdida -> false
```

Somente oportunidades fechadas são usadas no treinamento. As oportunidades abertas recebem inferência depois.

### Features usadas

- vendedor;
- gerente;
- escritório regional;
- conta;
- setor;
- produto;
- série do produto;
- faixa de receita;
- faixa de funcionários;
- receita anual;
- número de funcionários;
- preço sugerido do produto;
- idade/ciclo da oportunidade.

### Feature excluída de propósito

A etapa do negócio **não** é usada como entrada do modelo.

Motivo: nas oportunidades fechadas, a etapa `Ganha` ou `Perdida` é o próprio resultado final. Usar esse campo como feature causaria vazamento de informação e produziria métricas artificialmente boas.

## Score híbrido

A decisão final usa:

```text
score_hibrido = 55% score_regras + 45% probabilidade_ml
```

A razão dessa escolha é preservar interpretabilidade. O vendedor continua entendendo os componentes do score, mas o modelo supervisionado passa a capturar padrões combinados que uma regra simples pode deixar passar.

## Limitações

- O dataset tem apenas snapshots do CRM, sem histórico de atividades comerciais, cadência, origem do lead, e-mails, reuniões, propostas enviadas ou motivos de perda.
- A base permite prever padrões de ganho/perda, mas não explica causalidade.
- As métricas devem ser lidas como validação inicial, não como garantia de performance em produção.
- O modelo é treinado em memória ao iniciar a aplicação. Para produção, o ideal seria versionar o modelo, armazenar métricas e retreinar periodicamente.
- A avaliação real deveria ser feita com teste A/B: vendedores usando o ranking versus grupo controle.

## Saídas geradas

```text
outputs/prioridades_oportunidades_abertas_ptbr_ml.csv
outputs/modelo_ml_validacao.txt
```

O primeiro arquivo contém as oportunidades abertas com probabilidade ML, score híbrido e valor ponderado híbrido. O segundo documenta a validação exploratória usada para conferir a estratégia do modelo.
