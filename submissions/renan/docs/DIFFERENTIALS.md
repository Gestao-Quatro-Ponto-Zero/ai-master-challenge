# O que esta solução faz que o baseline não faz

O G4 já rodou este desafio em vários modelos (Claude, GPT, Gemini). Colando o brief, o resultado previsível é um app com:

- um score de **pesos inventados** ("stage 30%, valor 25%, ...") sem nenhuma validação;
- uma tabela ordenada pelo score, com filtros e um card de KPIs no topo;
- uma "explicação" que repete os pesos ("score alto porque o valor é alto");
- visual de template (cards cinza, gradiente, componentes padrão).

Esse é o piso. Cada item abaixo existe para ficar **acima** dele e responde a uma frase da Head de RevOps.

## 1. Um score testado, e honesto sobre o resultado

> *"Preciso de algo funcional."*

- **Backtest temporal em 3 datas de corte**, comparando com ordenar por preço, só tempo, taxa bruta do vendedor e ordem aleatória ([SCORING.md §4](./SCORING.md)).
- **O teste mostrou que ninguém prevê ganho vs. perda neste CRM** (AUC ≈ 0,5). Em vez de esconder isso, a ferramenta foi redesenhada em cima desse fato: prioriza pelo que é sabível (valor e tempo) e não vende uma "probabilidade" como se fosse precisa.
- **Pesos aprendidos por Bayes empírico:** produto, setor e porte recebem peso zero porque suas diferenças cabem no ruído estatístico. O baseline daria 20% a cada um.
- **Rankings de vendedor são ruído** (qui-quadrado compatível com taxas iguais). Não mostramos ranking que puniria pessoas por sorte; o baseline mostraria.

## 2. O que largar, não só o que atacar

> *"Gastam tempo demais em deals que não vão fechar."*

O baseline só ordena. Aqui existe uma fila explícita de **deals para revisar ou desqualificar**: os abertos há mais de 138 dias, quando nenhum dos 6.711 deals fechados levou mais que isso. São **81% dos deals em Engaging e 64% do valor do pipeline aberto**. Ordenando só por preço, 47% do topo da lista seriam esses deals mortos. Liberar tempo é metade do problema.

## 3. O momento certo, não só o deal certo

> *"Deixam oportunidades boas esfriar."*

Modelo de **janela de fechamento**: com base no ciclo dos deals ganhos, cada deal aberto recebe um status (no ritmo, na janela, esfriando, parado). A prioridade sobe quando o deal entra na janela e cai quando a chance de ainda fechar despenca.

## 4. Pauta do tamanho do tempo disponível

O vendedor não tem tempo infinito. Na tela Hoje ele escolhe quantos deals cabem na pauta (6, 10 ou 20), e a ferramenta mostra os de maior valor esperado entre os que ainda têm chance. Os parados ficam fora.

## 5. Alavancas acionáveis para o manager

O baseline mostra números. Aqui o manager recebe **sugestões**:

- vendedores com o pipeline concentrado em deals parados (pauta de higiene e coaching);
- deals sem conta cadastrada, que travam qualquer análise;
- o padrão de fim de trimestre (80,7% de vitória no último mês vs. 52,3% nos outros), com a ressalva de que pode ser artefato.

_Descartado após os dados:_ a ideia original de sugerir pareamento com o "vendedor que ganha mais naquele produto". O teste mostrou que essa diferença é ruído (correlação de −0,08 entre semestres).

## 6. Explicação como um "recibo"

Cada score é decomposto em fatores somáveis (log-odds convertidos em pontos), escritos em linguagem de vendedor e comparados com a média:

> Deal real, `1LY8CAXD` (GTK 500, Rosalina Dieter), **score 100**:
> **Chance 71%** = base 63,2% · **+7,5 pp** aberto há 95 dias (já passou da fase em que as perdas acontecem) · **+0,1 pp** vendedora · produto, setor e porte: 0 pp (diferenças dentro do ruído) · **× US$ 26.768 = valor esperado US$ 18,9 mil · Reta final: empurrar o fechamento**

## 7. Qualidade de dados como feature do produto

Inconsistências encontradas no CRM (nomes divergentes, deals sem conta, datas faltando) são tratadas no pipeline de dados **e mostradas** na interface e nos docs. Uma ferramenta de produção não esconde dado sujo; ela avisa.

## 8. IA onde ela agrega, e só ali

- **A explicação do score continua sem LLM:** é determinística e auditável.
- **O Agente Gestor é um analista de dados, não um chat genérico.** Ele só fala do pipeline, consulta ferramentas para cada número, e os deals da resposta vêm do motor de score, não do texto do modelo. Fora do escopo, ele redireciona.
- **O lado ativo (Radar) não usa IA:** alertas calculados, sem custo e sem risco de alucinação. A IA entra para aprofundar.
- **Cada usuário usa a própria chave da API**, configurada na tela Configurações; a ferramenta não tem chave própria.
- **Sem modelo de caixa-preta.** Um gradient boosting talvez ganhasse alguns pontos de AUC, mas perderia a explicação, que é o que faz o vendedor confiar.
- **Sem banco nem login.** Não agregam nada à decisão neste escopo; ficam na seção de escala.

## 9. Interface com identidade

Direção visual própria, escolhida por mim entre propostas geradas com as skills de design (processo em [DESIGN.md](./DESIGN.md)), com um único elemento memorável e todo o resto disciplinado. Pronta para produção: acessível, responsiva, modo escuro de verdade.

---

**Status final:** todos os itens foram implementados. O item 4 ficou mais simples que o plano original (escolha do tamanho da pauta em vez de uma otimização por tempo).
