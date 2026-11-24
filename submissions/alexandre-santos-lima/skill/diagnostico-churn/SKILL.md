---
name: diagnostico-churn
description: Roda de ponta a ponta o diagnóstico de churn da RavenStack (dataset Kaggle rivalytics/saas-subscription-and-churn-analytics-dataset) com um comando — baixa as 5 tabelas, liga por conta, audita chaves e datas, testa correlações por categoria com correção estatística, separa volume de taxa, testa base × mês × uso, gera a previsão e as sugestões, monta o dashboard React e valida no navegador. Use quando o usuário chamar /diagnostico-churn, pedir para "rodar o diagnóstico de churn", "atualizar o dashboard de churn", "refazer a análise com os dados novos" ou aplicar o mesmo método de diagnóstico de churn a outro dataset de assinaturas.
---

# Diagnóstico de churn

## Rodar (um comando)

```bash
~/.claude/skills/diagnostico-churn/scripts/rodar.sh             # usa os dados já baixados
~/.claude/skills/diagnostico-churn/scripts/rodar.sh --atualizar # baixa de novo do Kaggle (o dataset é mensal)
~/.claude/skills/diagnostico-churn/scripts/rodar.sh --servir    # no fim, deixa o dashboard em 0.0.0.0:5180
```

A skill não publica nada: ela gera o painel em `solution/dashboard/dist/`, que pode ser enviado para qualquer hospedagem
estática. Nenhuma credencial fica na skill (o único segredo usado é o token do Kaggle, lido de `~/.kaggle`).

Requisitos: `uv`, `node`/`npm`, token do Kaggle em `~/.kaggle/access_token` (ou `KAGGLE_API_TOKEN`).
A pasta da submissão é detectada a partir da skill; para outra pasta, `CHURN_ROOT=/caminho`.

O comando faz, nesta ordem, e para no primeiro erro:

| Etapa | Script | Sai em |
|---|---|---|
| Dados | `00_download.sh` | `data/raw/` (fora do git) |
| Ligar e auditar | `01_build_dataset.py` | `account_360.csv`, `subscription_360.csv`, `docs/auditoria_dados.md` |
| Correlações | `02_correlacoes.py`, `03_correlacoes_assinatura.py` | `docs/correlacoes_*.md` |
| Séries e safras | `04_export_dashboard.py`, `05_teste_safras.py` | `dashboard/src/data.json` |
| Base × mês × uso | `06_cancelamentos_mes_uso.py` | `dashboard/src/mes_uso.json` |
| Previsão e sugestões | `07_sugestoes_previsao.py` | `dashboard/src/sugestoes.json` |
| Dashboard | `npm run build` | `dashboard/dist/` |
| Validação | `dashboard/scripts/validar.mjs` (Playwright) | `solution/outputs/validacao/*.png` |

No fim imprime o resumo (safra, base, mês, uso, qualidade dos dados, previsão).

## Depois de rodar (o que o Claude deve fazer)

1. **Ler o resumo e comparar com a rodada anterior.** Se algum número central mudou de lado (por exemplo, uma variável passou
   a sobreviver à correção, a % por safra subiu além da faixa, a auditoria melhorou), isso é notícia: avise o usuário antes de
   qualquer outra coisa e cheque se os textos do dashboard ainda dizem a verdade.
2. **Abrir os prints** em `solution/outputs/validacao/` e olhar de verdade: layout, números em pt-BR, textos que citam números.
   A validação automática só pega erro de console, seção faltando e rolagem lateral.
3. **Textos com números fixos.** Os componentes leem quase tudo dos JSONs, mas títulos que afirmam uma conclusão
   ("não há sinal de que o churn piorou") precisam ser relidos quando os dados mudam.
4. Registrar no `process-log/` o que mudou e por quê.

## O método (vale para qualquer dataset de assinaturas)

Cada passo existe porque, sem ele, a conclusão saiu errada pelo menos uma vez neste projeto.

1. **Auditar as ligações antes de analisar.** Chaves (registros órfãos) e **datas** entre tabelas: uso dentro da vigência da
   assinatura? ticket depois do cadastro? evento de churn coincide com fim de assinatura? Aqui as chaves batiam 100% e as datas não
   (77,7% do uso fora da vigência). Com datas quebradas, nada de janelas como "90 dias antes do churn": ligar por chave e agregar.
2. **Testar se as definições de churn concordam.** Flag da conta, tabela de eventos e assinaturas encerradas descreviam contas
   diferentes (312 de 500 discordavam). Reportar a divergência é um achado, não um detalhe.
3. **Nunca concluir pela contagem.** Contagem cresce com a base. Comparar com a base ativa e, melhor, usar a **% de cada safra
   que cancela** (coorte por trimestre de entrada), que não depende da data exata do cancelamento.
4. **Auditar a data de encerramento antes de qualquer taxa mensal.** Dois testes rápidos: contratos anuais encerrados antes de
   365 dias (aqui 211 de 216) e a posição do cancelamento na janela disponível até o fim dos dados (sempre ~50% = data sorteada).
   Se falhar, a taxa mensal não serve. Este erro foi cometido duas vezes neste projeto antes de ser pego.
5. **Correlação por categoria com correção para múltiplos testes** (Benjamini-Hochberg), nos níveis conta e assinatura, para cada
   definição de churn. Força normalizada 0–1 (|AUC−0,5|×2 ou V de Cramér). Destaque com p bruto baixo que some na correção é ruído.
6. **Séries temporais: descontar a base antes de correlacionar.** Uso por assinatura × cancelamentos deu ρ = −0,97 ("menos uso,
   mais churn"), espúrio: as duas séries só refletem o crescimento. Usar modelo com a base (Poisson com offset/log da base,
   quase-Poisson se houver sobredispersão), resíduos ou primeiras diferenças.
7. **Robustez:** refazer cada teste sem os meses de contagem minúscula e sem a borda do fim dos dados. Aqui uma "tendência"
   (p = 0,006) e uma relação uso × churn (p = 0,014) sumiram assim.
8. **Teste antes × depois:** uso da conta nos 90 dias antes e depois de cada churn. Se não muda (aqui 62,0 × 62,2), o registro de
   churn não marca a saída real.
9. **Segmentos:** taxa com IC de 95%, teste do conjunto, e para cada destaque o tamanho de amostra necessário para confirmar
   com dados novos (e quanto tempo isso leva no ritmo atual).
10. **Previsão só do que os dados sustentam:** % por safra com IC e registros esperados por tamanho de base, marcando extrapolação.
    Sem previsão por data quando as datas não são confiáveis ou quando ela dependeria de prever o crescimento.
11. **Dizer o grau de certeza.** "Não há sinal de piora" ≠ "o churn caiu". Ausência de sinal sazonal com 2 anos ≠ prova de ausência.

## Regras do dashboard

- **Escrito para quem não é técnico.** Frases curtas, palavras do dia a dia, números como "X de cada 100". Sem siglas nem jargão no texto
  principal: "cancelamento" (não churn), "receita mensal" (não MRR), "número de clientes" (não base), "quem entrou no trimestre" (não safra/coorte),
  "pode ser acaso" (não p-valor), "margem de erro" (não IC). Os números estatísticos (ρ, p, AUC, IC, nome do teste) ficam no bloco
  **"Detalhe técnico"** (componente `Tecnico`), fechado por padrão: o leitor leigo entende, o avaliador técnico confere.
- Títulos são **respostas**, não perguntas. Nada de "quem disse o quê": só resultados, para quem não conhece a empresa.
- Toda frase que afirma um padrão precisa ser conferida contra o gráfico ao lado (ex.: "nenhum mês fica acima nos dois anos" era falso para dezembro).
- Todo número na tela vem dos JSONs gerados; texto com número fixo é exceção e precisa ser conferido.
- pt-BR: vírgula decimal, ponto de milhar, datas `mmm/aa`. Paleta validada para daltonismo, tema claro e escuro.
- Cada gráfico de prova traz o número do teste ao lado do título.
- Abas: Diagnóstico (achados), Sugestões (o que fazer), Dados (auditoria, mapa, contas). Sumário na barra lateral.
- Validar com Playwright e **olhar os prints** antes de dar como pronto, inclusive em 390 px.

## Adaptar a outro dataset

Os scripts esperam o esquema RavenStack (`accounts`, `subscriptions`, `feature_usage`, `support_tickets`, `churn_events` com as
colunas do README do dataset). Para outro dataset: mapear as colunas equivalentes em `01_build_dataset.py` (é o único que lê os
CSVs crus junto com 04, 05, 06 e 07), manter os prefixos de categoria (`perfil_`, `receita_`, `uso_`, `suporte_`, `churn_`) e
rodar. As etapas do método acima continuam valendo mesmo que o código precise de ajustes.
