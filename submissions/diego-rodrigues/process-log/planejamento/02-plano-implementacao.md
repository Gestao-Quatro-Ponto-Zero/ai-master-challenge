# Lead Scorer (Challenge 003) · Plano de implementação v2

> **Para quem executa com agente:** SUB-SKILL OBRIGATÓRIA — use `superpowers:subagent-driven-development` (recomendado) ou `superpowers:executing-plans` para implementar tarefa por tarefa. Os passos usam caixas (`- [ ]`) para acompanhamento.
>
> **v2 de 11/11/2026.** Reescrito depois da revisão técnica em [03-revisao-tecnica.md](https://github.com/DiegoAlves-data/ai-master-challenge/blob/submission/diego-rodrigues/submissions/diego-rodrigues/process-log/planejamento/03-revisao-tecnica.md), que conferiu o v1 contra o dataset e achou seis números pinados errados, um viés de sobrevivência na tabela de probabilidade, a ausência do prazo do trimestre, uma métrica de sucesso que mede mistura de preço e um piloto sem poder estatístico. Leia a revisão antes da primeira tarefa: ela explica **por que** cada decisão abaixo é o que é. O v1 está em `archives/02-plano-implementacao-v1.md`.

**Goal:** Entregar em 11/11/2026 o PR `[Submission] Diego Rodrigues — Challenge 003` com uma ferramenta de priorização de deals que roda com um comando, tem URL pública, score cujo ganho sobre a melhor alternativa honesta é medido com intervalo de confiança, discovery ensaiado com premissas pré-registradas, briefing por IA validado, kit de deploy e registro de processo auditável.

**Architecture:** Motor Python determinístico (pandas) com três fronteiras: `recortar` (única porta de entrada, apaga o futuro), `aprender` (histórico conhecido → janela de validade + tabela de destino por faixa de idade, lida das datas análogas de trimestres anteriores) e `pontuar` (tabela + deals abertos → fila, ordem, índice, explicação). `build.py` grava JSON em `app/data/`; o front estático lê os JSON e não tem regra de negócio; `run.py` serve local e grava ações; a Vercel serve a demo somente leitura. O backtest chama exatamente o mesmo motor com `hoje` no passado. A camada LLM gera briefings no build, com validador determinístico e fallback por template.

**Tech Stack:** Python 3.12+ (compatível com 3.9), pandas, pytest, `http.server` (stdlib), `anthropic` (opcional, só no build), HTML/CSS/JS sem framework, Vercel CLI.

**Spec:** `01-guia-fde.md` (seções 4 a 8 e 10; os números das seções 3, 3.4 e 8 estão corrigidos pela errata no fim do guia), [03-revisao-tecnica.md](https://github.com/DiegoAlves-data/ai-master-challenge/blob/submission/diego-rodrigues/submissions/diego-rodrigues/process-log/planejamento/03-revisao-tecnica.md) e `04-discovery-personas.md` (protocolo e roteiro da Tarefa 0B). Evidência: `analise/eda-04`, `eda-05` e `eda-06`, com as saídas `.saida.txt`.

## Global Constraints

- Tudo dentro de `submissions/diego-rodrigues/` no fork `DiegoAlves-data/ai-master-challenge`, branch `submission/diego-rodrigues`. Nenhum arquivo fora dessa pasta. Caminhos abaixo são relativos a `submissions/diego-rodrigues/`.
- **`submissions/` está no `.gitignore` do repositório oficial.** Todo `git add` desta pasta usa `-f`.
- Dependências do motor: só `pandas`. `anthropic` é opcional e só para `ia/briefing.py`. Front sem framework.
- Código, docs, commits e interface em português. Nomes de função em português, `snake_case`.
- Nenhuma regra de negócio no front: o JS lê JSON e exibe.
- **Nenhum limiar de fase escrito à mão.** A janela de validade (`ciclo_max`, regra do trimestre) e a tabela de destino por faixa são **aprendidas** do histórico conhecido na data. O que vive em `solution/config.json` é escolha de operação, não leitura dos dados: `horizonte_dias: 28`, `foco_por_vendedor: 5`, `p_decide_min: 0.05`, `bordas_faixa: [15,30,45,60,75,90,105,120]`, `n_min_faixa: 30`, `tolerancia_prazo_trimestre: 0.001`, `min_fechamentos_para_prazo: 500`, `semente: 7`, `hoje: null`.
- **`hoje` é parâmetro obrigatório de `aprender` e `pontuar`.** `null` em config significa "o `run.py` resolve e imprime"; o motor nunca inventa uma data.
- O motor nunca recebe coluna de desfecho futuro: `recortar(dados, hoje)` é a única porta de entrada, usada igual em produção e no backtest.
- Produto: `GTXPro` do pipeline casa com `GTX Pro` do catálogo comparando sem espaços e sem caixa. A tela mostra o nome do catálogo e guarda o apelido em `qualidade.json`. Setor `technolgy` vira `technology`; país `Philipines` vira `Philippines`.
- Nenhum número no README, na tela ou nos docs sem sair de `solution/avaliacao/numeros.py`. Toda razão entre políticas vem acompanhada do IC 95% por bootstrap de vendedor, semente 7, 5.000 reamostras.
- Ao fim de cada tarefa: commit com mensagem narrativa e uma entrada em `process-log/diario.md` pelo comando `registro-ia` (Tarefa 0).

## Review Focus

Cinco classes de entrada que a especificação implica e que nenhum teste de tarefa exercitaria por acaso. Cada uma tem seu teste na tarefa que é dona do código.

1. **Deal que fecha depois do corte** (no backtest) tem de chegar ao motor como aberto, nunca como decidido, e a saída de uma data não pode mudar quando o futuro muda. Teste na Tarefa 1 (`test_recortar_nao_vaza_futuro`, `test_pontuacao_independe_do_futuro`).
2. **Faixa de idade com poucas observações** não pode virar probabilidade: faixa com menos de `n_min_faixa` é agrupada com a vizinha e, se não houver observação nenhuma, a chance é 0 com motivo registrado, não `NaN` na tela. Teste na Tarefa 3 (`test_faixa_rala_e_agrupada`).
3. **Vendedor do cadastro sem nenhum deal** (5 casos reais) aparece na tela do time com estado vazio e carga de referência, e nunca divide por zero. Teste nas Tarefas 4 e 5 (`test_vendedor_sem_deal`).
4. **Produto do pipeline sem par no catálogo** (nome novo num export futuro) vai para `qualidade.json`, recebe valor 0 e fila `iniciar`, e não derruba o build. Teste na Tarefa 1 (`test_produto_desconhecido_vai_para_qualidade`).
5. **Briefing com número que não está nos fatos** é recusado e substituído pelo template; **POST `/acao` com JSON inválido ou `opportunity_id` inexistente** responde 400 e não grava. Testes nas Tarefas 9 e 10.

---

### Tarefa 0: Fork, estrutura, procedência dos dados, baseline e registro de IA

**Files:**
- Create: `README.md` (cópia de `templates/submission-template.md`, campos de nome, LinkedIn e challenge 003 preenchidos)
- Create: `solution/{motor,ia,avaliacao,app,tests}/.gitkeep`, `docs/.gitkeep`, `process-log/{prompts,screenshots,baseline,verificacao}/.gitkeep`
- Create: `solution/data/` com os 4 CSVs de `g4-challenge-003/dados/` (sem `metadata.csv`), `solution/data/FONTE.md`, `solution/data/SHA256SUMS`
- Create: `solution/requirements.txt` (`pandas>=2.0`, `pytest>=8`), `solution/requirements-ia.txt` (`anthropic>=0.40`)
- Create: `solution/config.json` com os valores de Global Constraints
- Create: `solution/.gitignore` (`.venv/`, `__pycache__/`, `.vercel/`, `app/data/acoes.jsonl`, `.env`)
- Create: `process-log/diario.md`, `process-log/baseline/{prompt.md,claude.md,outro-modelo.md,critica.md}`, `process-log/REGISTRO.md`

**Interfaces:**
- Produces: a estrutura que todas as outras tarefas assumem, e o comando `registro-ia` do kit (ver `.claude/skills/registro-ia/` no AIS-OS) instalado em `process-log/`.

- [ ] **Step 1: Fork e branch**

```bash
gh repo fork Gestao-Quatro-Ponto-Zero/ai-master-challenge --clone --remote -- ~/Documents/ai-master-challenge
cd ~/Documents/ai-master-challenge && git checkout -b submission/diego-rodrigues
```
Expected: `git remote -v` mostra `origin` (fork) e `upstream`.

- [ ] **Step 2: Estrutura, venv e procedência**

```bash
cd submissions/diego-rodrigues/solution && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
shasum -a 256 data/*.csv > data/SHA256SUMS
```
`data/FONTE.md`: URL do dataset no Kaggle, licença CC0, data do download, e a frase de que os quatro CSVs no repositório são cópia literal conferível pelo `SHA256SUMS`.

- [ ] **Step 3: Instalar o kit de registro de IA**

Copiar `.claude/skills/registro-ia/template/` (do AIS-OS) para `process-log/`, que traz `REGISTRO.md`, `registrar.py` e `MODELOS.md`. Rodar `python3 process-log/registrar.py --inicio "Tarefa 0"` e conferir que `diario.md` ganhou a entrada com data, hora, modelo e tarefa.

- [ ] **Step 4: Baseline**

Colar o README do challenge 003 (sem dados) em dois modelos de famílias diferentes, sem ferramentas. Salvar as respostas íntegras em `baseline/`. Em `critica.md`, listar o que cada baseline faz e o que o dado desmente: pesos para setor, porte e vendedor (AUC ~0,5); nenhum teste; nenhum zumbi; nenhuma noção de janela de decisão; métrica inventada.

- [ ] **Step 5: Commit**

```bash
git add -f submissions/diego-rodrigues
git commit -m "chore(003): estrutura, dados CC0 com procedência, baseline em dois modelos e registro de IA"
```

---

### Tarefa 0B: Discovery ensaiado com personas sintéticas

> Numerada 0B, e não 1, para não renumerar as tarefas já referenciadas em Review Focus e na revisão técnica. Roteiro completo, protocolo e perguntas prontas para colar: `04-discovery-personas.md`. Caixa de tempo: 75 minutos, ou 40 na versão curta da seção 9 daquele documento.
>
> Esta tarefa não bloqueia o motor (Tarefas 1 a 8), que já está especificado. O que ela muda é o texto da interface, o desenho do estado vazio, a tela do time, o `design.md`, o `sponsor-map.md`, o rollout e as limitações. Por isso roda cedo e é consumida tarde.

**Files:**
- Create: `docs/discovery-preregistro.md` (commitado **antes** da primeira entrevista)
- Create: `docs/discovery-transcricoes/{01-cacador-de-meta,02-consultor-do-empresario,03-operador-de-processo,04-embaixador-da-cultura,05-lider}.md`
- Create: `docs/discovery.md`
- Modify: `process-log/MODELOS.md` (o agente de persona, com a nota de que não é fonte de fato), `process-log/onde-a-ia-errou.md`

**Interfaces:**
- Consumes: os quatro arquétipos do estudo de perfis da área comercial, encarnados no agente do Copilot; os números já medidos em `analise/eda-06`, usados só como gabarito das perguntas de calibração.
- Produces: `docs/discovery.md` com a tabela de doze premissas (P1 a P12), cada uma com status (`confirmada` / `contrariada` / `indeterminada`), o que mudou no produto e **o teste real que a derrubaria** — a coluna que impede a etapa de virar teatro.

- [ ] **Step 1: Pré-registro e commit**

Preencher a tabela da seção 3 de `04-discovery-personas.md` com o que você espera ouvir em cada premissa. Commit **antes** de abrir a primeira conversa:

```bash
git add -f submissions/diego-rodrigues/docs/discovery-preregistro.md
git commit -m "docs(003): pré-registro das premissas, antes de entrevistar as personas"
```

O commit datado é a prova de que as hipóteses vieram antes das respostas. Sem ele, toda confirmação vira "eu já sabia".

- [ ] **Step 2: Registrar o agente de persona no inventário**

Em `process-log/MODELOS.md`, uma linha para o agente: produto e versão, papel ("informante sintético de discovery, quatro arquétipos"), dado sensível (nenhum — dataset CC0) e a nota: **não é fonte de fato; nenhum número do produto vem dele**.

- [ ] **Step 3: Quatro entrevistas em Modo A, uma conversa nova por persona**

Seguir as seções 4 a 7 de `04-discovery-personas.md`, na ordem: Caçador de Meta, Consultor do Empresário, Operador de Processo, Embaixador da Cultura. Colar o enquadramento no início de cada conversa, uma pergunta por mensagem, sem descrever a solução antes das perguntas de Classe B. Transcrição integral, sem edição, em `docs/discovery-transcricoes/`.

Expected: cada transcrição contém pelo menos uma resposta em que a persona discorda de você ou diz que não sabe. Se nenhuma contém, a entrevista foi cordial demais para valer: repita a última pergunta na forma "me dá a versão em que isso dá errado".

- [ ] **Step 4: Quinta entrevista, o líder** (recomendada; seção 8)

Seis perguntas. L2 e L4 decidem coisa concreta: se a fila de encerrar precisa de meta própria, e se a Tela 2 mostra indivíduo por padrão ou só agregado.

- [ ] **Step 5: Calibração em Modo B, conversa separada**

As perguntas de Classe C, cujas respostas já estão medidas: mediana de **2** negócios vivos numa carteira de ~70 abertos; **nenhum** produto ou setor separa ganho de perda; ciclo máximo de **138** dias; mediana de **79** negócios abertos por vendedor.

Expected: anotar, para cada uma, se a persona acertou, errou ou disse que não sabia. Toda resposta confiante e errada vai para `onde-a-ia-errou.md` pelo comando do kit:

```bash
python3 process-log/registrar.py --erro "persona sintética afirmou padrão que o dado não tem" \
  --propos "<o que ela afirmou>" --pego-por "gabarito de analise/eda-06" \
  --teste "pergunta de calibração C10" --ficou "nenhuma resposta de persona entra como fato; só como premissa com teste"
```

- [ ] **Step 6: Escrever `docs/discovery.md`** (uma página) com a tabela de síntese da seção 10. Toda premissa confirmada **continua sendo premissa**, com o teste real escrito ao lado.

- [ ] **Step 7: Aplicar o que mudou.** Anotar em `discovery.md`, na coluna "o que mudou no produto", cada decisão concreta que as respostas alteraram, e abrir as pendências nas tarefas donas: texto do estado vazio e do briefing (Tarefas 9 e 11), agregado contra indivíduo na Tela 2 (Tarefa 11), onda 1 por perfil em vez de por região e meta própria para a fila de encerrar (Tarefa 12).

- [ ] **Step 8: Commit**

```bash
git add -f submissions/diego-rodrigues
git commit -m "docs(003): discovery ensaiado com quatro personas sintéticas, com pré-registro e calibração"
```

---

### Tarefa 1: `motor/carregar.py` · carga, normalização, qualidade e o recorte temporal

**Files:**
- Create: `solution/motor/__init__.py`, `solution/motor/carregar.py`
- Test: `solution/tests/conftest.py`, `solution/tests/test_carregar.py`

**Interfaces:**
- Produces:
  - `carregar(pasta: str | Path) -> Dados`, com `Dados` um `dataclass`: `pipeline: DataFrame`, `contas: DataFrame`, `produtos: DataFrame`, `times: DataFrame`, `qualidade: dict`.
  - `pipeline` sai com as colunas originais mais `produto` (nome do catálogo), `produto_crm` (como veio), `valor_tabela` (float, NaN sem par), `engage_date`/`close_date` em datetime, e `gerente`, `regiao` (merge com `times`) e `setor` (merge com `contas`, pode ser NaN).
  - `qualidade` tem: `apelidos_de_produto` (dict crm→catálogo), `produtos_sem_par` (lista), `setores_corrigidos`, `paises_corrigidos`, `abertos_sem_conta`, `prospecting_sem_data`, `total_linhas`, `maior_data` (ISO), `primeiro_fechamento` (ISO), `vendedores_cadastro`, `vendedores_com_deal`, `vendedores_com_deal_aberto`.
  - `recortar(dados: Dados, hoje: pd.Timestamp) -> Dados`: devolve o export que existiria em `hoje`. Remove deals engajados em `hoje` ou depois; nos deals com `close_date >= hoje`, apaga `close_date` e `close_value` e devolve `deal_stage` a `Engaging`. Quando `hoje` é anterior ao fim do export, descarta Prospecting sem data (não há como datá-los no passado).
- `conftest.py` expõe `dados` (sessão) = `carregar("data")`, `config` e `hoje` = `pd.Timestamp("2018-01-01")`.

- [ ] **Step 1: Escrever os testes**

```python
def test_apelido_de_produto_casa_com_catalogo(dados):
    assert dados.qualidade["apelidos_de_produto"] == {"GTXPro": "GTX Pro"}
    assert dados.qualidade["produtos_sem_par"] == []
    assert dados.pipeline.valor_tabela.isna().sum() == 0
    assert (dados.pipeline.produto_crm != dados.pipeline.produto).sum() == 1480

def test_qualidade_do_export(dados):
    q = dados.qualidade
    assert q["total_linhas"] == 8800 and q["abertos_sem_conta"] == 1425
    assert q["prospecting_sem_data"] == 500
    assert q["maior_data"] == "2017-12-31" and q["primeiro_fechamento"] == "2017-03-01"
    assert q["setores_corrigidos"] == {"technolgy": "technology"}
    assert (q["vendedores_cadastro"], q["vendedores_com_deal"], q["vendedores_com_deal_aberto"]) == (35, 30, 27)

def test_produto_desconhecido_vai_para_qualidade(tmp_path):
    # copia os CSVs para tmp_path e acrescenta uma linha Engaging com product="ZZZ Novo"
    d = carregar(tmp_path)
    assert d.qualidade["produtos_sem_par"] == ["ZZZ Novo"]
    assert d.pipeline.loc[d.pipeline.produto_crm == "ZZZ Novo", "valor_tabela"].isna().all()

def test_recortar_nao_vaza_futuro(dados):
    r = recortar(dados, pd.Timestamp("2017-07-01"))
    assert r.pipeline.close_date.max() < pd.Timestamp("2017-07-01")
    assert r.pipeline.engage_date.max() < pd.Timestamp("2017-07-01")
    assert r.pipeline.close_value[r.pipeline.close_date.isna()].isna().all()
    assert len(r.pipeline[r.pipeline.deal_stage == "Prospecting"]) == 0

def test_recortar_no_fim_do_export_preserva_tudo(dados, hoje):
    r = recortar(dados, hoje)
    assert len(r.pipeline) == 8800
    assert (r.pipeline.deal_stage == "Prospecting").sum() == 500
```

- [ ] **Step 2: Rodar e ver falhar** · `cd solution && .venv/bin/pytest tests/test_carregar.py -v` · Expected: FAIL (módulo não existe)

- [ ] **Step 3: Implementar `carregar` e `recortar`** em `motor/carregar.py`. A chave de produto é `str.replace(" ", "").str.lower()` dos dois lados; merges `left`.

- [ ] **Step 4: Rodar e ver passar** · Expected: 5 passed

- [ ] **Step 5: Commit** · `feat(003): carga com procedência, relatório de qualidade e recorte temporal sem vazamento` · Diário: que o merge ingênuo de produto derrubaria 1.480 linhas e US$ 1,6 mi de pipeline aberto, e que `recortar` existe para que o backtest não possa divergir do produto.

---

### Tarefa 2: `motor/janela.py` · a janela de validade de um deal, aprendida

**Files:**
- Create: `solution/motor/janela.py`
- Test: `solution/tests/test_janela.py`

**Interfaces:**
- Consumes: `Dados` recortado, `config`.
- Produces:
  - `aprender_janela(dados, config) -> Janela`, `dataclass` com `ciclo_max: int`, `usa_prazo_trimestre: bool`, `n_fechamentos: int`, `fechamentos_apos_prazo: int`.
  - `ciclo_max` = maior ciclo entre os fechamentos **conhecidos**. `usa_prazo_trimestre` é True quando há pelo menos `min_fechamentos_para_prazo` fechamentos conhecidos e a fração deles fechada depois do fim do trimestre seguinte ao engajamento é ≤ `tolerancia_prazo_trimestre`.
  - `prazo_do_deal(engage_date: Series, janela) -> Series`: o menor entre `engage_date + ciclo_max` e o fim do trimestre seguinte ao do engajamento (este só quando `usa_prazo_trimestre`).
  - `estado(pipeline, janela, hoje) -> Series` ∈ {`vivo`, `vencido`, `sem_data`}: `sem_data` quando não há `engage_date`; `vivo` quando a idade é ≤ `ciclo_max` **e** o prazo é ≥ `hoje`; `vencido` nos demais.

- [ ] **Step 1: Escrever os testes**

```python
def test_janela_aprendida_no_fim_do_export(dados, config, hoje):
    j = aprender_janela(recortar(dados, hoje), config)
    assert j.ciclo_max == 138 and j.n_fechamentos == 6711
    assert j.fechamentos_apos_prazo == 1 and j.usa_prazo_trimestre is True

def test_regra_do_trimestre_ja_valia_no_passado(dados, config):
    for d, n in [("2017-07-01", 2679), ("2017-10-01", 4726)]:
        j = aprender_janela(recortar(dados, pd.Timestamp(d)), config)
        assert j.ciclo_max == 138 and j.n_fechamentos == n
        assert j.fechamentos_apos_prazo == 0 and j.usa_prazo_trimestre is True

def test_estado_em_2018_01_01(dados, config, hoje):
    r = recortar(dados, hoje); j = aprender_janela(r, config)
    e = estado(r.pipeline, j, hoje)
    assert (e == "vivo").sum() == 115 and (e == "sem_data").sum() == 500
    venc = r.pipeline[e == "vencido"]
    idade = (hoje - venc.engage_date).dt.days
    assert len(venc) == 1474 and (idade > 138).sum() == 1301 and (idade <= 138).sum() == 173

def test_prazo_do_deal_pega_o_limite_mais_curto(dados, config, hoje):
    r = recortar(dados, hoje); j = aprender_janela(r, config)
    p = prazo_do_deal(r.pipeline.engage_date, j)
    por_idade = r.pipeline.engage_date + pd.Timedelta(days=138)
    assert (p <= por_idade).all() and (p < por_idade).sum() > 0

def test_sem_fechamentos_suficientes_desliga_a_regra(dados, config):
    j = aprender_janela(recortar(dados, pd.Timestamp("2017-03-15")), config)
    assert j.usa_prazo_trimestre is False   # menos de 500 fechamentos conhecidos
```

- [ ] **Step 2: Falhar** · **Step 3: Implementar** (fim do trimestre seguinte: início do trimestre do engajamento + `QuarterBegin(2)` − 1 dia) · **Step 4: Passar** (5 passed)
- [ ] **Step 5: Commit** · `feat(003): janela de validade do deal aprendida do histórico, com a regra do trimestre` · Diário: que a regra de 138 dias é só metade, que o PR público #242 tem a outra metade, que conferi com script próprio e adotei creditando.

---

### Tarefa 3: `motor/aprender.py` · a tabela de destino (o relógio do trimestre)

**Files:**
- Create: `solution/motor/aprender.py`
- Test: `solution/tests/test_aprender.py`

**Interfaces:**
- Consumes: `Dados` recortado, `Janela`, `config`, `hoje`.
- Produces:
  - `datas_analogas(dados, hoje) -> list[Timestamp]`: `hoje` menos 3, 6, 9… meses, enquanto a data não for anterior ao primeiro fechamento conhecido.
  - `tabela_destino(dados, janela, config, hoje) -> DataFrame` indexado pelo rótulo da faixa (`"1-15"`, `"16-30"`, …, até `ciclo_max`), com `n`, `decidiram_28d`, `ganharam_28d`, `decidiram_trimestre`, `ganharam_trimestre`, `p_decide`, `p_ganha_28d`, `p_ganha_trimestre`, `agrupada` (bool). Em cada data análoga, os deals abertos naquela data entram com a idade que tinham; o desfecho é o que aconteceu nos `horizonte_dias` seguintes e até o fim daquele trimestre. Faixa com `n < n_min_faixa` é agrupada com a vizinha mais velha; faixa sem observação recebe probabilidade 0 e `agrupada = True`.
  - `carga_referencia(dados, hoje) -> Series`: mediana, entre as datas análogas, do número de deals que estavam abertos por vendedor e depois fecharam. É o retrato do que o vendedor costuma carregar, não um teto inventado.
  - `tabela_vazia_para(hoje) -> DataFrame`: tabela toda em zero, para quando não há data análoga (primeiro trimestre de operação), com `motivo` preenchido.

- [ ] **Step 1: Escrever os testes**

```python
def test_datas_analogas(dados, hoje):
    assert datas_analogas(recortar(dados, hoje), hoje) == [
        pd.Timestamp("2017-10-01"), pd.Timestamp("2017-07-01"), pd.Timestamp("2017-04-01")]

def test_relogio_do_trimestre(dados, config, hoje):
    t = tabela_destino(*_ctx(dados, config, hoje))
    assert t.loc["1-15", "n"] == 1117 and t.loc["1-15", "decidiram_28d"] == 395
    assert round(t.loc["1-15", "p_decide"], 3) == 0.354
    velhas = t.drop(index="1-15")
    assert velhas.n.sum() == 3618 and velhas.decidiram_28d.sum() == 0   # o achado central
    assert t.loc["16-30", "decidiram_trimestre"] == 691                  # mas no trimestre decidem

def test_probabilidades_sao_validas(dados, config, hoje):
    t = tabela_destino(*_ctx(dados, config, hoje))
    for c in ["p_decide", "p_ganha_28d", "p_ganha_trimestre"]:
        assert t[c].between(0, 1).all() and t[c].notna().all()
    assert (t.p_ganha_trimestre <= t.decidiram_trimestre / t.n + 1e-9).all()

def test_nao_ha_vies_de_sobrevivencia(dados, config, hoje):
    """A fórmula do v1 dava 100% aos 120 dias; a tabela com os abertos em risco dá quase zero."""
    t = tabela_destino(*_ctx(dados, config, hoje))
    assert t.loc["106-120", "p_decide"] < 0.05 and t.loc["121-138", "p_decide"] < 0.05

def test_faixa_rala_e_agrupada(dados, config, hoje):
    cfg = {**config, "n_min_faixa": 500}
    t = tabela_destino(*_ctx(dados, cfg, hoje))
    assert t.agrupada.any() and (t.n >= 500).all()

def test_carga_de_referencia(dados, config, hoje):
    c = carga_referencia(recortar(dados, hoje), hoje)
    assert len(c) == 30 and c.median() == 33.0 and c.min() == 12.0 and c.max() == 77.0

def test_sem_analoga_devolve_tabela_vazia(dados, config):
    d = pd.Timestamp("2017-04-15")
    t = tabela_destino(*_ctx(dados, config, d))
    assert (t.p_decide == 0).all() and t.motivo.notna().all()
```

- [ ] **Step 2: Falhar** · **Step 3: Implementar** · **Step 4: Passar** (7 passed)
- [ ] **Step 5: Commit** · `feat(003): tabela de destino por idade e altura do trimestre, com censura` · Diário: que a fórmula do v1 chegava a 100% de chance aos 120 dias por contar só fechados, e o teste que fixa a correção.

---

### Tarefa 4: `motor/pontuar.py` · fila, ordem, foco, índice

**Files:**
- Create: `solution/motor/pontuar.py`
- Test: `solution/tests/test_pontuar.py`

**Interfaces:**
- Consumes: `Dados` recortado, `Janela`, tabela de destino, `carga_referencia`, `config`, `hoje`.
- Produces: `pontuar(...) -> DataFrame`, uma linha por deal aberto, com `opportunity_id, vendedor, gerente, regiao, produto, produto_crm, conta, setor, stage, engage_date, idade, faixa, prazo, dias_restantes, estado, p_decide, valor_tabela, ve_28, ve_trimestre, fila, chave, posicao, em_foco, indice`.
  - `ve_28 = valor_tabela × p_ganha_28d` da faixa; `ve_trimestre = valor_tabela × p_ganha_trimestre`.
  - `fila`: `iniciar` se `sem_data`; `encerrar` se `vencido`; `fechar` se `p_decide >= p_decide_min`; `preparar` nos demais vivos.
  - `chave` de ordenação: `ve_28` em `fechar`, `ve_trimestre` em `preparar`, `valor_tabela` em `iniciar` e `encerrar`. Ordem dentro do vendedor: fila (`fechar`, `preparar`, `iniciar`, `encerrar`), `chave` desc, `dias_restantes` asc, `opportunity_id` asc (desempate estável).
  - `posicao` 1..n dentro de vendedor × fila. `em_foco` marca os primeiros `foco_por_vendedor` deals do vendedor ignorando `encerrar`.
  - `indice` 0 a 100 só para os vivos: percentil da posição global entre os vivos na ordem acima, com piso 1; `vencido` recebe 0; `sem_data` recebe NaN (não há como pontuar sem data). Tem de ser monótono com a ordem da fila.
  - `verbo` por fila: `fechar` → "Ligar e propor data de fechamento"; `preparar` → "Avançar uma etapa: próxima reunião ou proposta"; `iniciar` → "Registrar data de engajamento e fazer o primeiro contato"; `encerrar` → "Confirmar ou fechar como perdido no CRM".

- [ ] **Step 1: Escrever os testes** (valores de ouro de `analise/eda-06-prototipo-motor-v2.saida.txt`, seção C)

```python
def test_filas_em_2018_01_01(s):
    assert s.fila.value_counts().to_dict() == {
        "encerrar": 1474, "iniciar": 500, "preparar": 108, "fechar": 7}
    assert len(s) == 2089 and s.vendedor.nunique() == 27

def test_valor_por_fila(s):
    v = s.groupby("fila").valor_tabela.sum().round().astype(int).to_dict()
    assert v == {"encerrar": 3656299, "fechar": 16385, "iniciar": 1073986, "preparar": 219545}

def test_valor_esperado_total(s):
    assert round(s.ve_trimestre.sum(), 2) == 65482.05
    assert round(s.ve_28.sum(), 2) == 2699.05

def test_fila_fechar_e_so_deal_novo_na_virada_do_trimestre(s):
    f = s[s.fila == "fechar"]
    assert len(f) == 7 and f.idade.max() <= 15
    assert set(f.opportunity_id) == {"NGTVHTFH", "RDHTQLNI", "DB801ISB", "HB740BLB",
                                     "RTWE19SU", "T6MPH7JC", "HCQK8NQ8"}

def test_indice_monotono_com_a_ordem(s):
    viv = s[s.estado == "vivo"]
    assert viv.indice.between(1, 100).all()
    assert (s[s.estado == "vencido"].indice == 0).all()
    assert s[s.estado == "sem_data"].indice.isna().all()
    for _, x in viv.groupby("vendedor"):
        assert x.sort_values(["fila_ordem", "posicao"]).indice.diff().dropna().le(0).all()

def test_foco_cabe_e_ignora_encerrar(s, config):
    foco = s[s.em_foco]
    assert (foco.groupby("vendedor").size() <= config["foco_por_vendedor"]).all()
    assert (foco.fila != "encerrar").all() and len(foco) == 127

def test_ordem_dentro_do_vendedor(s):
    x = s[(s.vendedor == "Boris Faz") & s.em_foco].sort_values("indice", ascending=False)
    assert list(x.opportunity_id) == ["NGTVHTFH", "I5VHXAWW", "BREOLQD9", "EP5QRHID", "W4XB23IP"]

def test_vendedor_sem_deal(s, dados):
    assert "Carl Lin" not in set(s.vendedor)   # tratado na Tarefa 5, não aqui

def test_pontuacao_independe_do_futuro(dados, config):
    """A lista de uma data não muda quando o futuro é alterado."""
    d1 = pontuar_em(dados, config, pd.Timestamp("2017-08-28"))
    alterado = _apagar_desfechos_depois_de(dados, pd.Timestamp("2017-10-01"))
    d2 = pontuar_em(alterado, config, pd.Timestamp("2017-08-28"))
    assert d1.drop(columns=["gerado_em"]).equals(d2.drop(columns=["gerado_em"]))
```

- [ ] **Step 2: Falhar** · **Step 3: Implementar** · **Step 4: Passar** (9 passed)
- [ ] **Step 5: Commit** · `feat(003): fila e ordem por valor esperado na altura do trimestre`

---

### Tarefa 5: `motor/explicar.py` · por que este deal, e o que o score não sabe

**Files:**
- Create: `solution/motor/explicar.py`
- Test: `solution/tests/test_explicar.py`

**Interfaces:**
- Consumes: linha de `pontuar`, `Janela`, tabela de destino, `carga_referencia`.
- Produces:
  - `explicar(linha, janela, tabela) -> dict` com `cartoes: {valor, momento, prazo}` e `nao_sabe: list[str]`.
  - `momento` é o cartão novo e o mais importante: para `fechar`, "nas três viradas de trimestre anteriores, cerca de 35 em cada 100 deals nessa idade decidiram nas quatro semanas seguintes"; para `preparar`, "nessa idade, deals decidem mais tarde no trimestre: 79 em cada 100 decidiram até o fim dele, mas quase nenhum nas próximas quatro semanas"; para `encerrar`, o motivo exato (passou de 138 dias **ou** o trimestre em que ele podia fechar terminou), com a data; para `iniciar`, que não há data de engajamento e por isso não há como estimar.
  - `valor`: preço de tabela formatado `US$ 5.482` e a posição no pipeline vivo do vendedor. `prazo`: dias restantes e qual dos dois limites manda.
  - `nao_sabe`: três itens fixos (sem registro de atividade, sem desconto ou quantidade, sem motivo de perda) mais, quando a conta é nula, "esta oportunidade não tem conta no CRM".
  - `resumo_vendedor(sub: DataFrame, carga) -> dict`: contagens e valores por fila, carga de referência e a frase do estado vazio quando o vendedor não tem nenhum deal vivo.

- [ ] **Step 1: Testes** verificando: `cartoes.valor` do deal `RDHTQLNI` contém `"US$ 5.482"`; `cartoes.momento` de um `preparar` contém `"até o fim"` e não contém `"quatro semanas seguintes"` como promessa; o `momento` de um vencido por prazo do trimestre nomeia o trimestre e não os 138 dias; `nao_sabe` tem 4 itens quando a conta é nula e 3 quando não; `resumo_vendedor` de "Carl Lin" (sem deal) devolve zeros, a carga de referência e a frase de estado vazio, sem exceção.
- [ ] **Step 2–5:** falhar, implementar, passar, commit `feat(003): explicação por deal, com o cartão de momento do trimestre`.

---

### Tarefa 6: `build.py` · contrato JSON e determinismo

**Files:**
- Create: `solution/build.py`, `docs/contrato.md`
- Test: `solution/tests/test_build.py`

**Interfaces:**
- Produces: `construir(pasta_dados, config, saida="app/data", hoje=None) -> dict` que grava:
  - `scored.json`: `{"gerado_em", "hoje", "semana_do_trimestre", "config", "janela": {...}, "tabela_destino": [...], "deals": [...com cartoes e nao_sabe...], "vendedores": [...todos os 35 do cadastro, com totais e valores por fila, carga de referência e `tem_deal`...], "time": {total_abertos, valor_aberto, valor_vivo, valor_vencido, pct_vencido, ve_trimestre, por_regiao, por_gerente}}`
  - `qualidade.json`: o dict `qualidade` mais `vendedores_sem_deal` (os 5 nomes).
  - `hash.txt`: SHA-256 do `scored.json` sem o campo `gerado_em`.
- `build.py` roda como script: `python build.py [--hoje AAAA-MM-DD]`. `docs/contrato.md` descreve cada campo em uma linha.

- [ ] **Step 1: Testes**

```python
def test_build_grava_e_soma(tmp_path, config):
    construir("data", config, saida=tmp_path, hoje="2018-01-01")
    j = json.load(open(tmp_path / "scored.json"))
    assert len(j["deals"]) == 2089 and len(j["vendedores"]) == 35
    assert sum(v["por_fila"]["encerrar"] for v in j["vendedores"]) == 1474
    assert round(j["time"]["pct_vencido"], 3) == 0.736
    assert j["time"]["valor_vivo"] == 235930 and j["semana_do_trimestre"] == 1
    assert [v for v in j["vendedores"] if v["vendedor"] == "Carl Lin"][0]["tem_deal"] is False

def test_build_e_deterministico(tmp_path, config):
    a = construir("data", config, saida=tmp_path / "a", hoje="2018-01-01")
    b = construir("data", config, saida=tmp_path / "b", hoje="2018-01-01")
    assert (tmp_path / "a/hash.txt").read_text() == (tmp_path / "b/hash.txt").read_text()
    assert a["hash"] == b["hash"]
```

- [ ] **Step 2–5:** falhar, implementar (`json.dump(..., ensure_ascii=False, indent=1, sort_keys=True)`), passar, commit `feat(003): build do contrato JSON com hash determinístico`.

---

### Tarefa 7: `avaliacao/` · backtest honesto, três métricas e intervalo de confiança

**Files:**
- Create: `solution/avaliacao/{__init__.py,backtest.py,permutacao.py,numeros.py}`
- Create: `docs/logica.md`
- Test: `solution/tests/test_backtest.py`

**Interfaces:**
- Consumes: todo o motor, pelas mesmas funções que o produto usa.
- Produces:
  - `backtest(dados, config, cortes=None, k=None) -> DataFrame`, uma linha por corte com `corte, semana_do_trimestre, n_analogas, vivos, fila_fechar` e, para cada política, valor ganho no horizonte e taxa de acerto. Cortes padrão: segundas a cada 4 semanas de 03/07 a 03/12/2017 — **janelas que não se sobrepõem**, para que os cortes sejam observações independentes. Políticas: `relogio` (a ordem do motor), `preco_prazo` (preço entre os vivos pelas duas regras — a melhor alternativa honesta), `preco_138` (preço entre os de até `ciclo_max`, o que o v1 faria), `aleatorio` (sorteio entre os vivos) e `oraculo` (teto com o futuro na mão).
  - `razao_com_ic(backtest_detalhado, a, b, n=5000, semente=7) -> (razao, lo, hi)`: bootstrap **por vendedor** (a unidade de independência é o vendedor, não o deal).
  - `permutacao(historico, chave, estratificar_por=None, n=300, semente=7) -> dict`: variância observada, média permutada e p. Rodada também estratificada pelo mês do trimestre, para mostrar que a ausência de sinal nos atributos não é efeito de calendário disfarçado.
  - `numeros.py` imprime, com rótulo e fonte, cada número citado no README, nos docs e na tela.
  - Grava `app/data/eval.json` com a tabela, as razões com IC e os p-valores.

- [ ] **Step 1: Testes** (valores de ouro da seção F do eda-06)

```python
def test_backtest_as_of(dados, config):
    r = backtest(dados, config)
    assert len(r) == 6
    assert r.valor_relogio.sum() == 1097324 and r.valor_preco_prazo.sum() == 842462
    assert r.valor_aleatorio.sum() == 334520 and r.valor_oraculo.sum() == 2666327

def test_relogio_bate_a_melhor_alternativa_honesta(dados, config):
    razao, lo, hi = razao_com_ic(backtest(dados, config, detalhado=True), "relogio", "preco_prazo")
    assert round(razao, 2) == 1.30 and lo > 1.0        # o IC não cruza 1
    assert (round(lo, 2), round(hi, 2)) == (1.13, 1.52)

def test_a_vantagem_nao_e_mistura_de_preco(dados, config):
    r = backtest(dados, config)
    assert round(r.acerto_relogio.mean(), 3) == 0.227
    assert round(r.acerto_preco_prazo.mean(), 3) == 0.154
    assert round(r.acerto_aleatorio.mean(), 3) == 0.144

def test_fracao_do_teto(dados, config):
    r = backtest(dados, config)
    assert round(r.valor_relogio.sum() / r.valor_oraculo.sum(), 3) == 0.412
    assert round(r.valor_preco_prazo.sum() / r.valor_oraculo.sum(), 3) == 0.316

def test_nenhum_vencido_ganhou(dados, config):
    assert (backtest(dados, config).vencidos_ganhos == 0).all()

def test_atributos_continuam_sem_sinal(dados, config):
    h = _historico(dados, config)
    for chave, p_min in [("account", 0.5), ("sales_agent", 0.1), (["sales_agent", "product"], 0.1)]:
        assert permutacao(h, chave, estratificar_por="mes_do_trimestre", n=100)["p"] > p_min
```

- [ ] **Step 2–4:** falhar, implementar, passar (6 passed). Rodar `python -m avaliacao.numeros > ../docs/numeros-saida.txt`.
- [ ] **Step 5: Escrever `docs/logica.md`**: as regras aceitas com a evidência (a tabela do backtest e os IC); as rejeitadas com o número que as derrubou (setor, porte, região, gerente, conta, vendedor, vendedor×produto, e **"3× o aleatório como métrica"**, com a conta da taxa de acerto); o que é aprendido e o que é configuração; e o parágrafo sobre o PR #240 ter visto o efeito de calendário e descartado, e por que a pergunta "quando decide" é diferente de "quem ganha".
- [ ] **Step 6: Commit** · `feat(003): backtest as-of com três métricas, bootstrap por vendedor e regras rejeitadas`

---

### Tarefa 8: `drift.py` · avisar quando o mundo mudar

**Files:**
- Create: `solution/drift.py`, `solution/janela.json` (o que foi aprendido no build)
- Test: `solution/tests/test_drift.py`

**Interfaces:**
- Produces: `conferir(pasta_dados, janela_guardada, config) -> dict` com, para cada item (`ciclo_max`, `usa_prazo_trimestre`, `p_decide` por faixa, `carga_referencia`), o valor guardado, o novo e se passou da tolerância. Sai com código 1 e mensagem em português quando algo moveu. `build.py` grava `janela.json`.

- [ ] **Step 1: Testes**: contra os mesmos CSVs, nada moveu (código 0); com um CSV em que um deal foi ganho aos 200 dias, `ciclo_max` muda e o comando sai 1 nomeando o item; com um fechamento plantado depois do prazo do trimestre, `usa_prazo_trimestre` cai para False e a mensagem explica o efeito na fila.
- [ ] **Step 2–5:** falhar, implementar, passar, commit `feat(003): relatório de desvio da janela e da tabela aprendidas`.

---

### Tarefa 9: `ia/` · briefing com validador, fallback e custo registrado

Antes de escrever código de API, carregar o skill `claude-api` (modelo, saída estruturada, SDK).

**Files:**
- Create: `solution/ia/{__init__.py,briefing.py,validar.py}`, `solution/ia/prompts/{briefing_vendedor.md,resumo_gestor.md}`
- Test: `solution/tests/{test_validar.py,test_briefing.py}`

**Interfaces:**
- Consumes: `scored.json`.
- Produces:
  - `fatos_vendedor(scored, vendedor) -> dict`: `nome`, `semana_do_trimestre`, `n_fechar`, `n_preparar`, `n_iniciar`, `n_encerrar`, `valor_encerrar`, `ve_trimestre`, `foco: [{produto, conta, valor, idade, dias_restantes, fila} × até 5]`, `sem_nada_vivo` (bool). Mesmo padrão em `fatos_gestor`.
  - `validar(texto, fatos) -> tuple[bool, str]`: recusa dígito fora de marcador `{chave}`, nome de conta ou produto ausente de `fatos`, palavra proibida (`garantido`, `certeza`, `vai fechar`, `com certeza`) e **afirmação de chance quando `p_decide` é zero** (um briefing não pode dizer que o deal está prestes a decidir numa semana em que a tabela diz zero).
  - `preencher(texto, fatos) -> str`; `template_vendedor(fatos) -> str`; `template_gestor(fatos) -> str`.
  - `gerar(scored, modelo="claude-sonnet-5-5", sem_ia=False) -> dict` → grava `app/data/briefings.json` com `{"gerado_em", "modelo", "vendedores": {nome: {"texto", "origem": "ia"|"template", "motivo"}}, "gestores": {...}, "custo_estimado_usd", "recusas"}`. Sem `ANTHROPIC_API_KEY` ou com `--sem-ia`, tudo vem de template. Saída estruturada, temperatura baixa, uma tentativa de correção, depois template.

- [ ] **Step 1: Testes do validador**

```python
def test_recusa_numero_fora_de_marcador(fatos):
    ok, motivo = validar("Você tem {n_fechar} deals e US$ 12.000 parados.", fatos)
    assert not ok and "número" in motivo

def test_recusa_conta_inventada(fatos):
    assert not validar("Ligue para a Acme Corporation hoje.", {**fatos, "foco": []})[0]

def test_recusa_promessa(fatos):
    assert not validar("O deal {conta_1} vai fechar com certeza.", fatos)[0]

def test_recusa_chance_quando_a_tabela_diz_zero(fatos_sem_fechar):
    ok, motivo = validar("Dois deals devem decidir nas próximas semanas.", fatos_sem_fechar)
    assert not ok and "chance" in motivo

def test_aceita_template(fatos):
    assert validar(template_vendedor(fatos), fatos)[0]

def test_template_do_vendedor_sem_nada_vivo(fatos_vazios):
    t = template_vendedor(fatos_vazios)
    assert "não há" in t.lower() and validar(t, fatos_vazios)[0]

def test_gerar_sem_ia_usa_template(scored):
    b = gerar(scored, sem_ia=True)
    assert len(b["vendedores"]) == 35
    assert all(v["origem"] == "template" for v in b["vendedores"].values())
```

- [ ] **Step 2–4:** falhar, implementar, passar (testes não chamam a API).
- [ ] **Step 5: Gerar de verdade** · `ANTHROPIC_API_KEY=... python -m ia.briefing` · anotar quantos vieram de `ia`, quantos caíram no template, o custo, e guardar dois exemplos recusados em `process-log/onde-a-ia-errou.md`.
- [ ] **Step 6: Commit** · `feat(003): briefing por IA com validador determinístico, fallback e custo registrado`

---

### Tarefa 10: `run.py` · um comando, servidor local, ações gravadas

**Files:**
- Create: `solution/run.py`
- Test: `solution/tests/test_run.py`

**Interfaces:**
- Produces: `python run.py [--port 8000] [--sem-build] [--sem-ia] [--hoje AAAA-MM-DD]`: resolve e **imprime** a data usada, roda `construir`, roda `gerar`, sobe `http.server` servindo `app/` com `GET /acoes` (lista de `acoes.jsonl`) e `POST /acao` (valida `{vendedor, opportunity_id, acao ∈ {feito, adiar, nao_vivo}}` e que o id existe em `scored.json`; grava com `ts` ISO e responde 201; inválido → 400 sem gravar). Classe `Manipulador(SimpleHTTPRequestHandler)` exportada para teste.

- [ ] **Step 1: Testes** (servidor em thread, porta livre, `tmp_path` como pasta de ações, `urllib.request`): `POST` válido grava e responde 201; `opportunity_id` inexistente responde 400 e não grava; corpo não-JSON responde 400; `acao` fora do conjunto responde 400; `GET /acoes` devolve o que foi gravado.
- [ ] **Step 2–4:** falhar, implementar, passar.
- [ ] **Step 5: Teste manual** · `python run.py` num clone limpo · Expected: abre em menos de 1 minuto, imprime `hoje = 2018-01-01 (semana 1 do trimestre)`, marcar "Não está vivo" e ver a tela do time refletir.
- [ ] **Step 6: Commit** · `feat(003): run.py com build, servidor local e registro de ações`

---

### Tarefa 11: `app/` · três telas

**Files:**
- Create: `solution/app/{index.html,app.js,estilos.css}`
- Create: `process-log/screenshots/`

**Interfaces:**
- Consumes: `scored.json`, `qualidade.json`, `eval.json`, `briefings.json` (se ausente, template local), `GET /acoes` (se 404, `localStorage`).
- Produces:
  - **Tela 1 · Segunda-feira**: seletor de vendedor (quem tem deal em `fechar` primeiro), briefing, e o foco do dia com verbo, produto, conta, valor, idade, dias restantes, chance quando existe, e "por quê" (três cartões + o que o score não sabe). Blocos FECHAR, PREPARAR, INICIAR e ENCERRAR colapsados com contagem e valor. **Estado vazio é primeira classe**: na data de referência, 18 dos 35 vendedores não têm nenhum deal vivo e a fila `fechar` tem 7 deals no time inteiro — a tela diz o que fazer nesse caso (começar os de `iniciar`), não finge lista cheia.
  - Faixa de topo com a data usada e a semana do trimestre, e a frase de que a janela de decisão deste negócio tem forma de trimestre.
  - **Tela 2 · O time**: filtros região/gerente/vendedor; tabela por vendedor com as quatro filas, valor vivo, valor vencido, carga de referência e os 5 sem nenhum deal; cobertura; adoção (vendedores com ação na semana, ações por fila, override = `nao_vivo` ÷ marcados); qualidade do dado; resumo do gestor.
  - **Tela 3 · Como decide**: a tabela de destino aprendida (com `n` de cada faixa e quais foram agrupadas), as datas análogas usadas, a tabela do backtest com as três métricas e os IC, as regras rejeitadas com o número que as derrubou, o que é aprendido e o que é configuração, e o que falta no CRM.
  - Faixa na Vercel: "Demo pública com dados fictícios (CC0). Ações não são gravadas."
- Design: carregar `frontend-design` e `ui-ux-pro-max` antes do CSS. Uma paleta sóbria, sem gráfico de BI, legível em 390 px, `prefers-color-scheme`.

- [ ] **Step 1: Escrever as três telas** (`fetch`, sem framework).
- [ ] **Step 2: Servir e conferir** · `python -m http.server 8000 -d app` · Boris Faz mostra 1 em `fechar` e 4 em `preparar`; Darcel Schlecht mostra 5 em `iniciar`; Carl Lin mostra o estado vazio com a carga de referência; o filtro por região muda a tabela; a Tela 3 mostra 6 linhas de backtest e 9 faixas.
- [ ] **Step 3: Prints** com `webapp-testing` (Playwright) em 1366 e 390 px: `01-segunda-desktop.png`, `02-segunda-mobile.png`, `03-por-que.png`, `04-vazio.png`, `05-time.png`, `06-como-decide.png`.
- [ ] **Step 4: Commit** · `feat(003): três telas, mobile-first, estado vazio como primeira classe`

---

### Tarefa 12: Operating map, sponsor map, design, deploy e experimento

**Files:**
- Create: `docs/{operating-map.md,sponsor-map.md,design.md,deploy.md,experimento.md}`
- Consome: `docs/discovery.md` da Tarefa 0B (não reescrever; citar)

Conteúdo pinado pelo guia (seções 4 fase 1, 5 e 8), com três mudanças:
- `sponsor-map.md` e `operating-map.md` usam as **palavras das personas** para o que cada papel ganha e perde, citando a transcrição; o workflow atual deixa de ser suposição e passa a ter origem declarada.
- `design.md` inclui as abordagens consideradas **e a rejeitada com número**: ordenar por preço (o que o campo faz) rende 0,77× o relógio, com IC que não cruza 1. As não-metas e a anti-meta passam a citar a premissa do discovery que as sustenta (P8, P7).
- `experimento.md` substitui o piloto por região: sorteio **por deal dentro do vendedor**, cada vendedor como seu próprio controle, ICC de 0,031, métrica primária taxa de decisão em 28 dias dos priorizados, **1.100 deals por braço** para detectar +5 pontos sobre a base de 22%, cerca de três semanas de pipeline do time. Valor ganho entra como secundária, com a conta explícita de que detectar +10% nele exigiria 109 vendedores por braço e por isso ele **não pode** ser o critério de aceite. Inclui a regra de parada e o que invalida o teste.
- `deploy.md` desenha a **onda 1 por perfil** (quem o Embaixador apontou como primeiro adotante), não por região, e trata a fila de encerrar como item com meta e patrocínio do gestor se P12 se confirmar.

- [ ] **Step 1: Escrever os cinco documentos**, cada um em até uma página, sem jargão.
- [ ] **Step 2: Conferir** · `wc -w docs/*.md` · cada arquivo entre 250 e 700 palavras. Conferir também que toda premissa marcada como `contrariada` em `discovery.md` tem consequência visível em pelo menos um destes documentos.
- [ ] **Step 3: Commit** · `docs(003): operating map, sponsor map, design, deploy por perfil e experimento com poder calculado`

---

### Tarefa 13: Deploy, resumo executivo, process log e PR

**Files:**
- Create: `solution/app/vercel.json` (`{"cleanUrls": true}`), `solution/app/.vercelignore` (`data/acoes.jsonl`)
- Create: `docs/{resumo-executivo.md,limitacoes.md,deploy-passos.md}`
- Modify: `README.md`, `process-log/{diario.md,onde-a-ia-errou.md,REGISTRO.md,verificacao/relatorio.md}`

- [ ] **Step 1: Deploy** · `cd solution/app && vercel --prod --yes --name lead-scorer-diego` · conferir no celular e no desktop: faixa de demo visível, três telas carregam, ação cai no `localStorage` com aviso.

- [ ] **Step 2: `docs/resumo-executivo.md`** em uma tela, na ordem medido → premissa:
  - **Medido**: US$ 3,66 mi dos US$ 4,97 mi de pipeline aberto (73,6%) não tem nenhuma chance histórica de fechar; o forecast está construído sobre isso. Sobram 115 deals e US$ 236 mil vivos. Os 500 em Prospecting valem US$ 1,07 mi e não têm data.
  - **Medido**: priorizar pelo relógio do trimestre captura 1,30× o valor da melhor alternativa honesta (IC 95% 1,13 a 1,52) e acerta 22,7% contra 15,4%.
  - **Premissa, declarada como tal**: a conta de horas, com o ponto de equilíbrio em vez de um número único.
  - A frase para o CFO, reescrita para não vender tautologia: *"Três quartos do pipeline que entra no forecast não fecha mais — isso é medido. O que sobra vivo cabe numa lista de cinco deals por vendedor, e priorizá-la pela janela de decisão do negócio rende 30% mais do que priorizar por valor, com intervalo de confiança que não cruza zero. Em 90 dias medimos o ganho com grupo de controle antes de expandir."*

- [ ] **Step 3: Fechar o README** (template oficial) com os números de `docs/numeros-saida.txt`, a URL da Vercel, a tabela de ferramentas de IA, os prints, e a linha de benchmark: *"Depois de fechar a minha tese com a minha análise, li as submissões públicas para saber o que já é baseline do campo. Achei lá a regra do prazo do trimestre (PR #242), conferi com script próprio e adotei, creditando. Achei também o efeito de calendário descartado como artefato (PR #240) e mostro por que a pergunta 'quando decide' tem resposta onde 'quem ganha' não tem."*

- [ ] **Step 4: `docs/limitacoes.md`** honesto: dataset sintético; o relógio do trimestre pode ser artefato do gerador e é por isso que `drift.py` existe; três trimestres de história; `hoje` fixo no fim do export; sem registro de atividade, desconto ou motivo de perda; sem escrita no CRM; sem login; a conta de horas é premissa; 1.425 dos abertos sem conta; e **o discovery foi ensaiado com personas sintéticas, não vivido** — nunca escrever "entrevistei vendedores", e cada premissa confirmada por persona continua listada como premissa com o teste real que a resolveria.

- [ ] **Step 5: Fechar o process log**: diário por sessão (saída do `registro-ia`), tabela de ferramentas e modelos com versão, workflow numerado, `onde-a-ia-errou.md` com os itens reais e o teste que derrubou cada um — os seis da revisão (números pinados errados, viés na tabela de probabilidade, prazo do trimestre que faltava, métrica que media mistura de preço, piloto sem poder, `git add` sem `-f`) e os da calibração das personas (afirmação confiante sobre padrão que o dado não tem) — "o que eu adicionei", contagem de iterações e prints.

O item das personas é de categoria diferente dos outros e merece parágrafo próprio no README: não é "a IA errou uma conta", é "usei informante sintético, medi a confiabilidade dele com perguntas de resposta já conhecida, e separei o que ele podia me dizer do que ele não podia".

- [ ] **Step 6: Verificação independente** · despachar um subagente revisor (só leitura, modelo diferente do que implementou) com o pedido: "recalcular do zero, a partir dos quatro CSVs e com código próprio, cada número do README; procurar vazamento temporal, viés de sobrevivência, limiar fora de config, regra no front e número sem fonte". Gravar o script, a saída e o relatório em `process-log/verificacao/`.

- [ ] **Step 7: Checklist da seção 10 do guia**, item a item. `git diff --stat upstream/main` deve listar só `submissions/diego-rodrigues/`.

- [ ] **Step 8: Push e PR**

```bash
git push -u origin submission/diego-rodrigues
gh pr create -R Gestao-Quatro-Ponto-Zero/ai-master-challenge --base main \
  --head DiegoAlves-data:submission/diego-rodrigues \
  --title "[Submission] Diego Rodrigues — Challenge 003" \
  --body-file submissions/diego-rodrigues/docs/resumo-executivo.md
```

- [ ] **Step 9:** Anotar o número do PR no `README.md` desta pasta e marcar o status.

---

## Auto-revisão do plano

- **Cobertura da spec:** guia seção 3 → Tarefas 1, 2, 3, 7; **seção 4 fase 1 → Tarefa 0B** (discovery) e Tarefa 12 (operating e sponsor map); fase 2 → Tarefa 7; 5.2 → Tarefas 1 a 6; 5.3 → Tarefas 2 a 5; 5.4 → Tarefa 0; 5.5 → Tarefa 9; 5.6 → Tarefas 8, 9, 10; seção 6 → Tarefa 11; seção 7 → Tarefas 0, 0B e 13; seção 8 → Tarefas 12 e 13; seção 10 → Tarefa 13. Revisão técnica: achados 1.x → Tarefas 0 a 6; 2 → Tarefa 3; 3 → Tarefa 2; 4 → Tarefa 7; 5 → Tarefas 3 e 4; 6.1 → Tarefa 12; 6.2 e 6.3 → Tarefa 13; 7.x → Tarefas 1 a 8 e 11. Discovery (`04-discovery-personas.md`): protocolo e roteiro → Tarefa 0B; premissas P5, P7, P8 e P12 → Tarefas 11, 12 e 13.
- **Consistência de nomes:** `carregar`, `recortar`, `Dados`, `aprender_janela`, `Janela`, `prazo_do_deal`, `estado`, `datas_analogas`, `tabela_destino`, `carga_referencia`, `pontuar`, `explicar`, `resumo_vendedor`, `construir`, `conferir`, `backtest`, `razao_com_ic`, `permutacao`, `validar`, `preencher`, `gerar`, `Manipulador`. Colunas: `vendedor`, `produto`, `produto_crm`, `valor_tabela`, `idade`, `faixa`, `prazo`, `dias_restantes`, `estado`, `p_decide`, `ve_28`, `ve_trimestre`, `fila`, `chave`, `posicao`, `em_foco`, `indice`, `verbo`.
- **Review Focus:** 1 → Tarefa 1 (`test_recortar_nao_vaza_futuro`) e Tarefa 4 (`test_pontuacao_independe_do_futuro`); 2 → Tarefa 3 (`test_faixa_rala_e_agrupada`); 3 → Tarefas 4, 5 e 6 (`test_vendedor_sem_deal`, `resumo_vendedor` de Carl Lin, `tem_deal` no contrato); 4 → Tarefa 1 (`test_produto_desconhecido_vai_para_qualidade`); 5 → Tarefas 9 e 10.
- **Valores de ouro:** todos vêm de `analise/eda-06-prototipo-motor-v2.saida.txt`, gerada pelo protótipo da mesma especificação. Se um teste falhar, a primeira coisa a conferir é se a implementação divergiu do protótipo, não se o número está errado.
- **Corte se o dia atrasar** (nesta ordem): Tarefa 0B vai para a versão curta de 40 minutos (seção 9 do roteiro), nunca para zero; Tarefa 9 vira só template (`--sem-ia`); Tarefa 10 vira `localStorage`; Tarefa 8 vira uma seção da Tela 3; Tarefa 11 perde a Tela 3 para o README; Tarefa 12 fica em tabelas curtas. **Tarefas 2, 3, 7 e 13 nunca são cortadas** — são o score com evidência e a comunicação, que é o que diferencia.
- **Por que a Tarefa 0B não pode ir a zero:** ela é a única coisa no plano que testa as quatro premissas capazes de matar o produto em adoção (P5, P7, P8, P12), e é a única que dá mecanismo ao achado central, que é também o maior risco declarado da submissão. Se ela for cortada, o `limitacoes.md` precisa dizer que nenhuma premissa de adoção foi testada.
