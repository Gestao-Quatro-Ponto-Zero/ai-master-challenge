# Submissão — Alexandre Santos Lima — Challenge 001

## Sobre mim

- **Nome:** Alexandre Santos Lima
- **LinkedIn:** _(a preencher)_
- **Challenge escolhido:** 001 — Diagnóstico de Churn (RavenStack)

---

## Executive Summary

Liguei as 5 tabelas por conta, auditei chaves **e datas** e testei cada explicação com estatística. **Não há sinal de que os
clientes estejam cancelando mais:** os cancelamentos por mês subiram 7×, mas a base ativa também cresceu 7×, e de cada 100
clientes que entram cerca de 10 cancelam (12 em 2023, 9 em 2024). O "algo não bate" do CEO tem outra causa: **a empresa não mede
o cancelamento.** Os dois registros de churn discordam em 312 de 500 contas, 211 de 216 contratos anuais "terminam" antes de um
ano e 99% dos clientes "cancelados" seguem usando o produto. A recomendação principal é corrigir a medição em 30 dias, ouvir as 15
contas de maior valor e só então testar ações de retenção com grupo de comparação.

**Entregáveis**

| | Onde |
|---|---|
| Painel interativo (Diagnóstico · Sugestões · Dados) | https://ravenstack-churn.apsolutions-technology-services.workers.dev |
| Relatório para o CEO (2 páginas, linguagem simples) | [`docs/relatorio-executivo.md`](docs/relatorio-executivo.md) |
| Diagnóstico inteiro com um comando (skill do Claude Code) | [`skill/diagnostico-churn/`](skill/diagnostico-churn/) |
| Scripts da análise (01–07) e código do painel | [`solution/`](solution/) |
| Process log | [`process-log/`](process-log/) |

---

## Solução

### Abordagem

1. **Entender antes de executar.** Li os READMEs do repositório e do dataset e tratei as três falas da diretoria
   ("churn subiu", "satisfação ok", "uso cresceu") como hipóteses a testar, não como fatos.
2. **Auditar a ligação entre as tabelas antes de analisar** (`01_build_dataset.py` → [`docs/auditoria_dados.md`](docs/auditoria_dados.md)).
   As chaves batem 100%, mas as datas não: 77,7% do uso cai fora da vigência da assinatura, 53,8% dos tickets são anteriores ao
   cadastro da conta. Por isso liguei as tabelas por chave e agreguei o histórico de cada conta (`account_360`, 500 × 71, colunas
   por categoria: perfil, receita, uso, suporte, churn), sem janelas do tipo "90 dias antes do churn".
3. **Correlação por categoria com correção para múltiplos testes** (`02`, `03`): 117 testes, nos níveis conta e assinatura e
   nas duas definições de churn por conta, com Benjamini-Hochberg.
4. **Separar volume de taxa** (`04`, `05`): proporção de cada safra (trimestre de entrada) que cancela, e teste de confiabilidade
   da data de encerramento antes de usar qualquer taxa mensal.
5. **Testar base × mês × uso** (`06`): quase-Poisson com o tamanho da base, robustez sem os meses atípicos, uso antes × depois
   de cada churn.
6. **Previsão só do que os dados sustentam e sugestões com tamanho de amostra** (`07`).
7. **Painel React** validado no navegador (Playwright, desktop claro/escuro e celular) e **skill** que refaz tudo com um comando.

### Resultados / Findings

| Pergunta | Resposta | Número que sustenta |
|---|---|---|
| O churn subiu? | Só em volume | Cancelamentos/mês 16 → 117 (7×); assinaturas ativas 437 → 3.174 (7×); % por safra 12% (2023) e 9% (2024) |
| O que explica o número de cancelamentos? | O tamanho da base | 96% da variação explicada; elasticidade 0,91 (IC 0,81–1,01); 16 de 17 meses na faixa esperada |
| Tem efeito de mês do ano? | Nenhum sinal | p = 0,19 (com a ressalva de só 2 anos de dados) |
| O uso cresceu? | Não; por cliente caiu 83% | Uso total estável (~10 mil/mês) com a base crescendo |
| Uso explica churn? | Não | Cru ρ = −0,97 (espúrio); descontada a base ρ = 0,40, p = 0,11; uso 90 dias antes × depois do churn = 62,0 × 62,2 (p = 0,96) |
| A satisfação está ok? | Mal medida | 41% dos tickets sem nota; zero notas 1 ou 2 em 2.000 |
| Quem está em risco? | Nenhuma característica isolada | 0 de 117 testes sobrevivem à correção; DevTools (31%) e canal "event" (30%) são hipóteses: confirmá-las exigiria 218 e 284 contas (~4 e ~6 anos) |
| Por que "algo não bate"? | A medição está quebrada | Registros de churn discordam em 312/500 contas; 211/216 anuais encerrados com < 1 ano; motivo × comentário sem relação (V = 0,06) |

Contas específicas: a aba **Sugestões** lista as 15 contas para ouvir primeiro (maior MRR entre as 75 em que flag e evento de
churn concordam, US$ 216 mil de MRR encerrado), e a aba **Dados** tem as 500 contas com todas as tabelas cruzadas.

### Recomendações

1. **Corrigir a medição (1º mês):** regra única de churn calculada pelo sistema; data de encerramento vinda da cobrança; uso e
   tickets validados contra a assinatura ativa; motivo de saída em lista fechada + texto livre classificado por IA (que sinaliza
   contradição para o CS confirmar); pesquisa de satisfação que ofereça e acompanhe notas baixas; checagem automática semanal
   (a própria skill).
2. **Descobrir o porquê (2º–3º mês):** ligar para as 15 contas da lista; refazer o diagnóstico com os dados corrigidos, testando
   nesta ordem: uso cai antes do churn? tickets escalados antecedem a saída? DevTools e "event" se confirmam?
3. **Reduzir o churn (a partir do 4º mês):** medir pela % de cada safra que cancela (hoje 9,7%, IC 8,8–10,6%); testar cada ação
   com grupo de comparação sorteado. Cada ponto percentual a menos ≈ 38 assinaturas e US$ 52–110 mil de MRR (conta direta, não promessa).

### Limitações

- Dados sintéticos: vários padrões têm assinatura de geração aleatória (datas sorteadas, motivo independente do comentário).
  Tratei isso como "problema de medição" porque é exatamente o que um analista veria numa empresa com registros ruins.
- Sem datas confiáveis, não dá para comparar a velocidade de cancelamento entre safras: a conclusão é "não há sinal de piora",
  não "o churn caiu".
- Sazonalidade: com 2 anos, só dá para dizer que nenhum sinal apareceu.
- Sem previsão por data (exigiria prever o crescimento da base).

---

## Process Log — Como usei IA

> Detalhe completo, em ordem: [`process-log/01_decisoes.md`](process-log/01_decisoes.md) ·
> conversa exportada (sem dados sensíveis): [`process-log/chat-exports/conversa-claude-code.md`](process-log/chat-exports/conversa-claude-code.md)

### Ferramentas usadas

| Ferramenta | Para que usou |
|------------|--------------|
| Claude Code (Claude Opus 5.5) | Toda a execução: download, scripts de análise, testes estatísticos, painel React, validação e skill |
| Python (pandas, scipy, statsmodels, matplotlib) via `uv` | Análise e testes |
| React + Vite + Recharts | Painel |
| Playwright | Validação visual do painel (desktop claro/escuro e celular) a cada mudança |
| Kaggle CLI, Cloudflare (wrangler) | Dados e publicação |

### Workflow

1. Pedi um plano antes de qualquer código. O Claude leu o repositório, baixou os dados e fez um reconhecimento rápido.
2. Pedi as tabelas ligadas e separadas por categoria → base `account_360` + auditoria de ligação + correlações com correção.
3. Pedi o painel. A cada iteração revisei os prints e devolvi feedback (12 mensagens minhas no total, ~200 ações executadas).
4. Questionei a conclusão sobre o churn, pedi provas visuais com certeza, a página de sugestões, a previsão "só com dado real",
   a linguagem para leigos e a skill de um comando.
5. Cada etapa virou commit (ver `git log` da branch) e entrada no process log.

### Onde a IA errou e como corrigi

- **A conclusão central saiu errada duas vezes.** Primeiro a IA disse "taxa estável em ~2,5%" (misturou eventos por conta com
  assinaturas). Depois, corrigindo, afirmou "a taxa subiu" e marcou "Verdade" para o CEO, usando datas de encerramento sem
  auditá-las. Eu desconfiei ("pelo que eu vi o churn não subiu") e pedi a checagem: 211 de 216 contratos anuais encerrados com
  < 1 ano, cancelamento sempre na metade da janela restante → datas inválidas; a medida correta é a % por safra.
- **Correlação espúria apresentada como achado:** "menos uso → mais churn" (ρ = −0,97) só reflete o crescimento da base. Pedi
  "certeza" e a IA refez com controle da base, robustez e teste antes × depois.
- **Afirmações de texto que o gráfico não sustentava:** "nenhum mês fica acima do esperado nos dois anos" (dezembro fica),
  "a relação some" (há leve inclinação não significativa), fev/24 com "21 esperados" (eram 19), "8–10% em todas as safras" (uma tem 15%).
- **Comunicação:** primeira tela com nove caixas repetindo números; títulos-pergunta sem resposta; enquadramento "o CEO diz / o
  CS diz", irrelevante para quem lê; jargão (MRR, safra, p-valor). Corrigido a cada feedback.
- **Git:** o `.gitignore` raiz ignora `submissions/`; o `git add -f` incluiu dados brutos e depois o `node_modules` — retirados antes do commit.

### O que eu adicionei que a IA sozinha não faria

- **Desconfiar da conclusão "óbvia".** A IA aceitou "o churn subiu" porque o número subia; eu não aceitei sem prova, e isso
  mudou o diagnóstico inteiro (de "churn em alta" para "medição quebrada").
- **Exigir certeza e honestidade sobre os limites:** previsão só do que o dado sustenta, "não há sinal de piora" em vez de
  "caiu", sazonalidade como ausência de sinal.
- **Pensar no leitor:** quem lê não conhece a empresa nem estatística → só resultados, títulos que respondem, linguagem do
  dia a dia e detalhe técnico escondido para quem quiser conferir.
- **Transformar a análise em processo repetível:** a skill `diagnostico-churn` refaz tudo (download → análise → painel → validação) em
  ~35 s, o que vira a "checagem semanal" recomendada.

---

## Evidências

- [x] Chat export: [`process-log/chat-exports/conversa-claude-code.md`](process-log/chat-exports/conversa-claude-code.md)
- [x] Narrativa das decisões: [`process-log/01_decisoes.md`](process-log/01_decisoes.md)
- [x] Git history: commits incrementais na branch `submission/alexandre-santos-lima`
- [x] Prints da validação automática: [`solution/outputs/validacao/`](solution/outputs/validacao/)
- [x] Outro: painel publicado e skill executável

## Como rodar

Requisitos: `uv`, Node 20+, token do Kaggle em `~/.kaggle/access_token`.

```bash
# tudo com um comando (download, análise, painel, validação, resumo)
skill/diagnostico-churn/scripts/rodar.sh
# só o painel
cd solution/dashboard && npm install && npm run dev   # http://localhost:5180
```

Dados: RavenStack, dataset sintético de River @ Rivalytics (Kaggle, licença MIT).

---

_Submissão enviada em: 24/11/2026_
