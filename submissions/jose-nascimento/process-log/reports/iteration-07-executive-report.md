# Report da Iteração 07 — Relatório executivo final e narrativa CEO

- **Executor:** agente único `deepseek-max` (via OpenCode Go), conforme plano de execução (regra 1).
- **HEAD base:** `fa6572f2913e0c001099b24993a7b4bc9634cb37` (esperado no prompt) — confirmado no início (working tree limpo, branch `submission/jose-nascimento`).
- **Prompt integral:** `process-log/prompts/iteration-07-prompt.md` (arquivado antes da implementação).
- **Narrativa pré-registrada:** `process-log/decisions/iteration-07-executive-report-outline.md` (commitada ANTES do gerador; adendo técnico §13 registra a remoção da âncora KM global não derivável e a 7ª tabela de segmentos).
- **Tempo de relógio:** ~2h30min (contexto + verificação de âncoras + outline + gerador com gates + integração pipeline/verifier + READMEs + validações + documentos).

---

## 1. Timeline (2 commits)

| Commit | Mensagem | Conteúdo |
|---|---|---|
| `1bbec67` (FASE A, antes do código) | `docs: define executive report narrative` | outline `process-log/decisions/iteration-07-executive-report-outline.md` + prompt arquivado `process-log/prompts/iteration-07-prompt.md`; push `fa6572f..1bbec67` |
| (FASE B) | `docs: deliver executive churn diagnosis` | gerador `solution/src/07_generate_executive_report.py`; `solution/report-executivo.md`; `README.md` da submissão (template oficial); `run.sh`/`Makefile` (estágio 07); `solution/src/06_verify_pipeline.py` (checks F1–F8); `solution/README.md` (41 derivados / 46 outputs); plano/checklist/este report |

FASE A: outline com 1 mensagem central, 3 provas (P1 pico 22,51% vs 13,01%; P2
mecanismo onboarding 83,7% + R1 ≤90d 68,4% + lift 1,57/1,56/1,83; P3 o resto
não explica), ask executivo (ACT-03 → ACT-01 + ACT-02; sem escala sem IC95),
claims permitidos/proibidos, 6 gráficos escolhidos, word budget (report
1.500–2.000; gate 1.400–2.400), critérios de CEO-readability.

## 2. Decisões (registradas no outline e adendo)

1. **Números derivados em runtime, nunca copiados:** o gerador lê tabelas/
   evidence/raw e deriva todos os números materiais (lentes, pico, R1,
   vereditos H3–H9 via células completas, segmentos t15, watchlist t16/t21,
   impacto t19, Wilson CI re-derivado de 83/193, MDE/poder/P(falso GO) do
   evidence 05 com gate de substring).
2. **Escrita all-or-nothing:** arquivo temporário + `os.replace` — o relatório
   só é escrito se TODOS os gates G1–G8 passarem; nunca fica parcial/stale.
3. **Gate G4 ciente de contexto:** claims proibidos são permitidos apenas com
   negação explícita no entorno (ex.: "não é perda"; seção "O que não fazer");
   contexto afirmativo = FAIL.
4. **Faixa ≠ CI:** incidência observada 0,3393–0,5417 rotulada como faixa
   observada entre cutoffs; CI de Wilson 95% (0,362–0,501) re-derivado em
   runtime e gateado contra o evidence 05.
5. **MDE/poder (68/51/37%; 11/31/61%; ≈24%)** citados do evidence 05 §5 com
   regex de âncora (re-derivação independente diverge 0–2 p.p. — convenções de
   arredondamento; adendo §13.3).
6. **KM global t6 removida** (adendo §13.1): pooled de t02b diverge da
   convenção do estágio 03 (0,462 vs 0,4428); usadas âncoras deriváveis (taxa
   global 70,4% e KM por coorte).
7. **Verifier ampliado sem renomear:** checks F1–F8 (presença, links, 6
   imagens 1×, word count, claims, contas ⊆ t16, ações ⊆ t18, 23 âncoras
   numéricas re-derivadas).

## 3. Word count e conteúdo

- `solution/report-executivo.md`: **2.389 palavras** (budget 1.400–2.400;
  alvo 1.500–2.000 no outline; dentro do gate); **executive summary: 322
  palavras** (gate 250–350); 6 imagens embutidas (1× cada); 41 links
  relativos (todos existentes); 7 tabelas compactas (lentes, segmentos,
  contas, ações, impacto, causal status/evidence map).
- `README.md` da submissão: índice executivo curto (~450 palavras de conteúdo
  próprio), template oficial preservado; tabela de ferramentas/orquestração
  INTACTA; data de submissão `pendente` (It10).

## 4. Gates do gerador (G1–G8) — PASS

| Gate | Check |
|---|---|
| G1 | 47 âncoras numéricas derivadas presentes no texto |
| G2 | contas citadas ⊆ t16 (10 de 20) |
| G3 | ações citadas ⊆ t18; decisões Now/Later consistentes |
| G4 | zero claims proibidos em contexto afirmativo |
| G5 | 41 links relativos existem; exatamente 6 imagens, cada uma 1× |
| G6 | word count 1.400–2.400; executive summary 250–350 |
| G7 | zero tokens proibidos (concorrentes/pesquisa interna/baseline) |
| G8 | sem marca de geração temporal (determinismo) |

Verifier: checks F1–F8 PASS (23 âncoras re-derivadas independentemente).

## 5. Erros reais encontrados e corrigidos (nunca "não houve erros")

1. **Regex de parêntese desbalanceado** no padrão H5 do gerador (`\\)` gravado
   como `\\;` — parêntese de fechamento sem abertura): corrigido com classes
   `[(]`/`[)]`; diagnóstico via `re.error` com posição.
2. **`to_string()` truncava células longas** do t10 (max_colwidth=50) e
   quebrava os regexes de vereditos: passou a extrair células completas por
   chave (`df[df[key]==k][col].iloc[0]`).
3. **Evidence 05 com quebras de linha no meio de frases** (markdown wrap):
   regexes falhavam; normalização `re.sub(r"\s+", " ", ev05)` antes de casar.
4. **Regex MDE não casava** `37%** de redução` (fechamento de negrito):
   padrão tolerante `[^\d]*de redução`.
5. **Frase "não é receita salva"** disparava o gate G4 ingênuo: gate
   reescrito como contexto-afirmativo (negação no entorno ±90 chars permite).
6. **Word count 3.103 → 2.389:** três rodadas de enxugamento de prosa
   (seções 1–10) com re-medição por seção; tabelas compactadas (contas 13→10
   linhas; células de ações truncadas com rstrip de pontuação pendurada).
7. **KM global 0,4428 não derivável** sem reimplementar a convenção do estágio
   03 (pooled t02b = 0,462): adendo técnico no outline; âncora substituída.
8. **`h4_churn`/`lifts_txt`** — erros de escopo/ordem de definição e de
   extração multi-grupo (`_extract` retornava só o 1º grupo): corrigidos com
   `_extract_multi` e helpers de módulo.
9. **MDE/poder truncados ao 1º grupo** (`68` em vez de `68% / 51% / 37%`):
   extração multi-grupo com junção `% / % / %`; re-render com 2.389 palavras e
   `p.p.` duplo corrigido (h6_gap sem sufixo; template adiciona o sufixo).

## 6. Validações executadas (detalhe final no commit)

1. `./run.sh` 2× + CWD diferente: outputs byte-idênticos (46 outputs;
   report novo incluso); tree limpa (zero untracked, zero `__pycache__`).
2. Clone fresco da branch em sandbox (sem `/tmp/opencode/ravendata`): run.sh
   regenera tudo; `report-executivo.md` byte-idêntico; verificador PASS.
3. Markdown: headings `## 1..10` únicos; 41 links relativos resolvem; 6
   imagens 1× cada (verifier F2/F3).
4. 6 PNGs inspecionados programaticamente (magic bytes + tamanho).
5. 3 spot checks manuais independentes (ver abaixo).
6. FAIL — input ausente (t16 removida): gerador exit **1** (confirmado sem
   pipe) SEM escrever o report (sem stale; `os.replace` não executa);
   verifier F6/F8/F1 também falham com diagnóstico.
7. Sem nova dependência: gerador usa stdlib + pandas (requirements intacto);
   verifier D4 (zero imports de rede) PASS com o script 07 incluído.
8. `git diff --check` limpo.
9. Verificador final: **77 PASS / 0 FAIL** (68 anteriores + 8 checks F +
   B4 do report); pipeline completo em ~65 s (6 estágios + verificação).

**Spot checks manuais (3):** (a) dez/24: 43 primeiros eventos / 191 elegíveis
= 22,51% e 117 episódios totais (t01 confirmado); (b) R1 ≤ 90d = 806.419 /
1.179.139 = 68,4% (t03 confirmado); (c) top-20 = 392.030 US$ = 10,7% de
3.668.852 US$; 8+12 split (t16/t21/painel confirmados).

## 7. Riscos remanescentes e handoff (Iteração 08)

1. **Word count próximo do teto (2.391/2.400):** margem estrutural pequena;
   revisões de It08/09 devem medir antes de adicionar texto (gate G6/F4).
2. **Gate G4 por janela de negação (±90 chars):** falso positivo possível se
   um termo proibido aparecer longe de sua negação; re-verificar no QA It09.
3. **Âncoras F8 acopladas ao template do gerador:** mudanças de fraseado no
   relatório exigem atualizar o verificador na mesma revisão (prática G13
   das It04/05).
4. **It08:** process log final (prompts literais, erros 5–8 com causa raiz —
   este report já registra 8), decisões "minha vs consenso vs IA", evidências;
   **It09:** QA integral (re-execução, greps de originalidade, checklist);
   **It10:** data de submissão no README + PR.
5. **Time budget:** acumulado segue acima do gatilho de contenção (registrado
   em F11 do checklist; decisão consciente por gates obrigatórios).

## 8. Estados (atualizados no plano/checklist)

- **It07 `CONCLUDED`** (implementação + validações acima; critérios de
  aceitação atendidos: causa raiz/segmentos/ações/impacto respondidos com
  números derivados; CEO lê e age; 6 gráficos embutidos; report reproduzível;
  README completo; honestidade estatística; process/git completos).
- **Review gate 3x da It07: `PENDING`** (dispara em seguida; ledger em
  `process-log/reviews/` quando concluído).
- It08–It10: `PENDING`.