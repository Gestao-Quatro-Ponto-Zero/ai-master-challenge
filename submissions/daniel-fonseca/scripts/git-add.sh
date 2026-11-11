#!/usr/bin/env bash
# Adiciona ao git os arquivos novos/alterados da submissão respeitando o .gitignore DESTA pasta.
# Necessário porque o .gitignore da raiz (upstream) ignora submissions/, e `git add -f <pasta>`
# forçaria também .venv/, data/ e .env.
set -euo pipefail
# Atenção: com --exclude-from, padrões com barra no meio são ancorados na raiz do repositório,
# por isso o .gitignore desta pasta usa **/ nesses casos (ex.: **/.claude/worktrees/).
cd "$(dirname "$0")/.."
git ls-files -o -m --exclude-from="$PWD/.gitignore" -z . | xargs -0 -r git add -f --
git status --short -- .
