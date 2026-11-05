# Tela do Lead Scorer (Lovable)

**App publicado:** https://lead-scorer-liberato.lovable.app

A tela foi construída no Lovable pelo Claude, a partir de prompts aprovados pelo Liberato (`process-log/prompts/`). Ela **não recalcula notas, chances, valores esperados nem classificações**. Tudo isso vem do motor (`solution/motor/`). A tela só carrega, filtra, conta, soma e formata.

## De onde vêm os dados
Ao abrir, a tela lê o arquivo gerado pelo motor, publicado nesta branch:
`https://raw.githubusercontent.com/libegouv/ai-master-challenge/refs/heads/submission/liberato-gouveia/submissions/liberato-gouveia/solution/motor/saida/deals_priorizados.json`

O arquivo fica num lugar só. Se o motor rodar de novo e a branch for atualizada, a tela passa a mostrar os dados novos em até ~5 minutos, que é o tempo de cache do GitHub.

## O que está nesta pasta
- `src/routes/index.tsx`: **o código da tela**, copiado sem edição do projeto Lovable (commit `396c42e`). Ele contém tudo o que é específico deste app: carregamento dos dados, faixa histórica, filtros, cartões, abas, cartões de deal e a aba "Como a nota funciona".

O resto do projeto é o modelo padrão do Lovable: TanStack Start, React 19, Vite, Tailwind 4, componentes shadcn/ui (Radix), recharts e ícones lucide. O projeto completo, com 78 arquivos, está no workspace Lovable do Liberato. Os únicos acréscimos do Lovable fora do `index.tsx` foram:
- em `src/styles.css`, as cores das ações e da faixa de aviso (`--warn`, `--act-blue`, `--act-orange`, `--act-gray`, `--act-green` e `--act-purple`) e a fonte IBM Plex Sans;
- em `src/routes/__root.tsx`, a língua `pt-BR` e o link da fonte.

## Como rodar localmente
É preciso ter o projeto completo. O caminho mais simples é exportá-lo pela integração do Lovable com o GitHub e depois rodar:
```bash
npm install
npm run dev
```
Para avaliar, não é preciso instalar nada: basta abrir o link do app publicado.

## Testes da tela
Ver `process-log/analises/resultados/fase3d_testes_tela.md`.
