# Component Architecture — Lead Scorer Redesign

## 🏛️ Hierarquia de Componentes (Atomic Design)

```
┌─────────────────────────────────────────────────────────────┐
│                     PAGES (Organisms)                        │
├─────────────────────────────────────────────────────────────┤
│  DashboardPage                 DealDetailPage               │
│  (TOP 5 Leads View)            (Lead Battle Card)           │
└─────────────────────────────────────────────────────────────┘
         │                              │
         └──────────────┬───────────────┘
                        │
┌───────────────────────┴─────────────────────────────────────┐
│                  MOLECULES (Composites)                      │
├─────────────────────────────────────────────────────────────┤
│  LeadCard            ScoreBreakdown      SPINSection         │
│  ├─ Card            ├─ Card              ├─ Card            │
│  ├─ Badge           ├─ ProgressBar       ├─ Card (x4)       │
│  ├─ Button          └─ Card              ├─ Button          │
│  └─ Button (x2)                         └─ Button          │
└─────────────────────────────────────────────────────────────┘
         │                  │                    │
         └──────────────────┼────────────────────┘
                            │
┌───────────────────────────┴─────────────────────────────────┐
│                    ATOMS (Primitives)                        │
├─────────────────────────────────────────────────────────────┤
│  Button  Card  Badge  ProgressBar  Stat                     │
│  ─────  ────  ─────  ─────────────  ────                    │
│   CVA    CVA   CVA        CVA        HTML                    │
└─────────────────────────────────────────────────────────────┘
         │      │     │          │      │
         └──────┴─────┴──────────┴──────┘
                    │
           Tailwind CSS + CVA
           (No custom CSS)
```

---

## 📦 Componentes Detalhados

### ATOMS — `src/components/ui/`

#### 1. **Button**
```tsx
// Props
interface ButtonProps {
  variant?: 'primary' | 'secondary' | 'ghost' | 'link' | 'danger' | 'success'
  size?: 'xs' | 'sm' | 'md' | 'lg'
  fullWidth?: boolean
  isLoading?: boolean
  disabled?: boolean
  children: ReactNode
}

// Variantes de Cor
primary     → bg-blue-600 hover:bg-blue-700
secondary   → bg-slate-700 hover:bg-slate-600
ghost       → bg-transparent hover:bg-slate-700/50
link        → bg-transparent hover:text-blue-400
danger      → bg-red-600 hover:bg-red-700
success     → bg-green-600 hover:bg-green-700
```

#### 2. **Card**
```tsx
// Props
interface CardProps {
  variant?: 'default' | 'elevated' | 'interactive'
  padding?: 'none' | 'sm' | 'md' | 'lg'
  children: ReactNode
}

// Variantes
default      → bg-slate-800 border-slate-700
elevated     → bg-slate-800 border-slate-600 shadow-lg
interactive  → bg-slate-800 hover:border-slate-600 cursor-pointer
```

#### 3. **Badge**
```tsx
// Props
interface BadgeProps {
  tier?: 'HOT' | 'WARM' | 'COOL' | 'COLD'
  children?: ReactNode
}

// Renderização
tier="HOT"   → 🔴 bg-red-900/30 border-red-700/50
tier="WARM"  → 🟡 bg-yellow-900/30 border-yellow-700/50
tier="COOL"  → 🔵 bg-blue-900/30 border-blue-700/50
tier="COLD"  → ⚫ bg-gray-900/30 border-gray-700/50
```

#### 4. **ProgressBar**
```tsx
// Props
interface ProgressBarProps {
  value: number
  max?: number (default: 100)
  size?: 'xs' | 'sm' | 'md' | 'lg'
  color?: 'blue' | 'green' | 'red' | 'yellow'
  showLabel?: boolean
}

// Auto-color logic
value >= 80% → green
value >= 50% → blue
value >= 25% → yellow
value < 25%  → red
```

#### 5. **Stat**
```tsx
// Props
interface StatProps {
  label: string
  value: ReactNode
  subtitle?: ReactNode
  icon?: ReactNode
  highlight?: boolean
}

// Estilos
highlight: false → bg-slate-900 border-slate-700
highlight: true  → bg-slate-800 border-blue-700/30
```

---

### MOLECULES — `src/components/composite/`

#### 1. **LeadCard**
```tsx
// Props
interface LeadCardProps {
  deal: DealScore
  onView?: (deal: DealScore) => void
  onCall?: (deal: DealScore) => void
  onEmail?: (deal: DealScore) => void
}

// Composição
Card (interactive)
├─ Header
│  ├─ Company Name + Days in Pipeline
│  └─ Badge (tier)
├─ Score Display
│  ├─ Score 94/100
│  └─ Recommendation text
├─ Main CTA
│  └─ Button (primary) "Ver Detalhes →"
└─ Quick Actions
   ├─ Button 📞 Call
   └─ Button 📧 Email

// Layout
5 cards em grid (lg: 5 colunas, md: 2, sm: 1)
```

#### 2. **ScoreBreakdown**
```tsx
// Props
interface ScoreBreakdownProps {
  factors: ScoreFactor[]
  totalScore?: number
}

// Composição
├─ For each factor:
│  ├─ Card
│  │  ├─ Factor Name + Weight
│  │  ├─ Explanation
│  │  ├─ Contribution points
│  │  └─ ProgressBar (visual)
│  └─ Raw value + normalized %
└─ Total Score Card (highlighted)

// Dados de entrada
7 fatores padrão:
1. Win Rate da Conta
2. Revenue Média
3. Tamanho da Empresa
4. Produtos Desafiados
5. Ciclo de Vendas
6. Histórico de Perdas
7. Valor do Ticket Médio
```

#### 3. **SPINSection**
```tsx
// Props
interface SPINSectionProps {
  script: SPINScript
  accountName?: string
}

// Composição
├─ [S] SITUAÇÃO
│  └─ Card (blue background)
├─ [P] PROBLEMA
│  └─ Card (yellow background)
├─ [I] IMPLICAÇÃO
│  └─ Card (orange background)
├─ [N] NECESSIDADE-PAYOFF
│  └─ Card (green background)
└─ Action Buttons
   ├─ Button "📋 Copiar Script"
   └─ Button "🖨️ Imprimir"

// Dados de entrada
SPINScript:
  situation: string (apresentação do contexto)
  problem: string (problemas atuais)
  implication: string (impactos)
  need_payoff: string (solução esperada)
```

---

## 🔄 Fluxo de Dados

### DashboardPage Flow
```
useDealScoring() ──┐
                   ├──> dealScores (DealScore[])
useAccountScoring()┘
                   │
                   ├──> Filter: tier === 'HOT'
                   │
                   ├──> Sort: score DESC
                   │
                   ├──> Slice: [0..5]
                   │
                   ├──> Fill with WARM if < 5
                   │
                   └──> topPriorityDeals
                        │
                        └──> map() → <LeadCard> x5
                             │
                             └──> onSelectDeal() callback
```

### DealDetailPage Flow
```
deal: DealScore ──┐
                  ├──> useSPINReports()
pipeline         ├──>
accounts         ├──> report: LeadReport
products         │
                 │
                 ├──> Header (Badge, Stat components)
                 │
                 ├──> <ScoreBreakdown factors={deal.factors} />
                 │
                 ├──> <SPINSection script={report.spin_script} />
                 │
                 ├──> Histórico (Card components)
                 │
                 └──> Próximos Passos (Button components)
```

---

## 🧪 Padrões e Melhores Práticas

### 1. **Type Safety**
```tsx
// ✅ Good
import { type ReactNode } from 'react'
interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant: VariantProps<typeof buttonVariants>['variant']
}

// ❌ Bad
import { ReactNode } from 'react' // Tipo, deveria ser type-only
let value: any // Sem type
```

### 2. **CVA para Variantes**
```tsx
// ✅ Good
const buttonVariants = cva('base', {
  variants: {
    variant: { primary: '...', secondary: '...' }
  }
})

// ❌ Bad
className={variant === 'primary' ? 'bg-blue...' : 'bg-slate...'} // Conditionals
```

### 3. **Component Composition**
```tsx
// ✅ Good — LeadCard é composição pura
<Card>
  <Badge tier={deal.tier} />
  <Button>Click me</Button>
</Card>

// ❌ Bad — LeadCard faria tudo sozinho
<LeadCard ... renderBadge renderButton ... />
```

### 4. **Props Interfaces**
```tsx
// ✅ Good
interface StatProps extends HTMLAttributes<HTMLDivElement> {
  label: string
  value: ReactNode
}

// ❌ Bad
interface StatProps {
  className?: string // Redundante se estender HTMLAttributes
  style?: CSSProperties
  ...
}
```

---

## 📊 Import Graph

```
DashboardPage.tsx
├── import { useDealScoring } from '@/hooks'
├── import { LeadCard } from '@/components/composite'
├── import { Card, Stat } from '@/components/ui'
└── [recharts charts]

DealDetailPage.tsx
├── import { useSPINReports } from '@/hooks'
├── import { Card, Badge, Button, Stat } from '@/components/ui'
└── import { ScoreBreakdown, SPINSection } from '@/components/composite'

composite/LeadCard.tsx
├── import { Card, Badge, Button } from '@/components/ui'
└── import type { DealScore } from '@/types'

composite/ScoreBreakdown.tsx
├── import { Card, ProgressBar } from '@/components/ui'
└── import type { ScoreFactor } from '@/types'

composite/SPINSection.tsx
├── import { Card, Button } from '@/components/ui'
└── No type imports needed

ui/Button.tsx, Card.tsx, Badge.tsx, ProgressBar.tsx, Stat.tsx
└── Only React types + CVA
```

---

## 🎨 Tailwind Classes Consolidadas

### Antes (Duplicação)
```tsx
// DashboardPage
className="bg-slate-800 rounded-lg border border-slate-700 p-4"
className="bg-slate-800 rounded-lg border border-slate-700 p-4"
className="bg-slate-800 rounded-lg border border-slate-700 p-4"
// ... 15+ vezes

// DealsPage
className="bg-slate-800 rounded-lg border border-slate-700 p-6"
// ... repetido
```

### Depois (Centralizado)
```tsx
// ui/Card.tsx — Uma única fonte de verdade
const cardVariants = cva('rounded-lg border', {
  variants: {
    variant: {
      default: 'bg-slate-800 border-slate-700'
      // ...
    },
    padding: {
      md: 'p-4'
      // ...
    }
  }
})

// Uso
<Card variant="default" padding="md" />
```

---

## ✨ Conclusão

A arquitetura de componentes segue **Atomic Design** rigorosamente:

1. **Atoms** → Blocos básicos reutilizáveis (Button, Card, Badge, etc.)
2. **Molecules** → Combinações de atoms (LeadCard, ScoreBreakdown, SPINSection)
3. **Organisms** → Páginas compostas de molecules (DashboardPage, DealDetailPage)

Benefícios:
- ✅ 0% duplicação de código
- ✅ 100% type-safe
- ✅ Fácil manutenção e evolução
- ✅ Reusabilidade garantida
- ✅ Documentação automática via props

