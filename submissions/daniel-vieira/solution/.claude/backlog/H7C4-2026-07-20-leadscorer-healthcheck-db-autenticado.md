---
id: H7C4
parent:
project: LeadScorer
subject: Endurecer o healthcheck do servico db para validar a conexao autenticada
author: dcvr@
priority: low
status: done
created: 2026-07-20
updated: 2026-07-21
---


# Descrição (o que será feito)

Avaliar e, se justificado, endurecer o healthcheck do servico 'db' em 'compose.yaml', hoje por
'pg_isready -U ${PGUSER} -d ${PGDATABASE}', para validar uma conexao efetivamente autenticada (por
exemplo, um 'psql' com a senha executando uma consulta trivial). Assim, uma incompatibilidade de
credencial faria o servico reportar 'unhealthy' em vez de 'healthy', em vez de o defeito so
aparecer depois, na tentativa de conexao da aplicacao.


# Motivações (por que será feito)

Registrado como desenvolvimento futuro no worklog da tarefa D3P7. O 'pg_isready' verifica apenas a
aceitacao de conexoes pelo servidor, nao a senha; por isso, em uma incompatibilidade de credencial
(por exemplo, um '.env' mal configurado), o banco reporta 'healthy', a aplicacao sobe (depende de
'service_healthy') e so entao falha a autenticacao (28P01), tornando o diagnostico mais tardio e
confuso. A D3P7 resolveu o caso especifico do volume obsoleto no 'quickstart', mas a lacuna geral
de diagnostico do healthcheck permanece.


# Recursos e dados necessários

- 'compose.yaml' (definicao do healthcheck do servico 'db');
- A imagem do Postgres, que dispoe de 'psql' para um teste autenticado;
- Docker com compose, para verificar o comportamento do healthcheck.


# Plano de trabalho (como será feito)

1. Avaliar o custo-beneficio: o 'pg_isready' e o healthcheck canonico e leve; um teste autenticado
   por 'psql' e mais pesado (executado a cada intervalo) e exige a senha no comando do healthcheck.
   Decidir explicitamente por implementar ou por descopar com justificativa registrada;
2. Se implementar: substituir o teste por um 'psql' autenticado (via 'PGPASSWORD' do ambiente ja
   presente no servico) executando 'SELECT 1', preservando a tolerancia a inicializacao (o teste
   so passa quando o servidor aceita e autentica);
3. Verificar ponta a ponta com Docker: credencial correta faz o servico ficar 'healthy' e a app
   conectar; credencial incompativel faz o healthcheck falhar (o defeito aparece no nivel do
   healthcheck, nao apenas na app).


# Riscos e ressalvas

- Trade-off real: o teste autenticado e mais custoso que 'pg_isready' e coloca a senha no comando
  do healthcheck (visivel em 'docker inspect', ainda que 'PGPASSWORD' ja esteja no ambiente do
  servico). Nao expor a senha em logs ou saida. Para o perfil MVP, a decisao pode legitimamente
  ser descopar;
- O teste autenticado deve tolerar a fase de inicializacao do banco, sem tornar o servico
  permanentemente 'unhealthy' durante o arranque a frio (o healthcheck ja tem 'retries').


# Dependências

- blocks:
- blocked-by:


# Definição de pronto

- Decisao registrada: implementar o healthcheck autenticado ou descopar com justificativa;
- Se implementado: uma incompatibilidade de credencial faz o servico 'db' reportar 'unhealthy' em
  vez de 'healthy', sem expor a senha, com o comportamento verificado ponta a ponta com Docker e a
  tolerancia a inicializacao preservada.
