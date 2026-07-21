#!/usr/bin/env bats
#
# Testes do script 'scripts/export-session'. Verificam a higienizacao (remocao de saidas de
# ferramenta, anexos, snapshots e conteudo de sistema; preservacao de prompts, texto e chamadas
# de ferramenta como nome mais argumentos), a validade do JSONL produzido, o caminho feliz e o
# comportamento fail-closed da varredura de segredos.

bats_require_minimum_version 1.5.0

setup() {
  REPO_ROOT="$(cd -- "${BATS_TEST_DIRNAME}/.." && pwd)"
  SCRIPT="${REPO_ROOT}/scripts/export-session"
  FIXTURES="${BATS_TEST_DIRNAME}/fixtures"
  TEST_SESSIONS_DIR="$(mktemp -d)"
  export SESSIONS_DIR="${TEST_SESSIONS_DIR}"
  REF="TST0-2026-07-19-1"
  OUT="${TEST_SESSIONS_DIR}/${REF}.jsonl"
}

teardown() {
  rm -rf -- "${TEST_SESSIONS_DIR}"
}

@test "erro de uso sem argumentos" {
  run "${SCRIPT}"
  [ "${status}" -eq 2 ]
}

@test "erro de uso com um unico argumento" {
  run "${SCRIPT}" apenas-um
  [ "${status}" -eq 2 ]
}

@test "referencia de sessao invalida aborta sem produzir arquivo" {
  run "${SCRIPT}" "${FIXTURES}/sample-raw.jsonl" "ref-invalida"
  [ "${status}" -ne 0 ]
  [ ! -f "${TEST_SESSIONS_DIR}/ref-invalida.jsonl" ]
}

@test "cc-session inexistente aborta com estado nao-zero" {
  local fake_home
  fake_home="$(mktemp -d)"
  run env HOME="${fake_home}" "${SCRIPT}" cc-inexistente "${REF}"
  rm -rf -- "${fake_home}"
  [ "${status}" -ne 0 ]
}

@test "caminho feliz produz arquivo higienizado e JSONL valido" {
  run "${SCRIPT}" "${FIXTURES}/sample-raw.jsonl" "${REF}"
  [ "${status}" -eq 0 ]
  [ -f "${OUT}" ]
  run jq empty "${OUT}"
  [ "${status}" -eq 0 ]
}

# Regressao T3F9: a resolucao por cc-session-id computa o slug do diretorio de projeto do
# Claude Code substituindo '/' e '.' por '-'. Um PWD com '.' no caminho (como '.claude' em
# um worktree) deve resolver a transcricao bruta sem contorno. O slug e computado aqui com
# as mesmas duas substituicoes do script, e o PWD sintetico contem 'proj.dir' para exercitar
# o '.'.
@test "resolucao por cc-session-id com '.' no PWD resolve o slug como o Claude Code" {
  local work_root work fake_home cc slug
  work_root="$(mktemp -d)"
  work="${work_root}/proj.dir/sub"
  fake_home="$(mktemp -d)"
  cc="cc-worktree-0001"
  mkdir -p "${work}"
  slug="${work//\//-}"
  slug="${slug//./-}"
  mkdir -p "${fake_home}/.claude/projects/${slug}"
  cp "${FIXTURES}/sample-raw.jsonl" "${fake_home}/.claude/projects/${slug}/${cc}.jsonl"
  cd "${work}"
  run env HOME="${fake_home}" "${SCRIPT}" "${cc}" "${REF}"
  rm -rf -- "${work_root}" "${fake_home}"
  [ "${status}" -eq 0 ]
  [ -f "${OUT}" ]
}

@test "higienizacao remove saidas, anexos, snapshots, sistema e assinaturas" {
  run "${SCRIPT}" "${FIXTURES}/sample-raw.jsonl" "${REF}"
  [ "${status}" -eq 0 ]
  grep -q "tool output stripped" "${OUT}" \
    && grep -q "attachment stripped" "${OUT}" \
    && grep -q "snapshot stripped" "${OUT}" \
    && grep -q "system content stripped" "${OUT}" \
    && ! grep -q "toolUseResult" "${OUT}" \
    && ! grep -q "SIG-SECRETA-DEVE-SUMIR" "${OUT}"
}

@test "higienizacao remove o segredo presente em saida de ferramenta" {
  run "${SCRIPT}" "${FIXTURES}/sample-raw.jsonl" "${REF}"
  [ "${status}" -eq 0 ]
  ! grep -q "AKIAIOSFODNN7EXAMPLE" "${OUT}"
}

@test "higienizacao preserva prompt, texto e nome mais argumentos da ferramenta" {
  run "${SCRIPT}" "${FIXTURES}/sample-raw.jsonl" "${REF}"
  [ "${status}" -eq 0 ]
  grep -q "Liste os arquivos" "${OUT}" \
    && grep -q '"name":"Bash"' "${OUT}" \
    && grep -q "ls scripts/" "${OUT}"
}

# O segredo de teste e montado em tempo de execucao a partir de fragmentos, de modo que nenhum
# literal com forma de segredo nao isentado fique versionado nas fixtures nem apareca na
# transcricao desta propria sessao. So o arquivo bruto temporario, efemero, o materializa.
@test "varredura fail-closed aborta, nao deixa arquivo e nao expoe o segredo" {
  local secret raw
  secret="AKIA$(printf '%s' 'Z7XMPLE4NOTREAL1')"
  raw="$(mktemp)"
  printf '%s\n' \
    "{\"type\":\"user\",\"uuid\":\"u1\",\"parentUuid\":null,\"sessionId\":\"s\",\"timestamp\":\"2026-07-19T00:00:00Z\",\"message\":{\"role\":\"user\",\"content\":\"Use a chave ${secret} agora.\"}}" \
    > "${raw}"
  run --separate-stderr "${SCRIPT}" "${raw}" "${REF}"
  rm -f -- "${raw}"
  [ "${status}" -ne 0 ]
  [ ! -f "${OUT}" ]
  [[ "${stderr}" == *"aws-access-key-id"* ]]
  [[ "${stderr}" != *"${secret}"* ]]
}

@test "deny-by-default remove tipo de registro desconhecido e campos top-level extras" {
  run "${SCRIPT}" "${FIXTURES}/sample-raw.jsonl" "${REF}"
  [ "${status}" -eq 0 ]
  ! grep -q "UNCOVEREDSECRETzZ9qWq7x2marker" "${OUT}" \
    && ! grep -q "EXTRAFIELDzZ9qWq7x2marker" "${OUT}" \
    && grep -q "unknown record type stripped" "${OUT}"
}

@test "varredura captura segredo em argumento de tool_use preservado (fail-closed)" {
  local secret raw
  secret="sk-proj-$(printf '%s' 'NONALLOWLISTED0FAKEKEY0000')"
  raw="$(mktemp)"
  printf '%s\n' \
    "{\"type\":\"assistant\",\"uuid\":\"a1\",\"parentUuid\":null,\"sessionId\":\"s\",\"timestamp\":\"2026-07-19T00:00:01Z\",\"message\":{\"role\":\"assistant\",\"content\":[{\"type\":\"tool_use\",\"id\":\"t1\",\"name\":\"Bash\",\"input\":{\"command\":\"export OPENAI=${secret}\"}}]}}" \
    > "${raw}"
  run --separate-stderr "${SCRIPT}" "${raw}" "${REF}"
  rm -f -- "${raw}"
  [ "${status}" -ne 0 ]
  [ ! -f "${OUT}" ]
  [[ "${stderr}" == *"openai-key"* ]]
  [[ "${stderr}" != *"${secret}"* ]]
}

@test "allowlist limpa um literal benigno preservado e permite a exportacao" {
  run "${SCRIPT}" "${FIXTURES}/allowlisted-raw.jsonl" "${REF}"
  [ "${status}" -eq 0 ]
  [ -f "${OUT}" ]
  # O literal benigno sobrevive a higienizacao (superficie preservada) e e isentado pela
  # varredura; a sua presenca na saida confirma que foi limpo, nao removido.
  grep -q "AKIAIOSFODNN7EXAMPLE" "${OUT}"
}

@test "allowlisted e nao-allowlisted no mesmo arquivo ainda aborta (fail-closed)" {
  local secret raw
  secret="AKIA$(printf '%s' 'Z7XMPLE4NOTREAL1')"
  raw="$(mktemp)"
  # Uma linha isentada (chave de exemplo) e uma nao isentada (montada) da mesma familia AWS.
  printf '%s\n' \
    "{\"type\":\"user\",\"uuid\":\"u1\",\"parentUuid\":null,\"sessionId\":\"s\",\"timestamp\":\"2026-07-19T00:00:00Z\",\"message\":{\"role\":\"user\",\"content\":\"Exemplo publico AKIAIOSFODNN7EXAMPLE.\"}}" \
    "{\"type\":\"user\",\"uuid\":\"u2\",\"parentUuid\":\"u1\",\"sessionId\":\"s\",\"timestamp\":\"2026-07-19T00:00:01Z\",\"message\":{\"role\":\"user\",\"content\":\"Chave real ${secret}.\"}}" \
    > "${raw}"
  run --separate-stderr "${SCRIPT}" "${raw}" "${REF}"
  rm -f -- "${raw}"
  [ "${status}" -ne 0 ]
  [ ! -f "${OUT}" ]
  [[ "${stderr}" == *"aws-access-key-id"* ]]
}

# Regressao do achado de auditoria A1: um token maior que apenas COMECA por uma cadeia isentada
# nao pode ser limpo por truncacao de prefixo. O segredo e montado em runtime como a chave de
# exemplo isentada seguida de caracteres adicionais da classe da regra; o casamento maximal difere
# da entrada do allowlist e deve abortar.
@test "token que apenas comeca por um literal isentado nao e limpo (fail-closed)" {
  local secret raw
  secret="AKIAIOSFODNN7EXAMPLE$(printf '%s' 'EXTRA9')"
  raw="$(mktemp)"
  printf '%s\n' \
    "{\"type\":\"user\",\"uuid\":\"u1\",\"parentUuid\":null,\"sessionId\":\"s\",\"timestamp\":\"2026-07-19T00:00:00Z\",\"message\":{\"role\":\"user\",\"content\":\"Chave ${secret} em uso.\"}}" \
    > "${raw}"
  run --separate-stderr "${SCRIPT}" "${raw}" "${REF}"
  rm -f -- "${raw}"
  [ "${status}" -ne 0 ]
  [ ! -f "${OUT}" ]
  [[ "${stderr}" == *"aws-access-key-id"* ]]
  [[ "${stderr}" != *"${secret}"* ]]
}

@test "transcricao bruta malformada aborta fail-closed sem produzir arquivo" {
  local bad
  bad="$(mktemp)"
  printf '%s\n' '{"type":"user","message":{"role":"user","content":"ok"}}' 'linha-nao-json' > "${bad}"
  run "${SCRIPT}" "${bad}" "${REF}"
  rm -f -- "${bad}"
  [ "${status}" -ne 0 ]
  [ ! -f "${OUT}" ]
}
