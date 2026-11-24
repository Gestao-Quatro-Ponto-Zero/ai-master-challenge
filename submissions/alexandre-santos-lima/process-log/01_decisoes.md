# Process log — decisões e correções (em ordem)

Ferramenta principal: **Claude Code** (Claude Opus 5.5) rodando numa VPS, com Python (pandas, scipy, matplotlib) via `uv`.
Cada etapa abaixo tem o script que a reproduz em `solution/scripts/`.

## Etapa 0 — Entender antes de executar
- Li os READMEs (geral, do challenge, guia de submissão, CONTRIBUTING, template) antes de abrir os dados.
- Achado de processo: o `.gitignore` raiz ignora `submissions/` → commit com `git add -f`, senão o PR iria vazio.

## Etapa 1 — Reconhecimento (antes de qualquer hipótese)
- Primeira leitura: eventos de churn subiram de 16 (dez/23) para 117 (dez/24) — **a narrativa do CEO**.
  Mas a base ativa cresceu de 651 para 4.707 assinaturas no mesmo período → a taxa fica ~2,5%. *A confirmar na etapa de tendência.*
- Satisfação: nenhuma nota 1 ou 2, 41% sem resposta → "CS diz que satisfação está ok" mede só quem respondeu.

## Etapa 2 — Ligar as tabelas (scripts 01)
- **Pedido do usuário:** tabelas diretamente ligadas e separadas por categoria → `account_360.csv` (500 × 71)
  com prefixos `perfil_ / receita_ / uso_ / suporte_ / churn_`, e `subscription_360.csv` (5.000 × 30).
- **Onde a abordagem "padrão de IA" erraria:** o caminho óbvio é medir "uso nos 90 dias antes do churn".
  Antes disso, auditei a coerência temporal (`docs/auditoria_dados.md`):
  - 0 das 110 contas com `churn_flag` têm todas as assinaturas encerradas;
  - 77,7% do uso cai fora da vigência da própria assinatura; 53,8% dos tickets são anteriores ao signup;
  - só 47 de 600 eventos de churn coincidem (±7d) com fim de assinatura.
  → **Decisão:** ligar por chave e agregar o histórico inteiro; não usar janelas temporais entre tabelas.
- Três "churns" que não concordam: `accounts.churn_flag` (110), `churn_events` (352 contas), `subscriptions.churn_flag` (486 assinaturas).
  Spearman entre os dois de conta = −0,03 (nem concordam entre si). → **Decisão:** testar todos e reportar a divergência como achado.

## Etapa 3 — Correlação por categoria (scripts 02 e 03)
- 49 variáveis × 2 alvos no nível de conta + 19 no nível de assinatura, com correção de Benjamini-Hochberg.
- **Resultado: nenhuma variável sobrevive à correção.** Os "achados" que pareciam fortes
  (DevTools 31%, canal event 30%, Alemanha 32%) têm p bruto 0,07–0,66 e somem com a correção (n=25 na Alemanha).
- Correção de bug do próprio script: no pandas 3 colunas de texto não são `object`; o teste categórico
  estava caindo no ramo numérico e gerando NaN. Detectado olhando a saída, corrigido com `is_numeric_dtype`.
