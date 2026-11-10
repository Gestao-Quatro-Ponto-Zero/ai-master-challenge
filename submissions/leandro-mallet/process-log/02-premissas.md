# Etapa 2 — Premissas de desenvolvimento

**Quando:** 09/11/2026, depois da análise dos dados e antes de construir qualquer coisa.
**Por quê:** antes de as sessões começarem a programar, eu quis fixar as regras de arquitetura, banco, backend e frontend que todas seguiriam. Minha intenção era que o sistema nascesse com o mesmo padrão de qualidade que uso nos meus produtos, e não com escolhas improvisadas por cada sessão.
**Decisões registradas:** 11 a 20 e 22 a 24, em [decisoes.md](decisoes.md).

## Como foi, em ordem

1. **Ponto de partida: o meu padrão, não um padrão genérico.** Pedi à IA que buscasse as premissas gerais, de arquitetura, de banco de dados, de backend e de frontend que já uso no meu portfólio e trouxesse tudo adaptado ao desafio. A IA achou o conjunto padrão (26 premissas em arquitetura, design e programação), reorganizou nos 5 grupos que pedi e marcou cada item como mantido, adaptado ou "não se aplica".

2. **Stack (decisão 11).** A IA mostrou que as sessões tinham proposto Python só com a biblioteca padrão e HTML/JS puro, para rodar sem instalar nada, e que isso fugia do padrão (TypeScript, Next.js e PostgreSQL). **Decidi manter a stack top tier.** Qualidade e manutenção pesam mais que "rodar sem instalar". O risco de higiene do repositório se controla com `.gitignore` e checklist.

3. **Onde a IA errou: premissas inventadas.** Na primeira versão, a IA acrescentou 6 premissas próprias ("regras do desafio", "julgamento visível", "banco opcional", "data de referência fixa", "score explicável", "linguagem do vendedor"). Eu tinha pedido as minhas premissas adaptadas, não premissas novas. **Mandei tirar.** O que elas cobriam já estava no checklist de QA e nos desenhos das sessões. A IA também tinha deixado uma premissa repetida em dois grupos, e ela saiu.

4. **Cortes no que não serve ao desafio (decisões 12, 13, 17 e 23).** Excluí a premissa de multi-tenant (há um cliente só), a de eventos e idempotência, a de "IA recomenda, regra decide" e a de OAuth (não há login). No fim, apaguei também as 4 premissas gerais que sobraram (só fatos comprovados, entrega com aceite, segurança e preservação de dados, design antes de expandir), porque não traziam regra concreta de construção. A regra de "inserir e atualizar sim, apagar nunca" foi para a premissa de migrações. Também saíram a de contratos estáveis e a de observabilidade e custo (decisão 24), e cada premissa adaptada ganhou um título que diz o que ela é agora, para não ser confundida com a premissa padrão de mesmo código.

5. **Identidade sem login (decisões 12 e 15).** A IA tinha adaptado a premissa de identidade para login com conta de demonstração. **Decidi que não há login nem senha:** o usuário escolhe o perfil (vendedor, manager ou admin) e, se for vendedor ou manager, o nome. As contas ficam numa tabela de usuários criada a partir do próprio dataset, então não há checagem de nome. O perfil serve para montar as telas e os filtros de cada papel.

6. **Sistema operacional (decisão 16).** A IA propôs ações só por acréscimo e o servidor bloqueando gravação em deal de outro vendedor. **Liberei inserir e atualizar, sem restrição por dono do deal:** o vendedor muda estágio, preenche a empresa e encerra deal de verdade. Continua proibido apagar, e toda alteração fica registrada com o antes e o depois.

7. **Duas premissas de banco que pedi (decisão 14).** Tabelas organizadas por prefixo de domínio (`core_`, `config_`, `score_`, `acao_`, `system_`) e toda relação declarada como chave estrangeira, com índice e sem exclusão em cascata.

8. **Marca e experiência (decisões 18 e 19).** Pedi a marca visual do G4 em fundo branco, com as cores da marca nos menus e objetos. Pedi também que a stack de backend e de frontend aparecesse completa e que UI, UX e estética fossem destacadas como no meu padrão: uma ação principal por tela, nada de jargão ou erro cru, tokens de design obrigatórios e nenhuma tela sem os estados de carregando, vazio e erro. Na revisão do tema, a sessão do app mediu o contraste e mostrou que o dourado da marca não pode ser cor de texto sobre branco, e que o cinza secundário precisa ser um pouco mais escuro para passar no nível AA.

9. **O produto é o CRM (decisão 20).** A IA tratava a entrega como uma ferramenta de priorização ao lado do CRM. Minha leitura do pedido da Head de RevOps: um sistema a mais não seria aberto. **O produto é o próprio CRM do time, com a prioridade dentro do pipeline.** O brief não diz isso literalmente; é a minha interpretação.

10. **Nome (decisão 22).** "Lead Scorer" é só o nome do desafio, e o nome provisório que a sessão do app usou soava como slogan. Pedi 10 sugestões a um segundo modelo de IA, mais forte em nomes, e escolhi **G4 Sight**.

## Resultado

Documento final com 22 premissas, todas com o "como fica no G4 Sight", em 4 grupos (arquitetura, banco de dados, backend e frontend): as premissas do padrão que ficaram, mantidas ou adaptadas, e 7 pedidas por mim (stack de backend, stack de frontend, UI/UX ultra simples, estética como requisito, prefixos de banco, chaves estrangeiras e marca do G4). Depois da minha aprovação, ele vira o arquivo comum que todas as sessões leem antes de construir.

## O que foi julgamento meu nesta etapa

- Exigir que as premissas viessem do meu padrão, e não de uma lista genérica.
- Cortar o que a IA inventou e o que não serve ao desafio.
- Trocar login por escolha de perfil e liberar escrita para o sistema ser operacional.
- Definir o produto como o próprio CRM, e não uma ferramenta a mais.
- Organização do banco, marca, stack e o nome.
