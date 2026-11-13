## Nota sobre a versão final

Estas capturas registram versões intermediárias anteriores à correção final R9 v4. Em particular, as capturas que exibem `AUTOMATIC` não representam a política final. Na versão final, nenhum ticket é roteado automaticamente; a regra R9 rebaixa esses casos para `ASSISTED`. Para o estado final, consulte `../ml/test_results_pos_ajuste.json` e `../ml/process_log_ml.md`, seção 12.

# Evidências visuais — Fase 4

Capturas feitas automaticamente com Playwright (`capture.py`) contra a preview do protótipo (Next.js + API FastAPI local, modelo v1.0.0, limiares 0,55/0,70). A resposta bruta da API de cada captura está em `capture_log.json`. Para reproduzir, suba a API e o app e rode `URL=<url> python3 capture.py`.

| Captura | Entrada (resumo) | Domínio | Categoria (conf.) | Decisão | Regra | Avaliação |
|---|---|---|---|---|---|---|
| 01 | Login/senha expirada/VPN | IT_INTERNAL | Access (0,962) | AUTOMATIC | R8_HIGH_CONFIDENCE | OK (encaminhamento; a troca de senha em si não é executada) |
| 02 | Reembolso + cobrança dupla | INDETERMINATE | — | HUMAN_REQUIRED | R2_DOMAIN_NOT_IT | Aceitável (foi para humano), mas o domínio esperado era FINANCIAL_COMMERCIAL |
| 03 | Rede inteira fora do ar | INDETERMINATE | — | HUMAN_REQUIRED | R2_DOMAIN_NOT_IT | Prioridade CRITICAL correta; o domínio deveria ser TI. Seguro, mas impreciso |
| 04 | Pedido de acesso admin | IT_INTERNAL | Hardware (0,641) | HUMAN_REQUIRED | R4_ADMIN_RIGHTS | Regra de segurança funcionou; categoria errada (esperado: Administrative rights) |
| 05 | "help" | INDETERMINATE | — | HUMAN_REQUIRED | R2_DOMAIN_NOT_IT | OK (abstenção) |
| 06 | Reserva de mesa para almoço da empresa | IT_INTERNAL | Hardware (0,748) | **AUTOMATIC** | R8_HIGH_CONFIDENCE | **FALHA**: fora do escopo e roteado automaticamente |
| 07 | Página /metricas | — | — | — | — | Renderiza |
| 08 | Página /sobre | — | — | — | — | Renderiza |

**Achado novo (não maquiado):** no teste #9 da suíte formal, a frase "company lunch" deu ASSISTED. Nesta captura, uma frase ligeiramente diferente deu AUTOMATIC com 0,748. O detector de domínio aceita como TI um texto corporativo genérico, e a confiança calibrada do classificador não protege contra entrada fora da distribuição. É a limitação mais grave do protótipo.
