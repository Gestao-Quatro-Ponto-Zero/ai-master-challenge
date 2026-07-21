# Dockerfile --- Imagem das aplicacoes web do LeadScorer (ADR D4M3).
#
# Multi-stage: o estagio 'build' instala o qlot fixado, resolve as dependencias
# a partir de 'qlfile.lock' e compila o sistema; o estagio 'runtime' recebe
# apenas os artefatos necessarios a execucao via 'qlot exec'. Nenhum segredo e
# embutido: as credenciais do banco e a configuracao de rede vem do ambiente
# (ver 'compose.yaml' e '.env.example'). Compativel com Docker e Podman.

# Imagem base com o registro qualificado, para que o Podman sob politica de
# nomes curtos ('short-name-mode') nao falhe nem exija escolha interativa.
ARG SBCL_IMAGE=docker.io/clfoundation/sbcl:2.6.1-bookworm

# === Estagio de build ===
FROM ${SBCL_IMAGE} AS build

ARG QLOT_VERSION=1.8.4
ENV DEBIAN_FRONTEND=noninteractive

# curl e ca-certificates sao necessarios ao instalador do qlot; git resolve
# eventuais fontes de dependencia versionadas.
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl ca-certificates git \
    && rm -rf /var/lib/apt/lists/*

# Instala o qlot fixado. Como root, o instalador o coloca sob '/usr/local'
# (binario em '/usr/local/bin/qlot', biblioteca em '/usr/local/lib/qlot'),
# autocontido para copia ao estagio de execucao.
RUN QLOT_URL="https://github.com/fukamachi/qlot/releases/download/${QLOT_VERSION}" \
    && curl -fsSL "${QLOT_URL}/qlot-installer-${QLOT_VERSION}.sh" | sh

WORKDIR /app

# Camada de dependencias: isolada para reaproveitar o cache enquanto o lock nao
# muda. 'qlot install' materializa './.qlot' a partir de 'qlfile.lock'.
COPY qlfile qlfile.lock leadscorer.asd ./
RUN qlot install

# Codigo, configuracao, migracoes e os dados versionados (ADR V9K3): a fonte
# normalizada do seed e as features derivadas que o agendador consome em runtime.
COPY src ./src
COPY config ./config
COPY db ./db
COPY data/normalized ./data/normalized
COPY data/derived ./data/derived
COPY scripts ./scripts

# === Estagio de execucao ===
FROM ${SBCL_IMAGE} AS runtime

ENV DEBIAN_FRONTEND=noninteractive
WORKDIR /app

# qlot autocontido e a arvore de dependencias resolvida. O qlot reside sob
# '/usr/local/lib/qlot'; o seu binario ('bin/qlot') e adicionado ao PATH em vez
# de copiado como symlink, que o COPY desreferenciaria e quebraria a resolucao
# interna de caminhos do wrapper. O software das dependencias reside no cache
# global do qlot; '/app/.qlot' (parte de '/app') guarda os metadados que o
# referenciam.
COPY --from=build /usr/local/lib/qlot /usr/local/lib/qlot
COPY --from=build /root/.cache/qlot /root/.cache/qlot
COPY --from=build /app /app
ENV PATH="/usr/local/lib/qlot/bin:${PATH}"

# Carrega o sistema e grava uma imagem de core do SBCL com tudo pre-carregado. O
# arranque do conteiner parte deste core (ver 'scripts/container-entrypoint'), de
# modo que nenhuma compilacao ocorre no boot. Isto evita a recompilacao das
# dependencias no arranque, que a reutilizacao do cache de fasls do ASDF nao
# resolvia: o ASDF 3.3.1 embutido na imagem base diverge do 'uiop' fixado pelo
# lock e se auto-atualiza a cada sessao nova de SBCL, forcando uma cascata de
# recompilacao ate que os fasls sejam reescritos. O core congela o estado ja
# carregado e elimina essa classe de problema, alem de tornar o arranque imediato.
#
# Invariante de seguranca: nenhuma configuracao ou segredo deve ser lido em tempo
# de carga (forma top-level), pois o core congelaria o valor de build-time (vazio
# ou default). Toda configuracao dirigida por ambiente e lida em tempo de chamada,
# em runtime (ver 'src/config.lisp' e 'src/web/config.lisp'). Preservar este
# invariante e obrigatorio ao adicionar codigo carregado por ':leadscorer/web'.
RUN qlot exec sbcl --non-interactive \
    --eval '(asdf:load-system :leadscorer/web)' \
    --eval '(sb-ext:save-lisp-and-die "/app/leadscorer.core")'

RUN chmod +x scripts/container-entrypoint

# Portas de escuta padrao das aplicacoes do agente e do gerente.
EXPOSE 8081 8082

ENTRYPOINT ["scripts/container-entrypoint"]
