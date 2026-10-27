#!/usr/bin/env sh
# O .gitignore da raiz do repositório ignora submissions/, então `git add` normal
# não vê nada aqui e `git add -f` inclui também node_modules/.next.
# Este script força só os arquivos que o .gitignore da solução não ignoraria.
cd "$(git rev-parse --show-toplevel)" || exit 1
git ls-files -o -m -i --exclude-standard -- submissions/renan \
  | grep -vE '/(node_modules|\.next|out|data/generated|.scratch|\.vercel)/|next-env\.d\.ts$|\.tsbuildinfo$|/\.env' \
  | xargs -r git add -f --
git add -u -- submissions/renan
git status --short -- submissions/renan
