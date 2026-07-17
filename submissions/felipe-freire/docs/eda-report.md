# Relatório exploratório

**Gate:** EDA
**População:** 52.214 posts, 29/05/2023–28/05/2025
**Métrica:** `(likes + shares + comments) / views`, derivada pelo projeto

## Resumo

O achado exploratório dominante é a ausência de diferenças materialmente úteis. Engagement médio é 19,905%, com desvio-padrão de apenas 0,487 ponto percentual. Plataformas, formatos, categorias, creator size, audiência e patrocínio apresentam médias muito próximas. Com este dataset, rankings pequenos são mais compatíveis com ruído/amostragem do que com uma estratégia acionável.

## Evidence records

### EDA-BASE-001 — distribuição artificialmente estreita

- Estado: `EXPLORATORY`.
- Média: 0,19905454; mediana: 0,19899232; desvio-padrão: 0,00486930.
- Range: 0,17880096–0,22227895; nenhum post com views ou engagement zero.
- Interpretação permitida: o dataset tem pouca variação de performance.
- Limite: provável geração sintética e ausência de cauda real/fracassos.

### EDA-PLAT-001 — plataforma não diferencia performance bruta

- Melhor média: RedNote 0,199098; menor: Instagram 0,198993.
- Amplitude: 0,0001051, ou 0,0105 ponto percentual.
- Todas as plataformas têm mais de 10 mil posts.
- Não há base exploratória para “migrar orçamento” entre plataformas.

### EDA-CONTENT-001 — formatos têm médias quase iguais

- Melhor média: text 0,199151; menor: video 0,199030.
- Amplitude: 0,0001213, ou 0,0121 ponto percentual.
- Isso contradiz qualquer narrativa genérica de que vídeo “vence” por si só.

### EDA-COMBO-001 — rankings granulares são instáveis

- Entre células com `n ≥ 100`, a maior média foi Bilibili × vídeo × lifestyle × creators 10k–50k: 0,200105 (`n=109`).
- A menor foi Bilibili × vídeo × beauty × creators 50k–100k: 0,198451 (`n=137`).
- A distância é pequena e células têm múltiplas comparações; não usar como recomendação antes de validação e shrinkage.

### EDA-SPON-001 — patrocínio bruto é neutro

- Orgânico: 0,199059; patrocinado: 0,199048.
- Diferença patrocinado menos orgânico: −0,0000107, ou −0,0011 ponto percentual.
- Por plataforma, o sinal muda e as diferenças continuam pequenas.
- Extremos por células são dominados por amostras minúsculas; por exemplo, alguns grupos nano têm apenas 5–15 posts patrocinados.
- Não há custo: nenhuma conclusão de ROI é possível.

### EDA-AUD-001 — audiência não gera separação útil

- Localização: amplitude bruta de aproximadamente 0,0002112 (0,0211 p.p.).
- Idade e gênero também apresentam médias praticamente iguais.
- Como o atributo é uma categoria agregada por post, não permite inferência individual.

### EDA-TIME-001 — estabilidade temporal excessiva

- Médias mensais variam entre 0,1988777 e 0,1991688, amplitude de 0,0291 p.p.
- Estabilidade é consistente com processo gerador estacionário/sintético; não comprova ausência de sazonalidade no mundo real.

## O que não funciona nesta EDA

- ranking de plataforma isolado;
- regra universal por formato;
- patrocínio indiscriminado;
- thresholds de followers derivados de diferenças minúsculas;
- targeting por audiência com base nas médias observadas;
- top performers sem correção de multiplicidade e validação temporal.

## Artefatos

- Tabelas: `outputs/tables/EDA-*.csv`.
- Figuras: `outputs/figures/EDA-*.png`.
- Records machine-readable: `outputs/evidence/eda-evidence-records.json`.
- Código: `src/analysis/run_eda.py`.

## Handoff ao Statistician

Validar se efeitos são estatisticamente detectáveis mas praticamente irrelevantes; estimar associação ajustada de patrocínio; diagnosticar overlap; usar erros clusterizados por creator; controlar multiplicidade/interações; quantificar equivalência prática, não apenas rejeição de hipótese nula.
