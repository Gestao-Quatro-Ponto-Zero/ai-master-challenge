# Prompt consolidado: como reconstruir esta solução

> **Este não é o prompt usado no trabalho.** Foi escrito depois de a solução ficar pronta, para registrar o raciocínio em um único pedido. O trabalho real foi iterativo, com erros e correções ao longo do caminho, e está em [`PROCESS_LOG.md`](PROCESS_LOG.md) e no histórico de commits.

O prompt descreve o método, não as respostas. Os achados são verificados nas etapas, e as hipóteses da seção 3 podem cair. A especificação da seção 5 reflete as decisões de produto já tomadas.

---

## O prompt

```text
Você vai trabalhar comigo como parceiro técnico em um desafio de seleção.

# 1. O problema real

A Head de RevOps de um time com 35 vendedores disse:
"Nossos vendedores gastam tempo demais em deals que não vão fechar e deixam
oportunidades boas esfriar. Quero uma ferramenta que o vendedor abra, veja o
pipeline, e saiba onde focar. Pode ser simples, mas precisa funcionar."

Dados: as 4 tabelas do CRM do Kaggle "CRM Sales Predictive Analytics"
(accounts, products, sales_teams, sales_pipeline).

Este brief já foi colado em várias IAs, e a entrega será comparada com essas
respostas. O padrão genérico é um score com pesos para produto, vendedor e porte
da conta, sem prova de que funciona. Não entregue isso sem evidência a favor.

A pergunta central não é "qual modelo prevê melhor?", e sim:
"Na segunda de manhã, o que este vendedor deve fazer, e por que deveria confiar?"

# 2. Como vamos trabalhar

- Execute por etapas. Pare e me mostre o resultado ao fim de cada etapa.
- Antes de desenhar a solução, tente entender onde os dados enganam.
- Um critério só entra no score se melhorar um teste feito fora da amostra.
- As decisões comerciais são minhas: traga opções com uma recomendação.
- Quando um resultado parecer bom, tente derrubá-lo antes de comemorar.
- Mantenha um log do que aconteceu, inclusive dos seus erros. Nunca o reconstrua
  depois nem atribua a mim algo que você fez.
- Não publique nada externamente sem minha autorização.

# 3. Hipóteses para testar, não para assumir

- As características fixas (vendedor, produto, setor, porte) podem prever pouco.
- A idade do deal pode importar mais, e não necessariamente em linha reta.
- Parte do pipeline aberto pode já estar morta.
- Pode haver efeito de calendário, como o fim de trimestre.
- Campos podem faltar de forma correlacionada com o resultado.

# 4. Etapas

## Etapa 1: auditar os dados
Verifique chaves, nulos por estágio, duplicatas, datas e distribuição do ciclo.
Procure especificamente:
- nomes que não batem entre tabelas;
- início do histórico cortado, que infla o win rate;
- campos que só existem depois do fechamento, porque vazam o resultado;
- deals abertos mais velhos do que qualquer deal já encerrado;
- diferenças de cobertura entre vendedores e regiões.
Pronto quando: houver uma lista de armadilhas, cada uma com números.

## Etapa 2: medir o poder de cada sinal
Use validação temporal e variáveis calculadas apenas com o passado de cada deal.
Treinar com deals encerrados e aplicar nos abertos é uma armadilha: mostre o
que muda entre os dois grupos.
Pronto quando: eu souber quais sinais importam e quais são ruído.

## Etapa 3: simular o uso real
Reconstrua segundas-feiras passadas com apenas o que se sabia em cada data. Monte
o top 10 de cada vendedor e meça a receita ganha nos 30 dias seguintes.
Regras obrigatórias:
- um teste automatizado deve provar que reescrever o futuro não muda o aprendizado;
- separe um período para decidir variantes e outro para conferir;
- desempate de forma neutra, pois a ordem do arquivo pode favorecer uma estratégia;
- compare contra rivais simples: aleatório, mais novo, maior valor;
- inclua o rival mais forte que eu conseguiria com bom senso, e não só os fracos.
Pronto quando: houver uma tabela de estratégias, com o critério de escolha
definido antes de ver o resultado.

## Etapa 4: desenhar o score para ser explicável
A ordem deve equivaler à receita esperada (chance x valor), decomposta em partes
que um vendedor entenda. Só mostre chances depois de conferir a calibração. Se o
modelo superestimar, mostre a taxa observada. Se não houver base para pontuar
algo, não pontue.

## Etapa 5: construir a ferramenta
Veja a especificação na seção 5. Depois de construir:
- teste em um navegador real, cobrindo os fluxos e os casos vazios;
- olhe as telas e questione cada número mostrado: ele contradiz algo que já
  descobrimos? Testes não pegam isso, e a revisão humana da tela pega.

## Etapa 6: atacar o próprio resultado
Antes de encerrar, tente derrubar o ganho principal:
- De onde ele vem? Separe o efeito de cada componente.
- Ele depende de poucos deals grandes? Ou de um período específico?
- Vale para a maioria dos vendedores? E com listas de outro tamanho?
- Ele prova aumento de vendas ou só boa identificação? Se for só identificação,
  calcule o que um teste real conseguiria detectar com este número de vendedores,
  por meio de divisões falsas em período sem tratamento.
Atualize a mensagem principal com o que sobreviver.

## Etapa 7: preparar a entrega
Faça o caminho de quem recebe: clone limpo, siga o README e rode tudo. Confira
números e links nos documentos e deixe para mim o que só eu posso escrever.

# 5. Especificação do produto

Página estática em HTML, CSS e JS, com dados pré-calculados em Python, que abra
com dois cliques, sem servidor, instalação ou login.

Três filas, porque um ranking único esconderia o problema:
- Foco: deals dentro do tempo em que deals costumam fechar. Recebem score.
- Decidir: deals mais velhos que qualquer deal já encerrado. Sem score. O vendedor
  confirma ou encerra, em triagem rápida com teclado. A ferramenta nunca encerra
  um deal sozinha.
- Prospecção: sem data, logo sem score. Diga isso na tela.

A data não é fixa: um filtro abre o pipeline como estava em cada segunda passada,
só para consulta e sem indícios do resultado. As listas também ordenam por data
de entrada.

Cada deal mostra fatos para preparar a conversa: fechamento típico do produto, porte
da conta, o que ela já comprou e o histórico do vendedor. Isso é contexto, calculado
só com o passado, e não entra no score.

Telas:
- Minha semana: o primeiro passo, um plano de 3 passos com progresso e os deals
  com motivo, fase do ciclo, ação sugerida e botões Feito e Adiar.
- Revisar: tudo o que foi marcado, com desfazer e exportação em CSV.
- Equipe: visão por região e vendedor e uma calculadora de tempo perdido, cujos
  minutos são premissas explícitas e ajustáveis.
- Máquina do tempo: escolher uma segunda passada, ver a lista e revelar o que
  aconteceu. Nada do resultado pode aparecer antes do clique, nem por indício.
- Como funciona: a lógica, a prova e o que a ferramenta não sabe.

Todo vendedor precisa de uma orientação útil, inclusive quem não tem deals vivos
ou não tem nenhum deal.

# 6. O que entregar

- Solução funcionando, com setup, lógica e limitações documentados.
- Testes automatizados, incluindo o teste contra vazamento de dados futuros.
- Plano de piloto para a Head de RevOps, com regra de decisão definida antes.
- Process log honesto: quem decidiu o quê, onde a IA errou e como isso apareceu.
- README no template do desafio.

# 7. O que considero um erro

- Afirmar que a ferramenta aumenta vendas sem teste com grupo de controle.
- Apresentar só a comparação que favorece a solução.
- Mostrar um número preciso que os dados não sustentam.
- Inventar premissas sem identificá-las como tal.
- Tratar um padrão possivelmente artificial do dataset como lei comercial.
- Escrever por mim o que só eu posso dizer sobre o meu julgamento.
```
