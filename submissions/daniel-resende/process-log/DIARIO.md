# Diário do processo

Escrito na mesma etapa em que cada coisa aconteceu. As horas vêm do comando `date` (fuso -03), nunca de estimativa.

## Quem faz o quê

- **Daniel (o candidato)** define a visão do produto (`process-log/produto.md`), dirige o trabalho, responde aos relatórios de decisão, usa o app como vendedor antes da entrega e aprova tudo o que é público. Só ele decide.
- **Orquestrador**: duas sessões do Claude Code que nunca constroem. Uma, no servidor do Daniel, leu as regras e desenha o caminho e os prompts; outra, neste laptop, leu as regras de forma independente, confere cada rascunho contra o disco, corrige e grava em `prompts/`. O Daniel leva cada prompt ao construtor à mão.
- **Construtor (esta sessão)**: lê, audita, desenha, constrói, testa e faz os commits. Quando há trabalho em paralelo é o líder: os subagentes escrevem arquivos e nunca rodam git.
- **Verificadores**, no fim: uma sessão limpa de outra família de modelo (Codex CLI) e uma sessão nova desta. Não editam a solução; tentam refutá-la. Quem construiu não aprova.

O piso fixo de todas as sessões está em `process-log/piso.md`; cada prompt em `process-log/prompts/` (sete deles como trechos, marcados na primeira linha).

## Ferramentas e por quê

| Ferramenta | Para quê | Por quê |
|---|---|---|
| Claude Code (extensão do VS Code), modelo Claude Fable 5 | construtor líder: fundação, desenho e validação do score, contratos, relatório | lê e roda no disco, então cada afirmação sai de um comando |
| Subagente do Claude Code (mesmo modelo) | auditoria dos dados (`solution/audit.py`) | roda em paralelo ao desenho, com contexto próprio |
| Subagente de pesquisa do Claude Code (com busca na web) | `docs/pesquisa.md`, fontes nomeadas e datadas | a tela e o score partem de práticas verificadas, não de memória |
| `claude -p` em contexto limpo (`--setting-sources "" --tools ""`) | o baseline "IA sozinha" | medir o que o texto cru do desafio produz, para saber onde esta entrega precisa ser melhor |
| GitHub CLI (`gh`) | checar o upstream; fork e PR só com o ok do Daniel | é o canal de entrega do teste |
| Duas sessões do Claude Code como orquestrador | planejar, redigir e conferir os prompts | separa quem planeja e confere de quem constrói |

## Preparação, antes de qualquer prompt (10/11/2026)

- As regras do teste foram lidas de forma independente por duas sessões e as leituras, comparadas.
- O laptop foi medido (o que roda aqui, com qual Python, como chamar o modelo sem chave de API).
- O produto foi escrito em `PRODUTO.md` antes de qualquer código, e o Daniel aprovou o texto.
- O plano foi revisado várias vezes antes do primeiro prompt.
- Tempo real: a primeira medição do orquestrador do laptop foi às 13:53 -03 (do `date`). Hora em que o Daniel começou: PENDENTE (pergunta feita a ele às 15:08).

## Etapa 1: fundação, auditoria e desenho (prompt `01-fundacao-auditoria-desenho.md`)

Início real: 15:06:55. Caixa de tempo: 60 minutos.

### 1.1 Fundação (15:06 a 15:10)

- `pwd` e `dados/` conferidos. A pasta tem os quatro CSVs pedidos e mais um `metadata.csv` (dicionário de campos do dataset), que não foi copiado.
- Upstream: nenhum PR do usuário `danielgresende`; a pasta `daniel-resende` não aparece nos arquivos de nenhum dos 238 PRs que listam arquivos (só títulos e listas de arquivos foram lidos). Existem `daniel-schkolnick`, `daniel-spinelli` e `daniel-vieira`: sem colisão.
- O fork ainda não existia e criar um fork é público. Perguntei ao Daniel e, sem esperar parado, clonei o upstream só para leitura (`upstream` configurado, `git rev-parse upstream/main` com saída 0), criei a branch `submission/daniel-resende` e a identidade local do git. O remoto `origin` entra quando o Daniel der o ok.
- Hook local de pre-commit instalado (não vai para o repositório). Prova às 15:09: um arquivo descartável com uma chave falsa foi recusado ("key-shaped string in the staged diff", saída 1) e um arquivo fora da pasta da submissão também ("staged path outside submissions/daniel-resende/", saída 1). Os dois foram tirados do stage e apagados.
- Lidos na íntegra: `README.md`, `CONTRIBUTING.md`, `submission-guide.md`, o template, `challenges/README.md`, o README do challenge 003 e o `.gitignore`.
- Esqueleto criado; `piso.md`, `produto.md` e o prompt copiados byte a byte; dados copiados com `SHA256SUMS` e `FONTE.md`.
