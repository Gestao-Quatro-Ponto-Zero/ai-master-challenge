---
id: 2H5K
parent:
project: LeadScorer
subject: Aquisição e verificação dos arquivos CSV do dataset CRM
author: dcvr@
priority: high
status: done
created: 2026-07-18
updated: 2026-07-18
---


# Descrição (o que será feito)

Obter os quatro arquivos CSV do dataset CRM Sales Predictive Analytics (accounts, products,
sales_teams, sales_pipeline) do Kaggle, depositá-los no diretório 'data/' (fora do controle de
versão) e verificar a sua integridade básica: presença dos arquivos, cabeçalhos esperados e
contagem de registros na ordem de magnitude documentada.


# Motivações (por que será feito)

A fase de modelagem opera diretamente sobre os arquivos CSV. A disponibilidade verificada do
dataset real é precondição das tarefas de scoring e distribuição. Esta tarefa foi separada da
ingestão em banco (9P4D) porque a modelagem não depende do PostgreSQL.


# Recursos e dados necessários

- Dataset CRM Sales Predictive Analytics no Kaggle, licença CC0; o download requer autenticação
  do usuário no Kaggle;
- Utilitário de leitura de CSV do sistema (read-csv-file) para a verificação de cabeçalhos e
  contagens.


# Plano de trabalho (como será feito)

- Obter os quatro CSV para 'data/' pelo método de aquisição escolhido pelo usuário;
- Implementar uma rotina de verificação que, para cada arquivo, leia o cabeçalho e conte os
  registros e compare com o esperado (accounts com cerca de 85, products com 7, sales_teams com
  35, sales_pipeline com cerca de 8.800);
- Executar a verificação e registrar o resultado; documentar o método de aquisição para o setup
  reprodutível.


# Riscos e ressalvas

- O download do Kaggle exige credencial do usuário; a ausência de um método reprodutível de
  aquisição afeta a reprodutibilidade do setup exigida pelo desafio;
- Os arquivos de dados não são versionados; a verificação deve ser um script executável sob
  demanda, não um teste que dependa dos dados no controle de versão.


# Dependências

- blocks: 1J8R
- blocked-by: 7K2M


# Definição de pronto

Os quatro arquivos CSV estão presentes em 'data/', a rotina de verificação lê cada um sem erro,
os cabeçalhos correspondem exatamente às colunas esperadas e as contagens de registros igualam
os valores canônicos confirmados (accounts com 85, products com 7, sales_teams com 35 e
sales_pipeline com 8.800), com o resultado registrado no worklog. A rotina é fail-closed:
avalia todos os arquivos e encerra com estado não nulo se algum divergir ou estiver ausente.
