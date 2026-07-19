# AI Usage Log

Registro de como IA foi usada no Challenge 002, incluindo as decisões humanas, as validações executadas e as limitações encontradas.

---

## Ferramentas utilizadas

| Ferramenta | Papel no trabalho | Controle aplicado |
|---|---|---|
| Claude Code (Fable 5) | Agente principal nas fases 0–8: exploração, análise, código, notebooks e documentação | Trabalho dividido por fases, com artefatos executáveis, testes e gates humanos |
| Codex | Auditoria pré-submissão e correções aprovadas uma a uma: ROI, bootstrap e coerência do process log | Nenhuma alteração seguinte sem aprovação explícita de Thales |
| Python 3.13 em `.venv` local | Auditoria, estatística, ML, geração de artefatos e testes | Resultados quantitativos derivados por código, não por cálculo manual |
| Navegador local | Verificação funcional da interface e dos fluxos cliente/admin | API, autenticação, telas e exemplos de decisão testados ponta a ponta |

## Divisão humano × IA

**Humano — Thales Barbosa**

- definiu o plano mestre de oito fases, reproduzido em [`project-plan.md`](project-plan.md);
- controlou os gates entre fases e a revisão pré-submissão;
- definiu a decisão econômica final: implantação interna, com custo incremental de implantação igual a **R$ 0**;
- aprovou individualmente as correções finais;
- manteve a responsabilidade pelas escolhas de produto e pela entrega.

**IA — Claude Code e Codex**

- executou descoberta, auditoria, análises, implementação e testes dentro do escopo autorizado;
- confrontou hipóteses com dados e registrou erros, correções e mudanças de direção;
- gerou rascunhos de código e documentação, sempre sujeitos a validação por execução e decisão humana;
- realizou a auditoria de empacotamento e reprodutibilidade antes da submissão.

## Registro por fase

### FASE 0 — Descoberta (2026-07-16)

- Leitura recursiva do repositório e dos documentos do challenge.
- A contagem com parser CSV corrigiu uma interpretação enganosa: o Dataset 1 tem **8.469 registros**, embora as quebras de linha internas produzam aproximadamente 29,8 mil linhas físicas.
- Foram identificados texto sintético no Dataset 1, dois datasets com papéis diferentes e ausência local inicial do template oficial.
- Artefato: `solution/docs/project_discovery.md`.

### FASE 1 — Auditoria dos dados (2026-07-16)

- Auditoria dos dois datasets: dimensões, schema, nulos, duplicados, cardinalidade, estatísticas, distribuições, outliers e inconsistências.
- As hipóteses sobre `First Response Time` e `Time to Resolution` foram testadas e rejeitadas como durações operacionais confiáveis; os campos se comportam como timestamps sintéticos.
- Artefatos: `solution/docs/data_audit.md`, `solution/notebooks/data_audit.ipynb` e gráficos.

### FASE 2 — Preparação e features (2026-07-16)

- Especificação revisada por lentes estatística, negócio/ROI e aderência ao challenge antes da implementação.
- Features e premissas centralizadas em `solution/src/data_prep.py`, com status machine-readable para separar medidas, premissas e demonstrações sintéticas.
- Bugs de dtype e de filtragem de nulos foram encontrados por execução e testes e corrigidos.
- Artefatos: módulo, testes, notebook, dicionário de features e parquets regeneráveis.

### FASE 3 — Diagnóstico e ROI (2026-07-16; revisão em 2026-07-19)

- Diagnóstico operacional separado entre sinais válidos e uma seção demonstrativa explicitamente rotulada para os tempos sintéticos.
- Validação independente recomputou 51 afirmações da primeira versão do relatório sem falhas.
- A formulação econômica inicial com implantação externa foi posteriormente **superada** por decisão humana. O modelo vigente fixa implantação incremental em **R$ 0** e mantém apenas custo recorrente.
- Resultado-base vigente: **R$ 84,5 mil líquidos no ano 1**, ROI de **282%**, payback **imediato**; em regime, **R$ 146,2 mil líquidos/ano** e ROI de **487%**.
- Artefatos: `solution/src/roi_model.py`, testes, notebook diagnóstico, relatório e gráficos.

### FASE 4 — Estratégia de automação (2026-07-17)

- Matriz de automação construída como código: automatizar, assistir e manter humano, com critérios de repetitividade, previsibilidade, risco, criticidade e julgamento.
- Regras de veto têm precedência sobre confiança do classificador.
- Tabelas do documento são geradas do código e protegidas contra divergência por testes.
- Artefatos: `solution/src/automation.py`, testes e `solution/docs/automation_strategy.md`.

### FASE 5 — Machine Learning (2026-07-17; extensão multilíngue em 2026-07-19)

- Comparação TF-IDF/LogReg, TF-IDF/LinearSVC e embeddings; o baseline inglês TF-IDF atingiu macro-F1 aproximado de 0,865.
- Para o portal pt-BR, foi adotado embedder multilíngue. O trade-off foi explicitado: macro-F1 inglês de 0,784, threshold 0,70, cobertura de 64,1% e accuracy de 91,7% nos casos cobertos.
- Busca semântica usa o corpus de 47.823 documentos e uma dupla trava: confiança do classificador e piso de evidência semântica.
- Uma sonda curta em pt-BR acertou 3 de 5 intenções; por isso o protótipo não é apresentado como modelo pronto para produção.

### FASE 6 — Protótipo funcional (2026-07-17 a 2026-07-19)

- A primeira interface foi construída em Streamlit e depois substituída. Seu código não integra o pacote final; a mudança permanece registrada nas decisões e iterações.
- A versão vigente é FastAPI + front-end próprio em `solution/web/`, com Dashboard Executivo, Mesa de Operações, Copilot, ROI, Central de Ajuda e Fila de Chamados.
- Foram adicionados perfis cliente/admin, persistência SQLite e reaproveitamento de resoluções humanas na base de conhecimento.
- Verificação real: servidor saudável, homepage HTTP 200, login admin, endpoint protegido, classificador multilíngue carregado, exemplo de senha em autoatendimento e texto vago bloqueado pelo piso de evidência.

### FASES 7–8 — Documentação e submissão (2026-07-17; revisão em 2026-07-19)

- Template oficial localizado e usado para estruturar o README.
- Submissão empacotada com dados brutos, código, notebooks, documentação, testes e process log; artefatos pesados regeneráveis ficam ignorados.
- `solution/bootstrap.py` transformou a preparação em um único fluxo retomável e idempotente. Uma execução limpa levou cerca de 27 minutos em CPU; a segunda execução levou cerca de 0,1 s.
- Estado verificado na auditoria: **51 testes passando**, notebook diagnóstico executado sem erros, JavaScript sintaticamente válido e aplicação testada ponta a ponta.
- Este process log contém **20 decisões**, **17 iterações** e **11 registros de prompts/gates**.

## Onde julgamento humano foi indispensável

- rejeitar métricas de duração que pareciam plausíveis, mas não eram sustentadas pelo dataset;
- escolher quais riscos nunca automatizar, independentemente da confiança do modelo;
- aceitar o trade-off entre desempenho inglês e experiência multilíngue;
- determinar que a implementação será interna e que o custo incremental de implantação é R$ 0;
- exigir aprovação atômica das correções pré-submissão.

## Limitações do uso de IA

- sugestões de IA foram tratadas como hipóteses, não como evidência;
- revisão multiagente não substituiu testes nem recálculo independente;
- não há export integral das conversas de IA nesta submissão; a evidência aceita é a narrativa rastreável, os prompts relevantes, notebooks executados e artefatos testados;
- o histórico Git só será apresentado como evidência depois de existir no repositório final; ele não é contado como evidência neste estado.
