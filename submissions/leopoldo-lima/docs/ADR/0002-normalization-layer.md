# ADR-0002 — Camada de normalização semântica separada do raw

## Status
Aceito

## Contexto
Foi identificada divergência real de join de produto (`GTXPro` no pipeline vs `GTX Pro` no catálogo). Corrigir no raw esconderia o problema e quebraria auditabilidade.

## Decisão
Criar camada de normalização separada:
- mapa versionado em `config/normalization-map.json`
- aplicação em `src/normalization/mapper.py`
- rastreabilidade de `original -> canonical` com `strategy` e `risk`

## Consequências
### Positivas
- preserva o raw como fonte da verdade
- explicita correção semântica auditável
- melhora consistência para joins e regras posteriores

### Negativas
- adiciona manutenção de mapa de aliases
- exige testes para evitar regressão silenciosa

## Guardrails
- não editar CSVs para “corrigir” alias
- qualquer novo alias exige teste e atualização documental
