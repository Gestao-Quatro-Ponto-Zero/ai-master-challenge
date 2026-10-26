# G4 Challenge 003 — BIOS Process Log | Adendo Histórico V1

**Natureza:** adendo documental ao `PROCESS_LOG.md` original, não substituição. Fontes: `conversasGPT.docx` e `conversasGPT2.docx`. Transcrições são registros do trabalho, não garantia de reexecução atual dos experimentos.

| Ordem lógica | Prompt/diretriz humana | Análise e alternativas da IA | Decisão e julgamento humano | Evidência / status |
|---|---|---|---|---|
| 1 | Aplicar Business First e BIOS ao case, evitando tecnologia pela tecnologia | Reformular Lead Scorer como problema de Sales Capacity Allocation | Direcionamento aprovado pelo usuário | Conversa 1, p. 14–24 |
| 2 | Exigir software simples, visual e útil | Blueprint com Action Cards, explicabilidade, NBA, UX-01 | Usuário aprovou Architecture Delta UX-01 | Conversa 1, p. 6–8 |
| 3 | Avaliar dados antes de congelar scoring | Auditoria CRM, missingness, risco temporal e leakage | GO WITH CONDITIONS para MVP; rejeitar confiança preditiva sem evidência | Conversa 1, p. 4–6 |
| 4 | Prosseguir com validação da Scoring Policy | Política experimental 50/30/20 e teste de sensibilidade | Arquitetura aprovada; pesos/limiares não congelados | Conversa 1, p. 10–14 |
| 5 | Adotar julgamento consultivo forte | Comparação heurística versus modelo estatístico, AUC exploratória ~0,488 | Preferir índice explicável e workflow comercial | Conversa 1, seção BIOS Data & Evidence Assessment |
| 6 | Testar proposta alternativa do Gemini | Análise de gaps, falhas de dados sintéticos e de alegações financeiras | Incorporar apenas ideias defensáveis | Conversa 2, p. 1–5 |
| 7 | Corrigir pressuposto indevido de Salesforce | Revisão da arquitetura de integração | CRM-agnostic explicitamente aprovado | Conversa 2, p. 5–6 |
| 8 | Preservar versões estáveis e testar | AS-IS, Architecture Delta, testes e UAT | Evolução incremental; evitar reintroduzir capacidades existentes | Conversa 2, p. 7–16 |
| 9 | Documentar toda metodologia e prompts | BIOS, rastreabilidade, Process Log e evidências | Usuário exigiu demonstrar o caminho até o resultado | Conversa 2, p. 17–24 |
| 10 | Estruturar BIOS em sete capítulos | Structured Thinking incluindo DMAIC, métodos e trade-offs | Estrutura de sete capítulos congelada | Conversa 1, seção de estrutura BIOS aprovada |

## Regras para publicação

- Separar prompts literais disponíveis de paráfrases resumidas neste adendo.
- Anexar fontes originais de código e dados quando alegar resultados reproduzidos.
- Identificar resultados da V4.6-A.11 e da RC4 separadamente.
- Não alegar causalidade ou uplift de receita em produção.
- Não assumir fornecedor de CRM não presente no enunciado.
- Registrar correções, decisões rejeitadas e limitações da IA como parte do processo.
