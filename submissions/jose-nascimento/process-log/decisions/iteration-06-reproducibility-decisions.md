# Decisões da Iteração 06 — Reprodutibilidade e execução em um comando

Data: 2026-08-28. Executor: agente único `deepseek-max` (via OpenCode Go).
Problema central: tornar o pipeline 01–05 executável com **1 comando** em clone
fresco e offline, com dependências mínimas documentadas e validação estrutural.

| # | Problema | Opções | Decisão | Trade-off |
|---|---|---|---|---|
| D1 | Pins de dependências: exatos vs faixas | `==3.0.5`/`==3.11.1` vs `>=X,<Y` | **Pins exatos** para `pandas` e `matplotlib` | Exato garante determinismo byte-a-byte (CSV/PNG) entre máquinas — requisito explícito da It06; faixa ampliaria compatibilidade mas arriscaria drift de bytes (ex.: pandas 2.x renderiza dtypes `object` vs `str` — ver review It01 L3). Trade-off documentado: migrar pin exige re-validar TODOS os 46 outputs e o teste de idempotência; mudança de bytes deve ser investigada, nunca normalizada silenciosamente (regra 9 do prompt) |
| D2 | `requirements.txt` tinha 6 pacotes | manter vs minimizar | **Minimizar** para `pandas` + `matplotlib` (inspeção de imports dos 5 scripts: zero imports de `duckdb`, `seaborn`, `jupyterlab`; `numpy` é transitivo do pandas/matplotlib e nunca importado diretamente — `grep np.` = 0) | Menos superfície de instalação e de drift; pip resolve `numpy` transitivamente. Documentado no próprio `requirements.txt` |
| D3 | Verificador: reimplementar análises vs validar contratos | reimplementação vs manifestos/contratos existentes | **Verificador read-only** (stdlib + pandas) que valida: manifesto de arquivos, parseabilidade, contratos **commitados** (MD5/contagens de `data/raw/README.md` e `data/processed/README.md`), invariantes estruturais **derivadas dos dados** (nenhum número de dados hardcoded; ex.: janela derivada do min/max de todas as colunas de data), gates dos próprios reports (`| FAIL | 0 |` em 01/02; ausência de `**FAIL**`/`| FAIL |` em 03–05), relações estruturais entre tabelas (t16⊆t11, t21⊆t16, t14b⊆t14, t19/t20⊆t18) | Sem duplicação de lógica analítica (risco de divergir do pipeline); verificador é um gate de higiene/estrutura, não re-deriva números de negócio |
| D4 | `clean-derived`: oferecer ou não | sem target vs lista explícita | **Oferecer com lista explícita** (41 arquivos: evidence 01–05, account_month + README processado, contrato, 26 tabelas, 6 PNGs) + guards (`01_ingest_audit.py` presente; `data/raw/` presente) | Seguro porque a lista é fechada e o pipeline regenera tudo byte-a-byte; **nunca** apaga `data/raw/` nem `process-log/` (verificado por teste). Risco residual: usuário rodar sem regenerar depois — mitigado por mensagem do target e pelo README |
| D5 | Medição de memória sem `/usr/bin/time` | não medir vs wrapper | **Wrapper python stdlib por estágio**: `resource.getrusage(RUSAGE_CHILDREN).ru_maxrss`, normalizado para KB (Linux KB; macOS bytes), rotulado "aproximação, não benchmark" | Honesto e portável; `ru_maxrss` é pico do processo filho — aproximação declarada, sem prometer benchmark universal (regra 6 do prompt) |
| D6 | `__pycache__`/artefatos de execução | aceitar vs evitar | **`PYTHONDONTWRITEBYTECODE=1`** exportado no `run.sh` e no `Makefile` | Tree limpa após regeneração (nenhum arquivo untracked); reforça a checagem D1 do verificador (zero `.pyc`) |
| D7 | Portabilidade do shell | POSIX sh vs bash | **bash** (`#!/usr/bin/env bash` + `set -euo pipefail`; `bash -n` validado) | `BASH_SOURCE`/arrays/`SECONDS` são bash; documentado no README. `shellcheck` não estava disponível no ambiente e **não foi instalado** (regra 6) — nota no report |
| D8 | Determinismo de locale/timezone | assumir vs verificar | **Verificado por inspeção**: zero `datetime.now()/today()/random/uuid` nos scripts; datas naive; formatação numérica explícita (pt-BR via `fmt_br_dec`, nunca locale do sistema) | Outputs independentes de TZ/locale; o verificador também não usa nada time-dependent |
| D9 | Paths pessoais no verificador | literal vs composto | Tokens de path pessoal **compostos em runtime** (ex.: `"/"+"tmp"`, `"ub"+"untu"`) para o verificador não casar consigo mesmo na varredura (item F2) | Auto-consistência do D2 do verificador; documentado no código |
| D10 | Gates dos reports têm formatos diferentes | padrão único vs por-formato | Verificador suporta os **dois formatos existentes**: tabela-resumo (`| Resultado | Quantidade |` em 01/02) e linhas de gate (`**PASS**`/`**FAIL**` em 03; `| PASS |` em 04/05) | Nenhum output analítico foi alterado para caber no verificador (regra 9 do prompt) — o verificador se adapta aos contratos existentes |

## Notas de implementação

- **Nenhum output analítico foi modificado** para acomodar a It06: os 46 arquivos
  de output (evidence, tabelas, PNGs, account_month, contrato) regenerados pelo
  pipeline são **byte-idênticos** aos commitados (MD5 iguais, 46/46).
- **Exceções reais encontradas no primeiro run do verificador** (corrigidas no
  verificador, nunca nos outputs): (1) reports 04/05 usam `| PASS |` sem negrito;
  (2) reports 01/02 documentam a semântica de `FAIL` em prosa e têm linha-resumo
  `| FAIL | 0 |` — a checagem passou a usar a tabela-resumo; (3) o verificador
  casava consigo mesmo na varredura de paths pessoais (D9).