# G4 Sight: como rodar

CRM do time comercial com a prioridade embutida no pipeline. Next.js 16 (App Router), React 19, TypeScript strict e Tailwind 4.

**Avaliação pelo link:** https://g4-sight.vercel.app. Lá o app roda com o banco, as notas do score e a rotina diária. Na tela de login, escolha um perfil e um usuário (não há senha).

Rodar localmente é opcional. **Sem credenciais, o app local mostra as telas com os dados do dataset, mas sem as notas** (os deals aparecem como "Sem nota ainda"), porque as notas ficam no banco.

## Rodar em 5 minutos

Pré-requisito: Node 20.9 ou mais novo.

```bash
cd submissions/leandro-mallet/solution/app
cp .env.example .env.local
npm ci
npm run dev
```

Abra **http://localhost:3010**, escolha o perfil e o usuário e clique em **Login**. Não há senha.

Sem preencher nada no `.env.local`, o app abre com os dados do arquivo `data/base.json`, em modo somente leitura. Para testar as mudanças sem banco, use `G4_ESCRITA_EM_MEMORIA=1` (elas somem ao reiniciar).

Versão de produção local: `npm run build` e depois `npm start` (mesma porta 3010).

## Variáveis de ambiente

Ficam em `.env.local` (fora do git). O modelo, sem valores, é o `.env.example`.

| Variável | Para que serve | Sem ela |
|---|---|---|
| `SUPABASE_URL` | Endereço do banco | O app lê `data/base.json` em modo somente leitura |
| `SUPABASE_SERVICE_ROLE_KEY` | Chave do banco, usada só no servidor | Igual à linha acima |
| `DATABASE_URL_ROTINA` | Conexão da rotina diária com o papel `g4_rotina` | A rotina responde com falha e registra o erro; as telas funcionam |
| `CRON_SECRET` | Segredo das rotas da rotina (`Authorization: Bearer`) | As rotas da rotina respondem 401 para todo pedido |
| `G4_ESCRITA_EM_MEMORIA` | `1` = sem banco, aceita mudanças em memória | Sem banco, as mudanças ficam desligadas |
| `G4_SOMENTE_LEITURA` | `1` = desliga as mudanças mesmo com banco | As mudanças funcionam normalmente |

## Telas

| Tela | O que tem |
|---|---|
| **Entrada** | Tela de login sem senha: "Selecione o Perfil" (Vendedor, Manager ou Admin), "Selecione o Usuário" (vendedores agrupados por time) e o botão **Login**. O perfil vale para a sessão do navegador; com perfil na sessão, aparece "Continuar como …". |
| **Painel** | Grade com os números: pipeline aberto, em negociação, leads e fechamentos de hoje, leads, fechamentos e conversão da janela (com a variação em relação à janela anterior) e total de leads. Um selo mostra quantos deals estão em risco de esfriar. O bloco **Prioridades do dia** tem fundo azul e mostra os 20 deals da meta, pela nota. Clicar no deal abre a explicação da nota. Feito, Pulado e Contato hoje marcam o item, que fica esmaecido no fim da lista. O **funil** tem 5 etapas: Novo lead, Atendimento, Em negociação, Fechado e Perdido. Manager e admin veem também o quadro por vendedor. |
| **Pipeline** | Cinco colunas, uma por etapa. O cartão mostra o nome, o contato, a barra da nota, a data de abertura e um ícone (super hot, em risco de esfriar ou esfriou). **Atendimento é automático:** o primeiro contato registrado leva o lead de Novo lead para Atendimento. A etapa muda arrastando o cartão ou pelo seletor. O filtro aceita texto livre, que vira etiquetas removíveis. |
| **Leads** | A base inteira (abertos e fechados) em tabela, com filtro livre, ordenação, **Novo lead** e ações em lote sobre os marcados ou sobre todos os do filtro: aplicar ou remover tag, comentar, mover para Em negociação e encerrar como perdido. O lote pode ser desfeito. |
| **Leads › Contas** | As 85 empresas com setor, porte, sede, deals abertos, compras e receita ganha. A ficha mostra o cadastro, o histórico de compras por mês, os produtos comprados, o padrão de compra e os deals abertos. |
| **Modal do deal** | Abre ao clicar no deal ou pelo link `?deal=ID`. Mostra a linha do tempo, os comentários, os botões **Liguei**, **Requalifiquei** e **Desisti** e a **explicação da nota em linhas** ("Por que a nota é N"): a conta (por exemplo "0,7 × 62 + 0,3 × 10 + 5 = 51"), a barra com a parte de cada componente e os motivos agrupados. O **FIT** aparece como **% de conversão**: "Performance do vendedor neste perfil (FIT) 62%" quer dizer que o vendedor fecha 62% dos leads com esse perfil. Embaixo, a conversão dele em cada característica do lead (por exemplo "Setor finanças 65%"); a característica com poucos fechados aparece como "poucos casos". |

Os valores aparecem em **R$**, com os mesmos números do dataset, sem conversão de moeda.

## Rotina diária do score

- **Quando:** cron da Vercel todo dia às **06:00 UTC** (03:00 de Brasília), em `GET /api/rotina/diaria` (`vercel.json`).
- **Relógio:** o dataset termina em 31/12/2017. A data de negócio anda 1 dia por dia real a partir de 10/11/2026 = 31/12/2017. A conta está em `config_parametros` (`data_ancora_real`, `data_ancora_negocio`), em `system_data_negocio()` no banco e em `src/lib/relogio.ts` no app.
- **Todo dia:** HEAT e nota novos numa execução nova, repasse por mudança de faixa sem contato e as Prioridades do dia.
- **No domingo de negócio:** além do diário, o job semanal recalcula o FIT (janela de 3 meses), os padrões de compra das contas e a redistribuição entre os vendedores ativos.
- **Uma vez por dia:** o dia de negócio já rodado não roda de novo. Erro desfaz tudo e grava o evento `rotina_diaria_falha`.
- **Rodar na mão:** `POST /api/rotina/rodar-agora` com o mesmo segredo. Com `?forcar=1`, roda mesmo com o dia já rodado e grava o evento `rotina_forcada`. Nada é apagado.

```bash
curl -X POST -H "Authorization: Bearer $CRON_SECRET" "https://g4-sight.vercel.app/api/rotina/rodar-agora?forcar=1"
```

## Testes

```bash
npm run typecheck
npm run lint
npm test
npm run build
```

`npm test` roda a suíte do Vitest. O teste da rotina contra o banco (`tests/rotina-integracao.test.ts`) sobe um Postgres em memória (PGlite) com todas as migrations e o dataset inteiro. Ele lê a pasta `../db` (ou `G4_DB_DIR`) e é pulado quando ela não existe. Leva alguns minutos.

## Organização do código

```
src/
  tema/tema.css        único arquivo com cores, fontes, tamanhos, raios e sombras
  app/                 páginas (/, /painel, /pipeline, /leads) e rotas de API (inclui /api/rotina)
  components/          peças de tela; components/ui é a biblioteca de objetos comuns
  lib/                 funções puras: cálculos, etapas, painel, prioridades, relógio, explicação da nota, filtro livre
  lib/score/           a lógica do score (FIT, HEAT, nota, padrões de conta, redistribuição, repasse)
  server/              só roda no servidor: banco, repositórios (banco e arquivo), sessão e base das rotas
  server/motor/        a rotina diária: liga lib/score ao banco, transação, idempotência e autorização
data/base.json         reserva usada sem banco (8.800 deals, 85 contas, 35 vendedores, 7 produtos)
tests/                 Vitest
vercel.json            o cron da rotina
```

Com o banco configurado, o app lê as views e grava só pelas funções do banco, com o usuário do perfil e um código de rastreio gerado no servidor. Cada mudança fica na auditoria. Se o banco não responder, o app passa para `data/base.json`, mostra a faixa "Modo somente leitura" e volta sozinho quando o banco volta.

## Segurança

- A chave do banco só existe no servidor (`import "server-only"`). O pacote do navegador não tem chave nem URL do banco.
- Toda rota de escrita valida a entrada, tem limite de 60 pedidos por minuto por endereço de rede e gera o código de rastreio no servidor.
- O usuário "sistema" nunca é aceito vindo da tela.
- As rotas da rotina comparam o segredo em tempo constante.

## Limitações

- **Sem login:** o perfil organiza a tela e assina as ações, mas não protege nada. Qualquer pessoa pode escolher qualquer nome.
- **Sem banco não há nota:** no modo arquivo, os deals aparecem como "Sem nota ainda" e as prioridades seguem a ordem super hot, em risco e maior valor.
- **Empresas:** criar e editar empresa ainda não tem função no banco. Com o banco ligado, esses botões ficam escondidos.
- **Importação de leads por CSV** não foi construída.
- **Dataset parado em 2017:** a data de negócio é simulada pelo relógio, então os números novos vêm só das ações feitas no app.
- **Lead novo** recebe o dono no cadastro (o banco exige vendedor). A rotina não faz roteamento automático de lead sem dono.

## Onde o app é desenvolvido

`node_modules` e `.next` não podem ficar no Google Drive. O app é editado e rodado numa cópia local fora do Drive, e `scripts/espelhar-para-drive.ps1` copia só o código para esta pasta, sem apagar nada.
