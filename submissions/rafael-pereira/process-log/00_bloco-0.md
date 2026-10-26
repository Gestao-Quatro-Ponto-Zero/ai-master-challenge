# Bloco 0 — setup, dados e reprodução da exploração inicial

## Objetivo

Montar a estrutura da submissão (pastas, dependências, configuração do pytest), conferir os quatro CSVs brutos e reproduzir a fase 0 com os scripts originais, sem alterá-los, comparando cada número com o briefing. Nenhum código de produto foi escrito nesta etapa.

## Executor

Claude Haiku (subagente executor). Execução da especificação E1 de `process-log/plano_execucao_opus.md`, planejada pelo Claude Opus em modo somente leitura.

## O que foi feito (comandos)

1. **Leitura.** `CLAUDE.md` (já no contexto), `docs/briefing.md`, `PROMPT_AUTONOMO.md`, `process-log/00_fase0_exploracao.md` (alternativas e motivos das decisões) e os scripts `process-log/scripts/eda.py`, `eda2.py` e `snapshot.py`. Os scripts só foram lidos, não alterados.
2. **Caminhos e ferramentas.** `Test-Path` confirmou `.venv\Scripts\python.exe`, `tools\gitw.py`, `PROMPT_AUTONOMO.md` e `solution\data\raw`. Sem executar git: `Get-Command git` e `Get-Command gh` não encontraram nenhum dos dois; `msedge.exe` existe em `C:\Program Files (x86)\Microsoft\Edge\Application`.
3. **Pastas.** Criadas `solution\{data\processed, scorer, tests, app, briefs, tools}` e `process-log\{chat-exports, screenshots, outputs}`. Receberam `.gitkeep` as pastas que estavam vazias: `solution\data\processed`, `solution\scorer`, `solution\tests`, `solution\app`, `solution\briefs`, `solution\tools` e `process-log\screenshots`.
4. **Contagem dos CSVs** com `& $PY -c` (pandas): `sales_pipeline` 8800, `accounts` 85, `products` 7, `sales_teams` 35. Sem divergência, então o bloco seguiu.
5. **Arquivos de dependência.** `solution\requirements.txt` (pandas>=2.2, numpy>=1.26, scipy>=1.11, pytest>=8), `solution\requirements-dev.txt` (playwright>=1.40) e `solution\pytest.ini` (`[pytest]`, `testpaths = tests`, `pythonpath = .`, `addopts = -q`).
6. **Instalação:** `& $PY -m pip install -r "$SOL\requirements.txt"`. Todas as linhas saíram como "Requirement already satisfied"; nada foi baixado.
7. **Versões:** `& $PY --version` e `& $PY -m pip freeze`. Python 3.11.9; pandas 3.1.0; numpy 2.4.6; scipy 1.17.1; pytest 9.1.1; playwright 1.64.1; dulwich 1.2.19.
8. **Reprodução da fase 0**, com `& $PY -B` e saída em `process-log\outputs\`: `eda.py` gerou `bloco0_eda.txt` (exit 0); `eda2.py` gerou `bloco0_eda2.txt` (exit 0); `snapshot.py` gerou `bloco0_snapshot.txt` (exit 0).
9. **Conferência** com `& $PY -c` (pandas), em `process-log\outputs\bloco0_conferencia.txt` (exit 0 na segunda tentativa; ver "O que deu errado"). Conteúdo: linhas com `product=="GTXPro"` no CSV bruto e após a normalização, o join com `products`, as tabelas completas dos snapshots de 30/06 e 30/09 com `display.width` 250 e `max_columns` 30, e a concentração exata da receita ganha.
10. **Documentos.** `docs\DECISIONS.md` (14 linhas), `process-log\chat-exports\LEIA-ME.md` e este log.
11. **Verificações finais.** `Test-Path` de todas as pastas e arquivos da E1; `Select-String` em `DECISIONS.md`; tamanhos dos outputs; `& $PY -m pytest -p no:cacheprovider` em `solution` (exit 5, "no tests ran", esperado neste bloco); `& $PY "$PM\tools\gitw.py" status`.
    - `scorer.docs` não foi rodado: o módulo só existe a partir do bloco 2.
    - `-p no:cacheprovider` evita criar `.pytest_cache` dentro da submissão.

## Resultados

Todos os números abaixo saem dos arquivos citados, que estão em `process-log\outputs\`.

| Item | Briefing | Reproduzido | Arquivo |
|---|---|---|---|
| Deals no pipeline | 8.800 | 8.800 (SHAPE (8800, 8)); CSV com 8800 linhas | bloco0_eda.txt; contagem por `-c` |
| Won / Lost / Engaging / Prospecting | 4.238 / 2.473 / 1.589 / 500 | 4.238 / 2.473 / 1.589 / 500 | bloco0_eda.txt (STAGES) |
| Win rate dos fechados | 63,2% | 0,632 (n fechados 6.711) | bloco0_eda.txt (OVERALL) |
| Linhas "GTXPro" | 1.480 perdidas no join | 1.480 no bruto; 0 após normalização; join mantém 8.800 | bloco0_conferencia.txt |
| Produto fora do catálogo | "GTXPro" | ['GTXPro'] | bloco0_eda.txt (PRODUCT names) |
| Setor "technolgy" | presente | 12 contas; 1.058 deals | bloco0_eda.txt (accounts sectors; WIN RATE by sector) |
| Deals sem conta | 1.425 (1.088 Engaging + 337 Prospecting) | 1.425; 1.088; 337 | bloco0_eda.txt (NULLS; stage vs null dates) |
| Prospecting sem `engage_date` | 500 | 500 | bloco0_eda.txt (NULLS) |
| Win rate por produto | 60% a 65% | 0,603 a 0,648 | bloco0_eda.txt (WIN RATE by product) |
| Qui-quadrado de produto | p=0,37 | 0,3719 | bloco0_eda2.txt |
| Qui-quadrado de vendedor | p=0,26 | 0,2639 | bloco0_eda2.txt |
| Vendedores: cadastro / com deals / sem deals | 35 / 30 / 5 | 35 / 30 / 5 (Carl Lin, Carol Thompson, Elizabeth Anderson, Mei-Mei Johns, Natalya Ivanova) | bloco0_eda2.txt (linha 1) |
| Correlação H1 x H2 dos vendedores | 0,57 | 0,573 | bloco0_eda2.txt |
| AUC das numéricas (preço, receita, funcionários, ano) | ≈ 0,50 | 0,493 a 0,498 | bloco0_eda.txt (Single-feature AUC) |
| AUC do ciclo | 0,58 | 0,578 | bloco0_eda.txt |
| Mediana do ciclo: perdido / ganho | 14 / 57 dias | 14,0 / 57,0 | bloco0_eda.txt (CYCLE DAYS) |
| Perdidos em até 14 dias | 1.249 de 2.473 | 657 + 592 = 1.249 de 2.473 | bloco0_eda2.txt (Lost cycle hist) |
| Ciclo máximo entre fechados | 138; nenhum acima | 138; 0 acima | bloco0_eda2.txt; bloco0_snapshot.txt |
| Engaging acima de 138 dias (em 31/12) | 1.291 (0,812) | 1.291 (0,812) | bloco0_eda2.txt (linha 3) |
| Valor de tabela desses Engaging | 3.198.664 de 3.892.229 | 3.198.664 de 3.892.229 | bloco0_eda2.txt (linha 3) |
| Faixas de idade em 31/12: até 90 / 91–138 / acima de 138 | 110 / 188 / 1.291 | 110 (18 + 39 + 53) / 188 / 1.291 (642 + 411 + 238) | bloco0_eda2.txt (age buckets) |
| Valor de Prospecting | ≈ US$ 1,07 mi | 1.073.986 | bloco0_eda2.txt (prospecting value) |
| Win rate com fechamento no 1º trimestre de 2017 | 82% | 0,821 (n = 647) | bloco0_eda.txt (WIN RATE by close quarter) |
| close_value / preço de tabela (Won) | média 100%; 66% a 134% | média 0,996; mín 0,657; máx 1,342 | bloco0_eda.txt |
| Concentração da receita ganha (top 3) | 35% + 26% + 22% = 83% | 0,3509 + 0,2628 + 0,2215 = 0,8352 (83,5%) | bloco0_conferencia.txt; ver divergência 1 |
| MG Special, participação na receita | 0,4% | 0,0044 | bloco0_conferencia.txt |
| Snapshot 30/09, % ganhos (até 30 / 31–60 / 61–90 / 91–138 / acima de 138) | 50% / 34% / 7% / 0% / 0% | 0,502 / 0,343 / 0,067 / 0,000 / 0,000 (mais a faixa 138–200 e a acima de 200, ambas 0,000) | bloco0_snapshot.txt; bloco0_conferencia.txt; ver observação 2 |
| Snapshot 30/09, % ainda abertos no fim | 16% / 45% / 86% / 99% / 100% | 0,162 / 0,451 / 0,859 / 0,990 / 1,000 | bloco0_conferencia.txt |
| Snapshot 30/06, % ganhos (até 30 / 31–60 / 61–90 / 91–138) | 53% / 45% / 22% / 0% | 0,529 / 0,445 / 0,216 / 0,000 | bloco0_snapshot.txt; bloco0_conferencia.txt |
| Deals abertos nos snapshots | não citado | 30/06: 1.686; 30/09: 2.409 | bloco0_conferencia.txt |
| Período de engajamento | out/2016 a dez/2017 | 2016-10-20 a 2017-12-27 | bloco0_eda.txt (date ranges) |
| Período de fechamento | mar/2017 a 31/12/2017 | 2017-03-01 a 2017-12-31 | bloco0_eda.txt (date ranges) |

**Divergências**

1. **Concentração do top 3.** O briefing diz 83%. A conta exata dá 0,8352, ou 83,5%, que arredondado ao inteiro vira 84%. É diferença de arredondamento, não de dado. Não editei o briefing, que está fora do escopo deste bloco. Nas docs, o número deve sair de script (83,5% ou 84%, com a regra de arredondamento explícita).
2. **Lista de faixas dos snapshots.** O plano citava 5 valores para o snapshot de 30/09 e 4 para o de 30/06. Os scripts usam 6 faixas (cortes em 30, 60, 90, 138, 200 e 1000 dias). As faixas acima de 90 dias dão 0,000 nos dois cortes, o que bate com o briefing ("0%" para 91–138 e para acima de 138). A diferença está só em como as faixas são listadas.
3. **Idade no eda.py e no eda2.py.** O `eda.py` mede a idade até 27/12/2017, que é o maior `engage_date`. O `eda2.py` mede até 31/12/2017. Por isso a idade média de Engaging aparece como 194,8 no eda.py e 199,0 no eda2.py. As faixas do briefing (110 / 188 / 1.291) são as de 31/12, reproduzidas pelo eda2.
4. **Truncamento do snapshot.** O `snapshot.py` trunca colunas na impressão (as colunas `won` e `n` ficam ocultas por `...`). A tabela completa, com `display.width` 250, está em `bloco0_conferencia.txt`.

**Nenhuma outra divergência** nos itens que a E1 pedia para conferir: win rate 0,632, 5 vendedores sem deals, 1.291 Engaging acima de 138 dias (0,812; 3.198.664 de 3.892.229) e os snapshots de 30/09 e 30/06.

## Autoverificação do checkpoint

Critérios "Pronto quando" da E1, conferidos depois que todos os arquivos do bloco estavam criados:

- [x] `Test-Path` é verdadeiro para todas as pastas e arquivos listados (`solution\data\processed`, `scorer`, `tests`, `app`, `briefs`, `tools`; `process-log\chat-exports`, `screenshots`, `outputs`; `requirements.txt`, `requirements-dev.txt`, `pytest.ini`; os 4 `bloco0_*.txt`; `chat-exports\LEIA-ME.md`; `docs\DECISIONS.md`).
- [x] `(Select-String -Path DECISIONS.md -Pattern '^\| 2026').Count` = 14, com o mínimo de 14.
- [x] Os 4 arquivos em `process-log\outputs` existem e não estão vazios: `bloco0_eda.txt` (9.088 bytes), `bloco0_eda2.txt` (1.780), `bloco0_snapshot.txt` (1.787) e `bloco0_conferencia.txt` (2.140).
- [x] `& $PY "$PM\tools\gitw.py" status` termina com "FORA da pasta da submissão: nada". Ele também mostra `untracked (não ignorados): 0`, porque o `.gitignore` do repositório ignora `submissions/`; os arquivos novos só entram no commit com `git add -f`.

Checagens extras:

- `pip install` com todas as dependências "already satisfied".
- `pytest` saiu com código 5 ("no tests ran"). Esperado, porque o bloco 0 não tem testes. O bloco comum manda rodar pytest antes de terminar, e o código 5 é o resultado real.
- Nenhum `__pycache__` foi criado em `process-log\scripts` (uso de `-B`).

## O que deu errado / iterações

1. **SyntaxError na conferência (1ª tentativa).** O código do `-c` tinha um `for` depois de `;` na mesma linha. Resultado: `SyntaxError: invalid syntax`, exit 1, e o arquivo de saída ficou vazio. Hipótese: `for` é instrução composta e não pode vir depois de `;`. A mensagem do Python confirmou. Correção: mesmo código, com quebras de linha reais. Depois: exit 0 e 2.140 bytes. A 2ª execução sobrescreveu o arquivo vazio.
2. **Nenhum erro** no `pip install`, nas três execuções da fase 0 (exit 0 em todas) nem nas verificações de caminhos.

## Decisões

Quatorze linhas em `docs/DECISIONS.md`, com data e alternativa descartada para cada uma:

- 7 da fase 0 (`2026-10-25 (fase 0)`), com o texto prefixado por "Fase 0 (kit do Rafael) —". Alternativas e motivos vêm do CLAUDE.md, do briefing e do `00_fase0_exploracao.md`. Exceção: o item de idioma. A alternativa "inglês" não aparece na fase 0; registrei como "não discutida na fase 0", sem atribuir nada ao Rafael.
- 6 de setup do orquestrador, com o sufixo "(decisão autônoma do Claude)". Verificadas nesta execução: `git` e `gh` ausentes (`Get-Command`); `dulwich==1.2.19` no `pip freeze`; `msedge.exe` presente; venv fora do repositório. Não verificado: o uso do Edge pelo Playwright, que só acontece no bloco 4.
- 1 atribuída ao pedido do Rafael em `PROMPT_AUTONOMO.md`, seção 3: checkpoints "espere meu ok" viram autoverificações registradas no log.

## Nota do orquestrador (Claude Opus 5.5, sessão principal) — setup feito antes da E1

O que aconteceu antes de o executor começar, em ordem:

1. **Ferramentas.** `gh auth status`, `git --version`, `node --version` e `py --version` falharam com "termo não reconhecido". Uma busca por `git.exe` em `%LOCALAPPDATA%`, `Program Files` e `%APPDATA%` (profundidade 6) não achou nada. Só existe `python` (3.11.9, da Microsoft Store), sem pandas.
2. **venv** em `<pasta-mãe>\.venv` com pandas, numpy, scipy, pytest, playwright e dulwich.
3. **Clone** do repositório original com `dulwich clone https://github.com/Gestao-Quatro-Ponto-Zero/ai-master-challenge.git`. Branch `submission/rafael-pereira` criada a partir de `main` (4aed364d) e definida como HEAD.
4. **Cópia** do kit (`kit-lead-scorer/*`) para `submissions/rafael-pereira/` e dos 4 CSVs para `solution/data/raw/`. O `metadata.csv` não foi copiado, porque é só o dicionário de dados e o pedido citava 4 CSVs.
5. **Helper `tools/gitw.py`**, fora do repositório. Faz o equivalente a `git add -f submissions/rafael-pereira` + commit (autor Rafael Pereira, com trailer `Co-Authored-By: Claude`), e o `status` alerta sobre qualquer mudança fora da pasta.
6. **Playwright + Edge:** testado no setup com `chromium.launch(channel="msedge", headless=True)`, que renderizou uma página de teste (Edge 156.0.4314.42). Isso resolve a pendência "uso do Edge não testado" acima. A verificação completa da página continua no bloco 4.
7. **Reprodução da fase 0 antes do plano:** o orquestrador rodou `eda2.py` e `snapshot.py` e notou que, no corte de 30/06, nenhum dos 201 deals com 90 a 138 dias fechou depois (nem ganho, nem perda). Isso foi passado ao planejador Opus como sinal de artefato do gerador.
8. **Planejamento:** um subagente Claude Opus 5.5, somente leitura, gerou o plano salvo em `process-log/plano_execucao_opus.md` (equivalente ao Plan Mode). Os blocos são executados por subagentes Haiku/Sonnet e verificados pelo orquestrador antes de cada commit.

**Divergência 1 (83% × 83,5%):** fica decidido que as docs citam o número gerado por script com 1 casa (83,5%). O briefing, que é insumo da fase 0, não é editado.

## Pendências

- O commit do bloco 0 é feito pelo orquestrador, com a mensagem "bloco 0: setup, dados e reprodução da exploração inicial". Não rodei git nem `gitw.py commit`.
- Os arquivos novos estão ignorados pelo `.gitignore`: o commit precisa de `git add -f submissions/rafael-pereira/...`.
- O briefing diz 83% para a concentração do top 3; o número reproduzido é 83,5%. Decidir a forma de citação no bloco 1 (SCOPE) e no bloco 2 (DATA_QUALITY).
- O uso do Edge pelo Playwright (`channel="msedge"`) ainda não foi testado; fica para o bloco 4.
- Próximo: bloco 1 (E2), escopo e as 4 perguntas do briefing.
