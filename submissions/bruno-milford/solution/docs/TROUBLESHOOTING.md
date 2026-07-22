# Solução de Problemas

## Python não é reconhecido

| Item | Detalhe |
| --- | --- |
| Sintoma | `python : O termo 'python' não é reconhecido`. |
| Possível causa | Python não instalado ou fora do PATH. |
| Correção | Instale Python 3.11+ e habilite PATH. No Windows, teste `py --version` se disponível. |

Diagnóstico:

```powershell
python --version
where python
```

## Ambiente virtual não ativa

| Item | Detalhe |
| --- | --- |
| Sintoma | Dependências não encontradas mesmo após instalação. |
| Possível causa | `.venv` não foi ativado. |
| Correção | Ative o ambiente antes de instalar/rodar. |

Windows:

```powershell
.\.venv\Scripts\Activate.ps1
```

Linux/macOS:

```bash
source .venv/bin/activate
```

## Política do PowerShell bloqueia ativação

| Item | Detalhe |
| --- | --- |
| Sintoma | `running scripts is disabled on this system`. |
| Possível causa | Política de execução restritiva. |
| Correção | Para a sessão atual, execute o comando abaixo e ative novamente. |

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

## Dependência ausente

| Item | Detalhe |
| --- | --- |
| Sintoma | `ModuleNotFoundError: No module named 'flask'` ou `pandas`. |
| Possível causa | Dependências não instaladas no ambiente ativo. |
| Correção | Instale pelo arquivo oficial do projeto. |

```powershell
pip install -r requirements.txt
```

## Banco SQLite não encontrado

| Item | Detalhe |
| --- | --- |
| Sintoma | `Banco SQLite nao encontrado. Esperado em database/ravenstack.db.` |
| Possível causa | Banco ausente, removido ou caminho incorreto. |
| Correção | Recrie o banco a partir dos CSVs. |

```powershell
python database/import_csv_to_sqlite.py
```

## Tabelas ausentes no SQLite

| Item | Detalhe |
| --- | --- |
| Sintoma | `Tabelas ausentes no SQLite: ...`. |
| Possível causa | Importação incompleta ou CSVs com nomes diferentes do esperado. |
| Correção | Confirme os CSVs em `database/` e reimporte. |

Arquivos esperados:

```text
database/ravenstack_accounts.csv
database/ravenstack_subscriptions.csv
database/ravenstack_feature_usage.csv
database/ravenstack_support_tickets.csv
database/ravenstack_churn_events.csv
```

## CSV não encontrado

| Item | Detalhe |
| --- | --- |
| Sintoma | O importador informa que nenhum CSV foi encontrado. |
| Possível causa | Arquivos fora de `database/` ou extensão incorreta. |
| Correção | Coloque os CSVs na pasta `database/` com extensão `.csv`. |

## Coluna obrigatória ausente

| Item | Detalhe |
| --- | --- |
| Sintoma | Erro SQL como `no such column: account_id`. |
| Possível causa | CSV sem coluna usada pelas consultas. |
| Correção | Compare o CSV com `docs/DATA_DICTIONARY.md` e ajuste o cabeçalho. |

## Erro de encoding no CSV

| Item | Detalhe |
| --- | --- |
| Sintoma | Falha ao ler arquivo ou caracteres quebrados. |
| Possível causa | Encoding fora de `utf-8-sig`, `utf-8`, `latin-1` ou `cp1252`. |
| Correção | Regrave o CSV em UTF-8 ou ajuste o script se uma nova codificação for necessária. |

## Banco SQLite bloqueado

| Item | Detalhe |
| --- | --- |
| Sintoma | `database is locked`. |
| Possível causa | Banco aberto por outro processo durante importação. |
| Correção | Pare o Flask, feche ferramentas SQLite e rode a importação novamente. |

## Porta 5000 ocupada

| Item | Detalhe |
| --- | --- |
| Sintoma | Flask informa que o endereço já está em uso. |
| Possível causa | Outro processo usando `127.0.0.1:5000`. |
| Correção | Encerre o processo ou altere temporariamente a porta em `app.py`. |

Diagnóstico no Windows:

```powershell
netstat -ano | findstr :5000
```

## API retorna filtro inválido

| Item | Detalhe |
| --- | --- |
| Sintoma | HTTP 400 com `Filtros invalidos`. |
| Possível causa | Query string com parâmetro não permitido. |
| Correção | Use apenas filtros aceitos no README. |

## Dashboard sem dados

| Item | Detalhe |
| --- | --- |
| Sintoma | KPIs vazios ou mensagem de erro. |
| Possível causa | Banco não carregado, tabelas vazias ou filtros muito restritivos. |
| Correção | Verifique o banco, limpe filtros e teste `/api/health`. |

```powershell
python database/check_database.py
```

```text
http://127.0.0.1:5000/api/health
```

## Gráficos não carregam

| Item | Detalhe |
| --- | --- |
| Sintoma | Gráficos Plotly não aparecem como interativos. |
| Possível causa | CDN do Plotly indisponível ou sem internet. |
| Correção | A aplicação possui fallback visual. Para gráficos Plotly completos, habilite acesso ao CDN. |

## Conta não encontrada

| Item | Detalhe |
| --- | --- |
| Sintoma | `/api/accounts/<id>` retorna 404. |
| Possível causa | `account_id` não existe ou foi digitado incorretamente. |
| Correção | Pesquise a conta em `/accounts` e abra pelo botão `Ver detalhes`. |

## Modelo preditivo não encontrado

| Item | Detalhe |
| --- | --- |
| Sintoma | Não há comando de treinamento ou arquivo de modelo. |
| Possível causa | O projeto não implementa ML preditivo. |
| Correção | Use o score heurístico documentado em `docs/MODEL.md`. |

## Comandos úteis de validação

```powershell
python database/check_database.py
python -m unittest discover -s tests
python app.py
```
