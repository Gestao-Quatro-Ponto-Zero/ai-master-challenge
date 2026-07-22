# Guia do Usuário

## O que é o Dashboard

O RavenStack Churn Intelligence é um painel local para analisar clientes, churn, receita, uso do produto, suporte e contas em risco. Ele foi pensado para apoiar decisões de Customer Success, Produto, Receita e liderança.

## Como Acessar

Depois que a aplicação estiver rodando, abra:

```text
http://127.0.0.1:5000
```

A página inicial é a Visão Executiva.

## Visão Executiva

A tela inicial mostra:

- resumo do período analisado;
- total de contas consideradas;
- KPIs de clientes, receita, suporte e risco;
- prioridades executivas;
- gráficos de churn, receita, uso e suporte;
- tabela de contas em risco.

## Filtros

Os filtros globais ficam no topo da página inicial.

Filtros disponíveis:

- período inicial e final, aplicados à data de cadastro da conta;
- plano;
- indústria;
- país;
- origem;
- trial ou pagante;
- status ativo ou churn;
- frequência de cobrança;
- renovação automática;
- motivo de churn.

Clique em **Aplicar filtros** para atualizar o painel. Clique em **Limpar** para voltar à base completa.

## Como Interpretar os KPIs

| KPI | Como interpretar |
| --- | --- |
| Total de contas | Quantidade de contas no filtro atual. |
| Contas ativas | Contas sem churn vigente segundo a regra consolidada. |
| Contas com churn | Contas canceladas ou marcadas com churn. |
| Taxa de churn | Percentual de contas com churn dentro da base filtrada. |
| MRR ativo | Receita mensal recorrente das contas ativas. |
| ARR ativo | Receita anual recorrente das contas ativas. |
| MRR perdido | Receita mensal associada a contas com churn. |
| ARR perdido | Receita anual associada a contas com churn. |
| Total de tickets | Volume de chamados de suporte. |
| Satisfação média | Média das notas de satisfação registradas nos tickets. |
| Alto risco | Contas ativas com score de risco igual ou maior que 60. |

## Seções do Dashboard

### Churn

Mostra eventos de churn por mês, MRR perdido, motivos declarados e segmentações por plano, indústria e país.

Use essa seção para identificar onde o churn se concentra e quais motivos aparecem com maior frequência.

### Receita

Mostra MRR ativo por plano, ARR ativo por indústria, MRR perdido por plano e faixas de MRR.

Use essa seção para entender impacto financeiro e priorizar segmentos com maior exposição.

### Produto e Uso

Mostra funcionalidades mais utilizadas, comparação entre contas ativas e churn, tendência mensal de uso e comparação de features beta versus gerais.

Use essa seção para observar engajamento, volume de uso e erros.

### Suporte

Mostra tickets por prioridade, comparação entre ativas e churn, tempos médios, satisfação e escalonamentos.

Use essa seção para avaliar se suporte pode estar associado a risco ou perda.

### Contas em Risco

A tabela combina risco operacional e valor financeiro. Ela permite:

- buscar por nome ou ID;
- filtrar contas críticas;
- filtrar alto risco;
- filtrar alto valor;
- filtrar contas sem uso recente;
- filtrar baixa satisfação;
- exportar CSV;
- abrir o detalhe de uma conta.

## Score de Risco

O score é uma pontuação heurística, não uma previsão estatística calibrada.

| Classe | Faixa | Significado prático |
| --- | ---: | --- |
| Baixo | 0 a 29 | Poucos sinais relevantes. |
| Médio | 30 a 59 | Alguns sinais merecem acompanhamento. |
| Alto | 60 a 79 | Conta deve entrar na rotina de priorização. |
| Crítico | 80 a 100 | Conta exige atenção imediata. |

No detalhe da conta, a área “Fatores do score” lista os sinais acionados.

## Explorar Contas

Acesse pelo menu lateral em **Explorar Contas** ou pela URL:

```text
http://127.0.0.1:5000/accounts
```

Essa tela permite buscar contas e usar filtros rápidos:

- todas;
- ativas;
- churn;
- risco alto;
- alto valor.

Clique em **Ver detalhes** para abrir a visão completa da conta.

## Detalhe da Conta

A página de detalhe mostra:

- status da conta;
- score de risco e prioridade;
- receita;
- uso total e erros;
- tickets;
- eventos de churn e reativação;
- dados cadastrais;
- fatores do score;
- histórico de assinaturas;
- gráfico de uso por funcionalidade;
- linha do tempo.

## Cuidados na Interpretação

- Churn e risco são análises associativas, não prova causal.
- O score de risco não é modelo de machine learning.
- Dados ausentes em satisfação ou uso podem afetar leitura.
- A regra consolidada pode divergir de flags individuais do dataset.
- O dashboard depende da qualidade e atualização dos CSVs locais.

## Atualizar os Dados

Para atualizar a base, um usuário técnico deve substituir os CSVs em `database/`, recriar o banco e reiniciar a aplicação:

```powershell
python database/import_csv_to_sqlite.py
python app.py
```
