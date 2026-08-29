# Process Log — Carlos Persike — Challenge 003 (Lead Scorer)

> Log capturado durante a construção, não reconstruído no final.

## 2026-08-29 — Troca de challenge

Comecei o repositório no Challenge 002 (suporte). Decidi trocar para o **003 — Lead Scorer**
porque (a) é o mais "mão na massa" — deliverable é software rodando, não documento — e
(b) o pool de submissões públicas do repo tem forte concentração no 002, então o 003
diferencia mais.

Removido tudo do 002 via `git rm` (commit `a95b178`), mantendo o histórico do 002 no log do
git — não é squash, é decisão registrada.

## Decomposição inicial

Antes de escrever qualquer prompt de análise, quebrei o problema em:

1. **Auditar os 4 CSVs antes de montar qualquer score.** Já rodei uma checagem rápida em
   Python puro (sem pandas, pra ser rápido) em `sales_pipeline.csv` contra `products.csv` e
   `accounts.csv`. Achados que mudam a arquitetura:
   - `deal_stage` = Won 4238 / Lost 2473 / Engaging 1589 / Prospecting 500. Só Engaging +
     Prospecting (2.089 deals, 23,7%) são "abertos" — é isso que o vendedor precisa
     priorizar. Won/Lost são histórico, servem pra treinar o sinal, não pra mostrar na tela.
   - **Bug de join:** produto `GTXPro` aparece no pipeline mas o catálogo tem `GTX Pro`
     (com espaço). Sem corrigir isso, todo deal desse produto perde o preço de tabela no
     join. Precisa de normalização de string antes de qualquer merge.
   - **1.425 de 8.800 linhas (16,2%) têm `account` em branco** — não dá pra usar
     revenue/employees da conta como feature nesses casos sem um fallback explícito.
   - `Prospecting` não tem `engage_date` preenchido (faz sentido — ainda não engajou), então
     "dias parado no estágio" só é calculável a partir de Engaging em diante.
2. **Scoring tem que ser explicável.** O brief é claro: "se o vendedor entender POR QUE o
   deal tem score 85, a ferramenta é 10x mais útil". Isso descarta caixa-preta pura. Decisão:
   combinar taxa de conversão histórica por segmento (produto × setor × porte de conta) —
   calculada a partir de Won/Lost reais — com um fator de urgência (tempo parado no estágio
   vs. mediana histórica de deals fechados) e valor do deal. Cada fator vira uma linha de
   explicação na interface, não um número solto.
3. **Interface:** Streamlit (dependência nova — justificativa: é o exemplo #1 do próprio
   brief, roda em uma página, e o time de RevOps não vai instalar nada além de
   `streamlit run`). Filtro por vendedor/manager/região, conforme sugestão de bônus do brief.

## Ferramentas usadas

| Ferramenta | Para quê |
|---|---|
| Claude Code | Auditoria de dados, arquitetura, implementação do scoring e da interface |

## Auditoria de sinal (antes de montar o score)

Rodei testes estatísticos em `sales_pipeline.csv` (Won vs. Lost, os únicos deals com
resultado conhecido) antes de decidir a lógica de scoring:

| Feature testada | Teste | Resultado | Tem sinal? |
|---|---|---|---|
| `product` → ganhar/perder | chi² de independência | p = 1,0 | **Não** |
| `sales_agent` → ganhar/perder | chi² de independência | p = 0,264 | **Não** |
| `revenue`/`employees` da conta → ganhar/perder | correlação ponto-bisserial | p = 0,31 / 0,49 | **Não** |
| Regressão logística (agente+produto+setor+valor+dias) → ganhar/perder, holdout 20% | AUC / acurácia | AUC 0,559 (quase aleatório); acurácia igual ao baseline de classe majoritária (0,63) | **Não, na prática** |
| Dias entre engajamento e fechamento → ganhar/perder | Mann-Whitney U | p = 1,2×10⁻²⁶ (mediana Won = 57 dias, mediana Lost = 14 dias) | **Sim, e é contraintuitivo** |

**Decisão que isso força:** um classificador de "probabilidade de fechar" baseado em
produto/setor/vendedor seria estatisticamente vazio — é exatamente o tipo de número que um
LLM geraria e reportaria como "acurácia 63%" sem checar contra o baseline (que também é
63%, porque a classe majoritária já é Won). Descartei essa abordagem.

O único sinal real e validado é **tempo de vida do negócio**: deals perdidos morrem rápido
(mediana 14 dias), deals ganhos demoram mais (mediana 57 dias) — ou seja, um deal que já
está engajado há um tempo **já sobreviveu** ao período onde a maioria dos deals ruins morre.
Isso inverte a intuição ingênua de "deal parado há muito tempo = deal esfriando" — pelo
menos para o campo `deal_stage=Engaging`. Validei com holdout 80/20 usando faixas de dias
(decis) calculadas só no treino: AUC 0,592, taxa de conversão sobe de ~53% (0-4 dias) pra
~70%+ (13+ dias) e se mantém nesse patamar. Sinal real, mas modesto — vou reportar isso com
o número, não inflar.

**Arquitetura de score decidida:** Valor Esperado = probabilidade histórica de ganhar (pela
faixa de dias desde o engajamento, calibrada no dataset completo) × valor do produto
(`sales_price`, corrigido o bug de join `GTXPro`/`GTX Pro`). Isso é honesto, explicável
linha a linha, e responde exatamente ao que a Head pediu — sem fingir um sinal de
produto/vendedor que os dados provam que não existe.

## Erros da IA capturados e corrigidos

- Primeira tentativa foi montar um classificador com produto + setor + vendedor + valor como
  features, sem testar significância antes — só percebi que não tinha sinal real quando rodei
  o holdout e vi AUC 0,559 e acurácia idêntica ao baseline. Corrigido: descartei a abordagem e
  testei feature por feature isoladamente pra confirmar que o problema era ausência de sinal,
  não erro de código.
- `auditoria.py` calculou "% sem conta vinculada" em cima do subconjunto errado (`fechados`,
  só Won/Lost) e rotulou como "todo o pipeline, incl. abertos" — deu 0,0%, porque Won/Lost tem
  100% de conta preenchida. Só percebi comparando com a checagem bruta que eu tinha feito antes
  em Python puro (1.425/8.800 = 16,2% em branco no pipeline todo). Corrigido: recalculei por
  `deal_stage` e o número real é bem mais grave — 68,5% do pipeline Engaging e 67,4% do
  Prospecting não têm conta, contra 0% em Won/Lost. Isso virou o segundo achado mais forte da
  submissão (é processo, não acaso: vendedor só preenche a conta perto do fechamento) e entrou
  como recomendação #1 no README.

## Workflow

1. Li o brief do 003 e os documentos de especificação (`submission-guide.md`,
   `CONTRIBUTING.md`, `templates/submission-template.md`) antes de tocar em dado.
2. Localizei o dataset (usuário já tinha baixado do Kaggle em `archive (2)/`), inspecionei os
   4 CSVs em Python puro pra achados rápidos (contagens, joins quebrados, nulos) antes de
   escrever qualquer script versionado.
3. Rodei os testes estatísticos de sinal (chi², correlação, Mann-Whitney, regressão logística
   em holdout) direto no terminal antes de decidir a arquitetura — essa parte não virou código
   de produção, foi exploração pra decisão.
4. Só depois de saber o que tinha sinal escrevi os módulos de domínio (`ingestao.py`,
   `auditoria.py`, `probabilidade.py`, `validar_modelo.py`, `priorizacao.py`) e a interface
   (`app.py`).
5. Rodei os scripts de auditoria/validação de ponta a ponta, corrigi o bug do `conta_desconhecida`
   (acima), subi o Streamlit local e testei no navegador: filtro por vendedor, filtro por
   região, tabela renderizando com explicação por linha — confirmado funcionando com o
   pipeline completo (2.089 negócios abertos), não com exemplos escolhidos a dedo.

## O que eu adicionei que a IA sozinha não faria

- A decisão de **testar significância estatística antes de escolher a feature**, em vez de
  aceitar o primeiro modelo que "roda" — o padrão de um LLM sem esse hábito seria reportar
  63% de acurácia como se fosse bom, sem checar o baseline de classe majoritária.
- A leitura de negócio de que "tempo de vida do deal" é sinal *positivo* pra deals ainda
  abertos (contraintuitivo) — não é um resultado que aparece sozinho no output do modelo, é
  interpretação de causa provável (deals ruins morrem rápido, então sobreviver é filtro).
- A decisão de **não** transformar o Valor Esperado numa decisão binária de
  ganha/não-ganha, e de deixar isso explícito nas Limitações — o risco de um vendedor tratar
  o score como profecia é real, e a submissão avisa disso.
- Corrigir o rótulo errado do `auditoria.py` em vez de aceitar "0% sem conta" — bater o
  número contra a checagem bruta anterior foi decisão minha, não algo que o script teria
  detectado sozinho.
- Primeira versão do `st.column_config.ProgressColumn` usava `format="%.0f%%"` com
  `min_value=0, max_value=1` — renderizou "1%" pra uma probabilidade de 72%, porque o
  formato printf-style não multiplica por 100 sozinho (só o preset `"percent"` faz isso, e
  esse preset trouxe casas decimais indesejadas, "71.69%"). Só percebi no teste visual no
  navegador, não no código. Corrigido: multipliquei a probabilidade por 100 antes de passar
  pra coluna e usei `min_value=0, max_value=100` com o printf-style, que dá controle exato
  de casas decimais.

## 2026-08-29 — Segunda rodada: UX/UI e formatação

Usuário reportou UI "muito feia" e formatação de R$ errada (estilo americano, vírgula como
milhar). Correções:

- `formatacao.py` novo: `moeda_brl()` e `moeda_brl_milhoes()` — o Streamlit não tem um
  formato de coluna pt-BR confiável (o preset `"localized"` depende do locale do navegador
  de quem está vendo, não é determinístico), então formatei como string em Python, testável.
- Tabela "Fila completa" deixou de ter uma coluna de texto corrido (`explicacao`) truncada e
  ilegível — virou colunas separadas (Dias, Probabilidade com barra visual, Valor do
  produto, Valor esperado), mais fácil de escanear e ordenar.
- Cards do "Top 5" e o "Detalhe de um negócio" ganharam badge de estágio (`st.badge`) e
  barra de progresso (`st.progress`) em vez de só texto.
- Adicionei testes pra `moeda_brl`/`moeda_brl_milhoes` em `test_dominio.py` — formatação de
  dinheiro pra um stakeholder de negócio é exatamente o tipo de coisa que não pode quebrar
  silenciosamente.

## 2026-08-29 — Terceira rodada: tema visual e textos mais simples

Usuário pediu textos mais simples e perguntou de onde vêm os dados / o que cada número
significa — respondi na conversa (dataset Kaggle CC0, 4 CSVs, `valor do produto` = preço de
tabela porque `close_value` real só existe pra negócio já fechado) e usei isso pra simplificar
a interface:

- `.streamlit/config.toml` — tema nativo do Streamlit (cor primária, fundo, fonte), em vez de
  CSS solto. Não existe "agente de designer" separado nas minhas ferramentas pra Streamlit
  rodando — expliquei isso ao usuário e fiz a passada de design eu mesmo.
- Texto técnico (`AUC`, `baseline classe majoritária`, fórmula do Valor Esperado) saiu da tela
  principal e virou um expander opcional "❓ Como o placar é calculado" — quem quer entender o
  método clica, quem só quer trabalhar não precisa ler.
- `_montar_explicacao()` em `priorizacao.py` ficou mais curta e conversacional: "Está aberto há
  95 dias. Negócios parecidos historicamente fecham em 72% dos casos." em vez de uma linha só
  de dados concatenados com `·`.
- Também respondi (sem construir, por enquanto) sobre puxar dado de Google Sheets/CRM via API
  em vez de CSV manual: tecnicamente simples pra Sheets, depende do CRM real pra CRM — mas não
  tem CRM real por trás desse dataset, então não construí, só documentei que `ingestao.py` já
  isola a leitura de dado bruto pra trocar depois sem afetar o resto do sistema.

