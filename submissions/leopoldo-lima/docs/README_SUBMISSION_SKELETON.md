# README de submissão — esqueleto

Copie as secções abaixo para o `README.md` da raiz (ou funda um `README.submission.md` se a política do desafio permitir) e **substitua** os marcadores por conteúdo concreto e verificável.

A submissão completa tem **duas partes obrigatórias**: (1) esta narrativa técnica no README e a **solução funcional** no repositório; (2) o **`PROCESS_LOG.md`** com evidências — **sem process log alinhado ao guia, há risco de desclassificação**. A integração no repo deve ocorrer **via Pull Request (PR)**.

Este esqueleto corresponde a uma **submissão forte**: **resumo executivo, abordagem, resultado, recomendações e limitações** — cada bloco com factos verificáveis, não texto genérico copiado sem validação (**anti-padrão**).

---

## Executive Summary

- **Desafio:** 003 — Lead Scorer (ou o identificador oficial).
- **O que foi entregue:** [1–3 frases: ranking, explicabilidade, API/UI se existir, dados usados.]
- **Diferencial auditável:** [ex.: testes, contratos, process log, demo reproduzível.]
- **Processo:** [referência explícita a `PROCESS_LOG.md` e a `artifacts/process-log/` — leitores e avaliadores devem conseguir auditar decisões, uso de IA e evidências.]

## Abordagem

- **Arquitetura em alto nível:** [componentes principais e fluxo de dados.]
- **Método:** [CRPs seguidos; **todo CRP** deve estar refletido no process log e com **evidência** onde aplicável; referência a ADRs se existirem.]
- **Uso de IA:** [ferramentas; o detalhe obrigatório — prompts resumidos, erros da IA, **julgamento humano** e iterações — fica em `PROCESS_LOG.md` e evidências em `artifacts/process-log/`. Não substituir o log por frases vagas.]

## Resultado

- **Como executar:** [comandos reais; ligação a `docs/SETUP.md` se existir.]
- **O que foi validado:** [testes, CI, checks manuais — com referências a logs ou artefatos; afirmações fortes exigem prova, não output genérico.]
- **Demonstração:** [ligação a `docs/DEMO_SCRIPT.md` ou passos curtos.]

## Recomendações

- **Próximos passos técnicos:** [priorizados, realistas.]
- **Melhorias de produto:** [se aplicável.]

## Limitações

- **Dados / ambiente:** [o que não está incluído ou não foi testado em produção.]
- **Escopo não coberto:** [features omitidas de propósito ou por tempo.]
- **Dependências de avaliação:** [ex.: dados oficiais apenas localmente, sem remoto.]

---

**Checklist antes de publicar**

- [ ] Nenhum segredo ou dado sensível no README ou nos paths citados.
- [ ] Comandos copiados foram executados pelo menos uma vez neste estado do repo.
- [ ] `PROCESS_LOG.md` está atualizado para **cada CRP** executado, com **evidências** ligadas, **ferramentas de IA**, **decomposição**, **erros da IA**, **correções humanas** e **iterações** onde relevantes.
- [ ] Não há dependência apenas de texto genérico de IA sem verificação e sem registo no process log (**anti-padrão**).
- [ ] Alterações integradas ou a integrar **via PR**, com CRP referenciado.

**CRPs no repositório:** definições de trabalho curadas em `crps/executed/` (por tema) e inventariadas em `indexes/crp-index.csv` — ver `docs/CRP_GOVERNANCE.md`.
