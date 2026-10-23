# ADR 0003: Método e política como config

**Status:** aceita

## Contexto

Duas coisas decidem o que o vendedor vê: **onde** cada negócio cai (a política: faixas de idade, textos) e **o que** ele confirma sobre o negócio (o método de qualificação: perguntas e efeito das respostas). As duas são escolhas de negócio da área de RevOps, não de engenharia: os limites dependem da curva medida, e o método pode ser BANT hoje e outro amanhã. Trocar qualquer uma não pode exigir mexer no motor.

## Decisão

- A política é um objeto em `packages/dominio/src/priorizacao/politica.provisoria.config.ts`, validado por `validarPolitica` (faixas em ordem crescente, a última sem teto, blocos válidos, todos os textos preenchidos).
- O método é um objeto em `packages/dominio/src/qualificacao/metodo.provisorio.config.ts`, validado por `validarMetodo` (ids únicos, critério do vendedor aponta para pergunta existente).
- A resposta "não" troca a ação pela frase da pergunta; nenhuma resposta muda o bloco, e o schema do método recusa um efeito sobre o bloco. (Substituído em parte pelo [ADR 0012](0012-score-e-qualidade.md): as respostas agora mexem no score, com pesos declarados como heurística num config próprio; o bloco continua sem mudar.)
- `criarServicos` aceita outra política e outro método como parâmetro; o padrão é o config ativo.
- Todo texto da tela mora na política, com `{…}` preenchidos pelo domínio.

## Consequências

- Trocar = trocar o arquivo. O teste `packages/dominio/src/aplicacao/aplicacao.test.ts` prova com configs só de teste:
  - outra política (Siga até 45 dias, Foque até 90) muda os blocos da fila real e mantém o total;
  - outro método, com perguntas que movem, muda as pendentes e, por regra, o bloco, com a precedência Nutrição > Foque agora;
  - nenhuma resposta muda o grupo dos 2.089 abertos, só a ação.
- A política está marcada `provisoria: true` e traz o aviso na própria config: os limites vêm da curva medida e podem ser recalibrados.
- O motor fica pequeno e estável; o que muda é dado.

## Alternativas consideradas

- **Regras no código do componente ou do motor:** cada ajuste vira mudança de código e risco de regressão.
- **Score por pesos somados (pontos por atributo):** foi medido e não discrimina neste histórico; ver [ADR 0004](0004-blocos-por-idade-valor-so-ordena.md).
- **Config em JSON/YAML lido em tempo de execução:** daria para trocar sem build, mas perde o typecheck do TypeScript; a validação por schema existe para quando a config vier de fora.
