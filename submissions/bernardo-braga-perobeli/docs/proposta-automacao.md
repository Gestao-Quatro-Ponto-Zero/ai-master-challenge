# Proposta de Automação com IA — G4 IA: Inteligência de Suporte

**Data:** 11 de Março 2026
**Autor:** Bernardo Braga Perobeli

---

## Resumo

A operação de suporte processa ~30.000 tickets/ano com satisfação de 3.0/5.0 e 67% de backlog. Com a implementação de LLM (Gemini 3.1 Flash Lite) + RAG (Gemini Embedding 2) sobre uma base de ~56.500 tickets históricos, estimamos **automatizar ~28% dos tickets** — reduzindo o tempo médio de atendimento de 7.7h para ~5.5h por canal.

---

## Situação Atual vs Projeção

| Indicador | Atual | Com IA |
|-----------|-------|--------|
| Satisfação do cliente | 3.0/5.0 | 4.0+/5.0 |
| Tempo médio de atendimento | 7.7h | ~5.4-5.7h (por canal) |
| Backlog sem resolução | 67% | < 20% |
| Tickets resolvidos por IA | 0% | ~28% |

---

## Como Funciona

Cada ticket que entra no sistema passa por um pipeline automático de IA:

**1. Análise contextual** — O ticket é comparado com ~56.500 casos históricos (~8.500 operacionais + ~48.000 IT) via busca semântica (Gemini Embedding 2). Os 5 casos mais similares já resolvidos são recuperados para dar contexto ao LLM. Se um ticket aberto tiver similaridade **> 90%**, é sinalizado como duplicata.

**2. Processamento inteligente** — O LLM (Gemini 3.1 Flash Lite) executa em sequência: classifica em 8 categorias, avalia severidade, resume o problema e gera 3 soluções baseadas nos casos similares. Custo: **~R$ 0,035 por ticket**.

**3. Triagem e ação automática:**

| Nível | O que a IA faz | Papel do humano |
|-------|---------------|-----------------|
| **Baixo** | Responde e fecha o ticket automaticamente | Nenhum |
| **Médio** | Responde e notifica um agente para acompanhar | Monitora (human-in-the-loop) |
| **Crítico** | Resume + sugere 3 soluções, atribui ao agente com menor carga | Resolve com apoio da IA |

**4. Governança** — Alertas automáticos para gestores quando o volume de tickets médios ou críticos excede limites. Duas interfaces separadas: painel operacional (agente) e painel de gestão (diretor/gestor).

```
Ticket entra (email / chat / telefone / webhook)
    │
    ▼
[Gemini Embedding 2] → Busca 5 casos similares + verifica duplicatas (> 90%)
    │
    ▼
[Gemini 3.1 Flash Lite] → Classifica → Resume → Avalia severidade → Gera 3 soluções
    │
    ▼
┌───────────┬────────────┬──────────────┐
│   BAIXO   │   MÉDIO    │   CRÍTICO    │
│ Auto-     │ IA + monit.│ Humano +     │
│ resolve   │ por agente │ sugestões IA │
└───────────┴────────────┴──────────────┘
```

---

## O que NÃO Automatizar

| Cenário | Motivo |
|---------|--------|
| Falhas de segurança ou sistemas fora do ar | Julgamento humano imediato |
| Contexto emocional elevado | Empatia humana é insubstituível |
| Ambiguidade ou múltiplos problemas | IA pode interpretar incorretamente |
| Impacto financeiro direto | Requer autorização formal |

**A IA atua como copiloto do agente, nunca como substituto para casos sensíveis.**

---

## Capacidades da Ferramenta

| Capacidade | Detalhe |
|-----------|---------|
| IA Generativa (Gemini 3.1 Flash Lite) | Respostas contextualizadas por LLM, não templates fixos |
| Base RAG (~56.500 tickets) | Respostas fundamentadas em casos reais resolvidos |
| Detecção de duplicatas | Similaridade semântica > 90% elimina retrabalho |
| Auto-assignment | Distribui tickets ao agente com menor carga |
| Pronto para produção | Upload de dados (CSV/XLSX), webhook para CRMs, gestão de usuários |
| Duas interfaces | Agente (operação) e gestor (governança e métricas) |
| Alertas em tempo real | Notifica gestores quando volume excede limites |
| Fallback robusto | Se Gemini indisponível, opera com DeBERTa + templates |
| Stack | FastAPI + Next.js 14 + JWT + Gemini Embedding 2 (768d) |
