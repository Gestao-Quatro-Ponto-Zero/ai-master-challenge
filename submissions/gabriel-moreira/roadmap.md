# Roadmap — Lead Scorer

## O que foi construído

Ferramenta de triagem de pipeline por **valor em risco**, não por probabilidade categórica de
conversão. A evidência que sustenta essa escolha: em 6.711 negócios fechados, nenhum atributo
firmográfico isolado (vendedor, conta, setor, escritório) prevê ganho/perda — AUC ≈ 0,50, testes
de permutação com p entre 0,26 e 0,98 (ver [solution/report.md](./solution/report.md) e
[docs/architecture.md](./docs/architecture.md)).

```
PRIORIDADE = P̂ganho(produto, idade) × VALOR(produto, porte) × URGÊNCIA(idade)
CONFIANÇA  = f(conta conhecida?, etapa, idade dentro da janela observada?)   →  A | B | C | D
ESTADO     = tabela 4×2 (CONFIANÇA × SCORE)  →  Foco urgente / Acompanhar / Engajar / Qualificar / Desistir
```

Entregue: API FastAPI + frontend React com controle de acesso por papel (Sales Agent / Supervisor /
Manager, escopo real derivado de `sales_teams.csv`), validação reprodutível (`make validate`) e
suíte de testes (unitário + e2e). Stack e detalhes completos em
[docs/architecture.md](./docs/architecture.md); decisões e porquês em
[docs/decisions-log.md](./docs/decisions-log.md).

**Limitação central, já documentada:** o modelo diferencia por valor e urgência, não por
probabilidade real — `p̂` varia só entre 0,60 e 0,75 porque não existe dado comportamental nos 5
arquivos de origem. É a lacuna que os itens abaixo endereçam.

---

## Próximos passos selecionados

### 1. Saneamento em lote do funil congelado

A mediana de idade dos 2.089 negócios abertos é 165 dias — mais velha que o negócio mais longo
que já fechou na história (138 dias). 61,8% do funil (1.291 negócios) está fora de qualquer
precedente histórico, hoje classificado como **Desistir**.

- **Ação:** mutirão de revisão em lote (fechar ou descartar) guiado pela aba Desistir, com
  exportação CSV já pronta na ferramenta.
- **Esforço:** baixo — não exige nova engenharia, só operação.
- **Impacto de negócio:** o forecast reportado hoje inclui receita fantasma. Limpar o funil
  restaura a credibilidade do número que o board vê e libera atenção do vendedor para o que
  ainda tem chance real.

### 2. Persistir histórico de score

Tudo roda in-memory hoje, recalculado a cada carga — não existe série temporal por negócio.

- **Ação:** banco gerenciado (ex.: Supabase) guardando SCORE/ESTADO/CONFIANÇA por negócio a cada
  execução do pipeline.
- **Esforço:** baixo-médio — schema simples, sem mudança na lógica de scoring.
- **Impacto de negócio:** habilita trajetória ("este negócio está piorando há 3 semanas", que a
  foto do dia não mostra), auditoria de decisão, e é pré-requisito técnico direto dos itens 6, 8
  e 9 abaixo — sem histórico, nenhum deles pode ser medido ou construído.

### 3. A/B do próprio score

Metade dos vendedores prioriza pela ferramenta, metade continua no processo atual; medir receita
por trimestre entre os dois grupos.

- **Esforço:** baixo em engenharia, médio em processo (requer coordenação com liderança de
  vendas e período de espera para significância estatística).
- **Impacto de negócio:** é a evidência que compra orçamento para a fase seguinte (instrumentação
  comportamental, modelo real) e defende a ferramenta com dado quando alguém perguntar se ela
  vale o custo. Sem isso, o valor de tudo o resto fica em opinião, não em número.

### 4. Forecast probabilístico (commit vs. upside)

Somar `p̂ × valor` com intervalo de confiança, agregado por escritório e trimestre.

- **Esforço:** médio — a fórmula unitária já existe; o novo trabalho é agregação, intervalo de
  confiança e visualização por período/escritório.
- **Impacto de negócio:** muda quem compra a ferramenta internamente. Sai de "ferramenta de
  priorização do vendedor" para "instrumento de forecast do CFO/head de vendas" — patrocínio
  mais alto, orçamento maior, e uma segunda razão de existir além da fila individual.

### 5. Modelo de sobrevivência para time-to-close

As curvas de aging atuais (`risco(t)`, `p_ganho(t)`) já são metade de um modelo de sobrevivência;
falta tratar censura formalmente (hoje é um corte fixo em 138 dias) e responder diretamente
"este negócio fecha neste trimestre ou no próximo".

- **Esforço:** médio-alto — requer troca do encolhimento em degraus atual por um modelo de
  sobrevivência real (ex.: Cox, Kaplan-Meier com covariáveis) e nova validação.
- **Impacto de negócio:** responde a pergunta que gestor de vendas mais faz — alocação de esforço
  dentro do trimestre corrente — com mais precisão do que o corte binário de hoje, e melhora a
  acurácia do próprio forecast do item 8.

---
