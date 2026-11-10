#!/usr/bin/env bash
# Adiciona ao git os arquivos novos/alterados da submissão respeitando o .gitignore DESTA pasta.
# Necessário porque o .gitignore da raiz (upstream) ignora submissions/, e `git add -f <pasta>`
# forçaria também .venv/, data/ e .env.
set -euo pipefail
cd "$(dirname "$0")/.."
git ls-files -o -m --exclude-from="$PWD/.gitignore" -z . | xargs -0 -r git add -f --
git status --short -- .
