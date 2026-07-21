---
id: D3P7
parent:
project: LeadScorer
subject: Tornar o quickstart robusto a volume e imagem Docker obsoletos de execucao anterior
author: dcvr@
priority: high
status: done
created: 2026-07-20
updated: 2026-07-20
---


# Descrição (o que será feito)

Tornar a execucao em um passo ('scripts/quickstart') robusta a estado Docker preexistente de um
projeto de compose de mesmo nome. Hoje, quando um clone novo gera um '.env' com senha nova, um
volume nomeado persistente de execucao anterior (inicializado com outra senha) e reutilizado: o
Postgres pula a inicializacao ('Skipping initialization'), mantem a senha antiga, o healthcheck
por 'pg_isready' reporta 'healthy' sem validar credencial e a aplicacao falha a autenticacao
permanentemente (SQLSTATE 28P01). Uma imagem 'app' em cache de build anterior agrava o quadro.
Estabelecer a invariante "senha nova gerada implica volume e imagem novos": quando 'quickstart'
gera um '.env' novo, remover o volume do projeto e forcar a recompilacao antes do 'up'.


# Motivações (por que será feito)

Defeito de reprodutibilidade surgido no teste de compilacao Docker da tarefa 6X9H (empacotamento
e entrega): a partir de um clone limpo, 'quickstart' travou em '28P01 password authentication
failed' repetido ate exaurir as tentativas de conexao, porque o volume nomeado
'leadscorer-db-data' (prefixado pelo nome do projeto de compose) sobrevive a um novo 'git clone'
e carrega a senha de uma execucao anterior. O criterio central da 6X9H e a "execucao em um passo"
confiavel a partir do clone; este defeito o quebra sob condicao realista (reexecucao de um
projeto homonimo). Nao ha relacao com a divida tecnica da sessao W3Q6-2.


# Recursos e dados necessários

- 'scripts/quickstart' (funcao 'ensure_env' e 'main') e 'compose.yaml' (volume nomeado
  'leadscorer-db-data', servico 'db' com healthcheck por 'pg_isready');
- Docker com o plugin de compose, para a verificacao ponta a ponta (reproduzir o estado obsoleto,
  aplicar a correcao e confirmar o provisionamento);
- 'shellcheck' e 'bats-core' para a verificacao do script.


# Plano de trabalho (como será feito)

1. Capturar em 'main' se '.env' ja existia antes de 'ensure_env'; quando '.env' e recem-criado
   (senha nova), executar 'compose down --volumes --remove-orphans' e forcar '--build' antes do
   'up', com mensagem clara ao usuario;
2. Preservar a idempotencia: quando '.env' ja existe, o comportamento atual (reuso de volume e
   imagem) e mantido;
3. Verificar 'shellcheck' sem avisos;
4. Verificar ponta a ponta com Docker: reproduzir o estado obsoleto (volume com senha antiga),
   confirmar a falha no codigo atual, aplicar a correcao e confirmar o provisionamento bem
   sucedido, sem intervencao manual.


# Riscos e ressalvas

- O 'down --volumes' e destrutivo, mas so corre no caminho em que uma senha nova e gerada, no qual
  qualquer volume preexistente ja e inutilizavel (senha divergente); nao ha perda de dado
  aproveitavel. Ainda assim, a acao deve ser anunciada ao usuario;
- A verificacao ponta a ponta deve usar um nome de projeto de compose descartavel, para nao tocar
  os conteineres de desenvolvimento em uso ('leadscorer-db', 'leadscorer-eval-db-1').


# Dependências

- blocks: 6X9H
- blocked-by:


# Definição de pronto

- A partir do estado que hoje falha (volume nomeado com senha divergente da do '.env' recem
  gerado), 'quickstart' provisiona o banco e sobe as aplicacoes sem intervencao manual;
- A idempotencia e preservada: com '.env' existente, o volume e a imagem sao reutilizados;
- 'shellcheck' nao relata avisos e o comportamento e verificado ponta a ponta com Docker.
