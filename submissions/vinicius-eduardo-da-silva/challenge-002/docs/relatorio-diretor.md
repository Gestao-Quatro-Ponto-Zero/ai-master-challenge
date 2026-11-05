# Redesign do suporte: o que os dados dizem e o que fazer

**Para:** Diretor de Operações

## Resumo

Você pediu três respostas: onde perdemos tempo, o que automatizar e uma prova de que funciona.

- **Onde perdemos tempo:** os dados atuais não permitem responder. Eles se comportam como ruído, e apontar um gargalo seria um palpite com aparência de análise.
- **O que automatizar:** o roteamento de tickets. O teste mostrou que 52% poderiam ser roteados sozinhos, com 92,7% de acerto, em tickets internos de TI.
- **A prova:** o protótipo está rodando em [`solution/app/index.html`](../solution/app/index.html). Ele ainda não funciona com tickets de clientes, e uma trava impede que atue neles.

**Decisão pedida:** aprovar a coleta dos dados listados abaixo e um piloto em modo sombra, sem afetar clientes.

## Onde estamos perdendo tempo?

| Pergunta | O que parece | Por que não dá para confiar |
|---|---|---|
| Onde o fluxo trava? | Chat + High + Refund: 11,4h, contra 4,3h na melhor combinação | Dados embaralhados produzem a mesma diferença (7,1h contra 6,9h; p = 0,38) |
| O que impacta a satisfação? | Nenhum fator se destaca | As notas se distribuem por igual, e nenhum dos 6 fatores testados é relevante |
| Quanto desperdiçamos? | Não dá para calcular | 49% dos tickets encerrados são resolvidos antes da primeira resposta, e não há data de abertura |

Além disso, o arquivo tem 8.469 tickets, não ~30.000. Todas as descrições têm o marcador `{product_purchased}`, e as resoluções não têm relação com o problema. **Os dados parecem artificiais, e nenhuma decisão deve se basear neles.**

## O que automatizar e onde parar

Testamos em 9.568 tickets internos de TI que o modelo nunca viu:

| Fila | Tickets | Resultado | O que acontece |
|---|---:|---|---|
| **Rotear sozinho** | 52% | 92,7% de acerto (7,3 erros em 100) | Vai direto para o time |
| **Sugerir ao atendente** | 37% | A categoria certa está nas 2 primeiras opções em 92,5% | O atendente confirma |
| **Enviar a um humano** | 11% | Assunto sensível, ticket desconhecido ou modelo inseguro | Uma pessoa decide |

**Fica com as pessoas:**

- **A resposta ao cliente:** os dados não permitem treinar nem medir a qualidade.
- **Assuntos sensíveis**, como demissão, salário, assédio ou fraude: é uma decisão de cuidado, e a lista deve ser definida com RH e jurídico.
- **Acessos de administrador:** envolvem privilégios, e essa categoria foi das mais instáveis no teste.
- **A prioridade:** a registrada hoje não tem relação com o texto do ticket.

## Os riscos que encontramos

1. **O modelo não funciona em tickets de clientes.** Ele foi treinado com tickets internos de TI e diria "Hardware" para 70% dos tickets de clientes, seja qual for o tipo. Em 19% deles, teria confiança para rotear sozinho. A trava de ticket desconhecido reduz isso a 0,07%: 98,9% vão para um humano.
2. **Os tickets mudam ao longo do tempo.** O acerto geral cai de 85% em uma divisão aleatória para 80% nas últimas linhas. A categoria Purchase quase some no fim do arquivo, então o acompanhamento precisa ser contínuo.
3. **O acerto pode estar um pouco otimista.** O limite de confiança foi escolhido vendo o resultado do teste. O arquivo não tem datas, e a ordem das linhas é só uma aproximação do tempo.

## ROI: um cenário, não uma medição

Os dados não têm tempo de trabalho nem custo. Com as premissas abaixo, **a economia seria de cerca de 865 horas por ano (72 por mês), ou R$ 39 mil**.

| Premissa | Valor | Origem |
|---|---:|---|
| Tickets por ano | 30.000 | Enunciado |
| Minutos para triar um ticket | 3 | Suposição |
| Minutos com a sugestão pronta | 1 | Suposição |
| Minutos de retrabalho por erro | 15 | Suposição |
| Custo da hora | R$ 45 | Suposição |

A economia acaba se cada erro custar mais de 61 minutos. As taxas vêm de tickets de TI, então o cenário só vale depois de confirmado com tickets reais. Os valores podem ser ajustados na aba Cenário de ROI do protótipo.

## Próximos passos

| Quando | O que fazer | Como saber se deu certo |
|---|---|---|
| **Agora** | Capturar datas de abertura, de cada transferência e de encerramento, o tempo ativo do atendente e a fila correta | As três perguntas passam a ter resposta |
| **Depois** | Treinar com tickets reais e rodar em modo sombra, sem afetar clientes | Acerto medido contra o que os atendentes fizeram |
| **Em seguida** | Ligar a sugestão ao atendente | Tempo de triagem medido e queda nas transferências |
| **Por último** | Ligar o roteamento nas categorias aprovadas | Acerto mínimo definido por você antes do início |
