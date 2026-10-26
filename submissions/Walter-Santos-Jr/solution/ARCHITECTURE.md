# Arquitetura técnica — RC4

## Componentes

```text
Usuário / Navegador
  └── static/index.html + static/style.css + static/app.js
        └── HTTP JSON (localhost:8050)
              └── app.py (ThreadingHTTPServer; validações e APIs)
                    ├── data/opportunities.csv (snapshot de oportunidades)
                    ├── data/sales_pipeline_history.csv (histórico)
                    ├── data/historical_dimensions.csv (dimensões)
                    └── data/workspace.sqlite3 (estado operacional)
```

## Domínios funcionais

- **Head:** inteligência executiva e segmentação regional, gerencial e setorial.
- **Manager:** inteligência gerencial e análise de vendedores, com escopo por persona.
- **Seller:** pipeline, detalhe da oportunidade, qualificação, execução, Rework e encerramento.
- **Rework:** jobs com estados e eventos, resolução condicionada à evidência estruturada.
- **Deal Closure:** persistência Won/Lost e reconciliação com a base histórica.

## Segurança

O modo demonstração possui identidade por persona e restrições de escopo em endpoints, mas não substitui autenticação e autorização corporativas. Não utilizar em produção sem hardening, autenticação real, proteção CSRF, observabilidade e revisão de privacidade.

## Dados e métricas

O preço de catálogo não equivale ao valor negociado; este não equivale à receita faturada. A pontuação é heurística, não probabilidade estatisticamente calibrada. Os dados históricos não são apresentados como transações em tempo real.

## Rastreabilidade

A justificativa metodológica BIOS e as análises estatísticas devem ser documentadas a partir do enunciado oficial e das evidências originais do desenvolvimento, sem reconstruir resultados como se fossem históricos.
