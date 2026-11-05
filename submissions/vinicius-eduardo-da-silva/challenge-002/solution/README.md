# Triagem Assistida: documentação técnica

## Setup

**Para usar:** abra `app/index.html` no navegador, com dois cliques. O modelo roda na própria página, sem servidor, instalação ou envio de dados.

**Para recalcular tudo,** baixe os datasets públicos do Kaggle, a partir desta pasta (`solution/`). Eles não estão no repositório por causa do tamanho:

```bash
mkdir -p data
curl -L -o data/it.zip https://www.kaggle.com/api/v1/datasets/download/adisongoh/it-service-ticket-classification-dataset
curl -L -o data/support.zip https://www.kaggle.com/api/v1/datasets/download/suraj520/customer-support-ticket-dataset
(cd data && unzip -o it.zip && unzip -o support.zip && rm it.zip support.zip)

python -m venv .venv
.venv/Scripts/python -m pip install -r training/requirements.txt   # Linux/Mac: .venv/bin/python
cd training
../.venv/Scripts/python -m pytest -q             # testes
../.venv/Scripts/python evaluate.py              # gera results.json
../.venv/Scripts/python build_app_data.py        # gera ../app/model.js e ../app/data.js
```

**Para rodar o teste no navegador,** que exige Microsoft Edge e `pip install playwright`, a partir de `solution/`:

```bash
.venv/Scripts/python tests/ui_check.py app/index.html ../docs/screenshots
```

Testado com Python 3.12 no Windows e com o navegador Edge. Sem os dados, os testes que dependem deles são pulados.

## Organização

| Caminho | O que é |
|---|---|
| `app/` | Interface em HTML, CSS e JS puros. `model.js` e `data.js` são gerados, não edite à mão |
| `training/triage_model.py` | Separação dos dados, treino, travas e política de decisão |
| `training/evaluate.py` | Gera todos os números do protótipo e do relatório |
| `training/build_app_data.py` | Exporta o modelo e os dados para o navegador |
| `training/test_triage.py` | Testes da política e da separação dos dados |
| `tests/ui_check.py` | Teste em navegador real, incluindo a igualdade entre o modelo em JS e em Python |

## Lógica

**Modelo:** regressão logística com TF-IDF das 5.000 palavras mais frequentes. Modelos mais complexos ficaram cerca de 1 ponto à frente na validação, mas este roda no navegador e mostra as palavras que pesaram. Embeddings e LLMs não foram testados.

**Separação dos dados:** o teste usa as últimas 20% das linhas. Treino e calibração vêm das primeiras 80%. O arquivo não tem datas, então a ordem é só uma aproximação do tempo.

**Política, na ordem em que é verificada:**

| Regra | Decisão | Origem |
|---|---|---|
| Tem palavra sensível | Humano | Julgamento |
| Menos de 93,3% das palavras conhecidas | Humano | Percentil 5 da validação |
| Confiança abaixo de 50% | Humano | Julgamento |
| Categoria "Administrative rights" | Sugerir | Julgamento |
| Confiança abaixo de 90% | Sugerir | Decisão de Vinicius, depois de ver o resultado do teste |
| Demais casos | Rotear | |

## Resultado

Medido em 9.568 tickets de TI nunca vistos:

| Medida | Valor |
|---|---:|
| Acerto, divisão aleatória | 84,8% |
| Acerto, últimas 20% das linhas | 80,0% |
| Maior categoria (referência) | 45,7% |
| Roteados sozinhos | 51,7%, com 92,7% de acerto |
| Sugeridos | 37,3%, com 92,5% de acerto nas 2 primeiras opções |
| Enviados a um humano | 11,0% |
| Tickets de clientes enviados a um humano | 98,9% |

## Limitações

- **O modelo não serve hoje para tickets de clientes.** Precisa ser treinado com tickets reais antes de qualquer uso.
- **O dataset de suporte parece artificial.** Nada dele descreve uma operação real.
- **O acerto pode estar otimista.** O limite de 0,9 e as regras de julgamento foram definidos depois de ver os resultados do teste.
- **A trava mede vocabulário, não sentido.** Um ticket com palavras conhecidas e assunto novo passaria por ela.
- **A lista de palavras sensíveis é curta, fixa e em inglês.** Uma versão real precisa ser definida com RH e jurídico.
- **Os dados de TI têm rótulos imperfeitos.** Parte dos "erros" com alta confiança pode ser erro de rótulo.
- **O ROI é um cenário.** Só as taxas vêm do teste, e o restante são premissas.

## O que seria preciso para produção

1. Coletar tickets reais de clientes com a fila correta, sem dados pessoais
2. Treinar de novo e rodar em modo sombra
3. Integrar com a ferramenta de atendimento
4. Acompanhar acerto, deriva e correções de forma contínua
5. Revisar a lista de assuntos sensíveis com RH e jurídico
