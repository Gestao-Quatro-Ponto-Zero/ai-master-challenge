# Analysis — Challenge 004 (Marketing Social)

## 1. Executive Summary
A análise de 52.214 posts mostra que o desempenho é determinado mais por **segmento específico** (plataforma + período + categoria + faixa de creator + formato) do que por regra geral de canal. Em média, patrocínio não melhora resultado quando comparado de forma justa com orgânico no mesmo estrato. O melhor caminho é operar com segmentação fina e governança semanal: escalar células comprovadas, pausar células negativas e manter testes controlados.

## 2. Key Insights

### 2.1 O que gera engajamento de verdade?
- Não existe um “vencedor universal” por plataforma; o padrão consistente foi:
  - **Creators 50k–200k + vídeo 120s+** com eficiência maior de alcance por seguidor.
- Exemplos concretos:
  - `YouTube | orgânico | beauty | 50k-200k | video | 120s+`
    - `n=147`
    - `ERR +0,54%` vs baseline da plataforma
    - `share_rate +0,30%`
    - `reach_per_follower +45,4%`
  - `Instagram | orgânico | lifestyle | 50k-200k | video | 120s+`
    - `n=136`
    - `ERR -0,06%` (praticamente estável)
    - `share_rate +0,01%`
    - `reach_per_follower +46,7%`

### 2.2 Patrocínio funciona?
- **No agregado, não**: resultado médio patrocinado ficou quase idêntico ao orgânico quando pareado por estrato.
  - `ERR ratio ponderado = 0.99995`
  - `share ratio ponderado = 0.99982`
- **Em células específicas, sim**:
  - `YouTube|2024-Q3|beauty|500k+`:
    - `n_sponsored=126`, `n_organic=168`
    - `lift ERR +0,59%`
    - `lift share +1,32%`
    - confiança: `High`
  - `Instagram|2023-Q4|lifestyle|500k+`:
    - `n_sponsored=126`, `n_organic=146`
    - `lift ERR +0,50%`
    - `lift share +1,07%`
    - confiança: `High`

### 2.3 Qual perfil de audiência mais engaja?
- Diferenças por idade existem, mas são pequenas; ainda assim ajudam no desempate tático por plataforma:
  - `TikTok`: faixa `26-35` foi a melhor (`ERR +0,05%`, `share +0,09%` vs baseline TikTok)
  - `RedNote`: faixa `19-25` foi a melhor (`ERR +0,06%`, `share +0,14%`)
  - `YouTube`: faixa `50+` teve melhor share relativo (`+0,28%`)
- Conclusão prática: usar idade como **ajuste fino de criatividade/ângulo**, não como driver principal de investimento.

### 2.4 O que NÃO funciona?
- Patrocinar células com histórico negativo reduz performance:
  - `TikTok|2024-Q3|beauty|500k+`:
    - `lift ERR -0,79%`
    - `lift share -1,00%`
  - `YouTube|2024-Q3|lifestyle|500k+`:
    - `lift ERR -0,55%`
    - `lift share -0,97%`
- Faixas com creators muito grandes (`500k+`) tiveram menor eficiência de `reach_per_follower` em vários recortes, principalmente com formatos curtos/imagem.

## 3. Evidence (números e comparações)
- Base: **52.214 posts válidos** (`2023-05-29` a `2025-05-28`).
- Segmentação aplicada: plataforma, trimestre, categoria, creator band, patrocínio, tipo e duração de conteúdo, faixa etária.
- Comparação patrocinado vs orgânico: **280 estratos** com mínimo de 30 posts por lado.
- Anti-survivorship:
  - Não há zeros absolutos em views/likes/shares/comments.
  - Quartil inferior (proxy de baixo desempenho):
    - `ERR p25 = 0.19575824` (`13.054 posts`, 25%)
    - `share_rate p25 = 0.02852050` (`13.054 posts`, 25%)

## 4. Risks & Bias Checks
- O dataset não possui `engagement_rate` nativo; foi usada métrica derivada documentada.
- Sinal estatístico entre segmentos é, em geral, pequeno; overclaim foi evitado.
- Atributos de negócio (Lead/MQL/SQL/CAC) não estão no dataset, então ROI final depende de instrumentação adicional.
- Regra de robustez aplicada: insights estratégicos com `n >= 80`.

## 5. Open Questions
- Qual prioridade do próximo trimestre: alcance, engajamento ou pipeline?
- Qual orçamento máximo de patrocínio por plataforma para testes controlados?
- Qual janela de atribuição será adotada (7/14/30 dias) para fechar ciclo com receita?

## 6. Supporting Files
- Evidências completas: `/docs/evidence_register.md`
- QA de dados: `/docs/data_qa_report.md`
- Tabela segmentada: `/docs/segment_performance.csv`
- Comparação patrocinado vs orgânico: `/docs/sponsorship_comparison.csv`
