# Solução — Lead Scorer

Para o revisor técnico. Visão de negócio e resultados: [../README.md](https://github.com/DiegoAlves-data/ai-master-challenge/blob/submission/diego-rodrigues/submissions/diego-rodrigues/README.md).

Motor determinístico em Python (pandas) que lê os quatro CSVs do CRM, aprende a janela de decisão e a tabela de destino do histórico, e entrega uma fila por vendedor com explicação por negócio. O front é estático e só lê JSON.

## Requisitos

Python 3.11 ou superior (testado em 3.14.7). `requirements.txt` traz pandas e pytest. `requirements-ia.txt` traz o cliente da Anthropic, usado só pelo módulo opcional `ia/`.

```bash
cd submissions/diego-rodrigues/solution
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt -r requirements-ia.txt
```

## Estrutura

| Caminho | Papel |
|---|---|
| `data/` | Os quatro CSVs do desafio (licença CC0) e `metadata.csv` |
| `motor/carregar.py` | Carga com procedência e relatório de qualidade; `recortar` apaga o futuro |
| `motor/janela.py` | Janela de validade: ciclo máximo aprendido e prazo do trimestre |
| `motor/aprender.py` | Tabela de destino por faixa de duração, com censura |
| `motor/pontuar.py` | Quatro filas (fechar, preparar, iniciar, encerrar), ordem e índice |
| `motor/explicar.py` | Cartões Valor, Momento e Prazo, e a lista "o que não sei" |
| `avaliacao/` | Backtest, permutação de atributos e `numeros.py` (fonte única dos números) |
| `build.py` | Gera `app/data/` a partir de `data/` |
| `run.py` | Build, briefings opcionais e servidor local |
| `drift.py` | Confere se a janela aprendida ainda vale para um novo export |
| `ia/` | Briefing com validador; **desligado** nesta entrega |
| `app/` | Front estático (HTML, JS, CSS) e os JSON gerados |
| `config.json`, `janela.json` | Parâmetros e janela aprendida |

Fluxo: `carregar` → `recortar` → `janela` e `aprender` → `pontuar` → `explicar` → `build.py` → `app/data/*.json` → front. O front não contém regra de negócio; campos do contrato em [../docs/contrato.md](https://github.com/DiegoAlves-data/ai-master-challenge/blob/submission/diego-rodrigues/submissions/diego-rodrigues/docs/contrato.md).

## Comandos

Todos de dentro de `solution/`.

```bash
python -m pytest -q                        # 68 testes, cerca de 90 s
python build.py --hoje 2018-01-01          # regera app/data/ (determinístico, imprime o hash)
python run.py --hoje 2018-01-01 --sem-ia   # build + servidor em http://localhost:8000
python -m avaliacao.numeros                # backtest, permutação e todos os números citados
python drift.py                            # compara a janela aprendida com um novo export
```

Sem o cliente da Anthropic instalado, rode o núcleo (52 testes, sem chave de API):

```bash
python -m pytest -q --ignore=tests/test_briefing.py --ignore=tests/test_gerar_ia.py --ignore=tests/test_validar.py
```

## Artefatos gerados

`build.py` grava em `app/data/`: `scored.json` (negócios, filas, vendedores, tabela de destino), `qualidade.json`, `eval.json` (resultado da avaliação), `briefings.json` e `hash.txt`. O mesmo dado gera os mesmos bytes e o mesmo hash. `python -m avaliacao.numeros` imprime os números com rótulo e fonte e regrava `eval.json`; a saída de referência está em [../docs/numeros-saida.txt](https://github.com/DiegoAlves-data/ai-master-challenge/blob/submission/diego-rodrigues/submissions/diego-rodrigues/docs/numeros-saida.txt).

## Como reproduzir os números

Os resultados desta versão foram conferidos em ambiente limpo, nesta ordem: 68 testes passando; `build.py --hoje 2018-01-01` sem diferença em `app/data/`, com hash `1d22a7f4…eeae20`, igual ao publicado; `python -m avaliacao.numeros` com saída idêntica a `docs/numeros-saida.txt`; `drift.py` sem desvio. Um segundo cálculo, com código próprio e sem importar este motor, está em [../process-log/verificacao/](https://github.com/DiegoAlves-data/ai-master-challenge/tree/submission/diego-rodrigues/submissions/diego-rodrigues/process-log/verificacao).

## Módulo de IA (opcional)

`ia/briefing.py` gera o texto de abertura de cada vendedor com o Haiku 5.5, e `ia/validar.py` recusa qualquer texto cujos números não batam com os fatos, caindo para o modelo fixo. A chave `ANTHROPIC_API_KEY` fica só no ambiente do build e nunca vai ao navegador. **Nesta entrega a IA não está ligada:** a conta da API não tinha créditos e a primeira chamada foi recusada, então `--sem-ia` é o caminho documentado. O caminho crítico do score não depende de IA. Requisitos para ligar em produção: [../docs/deploy-passos.md](https://github.com/DiegoAlves-data/ai-master-challenge/blob/submission/diego-rodrigues/submissions/diego-rodrigues/docs/deploy-passos.md).

## Solução de problemas

- **`ModuleNotFoundError: anthropic` ao rodar o pytest:** instale `requirements-ia.txt` ou use o comando de 52 testes acima.
- **`run.py` recusa sem `--hoje`:** é proposital; em produção a data é a real, e a demo usa 2018-01-01.
- **Porta ocupada:** `python run.py --port 8001 --hoje 2018-01-01 --sem-ia`.

## Segurança e decisões técnicas

Sem chave no repositório nem no front; a demo pública não faz chamadas externas. Sem login: qualquer pessoa com o endereço vê os dados de todos os vendedores, aceitável para dados fictícios e inaceitável em operação real. A janela e a tabela são aprendidas do histórico e `recortar` é a única entrada do dado, igual em produção e no backtest, para que o futuro não vaze. Parâmetros em `config.json`; limites completos em [../docs/limitacoes.md](https://github.com/DiegoAlves-data/ai-master-challenge/blob/submission/diego-rodrigues/submissions/diego-rodrigues/docs/limitacoes.md).
