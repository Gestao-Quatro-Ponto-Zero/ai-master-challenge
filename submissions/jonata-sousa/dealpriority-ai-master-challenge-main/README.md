# DealPriority

### Inteligência de priorização para operações comerciais

## Acesso rápido

**Demo online:**  
https://opportunity-focus-hub.lovable.app/auth

**Credenciais para avaliação:**  
E-mail: jonatamarinssousa@gmail.com  
Senha: Jojuan22@

> Observação: não publique senha pessoal em repositório público. Use uma senha temporária/teste para avaliação.

\---

## 1\. Visão Geral

**DealPriority** é uma ferramenta interativa de priorização comercial desenvolvida para o **Challenge 003 — Lead Scorer**, do processo seletivo de AI Master.

O produto ajuda vendedores e gestores a identificar quais oportunidades abertas merecem atenção primeiro, usando um score explicável e recomendações práticas por deal.

A entrega inclui:

* aplicação funcional;
* URL pública de demonstração;
* lógica de scoring reproduzível;
* documentação de metodologia;
* seed para recriação da base;
* evidências do processo de construção.

\---

## 2\. Problema de Negócio

Em operações comerciais com pipeline ativo, o volume de oportunidades abertas torna inviável dar atenção uniforme a todos os deals.

Sem uma lógica clara de priorização, vendedores e gestores ficam expostos a:

* investir tempo em oportunidades com baixa chance de avanço;
* deixar deals relevantes perderem cadência;
* tomar decisões com base em intuição, sem critério operacional;
* não saber onde concentrar esforço comercial no curto prazo.

\---

## 3\. Solução Proposta

A solução é uma heurística de scoring explicável, combinada com uma interface prática de uso diário.

O app permite:

* calcular um score de prioridade por oportunidade aberta;
* classificar deals em **Foco Agora**, **Nutrir** e **Baixa Prioridade**;
* explicar os fatores positivos e riscos de cada oportunidade;
* sugerir uma ação recomendada;
* filtrar por vendedor, gestor, região, produto, estágio e prioridade;
* visualizar KPIs, gráficos, tabela e detalhe por deal.

\---

## 4\. Demo Online

A aplicação publicada pode ser acessada em:

```text
https://opportunity-focus-hub.lovable.app/auth
```

Credenciais de avaliação:

```text
E-mail: jonatamarinssousa@gmail.com
Senha: \[INSERIR\_SENHA\_DE\_TESTE\_AQUI]
```

\---

## 5\. Estrutura da Entrega

```text
dealpriority-ai-master-challenge-main/
├── README.md
├── process-log.md
├── ranked\_open\_deals\_final.csv
├── data/
│   ├── raw/
│   │   ├── accounts.csv
│   │   ├── products.csv
│   │   ├── sales\_pipeline.csv
│   │   └── sales\_teams.csv
│   └── output/
│       └── ranked\_open\_deals\_final.csv
├── docs/
│   └── scoring-methodology.md
├── scripts/
│   ├── generate\_scores.py
│   └── seed\_from\_csv.py
├── supabase/
│   └── seed.sql
├── public/
├── src/
├── package.json
└── package-lock.json
```

\---

## 6\. Reprodutibilidade do Scoring

A lógica de scoring pode ser reproduzida a partir dos CSVs originais do challenge.

Arquivos esperados:

```text
data/raw/sales\_pipeline.csv
data/raw/accounts.csv
data/raw/products.csv
data/raw/sales\_teams.csv
```

Rodar:

```bash
python -m venv .venv
source .venv/bin/activate
pip install pandas numpy

python scripts/generate\_scores.py
```

Saída esperada:

```text
data/output/ranked\_open\_deals\_final.csv
```

A metodologia completa está documentada em:

```text
docs/scoring-methodology.md
```

\---

## 7\. Lógica de Scoring

### Fórmula

```text
priority\_score = 100 × (
    0.45 × stage\_weight +
    0.20 × seller\_win\_rate +
    0.15 × product\_win\_rate +
    0.10 × regional\_win\_rate +
    0.10 × manager\_win\_rate
) − aging\_penalty
```

Penalidade:

```text
-10 pontos quando aging\_risk\_flag = true
```

O score é limitado ao intervalo 0–100.

### Pesos

|Variável|Peso|Justificativa|
|-|-:|-|
|`stage\_weight`|45%|O avanço no funil é o sinal mais direto de maturidade comercial.|
|`seller\_win\_rate`|20%|Histórico do vendedor é o sinal operacional mais granular.|
|`product\_win\_rate`|15%|Produtos têm padrões diferentes de conversão.|
|`regional\_win\_rate`|10%|A região influencia o comportamento histórico de conversão.|
|`manager\_win\_rate`|10%|O gestor adiciona contexto de performance da carteira.|

### Recalibração por percentis

|Regra|Label|
|-|-|
|`priority\_score >= p85`|Foco Agora|
|`p50 <= priority\_score < p85`|Nutrir|
|`priority\_score < p50`|Baixa Prioridade|

Essa regra foi usada porque a primeira distribuição por cortes fixos não produzia uma fila operacional útil.

\---

## 8\. Explicabilidade

Cada oportunidade recebe:

* `top\_positive\_reason\_1`
* `top\_positive\_reason\_2`
* `top\_risk\_reason\_1`
* `top\_risk\_reason\_2`
* `recommended\_action`

Exemplos de ações:

* `avançar para o próximo passo hoje`
* `revisar próximos passos nesta semana e manter cadência`
* `decidir se vale recuperar ou encerrar esta semana`

\---

## 9\. Como Rodar Localmente

### Pré-requisitos

* Node.js LTS
* npm
* Python 3.10+ para reprodução do scoring

### Instalar dependências

```bash
npm install
```

### Rodar app

```bash
npm run dev
```

O Vite está configurado para a porta 8080:

```text
http://localhost:8080
```

### Build

```bash
npm run build
```

### Preview

```bash
npm run preview
```

\---

## 10\. Supabase Seed

Para recriar a tabela usada pelo dashboard a partir do CSV final:

```bash
python scripts/seed\_from\_csv.py
```

Esse comando gera:

```text
supabase/seed.sql
```

O arquivo `supabase/seed.sql` já está incluído nesta entrega e pode ser executado no SQL Editor do Supabase ou em um Postgres local.

Tabela criada:

```text
public.deals
```

\---

## 11\. Variáveis de Ambiente

Use `.env.example` como base.

```env
VITE\_SUPABASE\_URL=your\_supabase\_url
VITE\_SUPABASE\_PUBLISHABLE\_KEY=your\_supabase\_anon\_or\_publishable\_key
VITE\_SUPABASE\_PROJECT\_ID=your\_supabase\_project\_id
```

Não publique segredos privados no repositório.

\---

## 12\. Uso de IA no Processo

### ChatGPT

* escolha estratégica do challenge;
* definição do MVP;
* estruturação da lógica de scoring;
* documentação;
* revisão crítica da solução.

### Julius AI

* inspeção dos CSVs;
* identificação de chaves;
* validação dos joins;
* cálculo inicial do score;
* recalibração;
* geração da base final.

### Lovable

* criação do app;
* implementação da interface;
* filtros, KPIs, gráficos e tabela;
* autenticação;
* PWA básico.

\---

## 13\. Limitações

* A base é um snapshot estático.
* A solução não está integrada a um CRM.
* O score é heurístico, não um modelo estatístico treinado.
* A autenticação está adequada ao escopo de challenge, não a produção.
* O seed permite recriar a base, mas credenciais de ambiente devem ser configuradas pelo avaliador.

\---

## 14\. Conclusão

O DealPriority entrega uma solução funcional, explicável e reproduzível para priorização comercial.

A correção desta versão endereça os dois pontos principais da revisão:

1. scoring reproduzível com script e metodologia documentada;
2. avaliação facilitada com URL pública, setup local e seed da base.

