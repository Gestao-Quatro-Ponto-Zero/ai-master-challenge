# Proposta de Automação com IA — Suporte ao Cliente

> **Resumo:** o diagnóstico mostrou que os dados operacionais são cegos — mas o **texto** dos tickets é a matéria-prima rica e subaproveitada. A automação de maior retorno é **classificar e rotear** tickets automaticamente, com um **gate de confiança** que decide o que a máquina resolve sozinha e o que vai para um humano. Não é "automatizar tudo" — é automatizar o que é seguro e mensurável, e parar onde o julgamento humano é insubstituível.

---

## A oportunidade

O suporte recebe volume alto, repetitivo e **classificável** — e hoje a triagem é manual. Enquanto os campos operacionais (tempo, prioridade, satisfação) não permitem diagnóstico confiável, o **texto** do ticket é suficiente para roteá-lo para a fila certa com boa acurácia. É aí que a IA gera retorno **agora**, sem depender de corrigir o histórico.

## 1. O que automatizar

**Classificação + roteamento automático (o núcleo).** Um classificador de texto atribui a cada ticket uma das 8 categorias e o encaminha à fila responsável. Não é promessa: está construído e medido — **86,5% de acurácia** (F1-macro 0,86) em teste, rodando localmente em milissegundos e a custo zero por ticket. → *ver `prototype/`*

**Detecção de duplicatas / tickets similares (extensão).** O mesmo motor de similaridade de texto agrupa tickets recorrentes, reduzindo retrabalho. Menor prioridade que o roteamento, mas barato de acoplar.

## 2. O que **NÃO** automatizar — e por quê (com base nos dados)

Automatizar 100% é *red flag*, não virtude. Onde paramos, e a evidência:

- **Abaixo do limiar de confiança → humano.** O modelo devolve uma confiança; abaixo de um limiar (0,69 → ~95% de precisão nos auto-roteados), o ticket vai para uma pessoa. No conjunto de teste isso é **26% dos tickets**. É assim que respondemos "o que não automatizar" com número, não opinião.
- **Sugestão de resposta automática → não (ainda).** O campo `Resolution` do Dataset 1 é **texto sintético incoerente** — não há corpus real de resoluções para treinar ou validar. Construir isso agora produziria sugestões sem sentido. Fica como trabalho futuro que exige **investimento em dados** (logar resoluções reais estruturadas), não como entrega.
- **Triagem automática de prioridade → não.** No Dataset 1 a prioridade é estatisticamente uniforme e **não correlaciona com a satisfação** — ou seja, não há *ground truth* de "o que deveria ser urgente". Automatizar aqui codificaria ruído.
- **Casos que exigem julgamento humano** (roteados à parte, sempre): disputas de **reembolso/cobrança** (dinheiro em jogo), tickets **Critical com CSAT baixo** (cliente insatisfeito de alto risco), e tickets **multi-tópico/ambíguos**. Exemplo real do dataset: um pedido que é só uma *aprovação* ou *mudança de grupo* cai em "Miscellaneous" — categoria de fronteira difícil, exatamente onde a confiança do modelo cai e o gate manda para humano.

## 3. Como funciona na prática (o fluxo)

```
Ticket entra
   │
   ▼
Classificador  ──►  categoria + confiança
   │
   ▼
GATE DE CONFIANÇA
   ├─ confiança ≥ limiar ──►  auto-roteia p/ a fila da categoria
   │                          (Hardware→time de Hardware, Access→IAM, …)
   └─ confiança < limiar ──►  fila humana (triagem)
                                   │
                                   ▼
                             agente resolve
                                   │
                                   ▼
                    correção do agente vira NOVO RÓTULO
                    de treino  ──►  loop de feedback (modelo melhora)
```

O limiar é um **valor de configuração** que o time de operações ajusta conforme a tolerância a erro: mais alto = mais preciso, menos automatizado; mais baixo = mais cobertura, mais risco. O protótipo deixa esse trade-off visível e ajustável ao vivo.

## 4. Por que um modelo supervisionado, e não um LLM

Testamos a hipótese óbvia ("é só jogar num LLM") de forma justa — TF-IDF supervisionado vs. Claude Haiku/Sonnet/Opus em zero-shot, na mesma amostra:

| Solução | Acurácia | Custo/passe (47.837) | Latência |
|---|---|---|---|
| **TF-IDF supervisionado** | **88,6%** | **~US$0** | <1 ms |
| Opus (prompt caprichado) | 55,8% | ~US$210 | ~2.100 ms |
| Opus (prompt cru) | 47,0% | ~US$54 | ~2.100 ms |

Mesmo dando ao LLM sua melhor chance (definições do dataset + few-shot), ele perde por ~33 pontos, custa mais e é ~1.000× mais lento. Motivo: os rótulos seguem convenções específicas do dataset que o zero-shot não conhece, e o texto pré-processado favorece o modelo treinado. **Para esta tarefa, supervisionado é a ferramenta certa em todos os eixos.** O LLM tem valor noutro lugar — categoria nova, *cold start*, ou tickets genuinamente ambíguos que o gate escala.

## 5. ROI — o que a automação recupera

O ganho concreto e verificável: **o sistema faz a triagem sozinho de 74% dos tickets** (a ~95% de precisão, limiar 0,69). Em 3 de cada 4 tickets, ninguém precisa ler e classificar manualmente — a máquina faz na hora, a custo marginal **~US$0**.

Quanto isso vale em horas depende de dois números que são **de vocês**, não meus: o volume de tickets e o tempo de triagem manual. Não invento um número de desperdício *atual* (não é mensurável nestes dados). Em vez disso, um exemplo com a conta aberta, para vocês trocarem pelos valores reais:

> **Exemplo ilustrativo:** ~30.000 tickets/ano *(volume citado pelo Diretor)* × 74% automatizados × ~2,5 min de triagem manual por ticket *(premissa — ajuste com o seu tempo real)* ≈ **~900 horas/ano** poupadas só na triagem.

Troque o "2,5 min" pelo tempo real e a conta se refaz. Para o Diretor, o ponto não é o número exato — é que **a triagem de ~3 em cada 4 tickets é recuperável a custo de infraestrutura desprezível**. O mesmo trabalho via LLM custaria ~US$7-210 por passe e seria ~1.000× mais lento.

## Limitações

Este é um protótipo de capacidade, não um sistema pronto. Para produção: **retreinar nos tickets e na taxonomia da própria empresa**; treinar em **texto cru** (dá mais sinal que o texto pré-processado do dataset); **calibrar** a confiança (o número exibido é *score*, não probabilidade — o limiar foi escolhido empiricamente); e adicionar **monitoramento + o loop de feedback** acima. Detalhes de arquitetura em `prototype/README.md`.
