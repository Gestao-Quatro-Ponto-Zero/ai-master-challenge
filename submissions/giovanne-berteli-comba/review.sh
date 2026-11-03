#!/usr/bin/env bash
# Open the reviewer workspace with its CodeTour, without repository/global settings.
set -euo pipefail
task_review_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
case "${1:-}" in
  --help|-h) printf '%s\n' 'Uso: bash review.sh' 'Abre o VS Code no workspace de revisão e oferece o CodeTour.'; exit 0 ;;
  '') ;;
  *) printf '%s\n' 'Opção desconhecida. Use bash review.sh --help.' >&2; exit 2 ;;
esac
if (( $# > 1 )); then printf '%s\n' 'Use bash review.sh sem argumentos.' >&2; exit 2; fi
if ! command -v code >/dev/null; then
  printf 'VS Code não encontrado no PATH. Abra %s/review.code-workspace pelo editor.\n' "$task_review_root" >&2
  exit 1
fi
printf '%s\n' 'Conferindo o CodeTour no perfil do VS Code…'
if ! task_review_extensions="$(code --list-extensions)"; then
  printf '%s\n' 'Não foi possível consultar o VS Code. Confira se o comando code funciona neste terminal.' >&2
  exit 1
fi
case $'\n'"$task_review_extensions"$'\n' in
  *$'\nvsls-contrib.codetour\n'*) ;;
  *)
    printf '%s\n' 'Instalando a extensão oficial CodeTour neste perfil…'
    code --install-extension vsls-contrib.codetour || { printf '%s\n' 'A instalação não terminou. Verifique o acesso ao Marketplace e execute novamente.' >&2; exit 1; }
    ;;
esac
printf '%s\n' 'Abrindo a revisão. Clique em Start CodeTour na notificação ou no tour Triagem IT assistida no Explorer.'
exec code --new-window "$task_review_root/review.code-workspace"
