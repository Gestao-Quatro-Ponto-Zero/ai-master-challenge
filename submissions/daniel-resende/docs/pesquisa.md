# Pesquisa de evidência: priorização de pipeline

Início 2026-11-10 15:10:53 -03; fim 2026-11-10 15:14:41 -03 (último `date`; gravação logo depois). Acesso a todas as fontes: 2026-11-10. Só conta como verificado o que abri e li.

## 1. Como deals abertos são ranqueados

- Salesforce mostra o score em três faixas (High 67–99, Med 34–66, Low 1–33), "replacing the 1–99 numeric scores" no Pipeline Inspection, com seta quando o deal muda de faixa (Trailhead, "Understand Deal Health...").
- Gong: o score é percentil, não probabilidade ("It doesn't represent an 80% probability of closing"); faixas Low 1–29, Fair 30–75, High 76–99 (Gong Help, "AI Deal Predictor", 2025-07-16). HubSpot descreve o score como "percentage probability", mas diz "for information only" e que o modelo "may not always be accurate" (HubSpot KB, 2025-12-08).
- "Mais velho que o normal": o Pipeline Inspection tem o insight "Deal progress", que compara o deal a deals parecidos ("too long in the current stage") (Trailhead, mesma página). O módulo "Identify Stuck Sales Deals" usa limite fixo por etapa (exemplo: 30, 45, 15 e 30 dias), definido com a liderança de vendas.
- Pipedrive mede inatividade, não idade: o deal fica vermelho após N dias parado na etapa, e atividade, nota, edição ou e-mail zera o contador (Pipedrive Support, 2026-09-03).
- Calibração: entre as amostras com probabilidade prevista perto de 0,8, cerca de 80% devem ser positivas; confere-se com diagrama de confiabilidade. O Brier score sozinho é "of limited use" para calibração; isotonic só supera sigmoid com mais de ~1000 amostras; o calibrador deve ser ajustado em dados separados (scikit-learn 1.9.1).
- Deal aberto é dado censurado: não misturar idade de aberto com duração de fechado numa média de ciclo (Trellus, 2026-10-29; blog de fornecedor).

**Inferências minhas:** (a) sem log de atividade, o único sinal de "esfriando" é a idade na etapa Engaging contra deals parecidos; (b) a chance condicional de ganhar, dado deal aberto na idade t, é (S(t) − S(t+Δ)) / S(t) na curva de sobrevivência, fórmula padrão que nenhuma fonte aberta enuncia; (c) uma regra por datas só vira "chance" se a taxa observada por faixa fechar em teste temporal.

**O que isso muda no desenho:** três grupos, sem número com cara de probabilidade. Idade contra o usual = percentil da idade entre deals fechados parecidos (mesmo produto ou setor), sem misturar abertos. Só chamar de "chance" o que passou por diagrama de confiabilidade em dados de teste.

**Não verificado:** o post "BizStat" (Columbia, 2019-10-08) deu 403; pipeline ponderado (valor × probabilidade), o corte de 200 deals ganhos do Einstein e o "50 dias" da Outreach só vi em resultados de busca; não achei fonte primária que avise contra ranquear só por valor.

## 2. Explicações geradas presas ao registro

- Saída estruturada garante forma, não verdade: "guarantee schema-compliant responses through constrained decoding"; a página não promete valores corretos e restrições numéricas (`minimum`, `maximum`) não são impostas (Claude API Docs, "Structured outputs", sem data).
- Técnicas da Anthropic: permitir "não sei", extrair citações literais antes, e retirar toda afirmação sem citação de apoio; a página diz que isso "reduz significativamente mas não elimina" (paráfrase de "significantly reduce hallucinations, they don't eliminate them entirely") (Claude API Docs, "Reduce hallucinations", sem data).
- Citação também falha: só 51,5% das frases estavam totalmente sustentadas por suas citações e 74,5% das citações sustentavam a frase, em quatro buscadores generativos (Liu, Zhang, Liang, arXiv 2304.09848, 2023). Até 57% das citações podem não ter informado a resposta ("post-rationalization") (Wallat et al., arXiv 2412.18004, 2024-12-23; só li o resumo).
- Verificação no renderizador: Proof-Carrying Numbers emite números como tokens ligados a afirmações estruturadas, checados por código (exato, arredondado, tolerância); o que não passa fica "não verificado" (Solatorio, arXiv 2509.06902, 2025-09-08). Preprint teórico, sem experimento; só li o resumo.

**Inferência minha:** citar fatos não basta; a checagem tem de ser feita por código sobre o texto final.

**O que isso muda no desenho:** o modelo nunca escreve número, data ou nome; escreve a frase com marcadores (`{dias_na_etapa}`, `{conta}`) que o código preenche do registro. Um verificador rejeita dígito ou nome próprio fora dos fatos do deal e, se falhar, usa texto fixo. Grupo e próximo passo vêm da regra.

**Não verificado:** taxa de erro numérico de modelos atuais com contexto curto como o nosso; nenhuma fonte aberta a mede.

## 3. O que o vendedor vê na primeira tela

- HubSpot: coluna "Deal Score" na tabela; o mouse mostra os fatores; o cartão do registro lista os cinco fatores principais, cada um positivo ou negativo, com tendência (HubSpot KB, 2025-12-08).
- Salesforce Pipeline Inspection: faixa colorida por deal, painel lateral de Insights, filtros rápidos por data de fechamento, dono e "recent changes", métricas clicáveis (Overdue, Increased) (Trailhead, duas páginas). As colunas por deal não estão descritas.
- Gong deal board: valor, data de fechamento esperada, dono e etapa; "Warnings" com sugestão de mitigação; score com sinais positivos e negativos (Gong Help, 2026-06-29).
- Pipedrive: um único estado visual, a cartela vermelha de deal parado, mais filtro de deals "rotten" (Pipedrive Support, 2026-11-06; as condições do filtro estão numa imagem que não li).

**Padrão (inferência minha sobre quatro produtos):** indicador curto por deal (faixa de 3 níveis ou cor), motivos com sinal a um clique ou hover, um estado único de alerta, filtros por dono e data. Nas páginas abertas, nenhum mostra o próximo passo como texto na linha.

**O que isso muda no desenho:** lista curta de cartões, não tabela; cada cartão com grupo, até 3 motivos com sinal (idade na etapa, valor de tabela, porte da conta) e próximo passo por regra; detalhe a um clique.

**Não verificado:** quantos itens cabem na primeira tela (nenhuma fonte diz); como qualquer produto trata "deixar ir" (nenhuma fonte aberta descreve; é decisão nossa, sem precedente verificado); a tela do Clari (só resultado de busca e página com 403).

## Fontes

| Título | Publisher | URL | Data da fonte |
|---|---|---|---|
| Understand Deal Health with Insights and Scores | Salesforce Trailhead | https://trailhead.salesforce.com/content/learn/modules/sell-smarter-with-pipeline-inspection/understand-deal-health-with-insights-and-scores | sem data |
| Review Deal Health with Pipeline Inspection | Salesforce Trailhead | https://trailhead.salesforce.com/content/learn/modules/introduction-to-revenue-intelligence-for-sales-cloud/review-deal-health-with-pipeline-inspection | sem data |
| Identify Stuck Sales Deals | Salesforce Trailhead | https://trailhead.salesforce.com/content/learn/modules/sales-deal-acceleration/identify-stuck-sales-deals | sem data |
| Understanding AI Deal Predictor | Gong Help | https://help.gong.io/docs/understanding-ai-deal-predictor | 2025-07-16 |
| Understanding deal boards | Gong Help | https://help.gong.io/docs/understanding-deal-boards.md | 2026-06-29 |
| Use deal scores | HubSpot KB | https://knowledge.hubspot.com/records/use-deal-scores | 2025-12-08 |
| The Rotting feature | Pipedrive Support | https://support.pipedrive.com/en/article/the-rotting-feature | 2026-09-03 |
| Filters: common uses | Pipedrive Support | https://support.pipedrive.com/en/article/filters-common-uses | 2026-11-06 |
| 1.16 Probability calibration (v1.9.1) | scikit-learn | https://scikit-learn.org/stable/modules/calibration.html | © 2007–2026 |
| Right-Censored Data: Keep Open Deals in the Picture | Trellus | https://www.trellus.ai/learning-center/right-censored-sales-cycle-data | 2026-10-29 |
| Structured outputs | Claude API Docs | https://platform.claude.com/docs/en/build-with-claude/structured-outputs | sem data |
| Reduce hallucinations | Claude API Docs | https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/reduce-hallucinations | sem data |
| Evaluating Verifiability in Generative Search Engines | arXiv (Liu, Zhang, Liang) | https://arxiv.org/abs/2304.09848 | 2023-04-19 (v2 2023-10-23) |
| Correctness is not Faithfulness in RAG Attributions | arXiv (Wallat et al.) | https://arxiv.org/abs/2412.18004 | 2024-12-23 |
| Proof-Carrying Numbers (PCN) | arXiv (Solatorio) | https://arxiv.org/abs/2509.06902 | 2025-09-08 |

Acesso a todas: 2026-11-10.

## 4. Figuras que se leem sozinhas (acrescentado em 10/11/2026, prompt 02x)

Fontes lidas pela pesquisa do orquestrador em 10/11/2026; o que cada uma sustenta nesta tela:

- **Posição numa escala comum se lê melhor que comprimento, área ou ângulo.** Heer e Bostock, "Crowdsourcing Graphical Perception", CHI 2010, https://homes.cs.washington.edu/~jheer/files/2010-MTurk-CHI.pdf . Aqui: a figura do vendedor é uma linha do tempo só, e cada negócio vivo é uma marca na posição da idade dele; as barras do gestor têm todas o mesmo comprimento e a mesma origem.
- **Projetar objetos 3D em duas dimensões distorce o dado; barras 3D parecem mais curtas do que são.** Wilke, "Fundamentals of Data Visualization", capítulo 26, "Don't go 3D", https://clauswilke.com/dataviz/no-3d.html . Aqui: saíram as colunas com volume; nada na tela está em perspectiva nem extrudado.
- **Mais de uma escala quantitativa no mesmo eixo convida a comparar grandezas que não se comparam.** Few, "Dual-Scaled Axes in Graphs", Perceptual Edge, 2008, https://www.perceptualedge.com/articles/visual_business_intelligence/dual-scaled_axes.pdf . Aqui: saiu o bloco com a contagem "para limpar" ao lado de colunas de "ganhos em cada 100"; a contagem virou uma linha de texto e a tabela do tempo saiu da primeira vista.
- **Posição e comprimento para quantidades, cor para destacar, sem 3D, leitura rápida com o mínimo de interação.** Laubheimer, Nielsen Norman Group, "Dashboards: Making Charts and Graphs Easier to Understand", 2017, https://www.nngroup.com/articles/dashboards-preattentive/ . Aqui: a cor de vivo, de alerta e de fora aparece só em marcas, palavras e barras finas; as áreas grandes ficam neutras.

**O que não teve fonte:** nenhuma das quatro aprova, pelo nome, profundidade decorativa. Manter a profundidade como luz e sombra que não carregam número nenhum é inferência nossa a partir delas, não uma afirmação delas.
