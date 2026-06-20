# Redesenho de processo — da priorização "no feeling" à rotina do Foco

> Complemento à submissão. A ferramenta (app **Foco**) é a estrela; este documento mostra **como o time de vendas passa a operar** com ela — a mudança de rotina, não só de software.
> Diagnóstico e números detalhados: [`GUIA-DO-PRODUTO.md`](GUIA-DO-PRODUTO.md) · [`decisoes.md`](decisoes.md).

---

## 1. Estado atual (As-Is)

Hoje a priorização é **"no feeling"**: cada vendedor decide no instinto onde focar, e ninguém limpa o que já morreu. Isso gera um ciclo que se realimenta — quanto mais entulho no pipeline, mais difícil enxergar o que vale, o que empurra o vendedor de volta pro feeling. Os nossos dados mostram o tamanho do problema:

- **61,8% dos deals abertos (1.291 de 2.089)** já passaram do ciclo de **qualquer** venda fechada na história (>138 dias — nenhum negócio ganho levou mais que isso). É pipeline inflado com deals provavelmente mortos.
- **68% (1.425 de 2.089)** estão **sem conta atribuída** no CRM — não dá nem para saber quem é o cliente.

Resultado: esforço gasto em deal que não fecha e boa oportunidade esfriando por falta de atenção, sem ninguém medindo nem corrigindo.

## 2. Estado futuro (To-Be) — o novo modelo operacional

O Foco vira a **rotina**, com um recorte por papel:

- **Vendedor** — abre o **Foco do Dia** toda segunda, ataca o **top 3–5** (a lista priorizada com o porquê de cada deal) e marca as ações (✓ Contatado · ✕ Descartar). O "feeling" vira exceção, não regra.
- **Gestor** — revisa semanalmente a **receita em risco** do time (hoje **R$ 302.340** na janela de fechamento 88–138d) e faz **drill-down por vendedor** para ver quem precisa de apoio em priorização.
- **RevOps** — assume a **higiene de CRM** como dono: acompanha o % sem conta e o % de pipeline morto na tela Saúde, e cobra a correção na origem.

| Fluxo | Antes (As-Is) | Depois (To-Be) |
|-------|---------------|----------------|
| Como o vendedor escolhe o foco | Instinto, deal a deal | Lista priorizada com score + motivo |
| O que acontece com deal morto | Fica no pipeline para sempre | Sai do foco e vai para Revisar/Descartar |
| Visão do gestor | Planilha/relatório pontual | Receita em risco semanal + drill-down |
| Higiene de dados | Ninguém é dono | RevOps mede e cobra na origem |
| Aprendizado | Nenhum | Loop: conversão dos "Foco Agora" recalibra o modelo |

## 3. Mudanças na ORIGEM (não só no app)

O app prioriza melhor, mas o ciclo vicioso só quebra de vez **a montante**, no processo e no CRM:

1. **Conta obrigatória na criação do deal** — elimina os 68% sem conta na raiz (campo obrigatório no formulário de abertura). É a maior alavanca de precisão hoje.
2. **Registrar a última interação real** — hoje a urgência usa `engage_date` como proxy fraco; capturar a última atividade por deal torna o "esfriando" confiável e fecha o buraco que infla o stale.
3. **Loop de feedback** — marcar os deals "Foco Agora" e medir a conversão deles **vs a base de 63%**; o resultado recalibra os pesos do score (melhora contínua, não modelo congelado).

## 4. Papéis e responsabilidades

| Papel | Responsável por | Cadência |
|-------|-----------------|----------|
| **Vendedor** | Atacar o top 3–5 do Foco do Dia; registrar ação por deal | Diária |
| **Gestor** | Receita em risco do time; apoio a quem tem muito a revisar | Semanal |
| **RevOps** | Higiene de CRM (conta + interação); saúde do pipeline; recalibração | Semanal / contínua |

## 5. Métricas de sucesso

- **% de pipeline morto cai** — reduzir os 61,8% de stale conforme o time limpa o que já morreu.
- **% de deals com conta sobe** — atacar os 68% sem conta na origem (meta: campo obrigatório → ~0% de novos sem conta).
- **Conversão dos "Foco Agora" supera a base** — os deals priorizados devem fechar **acima dos 63%** globais; é a prova de que a priorização funciona.

## 6. Riscos de adoção e mitigação

| Risco | Mitigação |
|-------|-----------|
| Vendedor ignora a lista e volta ao feeling | Cada deal mostra o **porquê** (win-rate, ticket, janela) — confiança em vez de caixa-preta; gestor acompanha a adesão no drill-down |
| Dados de interação não chegam ao CRM | Começar pelo campo **conta obrigatório** (ganho imediato) antes do histórico de interação; medir o % preenchido como métrica de RevOps |
| Limpeza do pipeline parece "perder" deals | Stale não some — vai para **Revisar/Descartar** (reversível e auditável); é decisão consciente, não exclusão silenciosa |
| Dataset histórico (~2017) limita a calibração | O loop de feedback recalibra com dados reais de produção; o modelo é regras + estatística defensável, fácil de reajustar |

---

> **Em uma frase:** o Foco transforma a priorização de um palpite individual numa rotina mensurável — e o redesenho garante que a melhoria não dependa só da tela, mas de **dados limpos na origem** e de um **loop que aprende**.
