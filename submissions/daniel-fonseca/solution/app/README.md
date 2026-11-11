# App — Triagem Inteligente (Case AI Master, challenge 002)

Next.js 16 (App Router, Cache Components) + Tailwind 4 + shadcn/ui (base) + Recharts. Deploy na Vercel (região `gru1`).
Especificação: [`docs/prd/01-prd.md`](../../docs/prd/01-prd.md) · decisões: ADR-0014.

## Estrutura
| Pasta | Dono | Conteúdo |
|---|---|---|
| `app/(painel)/`, `app/como-foi-feito/`, `components/painel/`, `components/metodo/` | Frente A | Painel (Diagnóstico · ROI · Operação) e Como foi feito |
| `app/console/`, `components/console/`, `app/api/triage`, `app/api/hitl`, `app/api/demo` | Frente B | Console (Triagem · Fila · Caixa) e rotas de API |
| `components/shell/`, `components/shared/`, `components/ui/`, `lib/` | Base | Shell, tokens Órbita, componentes e contratos compartilhados |

## Regras
- O navegador nunca recebe chave: Supabase só no servidor (`lib/supabase.ts`, service role), n8n só pelas rotas `/api/*` com `X-Webhook-Secret`.
- Toda rota `/api/*` aplica `checkLimit()` e grava `logUsage()` (`lib/usage.ts`, PRD §8). Abuso: o monitoramento só alerta (PRD §8.1).
- Interface com os nomes dos caminhos: Resposta automática · Revisão humana · Somente humano (`lib/paths.ts`).
- Um único número dourado por tela (`KpiCard protagonist`). Texto afirmativo, sem antagonismos nem analogias.

## Rodar localmente
```bash
cp ../../.env .env.local   # ou crie com as variáveis de .env.example
npm install
npm run dev
```
