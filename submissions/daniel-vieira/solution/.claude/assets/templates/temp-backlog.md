---
subject: Gabarito para tabela de resumo do backlog
author: dcvr@
---


# Escopo
- Este gabarito define o layout da tabela de resumo do backlog. Cada linha corresponde a um
  arquivo de tarefa no diretório '.claude/backlog/' de cada projeto interno e é preenchida a
  partir do frontmatter desse arquivo e de sua seção '# Motivations';
- A coluna 'Projeto' exibe o nome do identificador curto do projeto;
- A coluna 'Assunto e motivação' concatena dois campos para manter a tabela estreita: o assunto
  (seguido de 3 hifens) e um breve trecho da motivação (texto simples, truncado quando
  necessário).

# Tabela

| Prioridade | Status   | ID   | Projeto         | Assunto e motivação                     |
|------------|----------|------|-----------------|-----------------------------------------|
| {priority} | {status} | {id} | {short id}      | {subject} --- {motivation excerpt}      |
