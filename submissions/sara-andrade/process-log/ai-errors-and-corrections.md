# Onde a IA errou e como corrigi

Este arquivo resume os principais erros ou riscos das respostas de IA usadas durante o processo.

| Erro/Risco | Como apareceu | Como foi corrigido |
|---|---|---|
| Interpretar 67,3% como “aguardando cliente” | Uma análise sugeriu que 67,3% estavam em Pending Customer Response | Recontagem mostrou 34,0% Pending e 67,3% não fechados |
| Fazer diagnóstico por canal usando tempos sintéticos | Algumas análises priorizaram Social media/Email por “desperdício” | Teste Kruskal na subamostra positiva deu p=0,791; removido como recomendação |
| Usar dados positivos após filtrar negativos como se fossem confiáveis | Uma solução filtrou deltas negativos e usou os restantes para ROI | Verifiquei que os positivos também parecem sorteados; ROI temporal removido |
| Confundir aparência crítica com validação real | Algumas respostas tinham seções de “autonomia crítica”, mas não testavam as hipóteses | Substituí por testes reproduzíveis em Python |
| Usar `Resolution` como entrada de modelo | Sugestão de enriquecer features com resolução | Rejeitado por data leakage |
| Aplicar classificador IT no Dataset 1 | Parecia uma forma de cruzar os datasets | Teste mostrou domain shift; B2C não recebe auto-resolução |
| Automatizar refund/cancellation | Volume alto poderia parecer oportunidade | Mantido em humano/agent assist por risco financeiro e churn |
| Usar Streamlit como protótipo principal | Recomendação recorrente | Troquei para FastAPI, mais integrável em operação real |
