# Estratégia de automação assistida - Challenge 002

## 1. Resumo executivo
- Dataset 1 indica onde a operação perde mais tempo relativo (ex.: Chat/Refund High; Social Media/Billing ou Product Inquiry).
- Dataset 2 entrega um classificador TF-IDF + Linear SVM (SGD) treinado em 47.8k tickets (8 classes) com Macro F1 0.853 / accuracy 0.855.
- Estratégia: automação assistida começando por auto-roteamento + busca de similares nos fluxos repetitivos e menos críticos; humano permanece no loop para riscos de acesso/permissão e financeiros. Auto-resposta fica como piloto controlado (fase 2), não como rollout imediato.

## 2. O que o Dataset 2 permite fazer
- Categorizar tickets de TI em 8 grupos com F1 macro ~0.85 (baseline atual).
- Recuperar tickets similares via TF-IDF/cosseno para sugerir resolução ou especialista.
- Medir confiança por ticket para decidir automação vs revisão humana.
- Aplicar primeiro onde o Dataset 1 mostrou maior demora e o texto é previsível: fluxos repetitivos de menor criticidade (ex.: Billing/Product Inquiry) recebem roteamento assistido antes de tocar o agente.

## 3. Performance do classificador
- Melhor classe: Purchase (F1 0.913).
- Pior classe: Administrative rights (F1 0.727).
- Principais confusões (ver matriz em outputs):
  - HR Support → Hardware: 184 casos
  - Miscellaneous → Hardware: 130 casos
  - Hardware → HR Support: 119 casos

## 4. Onde IA ajuda no fluxo
- Classificação automática inicial com limiar de confiança (configuração inicial: 0.55 e 0.75, a serem calibrados).
- Auto-roteamento assistido como etapa principal: direcionar para squad/owner certo e sugerir prioridade quando confiança >= limiar e categoria é de baixa criticidade.
- Busca de similares para dar contexto e acelerar resolução pelo agente (reduz retrabalho, sem substituir decisão humana).
- Auto-resposta apenas em piloto controlado e opt-in, começando por FAQs de baixa criticidade; não recomendado rollout amplo até medir precisão real.
- Foco de priorização: fluxos que o Dataset 1 mostrou lentos e que o classificador do Dataset 2 consegue prever com boa confiança.

## 5. Onde humano deve permanecer
- Baixa confiança (<0.55) ou fora das 8 classes / texto ruidoso.
- Categorias sensíveis:
  - Access / Administrative rights: risco de permissão/segurança.
  - Purchase: risco financeiro e de política/aprovação.
  - Casos ambíguos onde o modelo confunde Hardware x HR x Misc (principais confusões).
- Revisão final de qualquer auto-resposta; decisões que impactam compliance, finanças ou segurança.

## 6. Fluxo proposto ponta a ponta
1) Receber ticket -> classificador retorna categoria + confiança.
2) Recuperar top similares e sugerir owner/próximo passo.
3) Se confiança >=0.75 e categoria de baixa criticidade: auto-rotear com sugestão de resposta opcional (agente valida).
4) Se confiança entre 0.55-0.75 ou categoria sensível: roteamento assistido + checagem humana obrigatória.
5) Se confiança <0.55: fila de revisão humana e feedback para re-treino.
6) Calibração: limiares 0.55/0.75 são ponto inicial; ajustar por categoria comparando confiança prevista vs. acurácia real em produção.

## 7. Estimativa de ROI (cenários ilustrativos, proxies de tempo)
- Base: TTR proxy total do Dataset 1 = 37,098 h; desperdício comparativo estimado (benchmark P25) = 5,338 h.
- Cenário A (redução sobre tickets-alvo): cobrir 30% dos tickets de menor criticidade e reduzir tempo em 20% ⇒ ~2,226 h economizadas (proxy, não mensalizado).
- Cenário B (redução sobre desperdício): aplicar 20% de redução no desperdício comparativo ⇒ ~1,068 h recuperáveis (proxy).
- Observação metodológica: para converter em ganho mensal real é preciso calibrar o modelo com o volume mensal da operação e medir o tempo real por estágio.

## 8. Limitações
- Dataset 1 e 2 têm taxonomias diferentes; mapeamento conceitual, não 1:1.
- Métricas de tempo são proxies relativas; ganhos reais dependem do fluxo produtivo.
- Classificador depende de texto limpo; entradas ruidosas derrubam confiança.

## 9. Próximos passos
- Ajustar limiares por categoria com feedback humano.
- Testar embeddings locais para aumentar recall das classes menores.
- Integrar motor de similares na ferramenta do agente com captura de feedback.
