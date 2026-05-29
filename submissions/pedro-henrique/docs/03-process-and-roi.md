# Processo, Matriz Humano vs IA e ROI

## 1) Fluxo operacional

- Cliente descreve problema (texto/áudio)
- IA recupera casos similares e gera sugestão
- Se resolver: registra deflexão
- Se não resolver: cria ticket priorizado para operação
- Admin acompanha métricas e ajusta operação

## 2) Matriz Humano vs IA

| Tipo de ticket | Decisão | Justificativa |
|---|---|---|
| Reset de senha / acesso básico | Automatizar com guardrail | Alto volume, baixa ambiguidade |
| Erro de VPN recorrente | Assistir humano | Necessita contexto de ambiente do usuário |
| Incidente crítico de produção | Humano primeiro | Alto risco de impacto e necessidade de decisão contextual |
| Solicitações administrativas simples | Automatizar parcialmente | Bom potencial de template + validação final |
| Casos ambíguos / baixa confiança | Escalar humano | Evita falso positivo e fricção adicional |

## 3) Modelo de ROI (MVP)

Premissas base:

- Custo hora-agente: R$ 35
- Horas recuperáveis estimadas/mês: 184h
- Potencial financeiro estimado/mês: R$ 6.440
- Deflexão alvo inicial: 15% a 25%

Cenários:

- Conservador: 15% deflexão -> ganho mensal reduzido, menor risco de erro
- Base: 20% deflexão -> equilíbrio entre impacto e segurança
- Agressivo: 25% deflexão -> maior ganho, exige monitoramento rigoroso de qualidade

## 4) Checklist de compliance executado

Data: 2026-05-28

- Branch atual: `submission/pedro-henrique-silva`
- Estrutura presente:
  - `submissions/pedro-henrique-silva/README.md`
  - `submissions/pedro-henrique-silva/solution/`
  - `submissions/pedro-henrique-silva/process-log/`
  - `submissions/pedro-henrique-silva/docs/`
- Build/Lint local:
  - `npm run lint` -> OK
  - `npm run build` -> OK

## 5) Próximos passos pós-MVP

1. Ativar autenticação Supabase completa no frontend.
2. Substituir fallback local por integração integral com base vetorial real.
3. Instrumentar observabilidade com métricas persistidas (latência, confiança, deflexão por categoria).
