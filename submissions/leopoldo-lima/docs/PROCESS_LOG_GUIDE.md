# Guia do PROCESS_LOG

O arquivo `PROCESS_LOG.md` na raiz do repositório regista **como** o trabalho foi feito: decisões, uso de IA, erros e correções, com ligação a evidências.

Faz parte da **segunda metade obrigatória da submissão** (junto com a solução funcional). **Ausência ou insuficiência do process log aumenta o risco de desclassificação.**

## O que o process log deve registar (checklist mínimo)

Para cada CRP ou iteração relevante, o registo deve cobrir, quando aplicável:

- **Ferramentas de IA** utilizadas (ou declaração explícita de que não houve IA).
- **Decomposição do problema** — como o trabalho foi partido em passos, hipóteses e decisões.
- **Erros ou limitações da IA** — alucinações, APIs erradas, omissões, etc.
- **Correções humanas** — o que foi validado, alterado ou descartado após revisão humana (**julgamento humano obrigatório** sempre que houver output de IA na contribuição).
- **Iterações** — ciclos relevantes (prompt → resposta → ajuste), contabilizados de forma honesta.
- **Evidências** — caminhos para `artifacts/process-log/` ou outros artefatos verificáveis.

**Texto genérico ou não verificável**, sem ligação a evidência e sem registo de revisão humana, **é anti-padrão** e não substitui critérios de aceite do CRP.

## Quando escrever

- Ao **abrir** um CRP: registe objetivo, decomposição inicial e hipótese (pode ser breve).
- Durante iterações: uma entrada por ciclo relevante (não é necessário logar cada mensagem trivial).
- Ao **fechar** o CRP: resultado final, número de iterações, evidências e referência ao **PR** de submissão.

**Todo CRP** deve deixar rasto no `PROCESS_LOG.md` e **gerar ou referenciar evidência** verificável.

## Template por CRP (copiar para `PROCESS_LOG.md`)

Use um bloco por execução ou por iteração significativa dentro do mesmo CRP.

```markdown
### CRP-XXX — <título curto> — <YYYY-MM-DD>

| Campo | Conteúdo |
|--------|-----------|
| **Data** | YYYY-MM-DD |
| **CRP** | CRP-XXX |
| **Problema** | O que precisava de ser resolvido. |
| **Decomposição / subpassos** | Como o problema foi dividido (tarefas, ordem, dependências). |
| **Hipótese inicial** | O que se assumiu antes de executar. |
| **Ferramenta de IA usada** | Ex.: Cursor, ChatGPT, Copilot, ou *nenhuma*. |
| **Prompt** | Texto ou resumo fiel do pedido (sem dados sensíveis). |
| **Resposta recebida** | Resumo do que a ferramenta devolveu ou *N/A*. |
| **Erro / limitação detectada** | Alucinação, omissão, stack incorreta, etc., ou *nenhuma*. |
| **Julgamento / correção humana** | O que o humano validou, alterou ou rejeitou (obrigatório se houve IA). |
| **Evidência associada** | Caminhos relativos, ex.: `artifacts/process-log/test-runs/...` |
| **Resultado final** | Estado ao fechar: feito / parcial / bloqueado + referência a arquivos. |
| **Número de iterações** | N (ciclos prompt → resposta → ajuste relevantes). |
| **PR** | Link, número (ex. `#42`) ou *pendente* — submissão via PR. |
```

Campos opcionais úteis numa segunda linha de tabela ou lista:

- **Commit(s):** hashes ou mensagens principais.
- **Comandos:** ex.: `.\scripts\tasks.ps1 test` (sem segredos).

## Boas práticas

1. **Sem dados pessoais ou credenciais** nos prompts ou exports.
2. **Exportar chats** para `artifacts/process-log/chat-exports/` quando o desafio pedir rastreabilidade de IA.
3. **Reproduzir**: para afirmações fortes (“todos os testes passam”), anexe ou cite o log em `test-runs/`.
4. **Ligar ao CRP**: o identificador no log deve coincidir com o arquivo em `crps/`.

## Relação com outros arquivos

- `LOG.md` — registo cronológico curto de alterações ao repo (changelog operacional).
- `PROCESS_LOG.md` — narrativa de processo, IA, decomposição, erros, correções humanas, iterações e evidências.
- `docs/SUBMISSION_STRATEGY.md` — como estes artefatos entram na submissão (solução + process log, via PR).
- `docs/README_SUBMISSION_SKELETON.md` — narrativa pública da entrega (resumo executivo, abordagem, resultado, recomendações, limitações).

## Migração do formato antigo

Entradas antigas em lista livre podem permanecer na secção **Registros legados** em `PROCESS_LOG.md`. Novos trabalhos devem usar o template em tabela.
