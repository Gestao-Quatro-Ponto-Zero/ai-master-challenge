# Arquitetura — Lead Scorer "Segunda-feira"

## O problema em uma frase

Os vendedores escolhem "no feeling" onde gastar o tempo: perdem tempo com vendas que não vão fechar e deixam esfriar as boas. A ferramenta diz ao vendedor **as 5 vendas da semana**, com o motivo e a próxima ação, e mostra à chefe de vendas **quanto do pipeline é real**.

## Visão geral

```mermaid
flowchart LR
    subgraph DADOS["1 · Dados (originais do desafio)"]
        A[sales_pipeline.csv<br/>vendas]
        B[accounts.csv<br/>clientes]
        C[products.csv<br/>produtos e preços]
        D[sales_teams.csv<br/>vendedores, gerentes, regiões]
    end

    subgraph MOTOR["2 · Motor (Python)"]
        E[Limpeza]
        F[Aprende com o passado]
        G[Nota de cada venda<br/>+ motivo + próxima ação]
        H[Previsão de receita<br/>do pipeline]
    end

    subgraph TELA["3 · Tela (navegador, sem instalar nada)"]
        I[Vendedor<br/>As 5 da semana]
        J[Chefe de vendas<br/>O pipeline de verdade]
        K[Como a nota funciona<br/>e a prova do teste]
    end

    subgraph TESTES["4 · Testes"]
        T1[Teste com o passado]
        T2[Teste da tela<br/>cliques automáticos]
    end

    A & B & C & D --> E --> F --> G & H --> L[(dados.js)] --> I & J & K
    F -.-> T1
    TELA -.-> T2
```

## As partes

| Parte | O que faz | Tecnologia |
|---|---|---|
| **1. Dados** | As 4 tabelas originais do desafio, sem alteração | CSV |
| **2. Motor** | Lê e limpa os dados, aprende com o passado, dá a nota de cada venda, escreve o motivo e a próxima ação, calcula a previsão de receita e grava tudo em `dados.js` | Python + pandas |
| **3. Tela** | Página estática que só lê `dados.js`. Abre com dois cliques ou por link | HTML + CSS + JavaScript |
| **4. Testes** | Conferem a nota contra o que aconteceu no passado e clicam em todos os botões da tela | Python e navegador automático |

## Decisões

- **O motor roda uma vez e grava um arquivo; a tela só lê.** Assim a página abre sem servidor e sem instalação, que é o que a chefe de vendas pediu: simples, mas funcionando.
- **Separar motor e tela.** No futuro, o motor pode ler direto do CRM em vez dos CSVs, sem mexer na tela. A tela também pode virar e-mail ou mensagem sem mexer no motor.
- **Testar sem olhar o futuro.** Para saber se a nota funciona, o motor volta a datas do passado, só enxerga o que se sabia naquele dia e depois conferimos o que aconteceu.

## Como a nota é calculada

1. **Chance pelo tempo aberta**, medida em 12 fotos do passado (só vendas com cliente).
2. **Ajuste pela relação vendedor-cliente:** 57% quando o vendedor já ganhou com o cliente, 48% sem histórico.
3. **Ajuste pelo último trimestre:** a chance caiu ao longo de 2017 e as fotos chegam com 90 dias de atraso. O motor volta 90 dias, prevê com o que se sabia lá, compara com o que fechou e corrige a chance de hoje nessa proporção (hoje: 78%).
4. **Valor esperado = chance × preço do produto.**
5. **Nota de 0 a 100** = posição do valor esperado entre as vendas abertas.
6. **As 5 da semana** = até 5 vendas de maior valor esperado de cada vendedor, com nota 20 ou mais (as de valor muito baixo ficam em "outras vendas"). As paradas (mais de 138 dias) e as sem cliente vão para as listas de limpeza.
7. **Previsão da chefe** = soma dos valores esperados das vendas vivas e com cliente.

## Prova de que funciona

`solution/testes/teste_passado.py`, 4 datas de 2017, o motor só enxerga o que se sabia em cada dia. Focando nos 20% do topo:

| Jeito de escolher | Receita dos 90 dias seguintes capturada |
|---|---|
| **Nota do Lead Scorer** | **59,2%** |
| Nota só pelo tempo aberta | 56,4% |
| Só o maior preço | 48,4% |
| Nota "óbvia" (taxa do vendedor no produto × preço) | 45,3% |
| Ao acaso | 20,0% |

O mesmo teste confere a previsão (o CRM mostrou 3 a 5 vezes o que entrou; a previsão errou entre −4% e +25%) e que o motor não espia o futuro. `solution/testes/teste_tela.mjs` clica em tudo na tela (33 conferências).

## Estrutura da pasta

```
├── README.md            entrega no formato do G4
├── solution/
│   ├── data/            os 4 CSVs originais
│   ├── analise/         scripts que olham os dados e reproduzem cada número
│   ├── motor/           o motor de nota (Python)
│   ├── app/             a tela (HTML, CSS, JS e dados.js)
│   └── testes/          teste com o passado e teste da tela
├── docs/                esta arquitetura e o resultado dos testes
└── process-log/         o registro de cada etapa
```

_Os números deste documento saem dos scripts de `solution/analise/` e `solution/testes/`._
