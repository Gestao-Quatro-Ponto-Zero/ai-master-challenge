---
id: D4M3
project: LeadScorer
subject: Empacotamento conteinerizado e interoperabilidade Podman/Docker
author: dcvr@
status: accepted
created: 2026-07-18
updated: 2026-07-18
---


# Contexto (por que a decisão é necessária)

O desafio exige que a solução execute de forma confiável conforme o setup documentado, e o
avaliador utiliza Docker. O desenvolvimento local emprega Podman. É necessário decidir o
empacotamento de modo que a mesma definição funcione em ambos os runtimes, sem estado inseguro.
A decisão foi precedida de pesquisa em fontes primárias (documentação do Podman, do Docker
Compose, da imagem oficial do PostgreSQL e das imagens SBCL). A implementação é diferida para a
fase de aplicação; esta decisão registra os princípios.


# Decisão (o que foi decidido)

A aplicação é empacotada em contêiner. A imagem base é clfoundation/sbcl, mantida pela Common
Lisp Foundation. O Dockerfile é multi-stage: um estágio instala o qlot e as dependências
fixadas a partir de qlfile e qlfile.lock, e compila o sistema. O ambiente de execução sobe via
um único arquivo compose, compatível com Podman e Docker, que define os serviços da aplicação e
do PostgreSQL oficial. O desenvolvimento local usa Podman; a compatibilidade com Docker é
requisito do avaliador. A execução standalone via asdf:make fica diferida como otimização.


# Alternativas consideradas (o que mais foi ponderado)

- Imagem base fukamachi/sbcl ou fukamachi/qlot: preteridas em favor de clfoundation/sbcl, de
  manutenção institucional, ainda que a imagem do autor do qlot seja conveniente como estágio.
- podman-compose (implementação em Python): preterido por implementar apenas um subconjunto da
  Compose Specification; a via robusta é o binário docker compose apontando para o socket do
  Podman, que executa o mesmo arquivo de forma idêntica nos dois runtimes.
- Campo version no topo do arquivo compose: descartado por estar obsoleto e gerar aviso.
- Executável standalone via asdf:make no MVP: diferido; carregar o sistema e iniciar o servidor
  via qlot exec é mais simples e suficiente para a entrega.


# Consequências (o que resulta da decisão)

- A reprodutibilidade da execução é assegurada para o avaliador via contêiner.
- Para máxima portabilidade, o arquivo compose omite o campo version, usa volumes nomeados,
  refere serviços pela rede por nome de serviço e mantem o env_file fora do controle de versão.
- A condição depends_on service_healthy não é honrada de forma confiável pelo podman-compose;
  portanto a aplicação deve tolerar e retentar a conexão ao banco, sem depender apenas do
  compose para a ordem de subida.
- Segredos, em particular a senha do PostgreSQL, não são embutidos no compose versionado; um
  arquivo .env.example versionado documenta as variáveis, e o .env real permanece fora do
  controle de versão.
- O qlot não reside no PATH global do ambiente de desenvolvimento; o Dockerfile deve instalá-lo
  explicitamente para a reprodutibilidade do build.


# Relações

- supersedes:
- superseded-by:
- related-tasks: 7K2M, 8W2N, 6X9H
