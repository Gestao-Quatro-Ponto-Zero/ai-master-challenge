# Prompts Log

Prompts relevantes usados no desenvolvimento (Claude Code). Os prompts do humano definem escopo e gates; a IA executa dentro deles.

---

## P-001 — System prompt do projeto (FASE 0)
Arquivo externo `SYSTEM_INSTRUCTIONS.md` completo carregado como instrução mestra: papel (Senior AI Master / DS / AE / PM), objetivo de negócio, regras de execução ("nunca pule uma fase", "nada baseado em achismos") e as 8 fases detalhadas. Seu conteúdo necessário para auditar a entrega está incorporado em [`project-plan.md`](project-plan.md).

## P-002 — Kickoff (FASE 0)
> "Leia todo o diretório para entender a estrutura (FASE 0). Liste os arquivos, valide a estrutura conforme o plano e crie docs/project_discovery.md. Não pule para a análise de dados. Confirme que entendeu a estrutura e o objetivo, leia SYSTEM_INSTRUCTIONS.md e diga em qual fase estamos."

**Resultado:** descoberta completa + 3 achados (8.469 registros reais vs ~30k do brief; texto sintético no Dataset 1; template de submissão ausente).

## P-003 — Gate da FASE 1
> "Ok, vá criando o process-log e siga para a fase 1. Implemente apenas a Fase 1. Faça uma auditoria completa dos dados: schema, tipos, nulos, duplicados, estatísticas, distribuições, inconsistências, análise profunda de First Response Time e Time to Resolution. Crie docs/data_audit.md e notebooks/data_audit.ipynb. Não avance além disso."

**Resultado:** process-log criado; auditoria executada; hipóteses A/B testadas; artefatos gerados.

## P-004 — Gate da FASE 2
> "Siga para a fase 2, atenção aos detalhes."

**Execução:** espec com 3 decisões contenciosas marcadas → painel multi-agente de 3 lentes (prompts do painel: estatístico sênior focado em semântica honesta/leakage; consultor de operações focado em defensibilidade perante Diretor de Operações; avaliador G4 focado em aderência ao plano e red flags de "número inventado") → implementação com testes → workflow de verificação adversarial dos artefatos.

**Resultado:** o painel rejeitou/ajustou pontos materiais da proposta original (lógica de SLA, ordenação de AHT, premissas sem faixa) — evidência de que revisão multi-perspectiva supera prompt único.

## P-005 — Gate da FASE 3
> "Siga para a fase 3."

**Execução:** espec com 4 decisões contenciosas → painel multi-agente (mesmas 3 lentes da FASE 2) → implementação (`src/roi_model.py` + notebook diagnóstico) com testes → verificação adversarial. Padrão consolidado: espec → painel → implementação testada → verificação.

## P-006 — Gate da FASE 4
> "Siga para a fase 4."

**Execução (inline):** levantamento de evidências nos 2 datasets → matriz como código com fonte única de deflexões → testes de invariantes + guarda doc↔código verbatim → `docs/automation_strategy.md` com fluxo mermaid, regras de veto, KPIs/gates de piloto e limitações.

## P-007 — Gate da FASE 5
> "Siga para a fase 5."

**Execução (inline):** módulo de ML com 3 candidatos + harness de avaliação → embeddings resumáveis em background → treino/comparação → gate de confiança calibrado (liga com o fluxo da FASE 4) → busca semântica FAISS → notebook de apresentação + `docs/ml_models.md`.

## P-008 — Gate da FASE 6
> "Siga para a fase 6."

**Execução (inline):** guia de dataviz carregado antes dos gráficos (paleta validada) → `src/copilot.py` com testes → `app.py` (4 páginas consumindo os módulos testados) → verificação funcional navegando o app no browser (Copilot ponta a ponta + conferência dos números do simulador contra o modelo).

## P-009 — Gates das FASES 6.5 e 7
> "Quero que redesenhe toda essa parte de front end (...) visualmente bonito, clean, atual." · "Siga para a fase 7."

**Execução:** redesign completo do protótipo com sistema visual próprio e verificação de acessibilidade no browser (iteração 12); depois busca e obtenção do template oficial de submissão, montagem da estrutura `submissions/thales-barbosa/` e README final seguindo o template à risca.

## P-010 — Auditoria comparativa antes da submissão
> "Vou submeter os arquivos necessários; confira exatamente o que preciso entregar e se esses arquivos estão seguindo a estrutura esperada e respondendo tudo que se espera."

**Contexto adicional do humano:** foram fornecidos os documentos oficiais, o template e uma captura da estrutura de entrega de outro candidato.

**Resultado:** checklist de requisitos e estrutura confrontado com o pacote real; identificados como pontos de correção o ROI incompatível com o contexto, setup fragmentado, process log dependente de arquivo externo, referências antigas e ausência de histórico Git utilizável.

## P-011 — Correções com aprovação atômica e regra econômica final
> "Então faça as alterações, validando uma a uma comigo; eu vou aprovar cada uma delas. [...] Sobre o payback/ROI, o único modelo que deve ser seguido é o de custo zero, implementação interna."

**Execução:** cada bloco foi proposto e só iniciado após aprovação explícita. A alteração 1 corrigiu o ROI; a alteração 2 criou e validou o bootstrap; a alteração 3 tornou o process log autocontido. O trabalho de README, validação final e Git permanece separado pelos próximos gates.

<!-- Novos prompts/gates devem ser adicionados abaixo. -->
