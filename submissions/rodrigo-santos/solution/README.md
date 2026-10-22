# Priorização de Deals

Ferramenta web que ajuda vendedores a decidir **em quais negócios focar**.
Ela lê o histórico de vendas, dá uma pontuação de 0 a 100 para cada negócio
aberto e explica, em linguagem simples, o porquê da nota e o que fazer.

```
backend/   API em Python (FastAPI + pandas): carrega os dados e calcula o score
frontend/  Tela em React + TypeScript (Vite): só exibe o que a API entrega
dados/     CSVs de origem (accounts, products, sales_pipeline, sales_teams)
```

## Como rodar

**Pré-requisito:** Python 3.10 ou mais novo (testado em 3.10, 3.12, 3.13 e 3.14).
Node.js só é necessário para alterar a tela (opção B).

Todos os comandos abaixo partem da pasta `solution/`.

### Opção A — Ver a aplicação (só Python, recomendado)

A tela já vem compilada em `frontend/dist`, e a própria API a serve.

**Windows (PowerShell ou CMD)**

```
cd backend
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python -m uvicorn app.main:app
```

**Mac / Linux**

```
cd backend
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m uvicorn app.main:app
```

Quando aparecer `Application startup complete`, abra **http://localhost:8000**.
A documentação da API fica em http://localhost:8000/docs. Para parar, use `Ctrl+C`.

> Os comandos chamam o Python de dentro do `.venv` diretamente, então não é preciso
> "ativar" o ambiente virtual (o que às vezes é bloqueado no PowerShell).

### Opção B — Desenvolver a tela (Python + Node.js 18 ou mais novo)

Deixe a API da opção A rodando e, em **outro terminal**, a partir de `solution/`:

```
cd frontend
npm install
npm run dev
```

Abra o endereço que o Vite mostrar (normalmente http://localhost:5173). As alterações no
código aparecem na hora. As chamadas `/api` são repassadas para a API na porta 8000
(ver `frontend/vite.config.ts`).

Depois de alterar a tela, rode `npm run build` para atualizar `frontend/dist`
(a versão servida na opção A).

### Testes

```
cd backend
.venv\Scripts\python -m pytest        # Windows
.venv/bin/python -m pytest             # Mac / Linux
```

### Problemas comuns

| Sintoma | Solução |
|---|---|
| `python` não é reconhecido (Windows) | Use `py` no lugar de `python` no comando que cria o `.venv`, ou instale o Python em python.org marcando "Add python.exe to PATH". |
| Erro de "Long Path" ao instalar (Windows) | O caminho da pasta ficou longo demais. Clone o repositório numa pasta curta, como `C:\projetos\`. |
| `address already in use` / porta 8000 ocupada | Outro programa usa a porta. Rode com `--port 8001` e abra http://localhost:8001. Na opção B, ajuste também a porta em `frontend/vite.config.ts`. |
| A tela mostra "Não foi possível carregar o pipeline" | A API não está rodando, ou não está na porta 8000. Veja o terminal da API. |
| http://localhost:8000 mostra `{"detail":"Not Found"}` | A pasta `frontend/dist` não existe. Rode `npm install` e `npm run build` em `frontend/` (ou use a opção B). |

## Como funciona o score

Só os negócios **abertos** (Prospecção e Em negociação) recebem nota. A lógica foi
definida **depois de testar o histórico** (ver "Validação" abaixo).

| Parte | Critério | Pontos (máx.) |
|---|---|---|
| Situação | Em negociação dentro do prazo histórico (até 138 dias): 40. Em prospecção: 20. **Parado** (aberto há mais tempo que qualquer negócio do histórico): 0. | 40 |
| Valor | Preço de tabela do produto, em escala logarítmica (de US$ 55 a US$ 26.768). Sem o log, só o produto mais caro importaria. | 40 |
| Reta final | Para negócios ativos: proporcional ao tempo aberto ÷ 138 dias. Quanto mais perto do prazo, mais urgente conduzir à decisão. | 20 |

- **Nota = soma dos pontos** (ex.: 40 + 40 + 14 = 94). A mesma conta aparece no detalhe de cada negócio.
- **Prioridade:** Alta (≥ 60), Média (≥ 40), Baixa (< 40). **Negócio parado é sempre Baixa**, com a ação "atualize ou encerre".
- **Valor esperado:** chance × valor. A chance é a taxa média da empresa (63%) para todos os negócios vivos, e 0 para os parados.
- **Principal motivo:** frase no cartão com o ponto forte (prioridade alta) ou o que segurou a nota (demais).
- **Na tela:** o botão "Como funciona a pontuação" explica as regras e mostra a evidência da validação (via `GET /api/regras` e `GET /api/validacao`).

Pontos e limites ficam em [`backend/app/config.py`](backend/app/config.py).

### Validação (backtest)

[`backend/app/servicos/validacao.py`](backend/app/servicos/validacao.py) "volta no tempo" em 4 datas de corte. Em cada
uma, calcula as estatísticas **só com negócios fechados antes do corte** (sem vazamento do futuro), pontua com a mesma
função da tela os negócios em andamento naquele dia e compara com o que aconteceu depois. Para gerar o relatório completo:

```
cd backend
.venv\Scripts\python -m app.servicos.validacao      # Windows
.venv/bin/python -m app.servicos.validacao           # Mac / Linux
```

O que a validação mostrou (relatório completo em [`../docs/validacao.md`](../docs/validacao.md)):

- **Negócios parados não voltam.** Nenhum negócio do histórico, ganho ou perdido, ficou aberto mais de 138 dias. Somando
  os cortes, 1.246 negócios já tinham passado disso, e **nenhum foi fechado depois**.
- **Nenhum atributo prevê quem ganha.** Vendedor, gerente, região, produto, setor, conta, porte, funcionários e até
  vendedor × produto ficaram com AUC entre 0,47 e 0,51 fora da amostra (0,5 = sorteio). As diferenças de taxa de
  vitória entre vendedores (55% a 70%) são compatíveis com o acaso. Por isso **a chance não entra na nota**.
- **A prioridade concentra receita.** A taxa de vitória é parecida entre as faixas, mas negócios de prioridade alta
  renderam em média **US$ 2.068** contra **US$ 159** nos de prioridade média.

> A primeira versão desta ferramenta usava chance por vendedor/produto/setor/conta (35 pts) e penalizava negócios a
> partir de 88 dias. A validação mostrou que a chance não prevê nada e que, dentro do prazo, negócios mais antigos
> ganham **mais** (63% → 76%), porque as perdas acontecem cedo. A lógica foi refeita com base nessa evidência.

### Tratamento dos dados (`backend/app/dados/carregador.py`)

- Produto `GTXPro` no pipeline é corrigido para `GTX Pro`.
- Setor `technolgy` é corrigido para `technology`.
- 1.425 negócios abertos não têm conta: aparecem como "Negócio XXXX (sem conta)".
- Negócios abertos não têm valor fechado: usamos o preço de tabela do produto.
- Os dados terminam em 31/12/2017, então essa é a data de "hoje"
  (`DATA_REFERENCIA` em `config.py`).

## Arquitetura do backend

```
app/
  main.py               cria a API e registra as rotas
  config.py             tudo que é ajustável
  esquemas.py           formato das respostas (Pydantic)
  dados/carregador.py   lê e limpa os CSVs        ← único ponto que conhece a origem dos dados
  servicos/
    estatisticas.py     taxa de vitória, prazo histórico e faixa de preços
    pontuacao.py        score, prioridade, motivos e sugestão   ← regra de negócio
    validacao.py        backtest da pontuação com o histórico
    consultas.py        filtros, resumo e conversão para a API
  rotas/                endpoints HTTP (finos, só chamam os serviços)
```

Endpoints: `GET /api/pipeline`, `GET /api/deals/{id}`, `GET /api/resumo`, `GET /api/filtros`, `GET /api/regras`, `GET /api/validacao`.
`/api/pipeline` e `/api/resumo` aceitam os filtros `vendedor`, `manager`,
`escritorio`, `produto`, `prioridade` e `busca`.

Os dados são carregados e pontuados uma vez, na subida do servidor, e ficam em memória.

## Próximos passos possíveis

- **Banco de dados:** reescrever `carregar_deals()` para ler de um banco, mantendo as colunas. O resto não muda.
- **Novos dados antes de machine learning:** com os atributos atuais, nenhum modelo vai prever vitória (a validação mostrou AUC ≈ 0,5). O ganho real viria de registrar atividades (ligações, reuniões, respostas do cliente, mudanças de etapa). Com esses dados, basta trocar o cálculo em `pontuar()` mantendo as colunas de saída e rodar `validacao.py` para comparar.
- **Rodar a validação periodicamente:** o teste `test_nenhum_atributo_preve_vitoria_melhor_que_o_acaso` avisa se, com dados novos, algum atributo passar a prever o resultado.
- **Login por vendedor:** abrir a tela já filtrada pelo vendedor logado.
- **Atualização dos dados:** hoje é preciso reiniciar o servidor para recarregar os CSVs.
