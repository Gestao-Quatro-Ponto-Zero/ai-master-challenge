# Plano de adoção e de medição de resultado

A ferramenta prova que ordena bem. Este plano é para descobrir se usá-la muda
alguma coisa, em um trimestre, e para decidir se ela fica. Tem três partes:
como o time passa a usar (adoção), o que medir e onde cada número aparece
(medição), e como separar efeito real de coincidência (piloto).

## Antes de ligar a ferramenta

1. **Limpar o pipeline por regra.** Encerrar no CRM tudo que passou de 138 dias:
   1.291 das 1.589 negociações em andamento, sem nenhum ganho histórico nesse
   grupo. Isso resolve a maior parte de "tempo em deal que não fecha" com uma
   regra, e deixa a previsão de receita com o tamanho real.
2. **Tornar a empresa obrigatória ao iniciar uma negociação.** Hoje 68% das
   abertas não têm o cliente preenchido.
3. **Guardar os registros num lugar só.** Hoje ficam no navegador de cada
   vendedor. Sem isso não há o que medir.

## Adoção

| Quando | O que | Quem |
|---|---|---|
| Semana 0 | Limpeza por regra; apresentar a fila em 20 minutos, com a página "Como funciona" aberta | RevOps e managers |
| Semanas 1 e 2 | Vendedor trabalha a fila do topo para baixo e registra cada contato. Não medir ainda: é período de costume | Vendedores do grupo de teste |
| Toda segunda | Manager abre o Painel e conversa sobre duas coisas: a faixa "Prioritárias sem contato" (clicando no nome abre o vendedor) e o que voltou em "Retornos" | Managers |
| Toda sexta | RevOps baixa os registros de contato em CSV (botão no Painel) e guarda a semana | RevOps |
| Semana 4 | Primeira leitura dos sinais de alerta (abaixo) | RevOps |
| Semana 13 | Decisão: manter, ajustar ou desligar | Head de RevOps |

O que ajuda a adoção, e já está na ferramenta: um botão por linha, a próxima
negociação em destaque, o motivo do score na ficha em dois fatores, a fila se
atualizando sozinha depois de cada registro, e lista ou kanban à escolha de
cada um.

O que atrapalha a adoção, e o que fazer:

| Risco | O que fazer |
|---|---|
| Registrar duas vezes, na ferramenta e no CRM | No piloto, a ferramenta é o registro de contato e o CRM só recebe o fechamento. Para ficar, precisa gravar direto no CRM |
| 91 das 128 negociações com chance não têm a empresa preenchida | Preencher a empresa dessas 91 na semana 0; é uma tarde de trabalho de RevOps |
| Os 10 vendedores do Central só têm primeiro contato na fila, sem prioridade real | Começar o piloto por East e West; no Central, a ferramenta serve de roteiro de prospecção, não de priorização |
| Vendedor registra em lote no fim do dia para "cumprir" | É um dos sinais de alerta abaixo; o registro tem data e hora |
| Gerente usar o painel para cobrar volume de contato | O painel não ranqueia pessoas de propósito: a taxa de ganho não diferencia vendedores nesta base |

## Como medir

| Problema | Métrica | Fonte | Hoje |
|---|---|---|---|
| Tempo em deal que não fecha | Negociações em andamento com mais de 138 dias ÷ em andamento | CRM | 81% |
| Tempo em deal que não fecha | Contatos em "reativar" e "encerrar" ÷ contatos totais | Ferramenta | Sem dado |
| Boas esfriando | Entre as iniciadas há mais de 138 dias: nunca fechadas ÷ total | CRM | 22% |
| Boas esfriando | Negociações com chance que tiveram contato nos últimos 7 dias | Ferramenta | Sem dado |
| Resultado | Entre as iniciadas há mais de 138 dias: ganhas ÷ total, por mês de início | CRM | 50% |

Não usar "ganhas ÷ (ganhas + perdidas)": ela cai de 63% para 53% só por encerrar
as 1.291 negociações mortas, sem nada ter mudado.

### Onde cada número aparece hoje

| O que acompanhar | Onde está | Limite atual |
|---|---|---|
| Quantas negociações têm chance e quanto devem render | Painel: "Com chance de fechar" e "Valor esperado das com chance" (preço × chance; não é a previsão do trimestre) | Recalcula só quando os dados são regerados |
| Quanto do pipeline está morto | Painel: "Em andamento sem chance" | – |
| Boa oportunidade parada | Painel: faixa "Prioritárias sem contato", por vendedor; filtro de mesmo nome na Carteira | Depende do registro |
| O time está usando? | Painel: "Atividade do time" (contatos em 7 dias, prioritárias já contatadas, resposta positiva, vendedores usando) | Só vê os registros feitos no mesmo navegador |
| Dado bruto para análise | Painel: "Baixar todos os registros de contato (CSV)": data, tipo, anotação, negociação, lista, vendedor, time, região, produto, preço, idade | Idem |

O limite da última coluna é o principal bloqueio do piloto: sem um registro
central, o gerente não enxerga o que cada vendedor fez. É o primeiro item a
construir.

## Piloto

- **Divisão:** sorteio por vendedor dentro de cada time de manager, 15 de um
  lado e 15 do outro. O grupo de controle também registra os contatos, mas vê a
  lista sem ordenação. **Esse modo sem ordenação ainda não existe**, assim como
  o registro central; os dois precisam ser construídos antes do piloto.
- **Duração:** um trimestre fechado, começando no primeiro dia. A taxa de ganho
  muda muito entre o primeiro e o último mês do trimestre.
- **O que este time consegue provar** (35 vendedores no cadastro, 30 com
  negociação no pipeline, por isso 15 e 15): diferença de comportamento (quem
  segue a fila contata mais as prioritárias?) e uma diferença de cerca de 18% no
  número de ganhos. **Não conseguem provar +10% de receita**: seriam precisos
  cerca de 120 vendedores por grupo.
- **Teste rápido da reativação:** sortear metade das 474 negociações para não
  receber mensagem. Como nenhuma parada foi ganha no histórico, 6 ganhos no
  grupo que recebeu já são um resultado claro.

## Sinais de que a ferramenta está só mascarando

- Menos da metade dos contatos nas 10 primeiras posições da fila: o vendedor
  registra, mas não segue a ordem.
- O pipeline morto cai (encerraram em massa) e o contato com as prioritárias não
  sobe: limpeza sem mudança de comportamento.
- Registros em lote no fim do dia, ou "fechou" na ferramenta sem ganho no CRM.

## Critério de decisão em 13 semanas

- **Manter:** 70% ou mais dos vendedores usando; contato com as prioritárias 20
  pontos acima do controle; número de ganhos sem queda.
- **Ajustar:** o comportamento mudou, mas ganhos e conversão seguem iguais.
  Rever os prazos de retorno e a regra de reativação, que são apostas.
- **Desligar:** menos de 40% usando na semana 8, ou comportamento igual ao do
  controle.
