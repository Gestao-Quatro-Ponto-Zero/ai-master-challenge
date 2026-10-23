#!/usr/bin/env bash
# Adiciona a pasta da submissão ao git respeitando o .gitignore dela.
# O .gitignore da raiz ignora submissions/; `git add -f` ignoraria também os .gitignore internos.
# Por isso listamos só os arquivos não ignorados pelo .gitignore da pasta e adicionamos esses.
set -euo pipefail
root="$(git rev-parse --show-toplevel)"
sub="submissions/tiago-canatelli"
cd "$root"
new_files="$(git ls-files -o --exclude-from="$sub/.gitignore" -- "$sub")"
if [ -n "$new_files" ]; then
  printf "%s\n" "$new_files" | git add -f --pathspec-from-file=-
fi
git add -u -- "$sub"
git status --short -- "$sub"
