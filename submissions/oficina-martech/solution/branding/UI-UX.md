# Foco — UI/UX Design System

> Princípio-mãe: **toda tela responde "o que eu faço agora?"** — não "como está o pipeline?". Decisão > exibição.

## 1. Princípios de usabilidade (e como aplicamos)

| Princípio | Aplicação no Foco |
|-----------|-------------------|
| **Decisão em 3 segundos** | Score grande + badge colorido + ação. Lê de relance. |
| **Progressive disclosure** | Lista priorizada primeiro; detalhe/breakdown só ao clicar. |
| **Reconhecimento, não memória** | Cor + ícone + rótulo de prioridade — sem decorar nada. |
| **Carga cognitiva mínima** | "Foco do Dia" mostra os **top 5-7** must-acts, não 2.089 linhas. |
| **Recuperação de erro** | Filtros reversíveis, estados vazios amigáveis, nada destrutivo. |
| **Confiança/transparência** | Todo score abre o **porquê** (breakdown) — nada de caixa-preta. |
| **Acessibilidade** | Cor nunca sozinha (ícone+texto); contraste AA; navegação por teclado. |

## 2. Estrutura de navegação

```
┌ Sidebar ──────────┐   3 visões por perfil, 1 clique:
│ 🎯 Foco            │   • Foco do Dia   (vendedor)   ← default
│ ─────────         │   • Time          (manager)
│ ▸ Foco do Dia     │   • Saúde         (RevOps)
│ ▸ Time            │
│ ▸ Saúde           │   Filtros globais: Vendedor · Manager · Regional
│ ─────────         │   (o bônus do brief — sempre acessível no topo)
│ Filtros: [▼]      │
└───────────────────┘
```

## 3. Telas (wireframes)

### 3.1 Foco do Dia (tela principal — vendedor)
```
┌──────────────────────────────────────────────────────────────┐
│ 🎯 Foco        O que fechar primeiro.        [Vendedor: Anna ▼]│
├──────────────────────────────────────────────────────────────┤
│ Bom dia, Anna. Você tem 6 deals merecendo atenção hoje.       │
│ [ 3 🔥 Foco Agora ]  [ 8 ⭐ Trabalhar ]  [ 12 ⏳ Baixa ]      │ ← KPIs clicáveis (filtram)
├──────────────────────────────────────────────────────────────┤
│ ┌── 🔥 FOCO AGORA ───────────────────────────────────────┐    │
│ │  84   GTX Pro · Cancity                       [ Ver ▸ ] │    │ ← score 32px, tabular
│ │  ███  Você fecha 70% · R$3.150 esperado · 64d (esfriando)│   │
│ │       ▸ Ação: priorizar contato hoje                    │    │
│ ├────────────────────────────────────────────────────────┤    │
│ │  79   MG Special · Isdom                      [ Ver ▸ ] │    │
│ │  ██▊  Alta probabilidade · valor alto                   │    │
│ └────────────────────────────────────────────────────────┘    │
│ ┌── ⭐ TRABALHAR ────────────────────────────────────────┐    │
│ │  61   GTX Basic · Konex ...                             │    │
│ └────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────┘
```
- Agrupado por tier (Foco Agora no topo). Cada card: **score grande**, deal+conta, 1 linha de motivo, ação, botão Ver.
- Barra de progresso fina (`███`) reforça o score visualmente.

### 3.2 Detalhe do deal (drawer / expander) — o "porquê"
```
┌ GTX Pro · Cancity ─────────────────────────────  84 · Foco Agora 🔥 ┐
│ Por que esse score?                                                 │
│  ● Win-rate do vendedor    70%   peso 55%   +46   🟢 seu trunfo     │
│  ● Valor esperado          R$3.150 peso 30% +25   🟢 alto           │
│  ● Urgência (64 dias)      >57d  peso 15%   −7    🟠 esfriando      │
│  ────────────────────────────────────────────────                  │
│  Ação recomendada:  Priorizar contato hoje — provável e esfriando.  │
│  Contexto: Anna fecha 70% em deals desse perfil (152 históricos).   │
└────────────────────────────────────────────────────────────────────┘
```
Fator a fator: valor, peso, pontos, cor do sinal e frase. É a explainability que ganha o critério.

### 3.3 Time (manager)
```
[ Manager: Dustin ▼ ]   Time: 5 vendedores · 41 deals em Foco Agora
┌ Vendedor ─────── Foco Agora ─ Pipeline esperado ─ Esfriando ─┐
│ Anna Snelling        3            R$ 12.400          1        │ ← ordenável
│ Cecily Lampkin       2            R$  8.900          0        │
│ ...                                                          │
└──────────────────────────────────────────────────────────────┘
Insight: 2 vendedores concentram 60% do valor esperado em Foco Agora.
```
Orientado a decisão do manager: onde está o valor e quem precisa de apoio — não contagem de volume.

### 3.4 Saúde (RevOps)
```
Qualidade do pipeline
[ ⚠ 1.425 deals (68% dos abertos) sem conta atribuída ]  ← maior bloqueio
[ Ciclo médio de fechamento: 57 dias ]
[ 2.089 deals abertos · esfriando na janela 88–138d ]
▸ Recomendação: tornar 'conta' obrigatório no CRM (impacta 68% dos abertos).
```
Transforma higiene de dados em ação executiva.

## 4. Componentes (biblioteca)

| Componente | Spec |
|------------|------|
| **Score badge** | número tabular 32px + barra fina; cor = tier |
| **Tier chip** | pill: ícone + rótulo, fundo `*-50`, texto `*-600` |
| **Deal card** | surface, border 1px `#E2E8F0`, radius 12px, padding 16, hover: sombra leve + borda `brand` |
| **Factor row** | ícone de sinal (🟢/🟠/🔴) + label + valor + pontos |
| **KPI pill** | contagem + ícone, clicável (vira filtro) |
| **Filtro** | select no topo + sidebar; mostra contagem do recorte |

Tokens centralizados em `app/theme.py` (espelha `BRANDING.md` §3) — uma fonte de verdade para cor/spacing/radius.

## 5. Estados (não esquecer — onde apps amadores falham)

| Estado | Tratamento |
|--------|------------|
| **Vazio** (sem Foco Agora) | "Nenhum deal em Foco Agora. Bom trabalho. 👏" + mostra Trabalhar |
| **Carregando** | skeleton dos cards (não spinner solto) |
| **Sem dado** (Prospecting sem engage) | chip "Ainda não engajado" em vez de erro/0 |
| **Filtro sem resultado** | "Nenhum deal para esse recorte" + botão limpar filtro |
| **Primeiro acesso** | banner de dica (ver §6) |

## 6. Dicas in-app (onboarding + tooltips)

- **Banner de boas-vindas (1ª vez):** *"💡 Comece pelo Foco Agora — são os deals com maior chance × valor esfriando. Clique em Ver para entender o porquê de cada score."*
- **Tooltip no score:** "Combina sua taxa de fechamento, o valor esperado e há quanto tempo o deal está aberto."
- **Tooltip em 'esfriando':** "Deals costumam fechar em ~57 dias. Acima disso, a chance cai."
- **Dica no filtro de manager:** "Veja onde está o valor do time e quem precisa de apoio."
- Dicas dispensáveis e não-repetitivas (não atrapalham o uso diário).

## 7. Responsividade e performance
- Layout em coluna única adaptável (Streamlit `use_container_width`); cards empilham bem em telas menores.
- Score pré-calculado uma vez por carga (cache) — interação de filtro é instantânea.

## 8. Checklist de UX (antes de "pronto")
- [ ] Tela inicial responde "o que faço hoje?" em 3s
- [ ] Todo score tem o porquê acessível em 1 clique
- [ ] Cor sempre com ícone+texto (acessível)
- [ ] Todos os 5 estados tratados (vazio/carregando/sem dado/sem filtro/onboarding)
- [ ] Filtros vendedor/manager/regional funcionando
- [ ] Microcopy sem jargão técnico
- [ ] Contraste AA verificado nos badges
