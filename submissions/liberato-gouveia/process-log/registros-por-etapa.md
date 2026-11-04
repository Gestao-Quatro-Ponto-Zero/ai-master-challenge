# Registros por etapa

Cada fase do trabalho termina com um registro neste formato, definido pelo Liberato em 04/11/2026. Há uma regra que vale para todos: **nada aqui é inventado.** O que foi sugerido pela IA e ainda não foi validado aparece separado do que o Liberato decidiu ou conferiu.

---

## Registro 00: Revisão crítica da análise inicial e início do histórico de versões (04/11/2026)

**Objetivo da etapa**
Antes de definir a lógica do score, revisar com olhar crítico a análise feita até aqui (Etapas 0 a 7 do `diario-de-bordo.md`), listar o que ainda precisa ser verificado e começar o histórico de versões no fork do Liberato.

**Ferramentas utilizadas**
- Claude (app Claude, modo agente com terminal): revisão da análise e organização dos arquivos
- git: histórico de versões, na branch `submission/liberato-gouveia` do fork
- GitHub: fork `libegouv/ai-master-challenge`, criado pelo Liberato

**Prompts relevantes** (escritos pelo Liberato, transcritos sem edição)
> "Estamos desenvolvendo o Challenge 003 — Lead Scorer do processo seletivo G4 AI Master. Vou utilizar você (Claude) integrado ao Lovable para construir a aplicação. A partir de agora, quero trabalhar com uma metodologia controlada, transparente e documentada.
> REGRAS DE TRABALHO
> 1. Não avance automaticamente por várias etapas. Antes de executar uma nova fase importante, apresente o plano e aguarde minha autorização.
> 2. Utilize linguagem simples. Quando houver termos técnicos, explique brevemente o significado.
> 3. Antes de gerar código, vamos compreender o problema, analisar os dados e definir a lógica de priorização.
> 4. Ao final de cada etapa, gere um pequeno registro para meu Process Log [...]
> 5. Nunca invente decisões humanas, testes, erros, resultados ou evidências. Identifique claramente o que foi sugerido pela IA e o que foi efetivamente validado por mim.
> 6. Antes de utilizar o Lovable para criar ou modificar a aplicação, explique o que será desenvolvido e por quê.
> 7. Utilize os dados reais do desafio e evite vazamento de informações futuras na lógica de scoring.
> 8. Priorize uma solução funcional, intuitiva e explicável, respeitando a recomendação de 4 a 6 horas de esforço do G4.
> 9. Não faça a submissão final ou abra um Pull Request sem minha autorização.
> [...] Agora, revise a análise inicial que você já realizou, identifique o que ainda precisa ser verificado e apresente somente a primeira etapa do plano. Não inicie a implementação ainda."

**Resultados obtidos**
- O histórico de versões começou: branch `submission/liberato-gouveia`, pasta `submissions/liberato-gouveia/`, primeiro registro salvo no commit `f9d7a75`. Por enquanto ele existe só no ambiente do Claude. Nada foi enviado ao GitHub.
- A revisão separou o que já está sólido do que ainda precisa de verificação:
  - **Sólido:** os dados batem com o README do case. Produto, setor, região, gerente, vendedor e empresa não preveem o resultado, e três métodos diferentes concordam nisso. Nenhum deal fechado levou mais de 138 dias.
  - **A verificar (8 itens):** estão listados na proposta da Fase 1, no fim deste registro.

**Decisões que realmente tomei (Liberato)**
- Confirmei que a versão 2 do diário ficou clara.
- Autorizei o início do histórico de versões.
- Criei o fork `libegouv/ai-master-challenge`.
- Defini as 9 regras de trabalho acima.
- Decidi construir a aplicação com o Claude integrado ao Lovable.

**Sugestões da IA ainda não validadas por mim**
- A divisão em fases e o conteúdo da Fase 1 proposta abaixo.
- Manter o cálculo do score num script separado e testável, com o Lovable cuidando só da tela. Isso vai ser apresentado antes da fase de construção.

**Erros encontrados e correções**

| Erro | Quem encontrou | Correção |
|---|---|---|
| O diário apresentava as 3 "regras de vendas" e as escolhas da Etapa 7 como contribuições do Liberato, mas as opções foram **formuladas pela IA**. Ele selecionou entre elas. | Claude, na revisão pedida pelo Liberato | **Corrigido:** as Etapas 1 e 7 do diário agora dizem quem sugeriu e quem escolheu. A versão anterior está em `versoes/diario-de-bordo_v2_2026-11-04.md`. |
| O Gráfico 3 agrupa os deals pela **duração total**, um dado que só existe depois que o deal termina. Usar isso na nota de um deal aberto seria "vazamento de futuro", ou seja, usar uma informação que ninguém teria no momento da decisão. | Claude, na revisão | **Pendente:** item A da Fase 1. |
| O diário dá a entender que tempo e valor pesam parecido. Os números já calculados (`analises/resultados/eda3.txt`) mostram que, para um deal ainda vivo, a idade muda a chance de fechar só de ~61% para ~70%. O efeito forte do tempo é o limite de 138 dias. | Claude, na revisão | **Pendente:** corrigir o texto do diário depois da Fase 1. |
| O `.gitignore` do repositório do G4 manda ignorar a pasta `submissions/`. Seguindo o passo a passo do CONTRIBUTING ao pé da letra, a entrega não seria salva. | Claude, ao criar o primeiro registro | **Resolvido:** os arquivos foram adicionados com `git add -f`, sem alterar nenhum arquivo fora da nossa pasta (regra do G4). |

**Testes ou evidências disponíveis**
- Commit `f9d7a75` (registro inicial) e o commit desta etapa
- `versoes/diario-de-bordo_v2_2026-11-04.md`: o diário antes da correção de atribuição
- `analises/resultados/eda3.txt`: chance de ganhar para deals que continuam vivos depois de X dias (números usados na revisão)

**Tempo aproximado**
Não informado pelo Liberato.

---

## Proposta: Fase 1, Verificação da análise (aguardando autorização)

**Objetivo:** confirmar ou corrigir cada conclusão antes de definir a lógica do score. Esta fase não tem código da ferramenta, não usa o Lovable e não envia nada ao GitHub.

| # | O que verificar | Por que importa |
|---|---|---|
| A | Refazer a "chance de fechar" usando só o que se sabe **hoje** sobre um deal aberto: a idade dele. A pergunta é: "dos deals que chegaram vivos a X dias, quantos foram ganhos?" | Evita vazamento de futuro. Essa tabela vira a base oficial da nota. |
| B | Checar se o limite de 138 dias é real ou se é efeito da janela da base, olhando por mês de início: deals que começaram em março tiveram até ~300 dias para fechar. | Se o limite não se sustentar, a regra dos zumbis muda. |
| C | Ajustar a linguagem sobre os zumbis: os dados dizem "nunca houve fechamento depois de 138 dias", não "o deal está morto". | Não afirmar mais do que os dados mostram. |
| D | Contar quantos deals **vivos** não têm empresa cadastrada antes de aplicar a regra "sem conta = sem dono". | 68% dos abertos não têm empresa. A regra pode esvaziar a lista de foco. |
| E | Deals em prospecção (500): confirmar que não existe dado nenhum para estimar a chance deles. | Para não inventar uma probabilidade. |
| F | Repetir o teste de machine learning separando por **tempo**: treinar com os deals mais antigos e testar com os mais novos, como na vida real. | É uma prova mais rigorosa contra vazamento de futuro. |
| G | Investigar o padrão de fim de trimestre (meses 3, 6, 9 e 12 têm ~80% de ganho, contra ~50% nos outros meses). | Um avaliador pode perguntar sobre isso. Precisamos saber se é útil sem vazamento ou se é só um efeito da base. |
| H | (Opcional, depende do Liberato) Comparar os nossos dados com o arquivo oficial do Kaggle. | Fecha a única dúvida que ainda existe sobre a origem dos dados. |

**Entregas da Fase 1:** o resultado de cada item (confirmado ou corrigido), a tabela oficial de chance por idade, o diário corrigido, o registro da fase neste arquivo e o commit.

**Decisões que vão ficar para o Liberato ao final:** como tratar deals sem empresa cadastrada (depende do item D), como tratar deals em prospecção (item E) e se o padrão de fim de trimestre entra ou não (item G).
