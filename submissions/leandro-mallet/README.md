# Submissão — Leandro Maia Mallet — Challenge 003

## Sobre mim

- **Nome:** Leandro Maia Mallet
- **LinkedIn:** https://www.linkedin.com/in/leandro-maia-mallet/
- **Instagram:** [@leandromaia.fly](https://www.instagram.com/leandromaia.fly/)
- **Challenge escolhido:** 003 — Lead Scorer
- **Perfil:** um conjunto raro de habilidades em um só profissional: o pensamento analítico de engenheiro, o domínio de metodologias de gestão empresarial e de gestão de projetos, o background em tecnologia e growth, e a mão na massa em IA, agentes e vibe coding.
- **Track record:** gestão de projetos de tecnologia e engenharia, mentoria e treinamento de pequenos e médios empresários, e design e validação de produtos e startups.

---

## Executive Summary

Construí o **G4 Sight**, o CRM do time comercial com a prioridade do dia dentro do pipeline. Está no ar em **https://g4-sight.vercel.app**, ligado a um banco Postgres no Supabase com os 8.800 deals do dataset. Não é um modelo num notebook: é a ferramenta que o vendedor abre de manhã para saber para quem ligar, com banco auditado, rotina automática diária e semanal e o motivo de cada nota na tela.

O Lead Score responde duas perguntas: **quem atende cada lead** e **em que ordem cada vendedor deve trabalhar os seus leads**. Cada lead vai para o vendedor de maior performance naquele perfil de lead nos últimos 3 meses (FIT). A fila de cada vendedor é ordenada por essa performance, pela urgência de atendimento (HEAT) e pela força de compra da empresa (bônus), e cada nota mostra o motivo.

Recomendação principal: **distribuir cada lead para o vendedor que mais converte aquele perfil e atender o lead novo em até 1 dia.**

---

## Solução

### Como avaliar

- **No ar (recomendado):** https://g4-sight.vercel.app. Escolha o perfil e o usuário na tela de entrada; não há senha.
- **Local:** [solution/app/COMO-RODAR.md](solution/app/COMO-RODAR.md) (Node 20+, `npm ci`, `npm run dev`). Sem as credenciais do banco, o app abre com os dados do arquivo para ver as telas, mas sem as notas, que ficam no banco.

### Datas: simulação com o dataset × produção

O dataset termina em 31/12/2017. Para a simulação, o "hoje" do sistema (a data de negócio, usada nos dias do lead, no HEAT, no Painel e no domingo da redistribuição) parte de 31/12/2017 e anda 1 dia por dia real a partir da publicação. Essas datas ficam na tabela `config_parametros` do banco:
- `modo_demonstracao` = true;
- `data_referencia` = 2017-12-31;
- `data_ancora_real` = 2026-11-10 e `data_ancora_negocio` = 2017-12-31.

**Para operar em produção, com dados reais:** remova as datas ancoradas (`data_ancora_real` e `data_ancora_negocio`) e use a data de hoje como referência, desligando o modo de simulação (`modo_demonstracao` = false). Assim o sistema passa a usar a data real do dia. Não é preciso mudar código.

### Abordagem

1. **Entender o pedido antes da tecnologia.** A Head de RevOps disse que o time não vai abrir mais uma ferramenta. Li isso como: **a prioridade tem que estar dentro do CRM que o vendedor já usa**. **O produto virou o próprio CRM** (Painel, Pipeline, Leads), numa versão enxuta para o desafio, com a nota em cada lead. A premissa considerada foi: **cada vendedor vai olhar no sistema para quem vai ligar**. Isso abriu a possibilidade de distribuir os leads de forma otimizada por vendedor, e não só de ordenar uma lista.
2. **Premissas antes de código.** Regras de arquitetura, banco, backend e frontend fixadas antes de construir ([02-premissas.md](process-log/02-premissas.md)): prefixos de domínio no banco, chave estrangeira em toda relação, nada se apaga, auditoria de toda mudança e marca do G4.
3. **Dados antes do score.** Limpeza reproduzível e teste de sinal de 18 variáveis ([findings.md](solution/analysis/findings.md)). Nenhuma característica do lead, sozinha, separa ganhos de perdas, e por isso a nota passou a olhar o encaixe entre o lead e o vendedor que atende.
4. **Construção em paralelo, com papéis fixos.** Uma sessão de IA orquestrou, e quatro construíram: dados e banco, score, telas e QA. Toda tarefa virou uma ordem numerada, e toda entrega foi conferida por outra sessão antes do commit e testada no ar.

### A metodologia do Lead Score

Documento completo: [regra-lead-score.html](solution/scoring/regra-lead-score.html).

**Premissas e benefícios**
- **Vendedor ideal para cada lead.** A priorização define a ordem de atendimento e também indica qual vendedor deve atender cada lead. Encaminhar o lead a quem mais converte aquele perfil aumenta a probabilidade de conversão.
- **Performance recente.** A conversão de cada vendedor num perfil de lead nos últimos 3 meses vale mais que a sua performance histórica, porque reflete o momento atual dele.
- **Análise multiparamétrica.** A probabilidade de conversão de cada vendedor é avaliada em 7 parâmetros do lead ao mesmo tempo, o que revela diferenças que não aparecem quando os parâmetros são analisados um a um.
- **Velocidade de atendimento.** Quanto mais recente o lead, maior a sua urgência na fila. A pontuação começa no máximo no primeiro dia e cai em faixas de tempo até zerar depois de 6 meses. A partir daí, a fila passa a ser decidida somente pelo perfil e pelo cliente.
- **Melhores clientes priorizados.** Empresas com maior histórico de compra, e as que estão no seu período usual de compra, ganham prioridade extra na fila.
- **Destaque para o lead novo.** O lead novo é priorizado para atendimento em até 1 dia e, se esse prazo passar sem contato, fica sinalizado.
- **Incentivo ao cumprimento da prioridade.** O lead que muda de faixa de tempo sem contato é redistribuído para outro vendedor com performance equivalente no mesmo perfil.
- **Distribuição equilibrada.** Cada vendedor tem um limite de leads ativos, sempre priorizando o vendedor de maior performance em cada lead.
- **Atualização contínua e transparência.** A performance é recalculada semanalmente e a urgência diariamente, e cada nota mostra o motivo.

**Como funciona**
- **Quem atende → FIT:** a conversão do vendedor naquele perfil de lead nos últimos 3 meses (FIT 62 = o vendedor fecha 62% dos leads com aquele perfil). O perfil são 7 parâmetros: produto, série, setor, porte por faturamento, porte por funcionários, empresa e sede. O FIT é a média da conversão do vendedor em cada um.
- **Em que ordem → nota = 0,7 × FIT + 0,3 × HEAT + BÔNUS.**
  - O HEAT é a urgência pelo tempo desde a entrada do lead, de 100 no primeiro dia a 0 depois de 180 dias.
  - O bônus é a força de compra da empresa, até +20 pontos: +10 ou +5 para as empresas que mais compram e +10 no período de compra.
- **Nivelamento:** o limite de leads ativos por vendedor é o total de leads dividido pelo número de vendedores. O excedente vai para o vendedor seguinte de maior performance.
- **Repasse:** o lead sem contato que muda de faixa de tempo vai para outro vendedor com performance equivalente.
- **Fica fora:** o valor do deal, porque não se sabe o valor antes de atender.
- **Operação:** o FIT e o bônus são recalculados todo domingo e o HEAT todo dia, por uma rotina automática dentro do próprio app (Vercel Cron). A lista do dia tem 20 leads, e o ✓ exige o tipo de atividade e um comentário, que vão para a linha do tempo do lead.

### Resultados

**O app (no ar):**
- **Entrada:** tela de login com "Selecione o Perfil" e "Selecione o Usuário", sem senha.
- **Painel:**
  - números do pipeline em reais e o funil em 5 etapas (Novo lead, Atendimento, Em negociação, Fechado, Perdido);
  - **Prioridades do dia**: 20 leads com a nota; o clique abre o porquê da nota.
- **Pipeline:**
  - 5 colunas, e o estágio muda arrastando o cartão;
  - o lead passa sozinho de Novo lead para Atendimento no primeiro contato;
  - filtro em texto livre.
- **Leads e Contas:** base completa, cadastro, tags, comentários, ações em lote com desfazer e a ficha de cada empresa com o padrão de compra.
- **Deal:** linha do tempo, comentários e a explicação da nota: a conta, a barra por parte, os motivos e a conversão do vendedor em cada parâmetro do perfil.
- **Perfis:** o vendedor vê o seu dia; o manager vê o time e uma lista só com o que pede ação dele; o admin vê todos.

**Telas** (em [docs/screenshots/](docs/screenshots/)):

![Painel do vendedor](docs/screenshots/02-painel-vendedor.png)
![Prioridades do dia](docs/screenshots/03-prioridades-do-dia.png)
![Por que a nota](docs/screenshots/06-por-que-a-nota.png)
![Pipeline](docs/screenshots/04-pipeline.png)

**Números da execução ativa** (2.089 deals abertos, conferidos no banco):
- **Notas:** de 35 a 75, todas iguais a 0,7 × FIT + 0,3 × HEAT + bônus. O FIT médio é 61,9.
- **Distribuição:** os 35 vendedores têm leads, com limite de 23 leads ativos por vendedor na redistribuição.
- **Paridade do motor:** o motor em TypeScript, que roda na rotina automática, reproduz o cálculo em Python deal a deal.

**Qualidade:**
- **Banco:** 34 migrations, com RLS e sem política pública, sem DELETE nem TRUNCATE, auditoria por gatilho, gravação só por funções e limite de escritas por usuário e global.
- **Revisão:** cada migration foi revisada e validada por uma sessão diferente da que escreveu ([solution/qa](solution/qa)).
- **Testes no ar:** dois ciclos completos, com prints ([teste-banco-online.md](solution/qa/teste-banco-online.md), [teste-n1-n4-online.md](solution/qa/teste-n1-n4-online.md)).
- **Testes automatizados:** 189 no app (`npm test`), entre eles a comparação do motor da rotina com o cálculo de referência em Python, deal a deal, e 13 no Python (`python -m unittest scoring/test_regra.py`). O Python não é necessário para rodar o app: serve de referência e validação ([validacao.md](solution/scoring/validacao.md)).

### Como superamos a baseline

A entrega típica de uma IA que recebe só o brief e os CSVs está reconstruída e medida contra os dados em [baseline.md](solution/qa/baseline.md). Onde o G4 Sight vai além:
- **Pesos medidos, não escolhidos.** A baseline dá pontos por setor, porte, região e produto, que nestes dados não separam ganhos de perdas (diferença de 1,4 a 4,8 pontos na taxa de ganho). O G4 Sight testou 18 variáveis antes de pontuar e mede a conversão de cada vendedor no perfil completo do lead.
- **Decide quem atende, não só a ordem.** A baseline ordena uma lista. O G4 Sight indica o vendedor ideal para cada lead, distribui a carga com limite por vendedor e repassa o lead parado.
- **Valor fora da nota.** Na baseline, o valor do deal pesa e o score vira "ordenar por produto caro", o que o brief proíbe. Aqui o valor não entra, e a força de compra vem do histórico da empresa.
- **Tempo como urgência, com data coerente.** A baseline penaliza a idade em linha reta e usa a data de hoje, o que zera todos os deals do dataset. Aqui o tempo é a urgência de atendimento por faixas, sobre a data de negócio da simulação.
- **Poucos casos tratados.** A baseline usa a taxa de ganho crua, e um vendedor com poucos deals vira extremo. Aqui a conversão é ajustada para poucos casos e exige 10 negócios por parâmetro.
- **Lead incompleto declarado.** 68% dos abertos não têm empresa. A baseline costuma preencher com média em silêncio. Aqui o lead é avaliado pelos parâmetros que tem e reavaliado quando é completado.
- **Explicação em frase, não lista de pontos.** Cada nota mostra a conta e frases como "O vendedor fecha 64% dos leads com este perfil".
- **CRM em uso, não painel de leitura.** No lugar de tabela, KPIs e gráfico, um CRM com Painel, Pipeline, Leads, lista do dia com ✓ registrado, lista própria do manager, banco auditado e rotina automática.
- **Process log com julgamento.** No lugar de "pedi o app e publiquei", 54 decisões registradas, a auditoria de cada entrega e os erros da IA que foram corrigidos.

### Recomendações

1. **Distribuir cada lead para o vendedor que mais converte aquele perfil.** A redistribuição de domingo e o roteamento do lead novo já fazem isso.
2. **Atender o lead novo em até 1 dia.** O lead novo entra no topo da fila e fica sinalizado se passar do prazo.
3. **Registrar todo contato.** O contato registrado alimenta a urgência, o repasse e a performance de cada vendedor.
4. **Limpar o pipeline parado.** 81% dos deals em negociação estão abertos há mais tempo que qualquer deal que já fechou.
5. **Medir a conversão por vendedor nos próximos 3 meses** com a nova regra e recalibrar os pesos com o resultado.

### Limitações

- **Período de compra do bônus:** nos dados do desafio, nenhuma empresa tem uma época de compra própria, então essa parte hoje vale 0.
- **Sem login.** O perfil é escolhido na tela (decisão para o desafio). Por isso as funções de gravação não conferem o dono do deal. A proteção vem da trava de contexto, dos limites de escrita, da auditoria e do desfazer. Com login, a conferência por dono vira obrigatória.
- **Regras em aberto:** o máximo de repasses por lead e a penalidade para quem perde lead estão em branco no banco (sem limite e sem penalidade).
- **Não construído:** a importação de leads por CSV na tela (a função do banco existe) e o cadastro de empresa nova com o banco ligado.
- **Moeda:** os valores aparecem em reais, com os mesmos números do dataset, sem conversão.
- **Para escalar:** login com perfis, importação contínua de leads e a validação da nota contra o resultado real dos deals atendidos com a nova regra.

---

## Process Log — Como usei IA

> Narrativas em [process-log/](process-log/): [00-preparacao.md](process-log/00-preparacao.md) e [02-premissas.md](process-log/02-premissas.md). Registro de decisões, uma linha por decisão: [decisoes.md](process-log/decisoes.md). Auditoria de cada entrega: [audit.md](process-log/audit.md).

### Ferramentas usadas

| Ferramenta | Para que usei |
|------------|--------------|
| Claude Code (Opus), 1 sessão orquestradora | Coordenar 4 sessões por ordens numeradas, auditar cada entrega, manter o registro de decisões e fazer todos os commits e publicações |
| Claude Code, sessão de dados e banco | Limpeza, teste de sinal e as migrations do banco |
| Claude Code, sessão de score | A regra do score em Python, a carga no banco e o motor em TypeScript com paridade |
| Claude Code, sessão de telas | O app em Next.js, as rotas, a rotina agendada e algumas migrations |
| Claude Code, sessão de QA | Revisão e aplicação de cada migration e testes do app no ar |
| Antigravity (Gemini) | Segunda opinião para o nome do produto (10 sugestões) |
| Vercel, Supabase | Publicação e banco |

### Workflow

1. **Preparação:** li o desafio com a IA, escolhi o 003 e decidi trabalhar em sessões dedicadas, com as decisões registradas na hora.
2. **Canvas do projeto:** situação atual, situação desejada, marcos e riscos, numa folha só.
3. **Dados:** pedi recortes específicos, entre eles a taxa por produto e preço, a concentração das top empresas, as faixas de tempo de venda e o padrão de conversão de cada vendedor. Daí saiu a ideia central: o lead vai para o vendedor que mais converte aquele perfil.
4. **Premissas:** trouxe o meu padrão de desenvolvimento e cortei o que não servia.
5. **Especificação antes de código:** todas as telas, depois todas as migrations, depois as telas em código. O banco é especificado, escrito por uma sessão e validado e aplicado por outra.
6. **Regra do score em iterações:** HEAT em 8 faixas definidas por mim, valor fora da nota, bônus da empresa, lead novo no topo, repasse e redistribuição com equilíbrio, ✓ com atividade e comentário. Revendo a conta em exemplos reais, troquei o FIT relativo à média do vendedor pela conversão do vendedor no perfil, que é comparável entre vendedores.
7. **Construção e QA no ar:** cada entrega passou por testes, revisão de outra sessão, publicação e conferência no ar.
8. **Ajustes de produto vendo o app no ar:** Painel refeito pelo modelo que desenhei, funil em 5 etapas, 20 prioridades, explicação da nota, valores em reais e tela de entrada.
9. **Automação:** motor portado para TypeScript, relógio da data de negócio e rotina diária ligada.

### Onde a IA errou e como corrigi

- **Premissas inventadas.** Pedi o meu padrão adaptado, e a IA acrescentou 6 premissas próprias. Mandei tirar.
- **"Protótipo".** A IA tratou a entrega como protótipo. Corrigi: é versão final, para uso.
- **Banco gravado duas vezes e ordens velhas na fila** entre sessões. Parei todas as sessões e criei as regras de coordenação: ordem numerada com confirmação, dono único por pasta e quadro de status.
- **FIT difícil de explicar e não comparável.** A primeira versão media o lead contra a média do próprio vendedor, numa escala que eu não conseguia explicar e que não dizia quem converte mais. Destrinchei a conta em exemplos reais e troquei pela conversão do vendedor no perfil.
- **Resumo que contradizia os dados.** A IA escreveu que "o que varia é o vendedor", o que a própria análise não sustentava. Reescrevi a metodologia com as premissas que de fato consideramos.
- **Painel fora do meu modelo.** A IA padronizou os objetos, mas não seguiu o modelo de Painel que eu tinha desenhado, e depois tentou um fundo escuro contra a minha regra de fundo branco. Cancelei e mandei refazer pelo modelo.
- **Rotina que desfez a redistribuição.** No primeiro teste no ar, a rotina usou a lista antiga de vendedores e devolveu 261 leads. Foi achado na conferência da própria rodada, corrigido e rodado de novo. Nada foi apagado, e as trocas ficaram registradas.
- **Achados de segurança e hash errado.** A revisão automática de cada commit apontou falhas, e cada uma virou correção revisada por outra sessão. Uma sessão reportou um sha256 que não era o do arquivo, e a conferência antes de aplicar no banco pegou.

### O que eu adicionei que a IA sozinha não faria

- **O produto é o CRM**, e não uma ferramenta ao lado. Foi a leitura da frase da Head de RevOps.
- **O vendedor ideal para cada lead:** a nota decide quem atende, e não só a ordem.
- **A performance recente (3 meses)** em vez da histórica, e a conversão do vendedor no perfil como medida simples e comparável.
- **O tempo como urgência de atendimento**, com faixas definidas por mim e o lead novo atendido em até 1 dia.
- **O valor fora da nota** ("nunca se sabe o valor antes de atender"), com a empresa que compra muito virando bônus.
- **As regras de operação do time:** o repasse que gera pressão para atender, o ✓ que exige registro, a redistribuição semanal com equilíbrio e todo vendedor com lead.
- **O desenho do Painel**, o funil com Atendimento automático e o padrão visual.
- **A disciplina do processo:** premissas antes de código, especificação antes de banco, nada se apaga, e cada entrega conferida por outra sessão e testada no ar.

---

## Evidências

- [x] Registro de decisões: [process-log/decisoes.md](process-log/decisoes.md)
- [x] Auditoria de cada entrega: [process-log/audit.md](process-log/audit.md)
- [x] Narrativas: [00-preparacao.md](process-log/00-preparacao.md), [02-premissas.md](process-log/02-premissas.md)
- [x] Git history: 100+ commits na branch `submission/leandro-mallet`
- [x] Relatórios de QA, com prints dos testes no ar: [solution/qa/](solution/qa/)
- [x] App no ar: https://g4-sight.vercel.app

---

_Submissão enviada em: 11/11/2026_
