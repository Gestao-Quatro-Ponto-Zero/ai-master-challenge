# Process log — comece por aqui

Resumo em cinco linhas: a IA foi usada em duas fases, planejamento e construção, com modelos trocados por mim entre etapas, por custo e qualidade. O motor e o score são determinísticos, sem IA no caminho crítico; a IA entrou no planejamento, na implementação assistida e num módulo opcional de texto, que não está ligado nesta entrega. Dezesseis erros da IA foram pegos e corrigidos, cinco deles de um agente de persona usado no discovery. Os números do produto foram recalculados de forma independente, com código próprio, e bateram. Tudo está rastreável: diário por sessão, inventário de modelos, git history e conversas exportadas.

## Linha do tempo

> Reconstruída a partir do diário, do git e dos registros de sessão do Claude Code.

### Fase A — planejamento (10/11, antes do fork)

| Etapa | Ferramenta e modelo | O que saiu | Evidência |
|---|---|---|---|
| Leitura da vaga e escolha do desafio | Claude Code, `claude-fable-5-1` | primeiro plano de ação para o desafio 003 | [chat-exports/claude-code-10-11-5b03c259.md](chat-exports/claude-code-10-11-5b03c259.md) |
| Comparação dos desafios 03 e 04 | Claude Code, `claude-fable-5-2` | decisão de seguir com o 003, com base nos PRs já enviados | [chat-exports/claude-code-10-11-3f2cfd05.md](chat-exports/claude-code-10-11-3f2cfd05.md) |
| Revisão do plano por três ângulos e plano v2 | Claude Code, `claude-fable-5-2` em esforço extra-alto, `claude-opus-5`, `claude-sonnet-4-6` | plano v2, com teste antes do código e regras de corte | [chat-exports/claude-code-10-11-2cb9516c.md](chat-exports/claude-code-10-11-2cb9516c.md), [planejamento/02-plano-implementacao.md](planejamento/02-plano-implementacao.md), [planejamento/03-revisao-tecnica.md](planejamento/03-revisao-tecnica.md) |
| Pesquisa de cultura comercial | Perplexity | síntese de fontes abertas sobre arquétipos de vendedor | [fontes-cultura-g4.md](fontes-cultura-g4.md) |
| Montagem do agente de personas | Microsoft 365 Copilot, GPT Sol 6.1 | agente com quatro arquétipos e um líder, com travas contra validação circular | [agente-personas-config.md](agente-personas-config.md) |
| HTML com as etapas e os modelos de cada uma | Claude Code, `claude-haiku-5-5` | artifact visual do passo a passo | [chat-exports/claude-code-11-11-e9679c22.md](chat-exports/claude-code-11-11-e9679c22.md) |

### Fase B — construção (11/11)

| Etapa | Ferramenta e modelo | O que saiu | Evidência |
|---|---|---|---|
| Fork, estrutura, Tarefas 0 e 0B | Claude Code, `claude-haiku-5-5` | repositório preparado, baseline em três modelos, pré-registro das premissas | [chat-exports/claude-code-11-11-9ab5e108.md](chat-exports/claude-code-11-11-9ab5e108.md), [chat-exports/claude-code-11-11-02c961fd.md](chat-exports/claude-code-11-11-02c961fd.md) |
| Motor, backtest, telas, deploy, documentos (Tarefas 1 a 13) | Claude Code, `claude-sonnet-4-6`, `claude-sonnet-5`, `claude-sonnet-5-5`, `claude-opus-5`, `claude-haiku-4-5`, `claude-haiku-5-5` | motor com teste antes do código, backtest com IC, três telas, demo publicada | [chat-exports/claude-code-11-11-6efc8e8f.md](chat-exports/claude-code-11-11-6efc8e8f.md), git log |
| Preparação de arquivos para a revisão externa | Claude Code, `claude-haiku-5-5` | lista de arquivos e prints para subir noutra ferramenta | [chat-exports/claude-code-11-11-89ca465e.md](chat-exports/claude-code-11-11-89ca465e.md) |
| Revisão externa da entrega | ChatGPT Sol 5.6, raciocínio estendido | plano de 20 prompts de ajuste, comparando a entrega com o pedido do desafio | — (link ou PDF, ver [MODELOS.md](MODELOS.md)) |
| Triagem do plano, formato final, PR | Claude Code, `claude-opus-5-5`, `claude-sonnet-5-5`, `claude-sonnet-5`, `claude-haiku-5-5` | auditoria do repositório, README, docs de apoio, verificação independente, este process log | esta sessão |

## Como a IA foi decomposta

O plano foi escrito antes de qualquer código, revisado por um segundo modelo sob três ângulos (engenharia de dados, software, operação comercial), e só então reescrito como plano v2. Cada módulo do motor foi implementado com teste antes do código, e cada um foi conferido contra os valores de ouro de um protótipo da fase de análise, não só contra os testes escritos na mesma sessão. O discovery foi tratado como fonte de hipótese, nunca de fato: pré-registro commitado antes da primeira pergunta, entrevistas e consulta ao dado em conversas separadas, calibração com perguntas de resposta já conhecida.

## Onde a IA errou

Dezesseis erros registrados, cada um com o teste ou a verificação que o pegou: [onde-a-ia-errou.md](onde-a-ia-errou.md). Cinco são do agente de persona (inventou situações vividas e acessos a dados que não tinha); onze são meus, pegos por teste ou verificação nas Tarefas 1 a 13 — entre eles, o vazamento do campo de conta na permutação e uma fórmula de chance com viés de sobrevivência.

## Como os erros foram detectados e corrigidos

Teste automatizado, comparação com o protótipo de análise, perguntas de calibração para os agentes de persona, e a verificação independente feita por outro revisor com código próprio. Nenhum erro foi corrigido só porque "parecia certo"; cada correção está ligada a um teste que passou a existir por causa dela.

## O que foi acrescentado por julgamento humano

Lista completa: [o-que-eu-acrescentei.md](o-que-eu-acrescentei.md). Resumo: a troca da pergunta "quem ganha" por "quando decide", depois que o dado recusou a primeira; a recusa do atalho de comparar com ordem aleatória; a exigência de intervalo de confiança em toda razão entre políticas; o desenho do piloto por sorteio dentro do vendedor; manter a IA fora do caminho crítico do score; e declarar em cada negócio o que a ferramenta não sabe.

## Verificação e evals

Backtest em seis cortes com IC por reamostragem de vendedor, permutação de atributos, 68 testes automatizados, e verificação independente com código próprio a partir dos CSVs, sem importar o motor: [verificacao/relatorio.md](verificacao/relatorio.md). Todos os números recalculados bateram; quatro ressalvas foram corrigidas.

## Número de iterações

Não há evidência suficiente para dar um total exato de iterações. O que o registro demonstra, com critério objetivo: **39 commits** na branch `submission/diego-rodrigues`, **9 sessões exportadas do Claude Code** (mais a revisão externa no ChatGPT Sol 5.6), e **27 sessões de trabalho** registradas no diário ([diario.md](diario.md)), com **16 erros da IA** pegos e corrigidos ao longo delas.

## Mapa das evidências

| Evidência | O que mostra |
|---|---|
| [REGISTRO.md](REGISTRO.md) | Índice geral de ferramentas, workflow e contagem |
| [diario.md](diario.md) | Diário por sessão, gravado na hora |
| [MODELOS.md](MODELOS.md) | Inventário com versão exata, papel, custo e dado exposto |
| [onde-a-ia-errou.md](onde-a-ia-errou.md) | Os 16 erros, com o teste que pegou cada um |
| [o-que-eu-acrescentei.md](o-que-eu-acrescentei.md) | O julgamento humano, com as rejeições |
| [baseline/](baseline/) | Três modelos sem o dado na mão (Tarefa 0) |
| [verificacao/](verificacao/) | Protocolo e relatório da verificação independente |
| [planejamento/](planejamento/) | Plano v2, revisão técnica e scripts de análise que fundamentaram o motor |
| [chat-exports/](chat-exports/) | Conversas do Claude Code exportadas e sanitizadas, por sessão |
| [agente-personas-config.md](agente-personas-config.md) | Configuração do agente de persona e as travas contra validação circular |
| [fontes-cultura-g4.md](fontes-cultura-g4.md) | Pesquisa de fontes abertas que fundamentou as personas |
| `screenshots/` | Prints **do produto**, não de conversas com IA |

## Limitações do registro

As sessões anteriores a 11/11 (Fase A) foram exportadas do histórico local do Claude Code; o export tira resultados de ferramenta e lembretes de sistema, então ele mostra prompts e respostas em texto, não a tela como ela apareceu. A revisão externa no ChatGPT Sol 5.6 está documentada em `MODELOS.md`, mas seu export (link ou PDF) depende de upload manual, feito fora desta sessão. A contagem de "27 sessões de trabalho" vem do diário, que é preenchido por mim ao longo do dia e pode não capturar toda troca de modelo dentro de uma mesma sessão.
