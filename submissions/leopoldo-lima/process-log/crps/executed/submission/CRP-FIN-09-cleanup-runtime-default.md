# CRP-FIN-09 — Limpeza: runtime padrão inequivocamente real

## Objetivo
Eliminar qualquer ambiguidade sobre o modo padrão de execução.

## Fazer
- garantir que o modo default usa dados reais
- deixar modo mock somente sob configuração explícita
- revisar mensagens, README e código para que isso fique inequívoco
- remover fallback silencioso para demo, se existir

## Impacto na submissão
Ataca diretamente o requisito de uso dos dados reais do dataset.

## Evidências obrigatórias
- prova de que o runtime padrão usa dataset real
- prova de que mock depende de ativação explícita
- trecho do README atualizado

## Atualizações obrigatórias de process log
Registrar:
- ambiguidade anterior
- revisão do default runtime
- como foi validado o caminho principal

## Definition of Done
- default = dados reais
- mock = explícito e isolado
- README e código contam a mesma história
