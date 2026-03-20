# Prompt 013 — README atrativo da submissão

**Data:** 2026-03-20
**Agente:** Claude Code
**Executado por:** Lucas Reis

---

## Prompt enviado ao Claude Code

> Crie o arquivo submissions/lucas-reis/README.md com um README
> profissional e visualmente rico usando Markdown avançado do GitHub.
>
> **Dados reais para usar:**
> - Candidato: Lucas Reis · Challenge 001 · Data: 20 de março de 2026
> - Churn rate: 22.0% (110/500), MRR perdido $229K/ano, MRR em risco $710K
> - DevTools 31% (OR=2.36×), canal event 30.2% (OR=2.53×)
> - LightGBM AUC=0.34 — discovery de fit segmental
> - 10 HIGH risk · $12,231 MRR · 8 erros da IA corrigidos · validação 20/20
>
> **Estrutura com todos os recursos visuais do GitHub Markdown:**
> 1. Header com 4 badges shields.io
> 2. Card "Sobre mim" em tabela
> 3. Executive Summary com blockquote destacado
> 4. Métricas em tabela com emojis
> 5. Entregáveis com links
> 6. Abordagem com timeline em codeblock
> 7. Findings por seção (causa raiz, segmentação, AUC, paradoxo)
> 8. Recomendações priorizadas + O que NÃO fazer
> 9. Process Log com tabela de erros da IA
> 10. Evidências com checkboxes

---

## Arquivo gerado

`submissions/lucas-reis/README.md` — 195 linhas

### Verificação (primeiras 30 linhas)

```
# [Submission] Lucas Reis — Challenge 001 · Diagnóstico de Churn

![Challenge](https://img.shields.io/badge/Challenge-001%20Churn-6366f1?style=for-the-badge)
![Stack](https://img.shields.io/badge/Stack-Python%20%7C%20DuckDB%20%7C%20LightGBM-0ea5e9?style=for-the-badge)
![Status](https://img.shields.io/badge/Status-Submitted-22c55e?style=for-the-badge)
![AUC](https://img.shields.io/badge/AUC-0.34%20(Discovery)-f97316?style=for-the-badge)
```

4 badges confirmados: Challenge (roxo), Stack (azul), Status (verde), AUC (laranja).

---

## Decisões editoriais

1. **URL do dashboard** — mantido como link relativo `solution/dashboard/index.html`
   (sem URL Vercel, que não existe no contexto local). Um deploy futuro substituiria o link.

2. **Tabela de erros da IA** — 8 erros documentados, do mais técnico (schema)
   ao mais conceitual (AUC como discovery). Ordem intencional: da causa menor
   para a descoberta principal.

3. **Seção "O que NÃO fazer"** — mantida como blockquote com `>` para destacar
   visualmente que são contraindicações baseadas em dados, não opinião.

4. **Timeline em codeblock** — uso de bloco de código para a sequência de steps
   funciona como separador visual e é renderizado com fonte mono no GitHub.

5. **"Bug do 60.9%" na tabela de findings** — mantida a nota `⚠️ era 60.9%`
   para mostrar transparência sobre a correção, não esconder o erro.
