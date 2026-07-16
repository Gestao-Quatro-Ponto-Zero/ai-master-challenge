# Relatório de métodos estatísticos

**Gate:** INF
**Unidade:** post; 52.214 observações; 5.000 clusters de creator
**Desenho:** observacional, provavelmente sintético

## Estimando principal

Diferença média ajustada em engagement por view associada a `is_sponsored`, controlando plataforma, tipo e categoria de conteúdo, log de seguidores, content length, hashtags, idioma, audiência agregada e mês. A incerteza usa erros-padrão clusterizados por `creator_id`.

## Resultado de patrocínio — INF-SPON-001

- Estimativa: −0,00001025, equivalente a −0,00103 ponto percentual.
- IC95%: −0,00009451 a 0,00007400, ou −0,00945 a +0,00740 p.p.
- `p=0,8115`; não há evidência contra efeito nulo.
- O intervalo inteiro fica dentro de ±0,05 p.p. e ±0,10 p.p.; isso é uma sensibilidade de equivalência, não um threshold comercial aprovado.
- R² do modelo: 0,000899. Os atributos disponíveis explicam menos de 0,1% da variação do engagement.

### Outcomes secundários

| Outcome | Efeito patrocinado | IC95% | p |
|---|---:|---:|---:|
| views | +0,262 view | −1,500 a +2,025 | 0,7705 |
| share rate | −0,00001372 | −0,00004382 a +0,00001639 | 0,3719 |
| views/follower | +0,0006089 | −0,003813 a +0,005031 | 0,7872 |

Nenhum outcome oferece evidência de ganho por patrocínio. Custos e receita não existem, portanto ROI permanece não estimável.

## Overlap e seleção observável

Um propensity model diagnóstico, com os mesmos controles observáveis, apresentou AUC in-sample 0,518. Propensities variam de 0,360 a 0,484, com 0% fora de `[0,1; 0,9]`. Há excelente suporte comum observável; ao mesmo tempo, o AUC próximo de 0,5 reforça que o patrocínio parece quase aleatório no processo gerador sintético. Isso não elimina confundimento não medido em dados reais.

## Heterogeneidade e multiplicidade

Interações patrocínio×plataforma foram testadas como uma família e corrigidas por Benjamini–Hochberg. O menor p ajustado foi 0,6968; nenhuma heterogeneidade foi validada. Rankings exploratórios de células pequenas foram rejeitados como base de decisão.

## Plataforma, formato e categoria

No modelo ajustado, todos os coeficientes desses grupos são pequenos e seus intervalos incluem zero. Exemplos:

- Instagram versus baseline Bilibili: −0,0095 p.p.; IC95% −0,0227 a +0,0038 p.p.;
- text versus baseline image: +0,0111 p.p.; IC95% −0,0053 a +0,0275 p.p.;
- tech versus baseline beauty: −0,0050 p.p.; IC95% −0,0164 a +0,0064 p.p.

Não existe evidência validada para declarar uma plataforma, formato ou categoria vencedora.

## Diagnósticos e limitações

- Erros clusterizados tratam repetição por creator, mas nomes inconsistentes limitam interpretação da entidade.
- OLS estima diferença média e facilita interpretação; robustez vem de clustering e outcomes alternativos.
- A extrema concentração e ausência de zeros reduzem relevância prática e validade externa.
- O processo parece sintético e quase estacionário; inferência descreve este arquivo, não o mercado.
- Não há desenho causal, custos, receita, frequência planejada ou exposição paga.
- Thresholds de equivalência e métrica primária ainda requerem validação humana antes de política permanente.

## Veredicto do Statistician

`INF-SPON-001=VALIDATED`: ausência de associação material detectável entre patrocínio e performance no dataset. Findings exploratórios que sugerem winners por rankings permanecem `REJECTED` para decisão. A estratégia deve priorizar instrumentação, experimentos e critérios de parada, não realocação baseada em diferenças artificiais.

Artefatos: `outputs/tables/INF-*.csv`, `outputs/evidence/inference-evidence-records.json` e `src/analysis/run_inference.py`.
