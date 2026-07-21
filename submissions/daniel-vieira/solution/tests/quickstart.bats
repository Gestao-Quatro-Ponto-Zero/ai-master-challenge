#!/usr/bin/env bats
#
# Testes do script 'scripts/quickstart'. Verificam a logica de decisao sem Docker real: um 'docker'
# de mentira, no PATH, registra as invocacoes de compose. O script roda sobre um repo temporario
# isolado (copia de 'quickstart' e de '.env.example'), de modo que 'ensure_env' escreva '.env' fora
# do repo real. O foco e a invariante "senha nova gerada implica reinicializacao do banco e
# recompilacao" (D3P7), preservada a idempotencia quando '.env' ja existe.

bats_require_minimum_version 1.5.0

setup() {
  REAL_REPO="$(cd -- "${BATS_TEST_DIRNAME}/.." && pwd)"
  TMP_REPO="$(mktemp -d)"
  mkdir -p "${TMP_REPO}/scripts"
  cp "${REAL_REPO}/scripts/quickstart" "${TMP_REPO}/scripts/quickstart"
  cp "${REAL_REPO}/.env.example" "${TMP_REPO}/.env.example"
  SCRIPT="${TMP_REPO}/scripts/quickstart"

  # 'docker' de mentira: registra os argumentos e conclui com sucesso, de modo que
  # 'detect_compose' resolva 'docker compose' e as chamadas de compose sejam observaveis.
  FAKE_BIN="$(mktemp -d)"
  DOCKER_LOG="$(mktemp)"
  export DOCKER_LOG
  cat > "${FAKE_BIN}/docker" <<'FAKE'
#!/usr/bin/env bash
printf '%s\n' "$*" >> "${DOCKER_LOG}"
exit 0
FAKE
  chmod +x "${FAKE_BIN}/docker"
  PATH="${FAKE_BIN}:${PATH}"
}

teardown() {
  rm -rf -- "${TMP_REPO}" "${FAKE_BIN}" "${DOCKER_LOG}"
}

@test "argumento desconhecido aborta com estado nao-zero" {
  run "${SCRIPT}" --nao-existe
  [ "${status}" -ne 0 ]
}

@test "sem .env: gera .env, reinicializa o volume e forca a recompilacao" {
  [ ! -f "${TMP_REPO}/.env" ]
  run "${SCRIPT}"
  [ "${status}" -eq 0 ]
  # O '.env' foi criado a partir do gabarito.
  [ -f "${TMP_REPO}/.env" ]
  # O volume obsoleto e removido antes do 'up'.
  grep -q "compose down --volumes --remove-orphans" "${DOCKER_LOG}"
  # A imagem e recompilada, para refletir o codigo e nao reusar cache obsoleto.
  grep -q "compose up --build" "${DOCKER_LOG}"
}

@test "com .env existente: preserva o estado, sem reinicializar nem recompilar" {
  cp "${TMP_REPO}/.env.example" "${TMP_REPO}/.env"
  run "${SCRIPT}"
  [ "${status}" -eq 0 ]
  # Idempotente: nenhum 'down' de volume e nenhum '--build' implicito. Em Bats, um
  # '! grep' isolado nao falharia o teste (SC2314); afirma-se pelo estado de saida.
  run grep -q "compose down" "${DOCKER_LOG}"
  [ "${status}" -ne 0 ]
  run grep -q -- "--build" "${DOCKER_LOG}"
  [ "${status}" -ne 0 ]
  grep -q "compose up" "${DOCKER_LOG}"
}

@test "com .env existente e --build explicito: recompila sem reinicializar o volume" {
  cp "${TMP_REPO}/.env.example" "${TMP_REPO}/.env"
  run "${SCRIPT}" --build
  [ "${status}" -eq 0 ]
  run grep -q "compose down" "${DOCKER_LOG}"
  [ "${status}" -ne 0 ]
  grep -q "compose up --build" "${DOCKER_LOG}"
}
