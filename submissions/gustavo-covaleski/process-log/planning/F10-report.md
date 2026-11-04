# F10 — Report (Console do piloto)

Caminhos relativos à submissão (`ai-master-challenge/submissions/gustavo-covaleski/`).

**Commit:** `b5c5f3369a2a5268f2f2167d1e3ad480b775e7dd`, "F10: console do piloto estático (fila, governança, sombra, injeção, duplicado)". Sem push. Não rodei a Vercel nem fiz login em nada.

## 1. O que foi feito

1. **`solution/f10_console_dados.py` → `console/data.js`** (`window.DADOS`, 683 KB). Contém:
   - `meta`;
   - `politicas` F9, F8 e F4, lidas dos CSV/JSON existentes;
   - `fila`: 300 tickets do holdout, seed 42, 20 dias de 15, texto até 400 caracteres com `truncado`, classificados por `triagem.classificar`, faixa e porquê nas 3 políticas;
   - `ataques`: 300 × 5 com o clássico;
   - `governanca`: holdout inteiro, ordem seed 42, 20 dias, acumulado;
   - `kpis`.

   A checagem obrigatória do dia 20 está no próprio script, que para se falhar.
2. **`solution/tests/test_f10.py`** (5 testes): JSON válido; 300 tickets em 20 dias; checagem do dia 20; sem nome ou e-mail do DS1; nenhum 8-grama de ticket fora dos 300 ids.
3. **`console/index.html`, `styles.css`, `app.js` e `vercel.json`:** HTML/CSS/JS puros, sem framework, sem CDN, sem backend; abre por `file://`. A tela tem:
   - barra com dia, modo ativo/sombra, política, alertas e ajuda;
   - fila com filtros e teclado (↑/↓, Enter confirma, 1–8 corrige);
   - detalhe com o porquê em 4 passos, confirmar/corrigir, reentrega duplicada (chave `evt:` como em `triagem.py`, citando `test_f8.py`), reembolso e injeção;
   - governança com a barra do IC e as metas, a regra de hoje (promover/manter/rebaixar) e o gráfico SVG;
   - cartões com as premissas editáveis;
   - alertas, log da tela e rodapé.
4. **Verificação no Playwright:** por `file://` e por `python -m http.server`, a 1440 × 900 e a 390 × 844. Foram gerados 4 screenshots com `deviceScaleFactor` 2.
5. **Documentos:** README (linha do console no topo, `c1` embutido e os demais linkados, Limitações, "Como rodar"); process log (linha 13 e a exceção dos 300 tickets com texto).

## 2. Resultados

| Item | Valor | Origem |
|---|---|---|
| Checagem do dia 20: LI de Access / Purchase | 0,9749 / 0,9782 = `li_ia_decide` do holdout | `f10_console_dados.py` → `data.js`; `f8_politica_por_categoria.csv` |
| Checagem do dia 20: cobertura de IA decide na F9 | 13,37% = `f8_faixas.json` (`implantada`) | idem |
| Governança sombra, dia 20: LI por categoria | Access 0,9749; Administrative rights 0,8968; HR Support 0,9604; Hardware 0,9428; **Internal Project 0,9506**; Miscellaneous 0,9636; Purchase 0,9782; Storage 0,9582 | `data.js` (`governanca[19]`) |
| Ataques nos 300 da fila com dano silencioso na F8 | 7 tickets (todos "categoria_repetida", HR Support → Storage); 0 na F9 | `data.js` (`ataques`) |
| Erros de JS (`file://` e `http`, 2 larguras) | 0. Único erro de console: 404 do `favicon` no `http.server` | Playwright |
| Rolagem horizontal | nenhuma (1440 e 390 px) | Playwright |
| Testes | **76 passed** | `pytest solution/tests -q` |
| `f1_splits.csv` | SHA-256 `37703450…865ba0` (inalterado) | — |

**Screenshots** (`process-log/screenshots/`):

| Arquivo | O que mostra |
|---|---|
| `c1_console.png` | visão geral no dia 20 |
| `c2_governanca.png` | painel de governança com Hardware no gráfico |
| `c3_injecao_f8_vs_f9.png` | ticket 10244 com o mesmo ataque: F8 → dano silencioso em IA decide; F9 → IA sugere |
| `c4_sombra.png` | modo sombra com o painel de alertas: queda de 13,4 p.p. na cobertura, injeção na F9 em 0 de 6.395, e Internal Project com a regra discordando da política vigente |

## 3. O que contraria a hipótese ou a expectativa

- **Internal Project:** a governança sombra no holdout inteiro dá limite inferior de 0,9506, abaixo da meta de IA sugere (0,9545). Pela regra da F4, a categoria cairia para humano, mas a política vigente (F9) a mantém em IA sugere: na seleção fora da dobra o LI foi 0,9669, e a confirmação no holdout só olha a faixa IA decide. O console mostra isso como alerta permanente.
- **Hardware:** a curva diária do limite inferior fica perto da meta de IA sugere ao longo do piloto, mas termina abaixo dela (0,9428 no dia 20).

## 4. Desvios da spec

- **`c3`:** é uma composição lado a lado de duas capturas do painel de detalhe (F8 e F9), montada numa página temporária no próprio Playwright, sem dependência nova.
- **Governança da política F4:** usa o limiar da F8/F9 (0,71) para a precisão sombra. As contagens por faixa usam os limiares de cada política.
- **`latencia_ms`:** fica `null` no log da tela, porque o console não mede latência.
- **Teste de texto (`test_texto_so_dos_300_ids_da_fila`):** ignora 8-gramas que também existem em algum dos 300 tickets, porque quase-duplicados compartilham trechos legitimamente.
- **Rodapé:** o link do README aponta para o arquivo na branch `submission/gustavo-covaleski` do fork no GitHub. Vale depois do push.

## 5. Erros e correções durante a execução

- A sessão foi interrompida por limite de uso depois da verificação no Playwright e retomada. Nenhum arquivo commitado mudou nesse intervalo (`git status` limpo nos arquivos rastreados).
- `findstr` falhou na checagem de segredo ("linha muito longa"), porque o `data.js` é uma linha única. Refiz com `git diff --cached | grep -c "sk-ant"` → 0.

## 6. Pendências e decisões que dependem do Gustavo

1. **Deploy (você roda):**
   ```
   cd ai-master-challenge/submissions/gustavo-covaleski/console
   npx vercel
   npx vercel --prod
   ```
   - Na 1ª vez, `npx vercel` pede login: ele abre o navegador para você entrar na conta da Vercel (GitHub, e-mail etc.) e autorizar o CLI. Depois pergunta escopo, nome do projeto e diretório; aceite os padrões. Não há build, porque o site é estático.
   - `npx vercel` gera uma URL de pré-visualização; `npx vercel --prod` publica e imprime a URL de produção.
   - Depois, troque `[URL — preencher após o deploy]` no README.
2. **Internal Project:** manter em IA sugere ou aplicar a regra da governança (humano)? Ver §3.
3. "Decisão minha" da F10 no process log.
4. Push e PR.

## 7. Tempo gasto × orçado

- Orçado: 90 min (teto 108).
- Relógio: 02:22–02:35 antes da interrupção e 13:32–13:36 depois. Cerca de 20 min de execução.
