# Data Audit: Challenge 002

## Resumo executivo

O Dataset 1 é a base operacional disponível da empresa fictícia e contém **8,469 tickets**. O volume de aproximadamente 30 mil por ano permanece como contexto do brief, não como contagem do arquivo. A base permite analisar filas, status, textos e sinais de cuidado, mas não possui o horário de abertura. `First Response Time` e `Time to Resolution` são timestamps, não durações. Entre 2,769 tickets com ambos os campos, **49.3%** têm resolução anterior à primeira resposta. Portanto, FRT, TTR, desperdício de horas e ROI observado não podem ser calculados de forma válida.

O Dataset 2 contém **47,837 tickets** em oito classes e pode sustentar uma prova técnica de classificação, desde que documentos duplicados sejam mantidos no mesmo split. Há 0 linhas pertencentes a textos duplicados e 0 documentos normalizados com rótulos conflitantes.

## Dataset 1: suporte ao cliente

- Linhas: **8,469**
- Colunas: **17**
- `Ticket ID` único: **True**
- Tipos observados: **5**, incluindo categorias não resumidas no brief.
- CSAT disponível em **2,769** linhas, todas sujeitas ao filtro de elegibilidade por status.
- Datas observadas em `First Response Time`: **2023-05-31, 2023-06-01, 2023-06-02**
- Datas observadas em `Time to Resolution`: **2023-05-31, 2023-06-01, 2023-06-02**
- Pares temporalmente inválidos: **1,365 de 2,769**
- Descrições com placeholder de template: **8,469**
- Descrições distintas: **8,077**
- Associação entre `Ticket Subject` e `Ticket Type`: **V de Cramér = 0.034** (`p = 0.981`)
- Relatos explícitos de contatos repetidos sem solução: **460**, sendo **152 abertos**, **156 pendentes** e **152 encerrados**

### Foco no cliente

`Ticket Description` é o campo que preserva a voz do cliente e, por isso, deve ser lido antes de qualquer sugestão automática. As **8,469 descrições** contêm placeholder de template e trechos ruidosos, mas ainda revelam situações operacionais do exercício. O principal sinal é o grupo de **460 clientes** que relata contatos repetidos sem solução, inclusive 152 casos marcados como encerrados.

O protótipo usa regras explícitas e conservadoras para reconhecer reincidência, dano financeiro, cancelamento, risco legal, segurança, privacidade ou forte insatisfação. Qualquer sinal encaminha o caso para uma pessoa. Na base fornecida, o gate sinaliza casos para inspeção humana; sua taxa de erro deve ser revisada durante o piloto da empresa fictícia.

### Consequência analítica

1. Não calcular FRT, TTR ou touch time.
2. Não chamar diferenças de CSAT de causais.
3. Usar `Ticket Subject`, `Ticket Type` e `Ticket Priority` como campos operacionais existentes, sem deixar que anulem sinais encontrados na mensagem.
4. Priorizar a revisão dos relatos de contato repetido sem solução, inclusive os marcados como encerrados.
5. Tratar qualquer ROI como cenário parametrizado, nunca como economia observada.

## Dataset 2: classificação de tickets de TI

- Linhas: **47,837**
- Classes: **8**
- Maior classe: **Hardware (13,617)**
- Menor classe: **Administrative rights (1,760)**
- Linhas em grupos de textos duplicados: **0**
- Documentos com rótulos conflitantes: **0**
- Comprimento mediano do texto: **175 caracteres**

### Consequência analítica

1. Separar grupos de textos normalizados entre treino e teste para evitar leakage.
2. Reportar macro-F1, recall por classe, matriz de confusão e cobertura versus precisão.
3. Não transferir a taxonomia de TI diretamente para o Dataset 1.
4. Apresentar o classificador como prova técnica para a fila de TI, não como classificador da fila de clientes.

## Integridade e privacidade

- Hash Dataset 1: `b06a9cde84da65db388bd964d75f88ee1eed96607cf75d0c35f09c3f11bf8bea`
- Hash Dataset 2: `044fdace33fa564e1e60453f2941dafc95539c99878b0d32746950394b9dd4d4`
- Nenhum nome, email ou texto bruto de cliente é exportado nos artefatos analíticos.

## Veredito

**Dataset 1: uso restrito.** Inadequado para medir tempos operacionais ou ROI observado.

**Dataset 2: utilizável com controles.** Adequado para experimento de classificação com split agrupado, métricas por classe, calibração e abstenção.
