# G4 Sight: como rodar

CRM do time comercial com a prioridade embutida no pipeline. App em Next.js 16 (App Router), React 19, TypeScript strict e Tailwind 4.

## Rodar em 3 comandos

Pré-requisito: Node 20.9 ou mais novo.

```bash
cd submissions/leandro-mallet/solution/app
npm ci
npm run dev
```

Abra **http://localhost:3010**. Não precisa de banco nem de senha: escolha um perfil (vendedor, manager ou admin) e use.

Para a versão de produção: `npm run build` e depois `npm start`.

## O que já está pronto

| Tela | O que faz |
|---|---|
| **Quem é você?** | Escolha de perfil sem login: vendedor ou manager escolhem o nome; admin entra direto. |
| **Painel** | Oito números (leads novos, em negociação, fechamentos, conversão, receita, pipeline aberto, total e em risco de esfriar), o funil por estágio e as **Prioridades do dia**. O ✓ pede o tipo de atividade e um comentário, salva o horário e vai para a linha do tempo do lead; o ✗ pula o deal hoje. Manager e admin veem também o quadro por vendedor. |
| **Pipeline** | Deals abertos em duas colunas (Prospecção e Em negociação), cartão com nome, contato, barra da nota, data de abertura e ícone (super hot, em risco de esfriar ou esfriou). O estágio muda arrastando o cartão ou pelo seletor. Filtro em campo livre, que vira etiquetas removíveis. |
| **Leads** | A base inteira (abertos e fechados) em tabela, com filtro livre, ordenação, **Novo lead** e ações em lote sobre os marcados ou sobre todos os do filtro: aplicar ou remover tag, comentar, mover para Em negociação e encerrar como perdido. O lote pode ser desfeito. |
| **Leads › Contas** | As 85 empresas com setor, porte, sede, deals abertos, compras e receita ganha. A ficha mostra o cadastro (editável), o histórico de compras por mês, os produtos comprados, o padrão de compra ("Calculado no domingo" até o score entregar) e os deals abertos. **Nova empresa** cadastra. |
| **Modal do deal** | Abre ao clicar no deal (ou pelo link `?deal=ID`): linha do tempo, explicação da nota, comentários (postar e apagar) e ações (Liguei, Requalifiquei, Desisti). |

Ainda não construído: importação de leads por CSV. A especificação completa está em [ESPEC-TELAS.md](ESPEC-TELAS.md).

## Dados

- O app lê `data/base.json` (8.800 deals, 85 contas, 35 vendedores e 7 produtos), gerado a partir dos CSVs limpos por `npm run dados -- <pasta solution/data>`.
- Se existir `data/deals_scored.json` (o arquivo de notas do score), o app mostra a nota, o FIT, o HEAT e o bônus. Sem ele, aparece "Sem nota ainda" e as prioridades seguem a ordem: super hot, em risco e maior valor.
- "Hoje" é 31/12/2017, o último dia com registro no dataset.
- **Nesta versão, as mudanças ficam em memória no servidor:** ações, comentários, estágios e prioridades somem ao reiniciar o servidor. A ligação com o banco entra depois, só na camada de dados (`src/server/`), sem mexer nas telas.

## Organização do código

```
src/
  tema/tema.css        único arquivo com cores, fontes, tamanhos, raios e sombras (marca G4, fundo branco)
  app/                 páginas (/, /painel, /pipeline, /leads) e rotas de API
  components/          peças de tela
  lib/                 funções puras: cálculos, números do painel, filtro livre por regras
  server/              só roda no servidor: fonte dos dados, repositório, perfil e base das rotas
data/                  dados que o app lê
scripts/               dados.mjs (traz os CSVs limpos) e espelhar-para-drive.ps1
```

## Cuidados de segurança

- Nenhuma fonte de dados vem da URL, e nenhum texto digitado entra na página como HTML.
- Toda rota de escrita valida a entrada, tem limite por endereço de rede (60 por minuto) e gera o código de rastreio no servidor.
- O usuário "sistema" nunca é aceito vindo da tela.
- Sem login, o perfil organiza a tela e assina as ações, mas não protege nada: qualquer pessoa pode escolher qualquer nome.

## Checagens

```bash
npm run typecheck
npm run lint
npm run build
```

## Onde o app é desenvolvido

As dependências (`node_modules`) e o build (`.next`) não podem ficar no Google Drive, e o volume do Drive não aceita junção. Por isso o app é editado e rodado numa cópia local fora do Drive, e `scripts/espelhar-para-drive.ps1` copia só o código para esta pasta. Esta pasta é um espelho de mão única.
