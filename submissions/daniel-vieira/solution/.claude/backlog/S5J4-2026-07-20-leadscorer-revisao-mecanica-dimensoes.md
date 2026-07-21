---
id: S5J4
parent:
project: leadscorer
subject: Reconciliacao documental da dimensao do agente (Especializacao) e dos achados da revisao
author: dcvr@
priority: high
status: done
created: 2026-07-20
updated: 2026-07-20
---


# Descrição (o que será feito)

Tratar, na camada de documentacao, os achados registrados em
'docs/revisao-dimensoes-scoring.md'. Esta e a Parte 1 do tratamento, estritamente documental: a
propagacao ao codigo, ao schema, aos testes, aos exemplos HTML e as telas de producao e diferida
para a Parte 2 (tarefa X7F2). O escopo cobre: renomear a dimensao do agente, hoje dispersa entre
"persuasao", "aderencia", "share de Won" e "capacidade demonstrada", para o nome canonico
unico "Especializacao" (rotulo curto) e "Especializacao do agente" (nome longo), em varredura
completa da documentacao (base de conhecimento, ADR e tarefas); reenquadrar o achado 1 na direcao
correta; registrar a nota do achado 2 (ancora neutra do momentum); registrar o diferimento
consciente da Opcao B; e criar o ADR G5W2.


# Motivações (por que será feito)

A revisao da mecanica, em 'docs/revisao-dimensoes-scoring.md', apontou tres achados. Ao reunir a
evidencia para o achado 1, a EDA ('docs/analise-exploratoria.md', linhas 62-83) mostrou que o win
rate e ruido e que a unica alavanca robusta do agente e a especializacao por produto, medida por
contagem de Won, o que o codigo ja faz. A recomendacao inicial de computar uma taxa foi retirada
por contrariar a evidencia. O achado 1 deixa de ser defeito de codigo e passa a ser defeito de
nomenclatura: os nomes dispersos, e em especial "persuasao" e "share", destoam do que a mecanica
mede. A decisao do usuario e a Opcao A: manter a contagem, corrigir o nome, rejeitar o win
rate e diferir a Opcao B (participacao no produto) por carater MVP. Como outro agente constroi em
paralelo as telas de producao do app, a alteracao do codigo e das interfaces e segregada
na Parte 2 para evitar conflito e confusao.


# Recursos e dados necessários

- O relatorio de revisao em 'docs/revisao-dimensoes-scoring.md', fonte dos achados;
- A EDA em 'docs/analise-exploratoria.md', que fundamenta a contagem e rejeita o win rate;
- A metodologia em 'docs/metodologia-scoring.md' (ADR C4X9) e a validacao em
  'docs/validacao-scoring.md';
- Os ADR B7Q3 (personalizacao por agente) e C4X9 (metodologia), tocados na varredura, e o novo
  ADR G5W2 (dimensao do agente: Especializacao);
- O inventario de ocorrencias do nome da dimensao em documentacao e em codigo, levantado na
  sessao S5J4-2026-07-20-1.


# Plano de trabalho (como será feito)

1. Renomear a dimensao para "Especializacao"/"Especializacao do agente" em 'README.md',
   'docs/metodologia-scoring.md', 'docs/analise-exploratoria.md', 'docs/validacao-scoring.md' e
   'docs/concepcao-inicial.md', preservando os falsos positivos (aderencia a design system, a
   stack, a std-shell) e marcando as referencias a simbolos de codigo ainda nao renomeados;
2. Reescrever o achado 1 em 'docs/revisao-dimensoes-scoring.md' na direcao correta, atualizar a
   tabela-sintese e ajustar os achados 2 e 3 ao novo nome e ao split de partes;
3. Corrigir a mecanica da dimensao 4 na metodologia (de "share de Won" para contagem), registrar
   a nota do achado 2 e o diferimento consciente da Opcao B;
4. Varredura completa nos registros: renomear o termo nos ADR B7Q3 e C4X9, atualizar
   '_adr-index.md' e renomear as referencias cruzadas nas tarefas 3RJ8 e 5T6Q;
5. Criar o ADR G5W2 (dimensao do agente: Especializacao por contagem, win rate rejeitado, Opcao B
   diferida) e cria-lo no indice;
6. Criar a tarefa X7F2 (Parte 2, diferida, blocked-by P3W7) e atualizar o worklog da sessao.


# Riscos e ressalvas

- Enquanto a Parte 2 nao e executada, a documentacao usa "Especializacao" e o codigo usa
  "adherence"; as referencias da documentacao aos simbolos de codigo atuais devem ficar marcadas
  como sujeitas a renomeacao na Parte 2, para nao induzir a contradicao doc-codigo;
- A varredura completa toca corpos de ADR e de tarefas ja concluidas ou canceladas; o cuidado e
  preservar o sentido historico e alterar apenas o termo da dimensao, nao os fatos registrados;
- Os falsos positivos de "aderencia" (design system, stack, std-shell) nao podem ser renomeados.


# Dependências

- blocks:
- blocked-by:


# Definição de pronto

- A dimensao do agente e nomeada de forma unica e coerente ("Especializacao"/"Especializacao do
  agente") em toda a documentacao viva (README, base de conhecimento) e nos registros varridos
  (ADR B7Q3 e C4X9, '_adr-index.md', tarefas 3RJ8 e 5T6Q), sem residuo de "persuasao", "share de
  Won" ou "aderencia" designando a dimensao, e preservados os falsos positivos;
- O achado 1 em 'docs/revisao-dimensoes-scoring.md' esta reenquadrado como defeito de
  nomenclatura, com a recomendacao de taxa retirada e a tabela-sintese atualizada;
- A metodologia descreve a mecanica da dimensao 4 como contagem, registra a nota do achado 2 e o
  diferimento da Opcao B;
- O ADR G5W2 esta criado e indexado, com cross-link a C4X9 e B7Q3;
- A tarefa X7F2 (Parte 2) esta registrada como diferida (blocked-by P3W7);
- A verificacao editorial passa: nenhuma linha dos arquivos tocados excede 96 colunas (contagem
  por caractere) e as referencias cruzadas estao coerentes.
