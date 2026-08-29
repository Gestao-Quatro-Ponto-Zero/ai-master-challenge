# Process Log

## Objetivo e formato

Este é um registro curado das decisões que mudaram a solução. Optei por uma narrativa verificável, formato aceito pelo guia, em vez de publicar conversas brutas. Cada etapa aponta para código, dados ou interface que pode ser reproduzida.

Antes de construir, decompus o challenge em cinco frentes: auditoria e proveniência dos dados; scoring determinístico; experiência do vendedor; backend com IA; validação, segurança e documentação. O processo abaixo resume **nove iterações materiais**. Ajustes visuais menores e tentativas repetidas foram agrupados para manter o log legível.

## Ferramentas usadas

| Ferramenta | Uso |
|---|---|
| ChatGPT / Codex | Decomposição do problema, crítica das fórmulas, implementação assistida, revisão de frontend/backend e documentação |
| Python + pandas | Auditoria reproduzível de qualidade, relacionamentos, datas, cobertura e risco de leakage |
| Python: biblioteca padrão | Pipeline determinístico de P/O/W/E e servidor local sem dependências |
| Supabase | Postgres, RLS, read model público e cache de recomendações |
| OpenAI Responses API | Geração estruturada de R na primeira abertura do card, com reutilização do resultado salvo |
| Pinterest e referências de CRM | Pesquisa visual de densidade, hierarquia, cards e padrões de pipeline; as referências orientaram decisões, sem copiar uma interface pronta |
| Pesquisa em fontes públicas | Confirmação da proveniência do dataset, do catálogo, das licenças dos assets e de decisões técnicas |
| Navegador e inspeção de console | Testes funcionais, responsividade, carregamento e validação visual |

## Workflow e principais iterações

### 1. Auditar antes de modelar

Comecei pelas quatro tabelas e pela proveniência do dataset. A auditoria verificou chaves, duplicidades, nulos, integridade referencial, datas e coerência por estágio. Três achados mudaram o desenho:

- apenas 30 dos 35 vendedores possuem oportunidades;
- 1.425 das 2.089 oportunidades ativas não possuem conta;
- 1.301 oportunidades em `Engaging` já excedem o maior ciclo fechado observado.

Também foi normalizada a divergência `GTXPro`/`GTX Pro` sem alterar o arquivo bruto. Evidências: [`../docs/data-audit.md`](../docs/data-audit.md) e [`../solution/scripts/audit_data.py`](../solution/scripts/audit_data.py).

### 2. Separar sinais que não deveriam virar uma nota opaca

A primeira direção tentava produzir um lead score único e opaco. A revisão humana apontou que chance histórica, valor, frescor e capacidade do vendedor respondem perguntas diferentes. A solução preserva um **POWER Profile** com quatro números explicáveis e uma recomendação textual:

- P: Propensity;
- O: Opportunity Value;
- W: Warmth;
- E: Execution Fit;
- R: Recommendation.

Para transformar as quatro leituras em ordem de trabalho, foi adicionado o **POWER Priority**: `PP = (12P + 3O + 4W + 6E) / 25`. A hierarquia de negócio declarada `P > E > W > O` foi convertida em fatores pelo inverso das posições (`1`, `1/2`, `1/3`, `1/4`), escalados para `12`, `6`, `4` e `3`. P/O/W/E continuam visíveis; PP apenas consolida a priorização e R não entra na equação.

### 3. Construir P com evidência e força da amostra

A taxa geral de Won/Lost era superficial. P passou a observar setor, produto, tier de ticket e match completo. Cada taxa é acompanhada por casos e ponderada por `min(casos / 30, 1)`. Para registros históricos, somente resultados encerrados antes do momento avaliado entram nos contadores; isso impede que uma oportunidade use o próprio resultado.

Implementação: [`../solution/scripts/build_power_dataset.py`](../solution/scripts/build_power_dataset.py).

### 4. Corrigir O sem esconder a economia do dataset

Ao aparecerem valores de US$ 55 e US$ 26.768, a primeira suspeita foi erro de importação. A conferência no CSV original e no banco mostrou que são preços reais do catálogo fictício. A decisão foi preservar a diferença no score `valor / maior valor`.

Os tiers deixaram de ser faixas universais ou rótulos manuais: preços distintos são ordenados e distribuídos matematicamente entre Bronze, Prata, Ouro e Diamante. Assim, a mesma regra funciona em outro catálogo.

### 5. Substituir uma temperatura arbitrária por distribuição empírica

Uma proposta inicial usava uma constante temporal sem base clara. Ela foi rejeitada. W passou a responder: “qual percentual dos ciclos encerrados durou pelo menos esta idade?”. Os rótulos Quente/Morna/Fria/Estagnada vêm dos quartis calculados nos 6.711 ciclos, não de prazos inventados.

### 6. Trocar confiança genérica por Execution Fit

Uma dimensão de completude/confiança ficaria quase constante em um CRM real e teria baixo valor para o vendedor. Ela foi substituída por E, que mede o histórico do vendedor em produto, setor e tier de ticket por atuações e ganhos.

Company Fit chegou a aparecer na documentação antes de existir na implementação. Na revisão pré-submissão, essa sobreafirmação foi removida: ele permanece como evolução até que bandas firmográficas sejam definidas e validadas.

### 7. Remover redundância entre P e o antigo Risk

Risk foi explorado como taxa de perda de negócios semelhantes. O problema é que isso repetia o inverso de P e exigia outra leitura do mesmo histórico. Relevance também foi descartado porque obrigaria varrer a base sem acrescentar uma decisão nova.

R tornou-se Recommendation: a IA recebe apenas o perfil já calculado e devolve uma ação curta e uma frase imperativa de até 24 palavras. A função usa schema JSON estrito, não envia o dataset inteiro e armazena a saída por hash e versão do prompt.

Implementação: [`../solution/supabase/functions/generate-recommendation/index.ts`](../solution/supabase/functions/generate-recommendation/index.ts).

### 8. Transformar o framework em ferramenta de vendedor

O primeiro frontend tratava Won e Lost como visões separadas. Isso foi corrigido para um único pipeline com quatro colunas simultâneas. Depois, a carga integral das 8.800 oportunidades causou lentidão, reconstrução da tela e contadores “pipocando”. A arquitetura final usa:

- amostra inicial estável por etapa;
- três páginas concorrentes no carregamento de fundo;
- scroll e renderização incremental por coluna;
- atualização final sem substituir os cards visíveis;
- proxy local de mesma origem com cache em memória;
- R automático na abertura do card e reutilização do resultado salvo.

Para a direção visual, busquei referências de CRMs, pipelines e cards no Pinterest e confrontei esses padrões com a rotina de um vendedor. ChatGPT/Codex ajudou a transformar as referências em componentes coerentes com o design system e a revisar acessibilidade, responsividade e estados de carregamento. A decisão humana foi manter densidade operacional, reduzir decoração e deixar PP como único sinal analítico no card.

Também foi feita uma auditoria para remover conteúdo teatral ou mockado da aplicação funcional. Os arquivos do protótipo visual estático ficaram isolados e não alimentam o CRM; a aplicação funcional usa o read model do Supabase. A folha de design system permanece compartilhada pela interface final.

### 9. Proteger o demo sem impedir a avaliação

A Recommendation Engine recebeu reserva atômica por oportunidade/hash/versão, limite generoso de 500 novas gerações por hora e 2.000 por dia, validação de origem e payload e mensagens de erro sem detalhes internos. Recomendações e contadores não possuem leitura pública; o cliente acessa somente o read model e a Edge Function. Assim, o avaliador consegue testar livremente sem expor chaves privadas ou permitir consumo irrestrito.

## Onde a IA errou e como corrigi

| Proposta ou erro inicial | Correção aplicada |
|---|---|
| Repetir a premissa de 35 vendedores ativos | Auditoria mostrou 30 com histórico e 5 sem oportunidades. |
| Usar tempo antigo como prioridade automaticamente | W passou a usar sobrevivência do ciclo; idade extrema virou sinal de requalificação, não bônus. |
| Criar uma constante arbitrária para temperatura | Quartis e distribuição empírica substituíram o chute. |
| Fazer Risk repetir taxa de perda já representada por P | R passou a ser Recommendation, uma camada realmente nova e acionável. |
| Tratar ausência de match como taxa zero | Ausência de evidência recebe peso zero e não reduz artificialmente P. |
| Apresentar Company Fit antes de implementá-lo | Documentação alinhada aos três critérios efetivamente calculados. |
| Recriar o board a cada lote de 1.000 registros | Consolidação em segundo plano e finalização in-place eliminaram flicker e contagem teatral. |

## O que adicionei com julgamento humano

- A exigência de que o resultado movesse receita e fosse utilizável por um vendedor, não apenas tecnicamente interessante.
- O nome e a arquitetura conceitual do POWER.
- A decisão de manter sinais diferentes visíveis em vez de criar uma média difícil de defender.
- O questionamento das fórmulas quando pareciam sofisticadas sem base operacional.
- A insistência em auditar a disparidade de preços antes de “corrigi-la”.
- A troca de Risk por Recommendation ao perceber redundância com Propensity.
- A política de custo: pré-calcular matemática barata e chamar IA automaticamente apenas na primeira abertura do card; depois, reutilizar o resultado salvo.
- A correção do CRM para um pipeline único, com UX orientada ao uso diário.

## Evidências reproduzíveis

- Aplicação: [`../solution/view/`](../solution/view/)
- Pipeline de scoring: [`../solution/scripts/build_power_dataset.py`](../solution/scripts/build_power_dataset.py)
- Migração e RLS: [`../solution/supabase/migrations/`](../solution/supabase/migrations/)
- Recommendation Engine: [`../solution/supabase/functions/`](../solution/supabase/functions/)
- Auditoria: [`../docs/data-audit.md`](../docs/data-audit.md)
- Framework: [`../docs/power-framework.md`](../docs/power-framework.md)
- Framework em PDF: [`../docs/power-framework.pdf`](../docs/power-framework.pdf)
- Capturas da aplicação: [`../docs/screenshots/`](../docs/screenshots/)

## Checkpoint de validação pré-submissão

- Rebuild completo: 8.800 oportunidades e as coberturas esperadas de P/O/W/E.
- Quatro testes determinísticos aprovados em 0,6 segundo.
- Pipeline, Directory e POWER Profile abertos pelo caminho documentado, sem erros ou warnings no console.
- Recommendation Engine testado na oportunidade fictícia `HKMMBDMW`: a primeira abertura gerou `Contatar`; a segunda reutilizou o mesmo resultado salvo.
- Leitura pública de recomendações bloqueada; origem não permitida rejeitada; concorrência simultânea convergiu para uma única geração.
- PDF do framework exportado em 19 páginas A4 e revisado visualmente.
- Varredura de credenciais confirmou que nenhuma chave privada foi colocada no código cliente.

## Limites deste log

- Não inclui conversas privadas, brainstorm bruto ou informações pessoais sem relação com o challenge.
- A narrativa registra mudanças materiais; microajustes visuais e tentativas repetidas não são apresentados como decisões independentes.
- Nenhum commit, push ou Pull Request foi executado durante a preparação deste checkpoint.
