---
id: D6P7
project: LeadScorer
subject: Estratégia de repositório e de entrega da submissão
author: dcvr@
status: accepted
created: 2026-07-18
updated: 2026-07-18
---


# Contexto (por que a decisão é necessária)

As regras da casa determinam que cada projeto seja versionado em seu próprio repositório Git,
independente de qualquer outro. O desafio, por sua vez, exige a submissão exclusivamente por
pull request para o interior do monorepo do próprio desafio, na pasta submissions/, com a
restrição de modificar apenas arquivos ali contidos. É necessário conciliar as duas exigências.
O usuário definiu ainda o espelhamento do repositório em seu GitHub pessoal.


# Decisão (o que foi decidido)

O repositório próprio do projeto, privado por padrão, é a fonte canônica do trabalho. O
entregável é exportado, ao final, para um fork do monorepo do desafio, onde a submissão é aberta
como pull request na pasta submissions/ conforme as regras do desafio. O repositório é ainda
espelhado no GitHub pessoal do usuário. Os segredos e dados sensíveis permanecem fora do
controle de versão.


# Alternativas consideradas (o que mais foi ponderado)

- Trabalhar diretamente em um fork do monorepo do desafio: descartado por contrariar a regra da
  casa de repositório próprio e independente e por misturar o histórico do projeto com o do
  desafio.


# Consequências (o que resulta da decisão)

- O histórico do projeto permanece limpo e independente, e a submissão é uma exportação
  pontual, não o repositório de trabalho.
- A criação dos repositórios remotos, o fork e o pull request são trabalho da tarefa de entrega
  6X9H e da fase de encerramento, sob confirmação humana.
- Todo repositório remoto é criado como privado e configurado com as práticas de segurança da
  plataforma, conforme as regras da casa; a exceção do fork público do desafio decorre da
  natureza pública do monorepo de destino.
- A varredura de segredos e a manutenção de dados sensíveis fora do controle de versão são
  precondição de qualquer publicação.
- O espelho pessoal foi criado no GitHub da conta dradicchi como repositório privado, com
  Dependabot habilitado, issues, wiki e projects desativados, merge restrito a squash e exclusão
  automática de branch pós-merge. A proteção server-side do branch main, no entanto, exige
  GitHub Pro em repositórios privados e não pôde ser aplicada no plano gratuito; por decisão do
  usuário, o repositório permanece privado sem essa proteção, cujo risco é mitigado pela
  disciplina local e pelas regras anti-desastre da casa que proíbem force-push e exclusão de
  branch sem confirmação. A proteção completa fica condicionada a uma futura assinatura do
  GitHub Pro.


# Relações

- supersedes:
- superseded-by:
- related-tasks: 7K2M, 6X9H
