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

## Etapa 4 — Dashboard em React (scripts 04 + solution/dashboard)
- **Pedido do usuário:** ver os dados num dashboard; React + Vite + Recharts, dados gerados por `04_export_dashboard.py`.
- **Correção de uma afirmação minha (IA):** no reconhecimento eu disse que a taxa de churn estava "estável em ~2,5%".
  A conta dividia *eventos por conta* por *assinaturas* — unidades diferentes. Refeita direito (assinaturas pagas
  encerradas ÷ ativas no início do mês), **a taxa sobe**: ~1% até ago/24 → 1,5% set → 2,4% nov → 5,3% dez.
  A narrativa mudou de "o churn não subiu" para "subiu, e o problema é outro".
- **Checagem do pico de dezembro:** 54 dos 167 encerramentos pagos de dez/24 caem nos dias 29–31 (borda do dataset).
  Sem eles: 3,6% em 28 dias — ainda o maior mês. Escrevi "perto de 4%" no primeiro rascunho do site; corrigido para o número exato.
- **Uso:** total estável (~10 mil eventos/mês, ρ 2024 = 0,05) enquanto a base cresce → uso por assinatura cai 83% em 2024.
- **Paleta validada** com o validador de daltonismo (skill de dataviz) antes de desenhar; tema claro/escuro.
- **Validação com Playwright** (desktop 1366 px claro/escuro e celular 390 px): sem erros de console, sem rolagem horizontal,
  rótulos ligados aos campos. Corrigido o que os prints mostraram: mapa de calor cortando as linhas de churn,
  matriz cortada no celular, rótulos "fraca/moderada" sobrepostos, números em formato americano na auditoria
  ("5,000", "22.0%"), "−0%" na leitura e nota que citava "pricing" quando a tabela mostra "preço".
- **Feedback do usuário:** "os gráficos estão excelentes, mas a primeira visão está horrível" (texto corrido + 9 caixas
  iguais repetindo números). Refeita em volta da pergunta do CEO: um número-manchete com a curva (churn de MRR 2024),
  três colunas "o que cada área disse × o que os dados mostram" com mini-gráfico e veredito, e uma faixa com o achado
  que ninguém pediu (registros de churn que discordam). Nota de honestidade no número: o "11×" usa dez/24, que tem
  efeito de borda — a nota mostra que nov/24 já está em 4× junho.

## Etapa 5 — O churn subiu? (correção apontada pelo usuário)
- **Feedback do usuário:** "a página está repleta de perguntas sem respostas; pelo que eu vi o churn não subiu, por que o CEO diria que subiu?"
  Dois problemas: (1) títulos-pergunta ("O churn subiu?") em vez de títulos-resposta; (2) o veredito "Verdade" estava errado.
- **Segunda correção da mesma conclusão.** Eu (IA) primeiro disse "taxa estável" (unidades misturadas), depois "taxa subiu"
  (aceitando datas de encerramento sem auditá-las). O usuário desconfiou; os testes (`05_teste_safras.py` + export 04) mostraram:
  - % de cada safra de assinaturas que cancela: 2023 = 12,1%, 2024 = 9,3% (p = 0,047); sem a safra minúscula T1/23, safras não diferem (p = 0,13);
  - eventos de churn por conta, por trimestre de cadastro: 1,1–1,4 em todas as safras;
  - cancelamentos/mês 16 → 117 (7×) e assinaturas ativas 437 → 3.174 (7×): **o volume acompanha a base**;
  - a "alta da taxa" em out–dez vem das datas: 211 de 216 contratos ANUAIS encerrados duraram < 1 ano (103 < 30 dias),
    e o cancelamento cai sempre na metade do tempo que resta até o fim dos dados (mediana 49%) em qualquer safra;
  - teste de composição por idade: não explica (a taxa padronizada também sobe) — o problema é a data, não o mix.
- **Conclusão reformulada com cautela:** "não há sinal de que o churn piorou" (e não "o churn caiu"), porque safras recentes tiveram
  menos tempo de exposição e a velocidade de cancelamento não pode ser medida com datas não confiáveis.
- **Por que o CEO vê alta:** olha a contagem de cancelamentos, que cresce com a base. Lição registrada: auditar as datas antes de calcular qualquer taxa.
- Dashboard: todos os títulos viraram respostas; abertura passou a mostrar "o que o CEO vê" (contagem) ao lado de "o que acontece" (% por safra).
- **Feedback do usuário:** o dashboard será lido por quem não faz parte da administração; não importa "quem disse o quê".
  Removido todo enquadramento por fala (CEO/Produto/CS, "o que ninguém disse", selos de veredito sobre afirmações);
  os blocos agora são temas (Churn, Uso, Satisfação, Qualidade dos dados) com o resultado como título.

## Etapa 6 — Cancelamentos × mês × uso (script 06 + seção "Base, mês e uso")
- **Pergunta do usuário:** a quantidade de cancelamentos é casual ou tem relação com o mês? E com o uso? Depois: "quero que os gráficos comprovem a tese, quero certeza".
- **Resultados (janela estável jul/23–nov/24, quase-Poisson):** base explica 96% da variação; elasticidade 0,91 (IC 0,81–1,01, inclui 1 = proporcional);
  16 de 17 meses dentro da faixa de 95% esperada; tendência além da base p = 0,44; mês do ano p = 0,19.
- **Armadilha evitada:** uso por assinatura × cancelamentos dá ρ = −0,97 ("menos uso, mais churn") — espúrio, ambos são função do crescimento da base.
  Descontada a base: ρ = 0,40 (p = 0,11), não significativo e no sentido oposto. Variação mês a mês: ρ = 0,43 (p = 0,10).
- **Achado forte:** uso da conta 90 dias antes × depois de cada churn = 62,0 × 62,2 (351 eventos, p = 0,96); 99% seguem usando depois de "cancelar".
  O registro de churn não marca saída real.
- **Robustez que mudou a leitura:** com todos os meses, "tendência" dava p = 0,006 e uso×churn p = 0,014 — ambos somem ao tirar jan–jun/23 (contagens 0–5)
  e dez/24 (borda). Dispersão: 2,05 com todos os meses, 0,61 na janela estável → faixa calculada com φ = max(φ, 1), a opção conservadora.
- **Limite declarado:** sazonalidade com 2 anos = 2 observações por mês; o gráfico mostra ausência de sinal, não prova de ausência.
- Correções de texto pegas nos prints: fev/24 tinha 19 esperados (eu tinha escrito 21); "a relação some" virou "não há relação significativa"
  porque a nuvem tem leve inclinação positiva.

## Etapa 7 — Sumário lateral, página de Sugestões, previsão e skill de um comando
- **Pedido do usuário:** sumário na barra lateral; aba "Sugestões" com o que fazer para ter clareza nos dados, reduzir o churn e
  entender os cancelamentos; previsão "se for possível, com certeza, sem nada inventado"; e uma skill que refaça tudo com um comando.
- **Previsão — o que entrou e o que ficou de fora (decisão de honestidade):** entrou a % por safra (9,7%, IC 8,8–10,6%, n = 4.222)
  e os registros esperados por tamanho de base (4.707 assinaturas → 83/mês, faixa 57–114, área de extrapolação marcada).
  Ficou de fora previsão por data: dependeria de prever o crescimento da base e as datas de encerramento não são confiáveis.
- **Hipóteses DevTools e "event":** em vez de recomendar ação sobre elas, calculei quanto falta para confirmá-las num teste novo
  (α = 0,05, poder 80%): 218 e 284 contas do segmento, ~4 e ~6 anos no ritmo atual. Daí a sugestão de entrevistar quem saiu.
- **Sugestões:** plano em 3 etapas (medir, entender, reduzir), 6 correções de medição cada uma ligada a um número do diagnóstico
  e com critério de "resolvido", lista das 15 contas onde os registros concordam (US$ 216 mil de MRR encerrado), e a regra de
  medir pela % por safra e testar ações com grupo de controle. O impacto de 1 p.p. é aritmética (38 assinaturas × MRR mediano/médio
  das que cancelaram), apresentado como "tamanho do prêmio, não promessa".
- **Abas:** Diagnóstico / Sugestões / Dados (auditoria, mapa e contas saíram da página principal, que estava inchada).
- **Skill `diagnostico-churn`** (`skill/diagnostico-churn/`): `rodar.sh` faz download → 7 scripts → build → validação Playwright
  (3 páginas × desktop claro/escuro/celular) → resumo, em ~34 s. O SKILL.md guarda o método com as armadilhas deste projeto
  (datas antes de taxas, safra em vez de contagem, descontar a base, robustez, antes × depois, grau de certeza).
- Bugs pegos na validação: sumário marcando a seção errada no fim da página e durante a rolagem suave; numeração dupla;
  gaveta do sumário que não fechava no celular; motivos em inglês na tabela; eixo da previsão com marcas quebradas.
