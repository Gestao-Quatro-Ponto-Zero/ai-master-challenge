# Classificador de categoria (Dataset 2)

Base: 47.837 textos. Treino 38.269 (80%) e teste 9.568 (20%), separados de forma estratificada antes de qualquer treino.

## 1. Comparação de modelos (validação cruzada de 5 partes, só no treino)

O vetorizador de texto fica dentro de cada parte, então nenhum modelo vê o vocabulário da parte em que é avaliado.

| Modelo | Acurácia | F1 macro (média das 8 categorias) | Tempo |
|---|---|---|---|
| Linha de base (sempre a categoria mais comum) | 28.5% | 5.5% (±0.0) | 3 s |
| Naive Bayes complementar | 80.8% | 79.5% (±0.7) | 5 s |
| Regressão logística | 86.0% | 85.9% (±0.5) | 44 s |
| Regressão logística com peso por categoria | 86.4% | 86.5% (±0.5) | 41 s |
| SVM linear | 86.1% | 86.1% (±0.4) | 7 s |

Escolhido pelo maior F1 macro: **Regressão logística com peso por categoria**.

## 2. Resultado no teste separado

Acurácia 87.0%, F1 macro 87.1% (linha de base: acurácia 28.5%).

Precisão: dos tickets que o modelo colocou na categoria, quantos eram dela. Cobertura: dos tickets da categoria, quantos o modelo encontrou.

| Categoria | Tickets no teste | Precisão | Cobertura | F1 |
|---|---|---|---|---|
| Hardware | 2724 | 85.7% | 85.5% | 85.6% |
| Suporte de RH | 2183 | 88.7% | 86.4% | 87.5% |
| Acesso | 1425 | 90.0% | 90.0% | 90.0% |
| Diversos | 1412 | 82.7% | 86.0% | 84.3% |
| Armazenamento | 555 | 90.3% | 90.8% | 90.6% |
| Compra | 493 | 94.6% | 89.5% | 92.0% |
| Projeto interno | 424 | 84.9% | 89.9% | 87.3% |
| Direitos de administrador | 352 | 79.6% | 79.8% | 79.7% |

## 3. Onde o modelo confunde (matriz de confusão do teste)

Linha = categoria real, coluna = categoria prevista, valor = % da linha.

| Real \ Prevista | Hardware | Suporte de R | Acesso | Diversos | Armazenament | Compra | Projeto inte | Direitos de  |
|---|---|---|---|---|---|---|---|---|
| Hardware | 85 | 4 | 3 | 4 | 0 | 1 | 1 | 2 |
| Suporte de RH | 6 | 86 | 2 | 3 | 1 | 0 | 1 | 0 |
| Acesso | 4 | 2 | 90 | 2 | 0 | 0 | 1 | 1 |
| Diversos | 6 | 4 | 2 | 86 | 1 | 0 | 1 | 0 |
| Armazenamento | 4 | 2 | 1 | 2 | 91 | 0 | 0 | 1 |
| Compra | 6 | 1 | 0 | 2 | 0 | 89 | 0 | 1 |
| Projeto interno | 4 | 3 | 0 | 2 | 0 | 0 | 90 | 0 |
| Direitos de administrador | 15 | 2 | 1 | 2 | 0 | 0 | 0 | 80 |

Maiores confusões:

- Suporte de RH previsto como Hardware: 135 tickets (6.2% de Suporte de RH).
- Hardware previsto como Diversos: 116 tickets (4.3% de Hardware).
- Hardware previsto como Suporte de RH: 112 tickets (4.1% de Hardware).
- Diversos previsto como Hardware: 81 tickets (5.7% de Diversos).
- Hardware previsto como Acesso: 73 tickets (2.7% de Hardware).

## 4. Compra com e sem o formulário automático

| Recorte de Compra | Tickets no teste | Cobertura (acerto) |
|---|---|---|
| Todos | 493 | 89.5% |
| Só o formulário "new purchase po" | 246 | 99.6% |
| Sem o formulário | 247 | 79.4% |

## 5. Confiança: quando o modelo decide sozinho e quando passa para uma pessoa

Se o modelo só classificar sozinho quando a confiança passar do limite, o resto vai para uma pessoa. A tabela mostra o acerto nos tickets que ele decide e quantos sobram para a pessoa.

| Limite de confiança | Decide sozinho | Acerto quando decide | Vai para uma pessoa |
|---|---|---|---|
| 0.0 | 100.0% | 87.0% | 0.0% |
| 0.5 | 91.6% | 90.3% | 8.4% |
| 0.6 | 84.7% | 92.6% | 15.3% |
| 0.7 | 77.0% | 94.8% | 23.0% |
| 0.8 | 68.4% | 96.4% | 31.6% |
| 0.9 | 57.4% | 98.1% | 42.6% |
## 6. Leitura e limites

- O modelo acerta 87,0% no teste contra 28,5% da linha de base, e todas as 8 categorias ficam entre 79,7% e 92,0% de F1.
- A categoria mais fraca é Direitos de administrador: 15% dos casos reais vão para Hardware.
- O acerto de Compra depende do formulário: 99,6% no formulário automático e 79,4% sem ele.
- A curva de confiança foi lida no próprio teste. Ela descreve o modelo, mas o limite de operação deve ser fixado
  com tickets novos da operação, não escolhido aqui.
- O Dataset 2 é de TI interna. O classificador prova o método (texto livre para categoria, com confiança e
  encaminhamento para pessoa), não o acerto nos 5 tipos do Dataset 1, que não têm texto real para treinar.
