# ADR 0009: Banco compartilhado com papel restrito, opcional e com queda para a memória

**Status:** aceita

## Contexto

O vendedor responde às perguntas e decide sobre a ação no aparelho dele; o manager acompanha a equipe no painel. Para as respostas valerem em qualquer aparelho e chegarem ao painel, elas precisam de um lugar comum. Ao mesmo tempo, a solução tem de rodar num comando, sem banco, e os testes não podem depender de rede.

## Decisão

- **Banco opcional, por `DATABASE_URL`.** Com a variável, a API usa um Postgres (lib `pg`); sem ela, `deals.json` + memória do processo. A URL só existe no ambiente: nunca no código, no repositório ou no log.
- **Schema `lead_scorer`, papel restrito.** As tabelas já existem e a aplicação não cria nem altera schema. O papel da aplicação só lê `deals`, `vendedores` e `metadados` e só lê e acrescenta (`SELECT` e `INSERT`) em `respostas` e `decisoes`. Nada é alterado nem apagado.
- **Linhas, não estado.** Cada resposta e cada decisão é uma linha nova com a data. O estado atual sai do domínio (`montarRegistros`): por pergunta vale a resposta mais recente, e a decisão também. O lote ("Encaminhar os N") é um `INSERT` só, então entra inteiro ou não entra.
- **Aceite e contestação sem coluna nova.** A tabela `decisoes` tem `acao` e `motivo`; a ação vai como `aceitar:<ação>` ou `contestar:<ação>` (`apps/api/src/qualificacao/armazem.ts`). Texto fora desse formato é ignorado na leitura.
- **Negócios do banco só se conferirem.** Na partida, a API lê `metadados` e só usa `deals` e `vendedores` do banco se o `sha256_deals_json` e o `formato` baterem com o `deals.json` embarcado. Se não baterem, usa o arquivo e diz no log por quê.
- **Disjuntor e queda para a memória.** Três falhas seguidas abrem o circuito por 30 s (`apps/api/src/infra/banco.ts`). Com o banco fora ou o circuito aberto, a API grava e lê na memória e responde `armazenamento: "memoria"`; quando o banco volta, junta as linhas que ficaram na memória. A conexão tem limites curtos: 3 conexões, 3 s para conectar, 4 s por consulta.
- **A web continua com a fonte local.** O navegador guarda tudo no `localStorage` ([ADR 0005](0005-respostas-no-localstorage-atras-de-porta.md)), envia cada gravação ao servidor e, com a API de pé, baixa os registros do servidor e junta por data. Só com `armazenamento: "banco"` a tela trata as respostas como compartilhadas.

## Consequências

- Sem banco, nada muda para quem roda localmente; o painel diz "Respostas gravadas neste navegador: x de n".
- Com banco, a resposta dada num aparelho aparece no outro e no painel.
- Um "Novo negócio" não vai para o banco: a chave estrangeira exige que o negócio exista em `deals`.
- Sem login, o banco grava o vendedor dono do negócio, não quem clicou ([ADR 0006](0006-sem-autenticacao.md)).
- Testes sem banco: `apps/api/test/banco.test.ts` (SQL só de `SELECT` e `INSERT`, conversão das linhas, lote num `INSERT` só, queda para a memória e disjuntor, metadado divergente) e `apps/api/test/registros.test.ts` (rotas). Com `DATABASE_URL`, o mesmo arquivo roda a integração: lê os negócios do banco e compara com o arquivo, grava e lê dentro de uma transação desfeita (ROLLBACK) e confere que `UPDATE` e `DELETE` são recusados.

## Alternativas consideradas

- **Só o navegador:** não chega ao painel nem a outro aparelho.
- **Atualizar a linha da resposta (upsert):** pediria `UPDATE` no papel; com linhas novas, o histórico fica e o papel fica menor.
- **Expor o schema pela API REST do provedor:** daria acesso direto às tabelas pela internet; a API própria valida a entrada e aplica a regra do domínio.
