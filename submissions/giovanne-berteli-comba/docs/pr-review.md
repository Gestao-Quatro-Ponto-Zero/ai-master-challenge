# Pesquisa de PRs do Challenge 002 — R01

**Triagem com encaminhamento humano e cuidado com a qualidade dos dados já aparecem
na amostra. A oportunidade para nossa entrega é demonstrar um fluxo útil com
avaliação rastreável, erros explícitos e interpretação correta das métricas.**
Isso é uma orientação para a execução, não uma alegação de exclusividade.

## Seleção, escopo e limites

Pesquisa em 02/11/2026, das 15:26:42 às 15:30:01 (America/Sao_Paulo): **3 min 19 s**
entre o início da pesquisa e a última inspeção de fontes. A redação e os checks
locais posteriores não entram nesse intervalo. O limite declarado era três PRs
ou 20 minutos; encerramos ao concluir os três, sem ampliar a amostra.

Consulta na API pública do GitHub: `repo:Gestao-Quatro-Ponto-Zero/ai-master-challenge
is:pr 002 in:title`, ordenada por atualização decrescente, incluindo abertos e
fechados. Os 49 resultados são correspondências de título, inclusive alguns
multidesafios; não são uma contagem exaustiva de submissões confirmadas do 002.
Os três primeiros foram elegíveis pelo título **e pelo README** e não são nossos.
Nenhum PR de outro desafio foi analisado.

| Ordem | PR | Última atualização retornada (UTC) | Commit inspecionado |
| --- | --- | --- | --- |
| 1 | [#211 — Paulo Vinicius Alves](https://github.com/Gestao-Quatro-Ponto-Zero/ai-master-challenge/pull/211) | 22/10/2026 19:16:30 | `366e7eb5b292582efa4d86aeaa199d56e5af3d06` |
| 2 | [#209 — Hoffman](https://github.com/Gestao-Quatro-Ponto-Zero/ai-master-challenge/pull/209) | 21/10/2026 17:46:25 | `dd5c5230e1a17b535c46e5925bbf69bf0399494a` |
| 3 | [#205 — Bernardo Meireles Corrêa](https://github.com/Gestao-Quatro-Ponto-Zero/ai-master-challenge/pull/205) | 20/10/2026 03:35:58 | `d8fd3a932350e0d1e217134acb93d3ff65b0d40e` |

O [snapshot](review-evidence/pr-review-snapshot.json) guarda consulta, ordem
retornada, horários, commits, oito arquivos consultados, intervalos inspecionados
e hashes. A identidade dos textos foi conferida com o blob informado pela API.
As páginas pelo navegador de busca deram cache miss; API e fontes raw funcionaram.

**Leitura não equivale a reprodução:** não executamos programas, testes ou modelos
alheios, não abrimos demos e não copiamos implementação para a solução. Não foram
inspecionados todos os arquivos ou históricos, nem comentários de avaliadores.
Os resultados abaixo são declarados pelos autores ou registrados em seus
artefatos, nunca medições nossas. Lacuna no recorte não comprova ausência no projeto.

## O que encontramos

### PR #211 — resposta assistida, regras e limites do leitor

O README descreve leitura por sinais, decisão por regras e verificação da resposta.
O autor expõe falhas em casos novos e distingue o resultado inicial do resultado
obtido após rever os mesmos casos. Informa que os tickets da demonstração foram
escritos para teste e que envio/espera são simulados. O ponto útil é a transparência
sobre origem e reutilização do teste; não é evidência de eficácia numa operação
real. [README fixado](https://github.com/Pauloviniciusd/ai-master-challenge/blob/366e7eb5b292582efa4d86aeaa199d56e5af3d06/submissions/vinicius-alves/README.md).

A proposta detalha os erros que persistem e separa política, leitor e revisão
humana. O caso estudado é diferente do nosso benchmark IT; não há uma comparação
direta de qualidade. Seus testes artificiais não substituirão os dados públicos
que escolhemos usar. [Proposta fixada](https://github.com/Pauloviniciusd/ai-master-challenge/blob/366e7eb5b292582efa4d86aeaa199d56e5af3d06/submissions/vinicius-alves/solution/04-proposta.md).

### PR #209 — classificador e política de roteamento simples

O README relata métricas globais e no subconjunto roteado, explicita exceções
humanas e reconhece a diferença entre clientes e IT. Também apresenta estimativas
ilustrativas baseadas em tempo posterior à resposta e anualização da quantidade
de registros. Não adotaremos essas premissas: D02 já distingue tempo decorrido de
trabalho ativo e não estabelece um período anual de observação.
[README fixado](https://github.com/MateusHoffman/ai-master-challenge/blob/dd5c5230e1a17b535c46e5925bbf69bf0399494a/submissions/hoffman/README.md).

No arquivo inspecionado, o treino usa TF-IDF e regressão logística com holdout
estratificado de 20%; a política contém um limiar fixo de 0,70 e exceções por
categoria. Não há nesse arquivo uma etapa separada de seleção do limiar em
validação. Isso não prova ajuste no teste; apenas não estabelece como o limite
foi escolhido. A lição para V00 é registrar essa escolha antes do teste final.
[Treino e política](https://github.com/MateusHoffman/ai-master-challenge/blob/dd5c5230e1a17b535c46e5925bbf69bf0399494a/submissions/hoffman/solution/prototipo.py#L17-L59).

### PR #205 — avaliação separada e evidências de cobertura

O README apresenta diagnóstico, protótipo e limitações, incluindo a distinção
entre revisão por IA e revisão humana sistemática. Sua narrativa relata uma
reconstrução após excesso de documentação; isso é um alerta útil para manter
nossa próxima entrega centrada em respostas e funcionamento.
[README fixado](https://github.com/meireles-bernardo/ai-master-challenge/blob/d8fd3a932350e0d1e217134acb93d3ff65b0d40e/submissions/bernardo-meireles-correa/README.md).

Os trechos de treino separam treino/calibração/teste, selecionam candidato e limiar
na calibração e apresentam baseline e análise de quase duplicatas. O artefato
registra cobertura de 74,26% com 95,03% de acerto de categoria nos selecionados;
isso não é garantia operacional nem meta escolhida para nós.
[Método](https://github.com/meireles-bernardo/ai-master-challenge/blob/d8fd3a932350e0d1e217134acb93d3ff65b0d40e/submissions/bernardo-meireles-correa/analysis/train.py#L83-L127),
[métricas publicadas](https://github.com/meireles-bernardo/ai-master-challenge/blob/d8fd3a932350e0d1e217134acb93d3ff65b0d40e/submissions/bernardo-meireles-correa/outputs/classifier_metrics.json).

A curva consultada escolhe limites na calibração e mede no teste. Não reproduzimos
esses resultados, nem adotamos um teto teórico de desempenho baseado apenas em
proximidade textual. [Curva](https://github.com/meireles-bernardo/ai-master-challenge/blob/d8fd3a932350e0d1e217134acb93d3ff65b0d40e/submissions/bernardo-meireles-correa/analysis/classifier_curve.py#L42-L63).

## Padrões e consequências para nossa entrega

- **Já presentes nos três READMEs:** problemas temporais, fronteira de atuação
  humana e estimativas com premissas. Não apresentar esses pontos isolados como
  inovação exclusiva. Esta amostra por recência não representa todos os PRs.
- **Métricas não comparáveis diretamente:** tarefas, conjuntos, políticas e
  populações diferem. Não transformar números dos candidatos em ranking ou em
  metas nossas; custo dos erros e V00 devem orientar a seleção.
- **A01 deve responder ao diretor:** mostrar composição da fila e satisfação com
  suporte/denominadores, indicar o que merece investigação e construir cenários
  de esforço explícitos. Evitar que a entrega seja apenas uma lista de ressalvas.
- **S01/I01 devem demonstrar utilidade:** um fluxo de triagem assistida, com motivo
  e encaminhamento humano, usando dados reais do domínio declarado. Anomalias
  altas/baixas e seus filtros continuam requisitos de F03; a pesquisa não demonstra
  que sejam exclusivos nem muda os critérios já aprovados.
- **V00/V01 devem tornar os limites verificáveis:** comparação com baseline,
  seleção na validação, teste reservado, erros por classe, cobertura e volume de
  revisão. Qualquer teste reutilizado deve ser identificado como tal.

As escolhas da [D02](../knowledge/dataset-usage.md) continuam vigentes. Esta pesquisa
não acrescenta integrações, dashboards ou novos modelos ao escopo. R01 está
concluída; a próxima tarefa é **A01 — diagnóstico operacional**.
