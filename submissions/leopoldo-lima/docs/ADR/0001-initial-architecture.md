# ADR-0001 — Arquitetura inicial orientada a CRPs e submissão

## Status
Aceito

## Contexto
O repositório precisa sustentar execução incremental por CRPs com rastreabilidade forte de processo, uso de IA e evidências de validação para submissão via PR.

## Decisão
Adotar uma arquitetura documental-operacional com:
- CRPs como unidade formal de mudança
- process log obrigatório por CRP
- estrutura explícita de evidências em `artifacts/process-log/`
- governança de submissão documentada em `docs/`

## Consequências
### Positivas
- melhora auditabilidade para o challenge
- reduz risco de output genérico
- facilita revisão por avaliador externo

### Negativas
- aumenta disciplina operacional exigida do time
- demanda manutenção contínua de logs e evidências

## Guardrails
- nenhum CRP fecha sem process log e verificação humana
- uso de IA deve ser registrado com correções aplicadas
- material de submissão deve refletir estado real do repositório
