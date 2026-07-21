# Camada de persistência (Fase B)

Este documento descreve os princípios, as políticas e o processo da camada de persistência em
PostgreSQL. As especificações e os valores concretos residem nos arquivos-fonte, que são a
fonte canônica de verdade; este documento os referencia pelo nome em vez de os reafirmar.


# Escopo e decisões de referência

- A persistência é introduzida apenas na fase de aplicação, conforme o ADR D2K9. A fase de
  modelagem opera diretamente sobre os CSV normalizados e não depende desta camada;
- O modelo de dados é o modelo do ciclo de engajamento fixado no ADR N4P8 e especificado em
  'docs/concepcao-inicial.md' (seção "Modelo relacional"). A oportunidade é o par conta-produto;
  cada linha do pipeline histórico é um ciclo em 'engagements';
- O acesso ao banco usa Postmodern, sem a camada de DAO de CLOS, conforme o ADR D2K9;
- O empacotamento e o provisionamento por contêiner seguem o ADR D4M3.


# Provisionamento

- O banco é provisionado por contêiner com a imagem oficial do PostgreSQL, na versão fixada pela
  variável 'POSTGRES_IMAGE'. O arquivo 'compose.yaml' define o serviço 'db'; o serviço da
  aplicação pertence à fase de aplicação (tarefa 8W2N);
- Os segredos residem em '.env', mantido fora do controle de versão. O arquivo '.env.example',
  versionado, é a fonte canônica das variáveis de ambiente esperadas; copie-o para '.env' e
  defina a senha antes de subir o serviço;
- Com o plugin Docker Compose v2 disponível, o serviço sobe com 'docker compose up -d db'. Na
  ausência do plugin, um contêiner equivalente pode ser provisionado com 'docker run' da imagem
  'POSTGRES_IMAGE', publicando a porta interna 5432 na porta de host 'PGPORT' e definindo
  'POSTGRES_DB', 'POSTGRES_USER' e 'POSTGRES_PASSWORD' a partir do '.env';
- A porta de host padrão é 5433, e não 5432, para evitar conflito com um serviço local eventual
  na porta canônica. Os scripts executados no host conectam-se a 'PGHOST:PGPORT'; dentro da rede
  do compose, os serviços referem-se ao banco pelo nome de serviço 'db' na porta 5432.


# Schema e migrações

- O schema é definido por migrações SQL numeradas e versionadas em 'db/migrations/', que são a
  fonte canônica do schema. O dialeto é PostgreSQL, verificado com 'sqlfluff' sob a configuração
  por diretório 'db/.sqlfluff';
- As migrações são aplicadas pelo runner idempotente 'src/migrate.lisp', que registra cada
  versão aplicada na tabela de controle 'schema_migrations' e ignora as já aplicadas, de modo
  que a aplicação a partir de um banco vazio seja idempotente. Cada migração é aplicada em uma
  transação;
- Uma migração pode conter várias instruções; o runner as separa e as aplica individualmente,
  pois o protocolo estendido do cl-postgres admite uma instrução por consulta.


# Carga (seed)

- O seed 'src/seed.lisp' materializa as tabelas a partir de 'data/normalized/*.csv',
  reutilizando a API de CSV do sistema. É idempotente: trunca e recarrega as tabelas em uma
  transação, reiniciando as identidades;
- As convenções de conversão são a fonte canônica no próprio 'src/seed.lisp': valores monetários
  como inteiro na menor unidade (centavos) com código ISO 4217, sem ponto flutuante; instantes
  como UNIX em milissegundos, UTC; usernames derivados do nome;
- Regra de derivação do ciclo (fixada no ADR R6T2): 'opportunities' é o conjunto dos pares
  distintos conta-produto com conta; 'engagements' são as linhas do pipeline em estágio Won,
  Lost ou Engaging que possuem conta. As linhas em estágio Prospecting e as linhas sem conta são
  excluídas, com registro do total em log, pois não formam um par conta-produto válido nem
  representam um ciclo engajado. O estado ativo do par é 'engaging' quando há ciclo aberto, senão
  'prospecting'; o desempate entre pares com vários ciclos abertos é determinístico, pelo
  'engage_date' mais recente e, em seguida, pelo identificador de proveniência;
- 'opportunity_scores' não é semeada nesta fase; o ranqueamento personalizado é computado pela
  aplicação (tarefa 8W2N).


# Verificação

- O verificador 'src/verify.lisp' é fail-closed: confere as contagens canônicas, a integridade
  referencial e a invariante do estado ativo, e sinaliza erro listando as falhas. As contagens
  esperadas são a fonte canônica no próprio 'src/verify.lisp';
- O ponto de entrada 'scripts/db-setup.lisp' carrega o sistema, aplica as migrações, executa o
  seed e verifica, encerrando com estado não nulo em caso de falha. A invocação canônica está no
  cabeçalho do próprio script.


# Testes

- A cobertura reside em 'tests/persistence.lisp' (Parachute). Os testes de conversão e de
  derivação são puros e independem de banco. O teste de integração materializa o schema e a
  carga contra o PostgreSQL e é ignorado quando o banco não está acessível ou os CSV
  normalizados estão ausentes, de modo que a suíte passe em um ambiente sem banco.
