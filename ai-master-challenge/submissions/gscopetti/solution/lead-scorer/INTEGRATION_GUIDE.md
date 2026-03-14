# Integration Guide — Lead Scorer Redesign

## 🚀 Como Integrar o Redesign no App

### 1. **Verificar o App.tsx/Main Component**

Seu arquivo principal provavelmente se parece com:

```tsx
// App.tsx (ANTES)
import { DashboardPage } from '@/components/pages/DashboardPage';
import { DealDetailPage } from '@/components/pages/DealDetailPage';

export function App() {
  const [selectedDeal, setSelectedDeal] = useState<DealScore | null>(null);

  return (
    <MainContent>
      {selectedDeal ? (
        <DealDetailPage deal={selectedDeal} ... />
      ) : (
        <DashboardPage ... />
      )}
    </MainContent>
  );
}
```

### 2. **Integração do Redesign**

O código acima já funciona com o redesign! Mas você pode melhorar passando os novos props:

```tsx
// App.tsx (DEPOIS)
import { DashboardPage } from '@/components/pages/DashboardPage';
import { DealDetailPage } from '@/components/pages/DealDetailPage';

export function App() {
  const [selectedDeal, setSelectedDeal] = useState<DealScore | null>(null);

  return (
    <MainContent>
      {selectedDeal ? (
        <DealDetailPage
          deal={selectedDeal}
          pipeline={pipeline}
          accounts={accounts}
          products={products}
          onBack={() => setSelectedDeal(null)}  {/* ← NOVO */}
        />
      ) : (
        <DashboardPage
          pipeline={pipeline}
          accounts={accounts}
          products={products}
          onSelectDeal={(deal) => setSelectedDeal(deal)}  {/* ← NOVO */}
        />
      )}
    </MainContent>
  );
}
```

---

## 📋 Checklist de Integração

### ✅ Fase 1: Verificação
- [ ] Confirmar que DashboardPage e DealDetailPage existem em `src/components/pages/`
- [ ] Verificar se há um componente de layout (MainContent, Sidebar, Header)
- [ ] Confirmar que `useDealScoring` e `useSPINReports` hooks existem
- [ ] Verificar se Tailwind CSS está configurado

### ✅ Fase 2: Imports
- [ ] Confirmar que imports de componentes resolvem corretamente
- [ ] Verificar que `@/components/ui` e `@/components/composite` estão no path
- [ ] Rodar `npx tsc --noEmit` para validar tipos

### ✅ Fase 3: Props
- [ ] Adicionar `onSelectDeal` prop em DashboardPage
- [ ] Adicionar `onBack` prop em DealDetailPage
- [ ] Passar callbacks corretamente do App

### ✅ Fase 4: Build & Test
- [ ] Rodar `npm run build`
- [ ] Testar navegação: Dashboard → Lead Detail → Back
- [ ] Testar responsividade (mobile, tablet, desktop)
- [ ] Rodar `npm run lint` e `npm run preview`

---

## 🔌 Próximos Passos (CTAs Functionality)

Os botões de "Próximos Passos" estão estruturados, mas não implementados. Para completar:

### 1. **Agendar Ligação** (📞)
```tsx
// src/components/pages/DealDetailPage.tsx — line ~200
onClick={() => {
  // TODO: Implementar modal de agendamento
  // ou redirecionar para Google Calendar / Calendly
}}
```

### 2. **Enviar Email** (📧)
```tsx
// Implementar:
onClick={() => {
  // TODO: Abrir composer de email com template SPIN
  // ou redirecionar para Gmail/Outlook
}}
```

### 3. **Adicionar Nota** (📝)
```tsx
// Implementar:
onClick={() => {
  // TODO: Modal para adicionar nota ao deal
  // salvar em localStorage ou API
}}
```

### 4. **Atualizar Estágio** (🔄)
```tsx
// Implementar:
onClick={() => {
  // TODO: Dropdown de estágios (Prospecting → Engaging → Closing)
  // atualizar deal_stage no backend
}}
```

---

## 🎨 Customização de Temas

Se quiser customizar cores, faça em um único lugar:

### Tailwind Config
```js
// tailwind.config.js
module.exports = {
  theme: {
    colors: {
      // Adicionar cores customizadas aqui
      'hot': '#dc2626',    // Red
      'warm': '#eab308',   // Yellow
      'cool': '#3b82f6',   // Blue
      'cold': '#64748b',   // Gray
    }
  }
}
```

### Depois use nos componentes
```tsx
// ui/Badge.tsx
const badgeVariants = cva('inline-flex...', {
  variants: {
    variant: {
      HOT: 'bg-hot/30 border-hot/50',  // Usa cor customizada
      // ...
    }
  }
})
```

---

## 🧪 Exemplos de Uso

### Usar Button em novo lugar
```tsx
import { Button } from '@/components/ui';

<Button variant="primary" size="md">
  Clique aqui
</Button>
```

### Usar Card para novo widget
```tsx
import { Card, Stat } from '@/components/ui';

<Card padding="lg">
  <Stat label="Metric" value={42} icon="📊" />
</Card>
```

### Combinar componentes
```tsx
import { Card, Badge, Button } from '@/components/ui';

<Card interactive padding="md">
  <Badge tier="HOT" />
  <Button variant="secondary">Details</Button>
</Card>
```

---

## 🐛 Troubleshooting

### Problema: "Cannot find module @/components/ui"
**Solução:** Verificar `tsconfig.json` paths:
```json
{
  "compilerOptions": {
    "paths": {
      "@/*": ["./src/*"]
    }
  }
}
```

### Problema: Tailwind classes não estão aplicando
**Solução:** Verificar `tailwind.config.js` content:
```js
module.exports = {
  content: [
    './src/**/*.{js,ts,jsx,tsx}',  // ← deve incluir src/components
  ]
}
```

### Problema: Build fail com "Module not found"
**Solução:** Rodar `npm install` para garantir dependências

### Problema: Type errors em "any"
**Solução:** Verificar que imports de tipos usam `type`:
```tsx
import { type ReactNode } from 'react';  // ✅
import { ReactNode } from 'react';       // ❌
```

---

## 📚 Documentação de Componentes

### Button Component
**Arquivo:** `src/components/ui/Button.tsx`
**Variantes:** primary | secondary | ghost | link | danger | success
**Tamanhos:** xs | sm | md | lg
**Props:** `variant`, `size`, `fullWidth`, `isLoading`, `disabled`, `children`

### Card Component
**Arquivo:** `src/components/ui/Card.tsx`
**Variantes:** default | elevated | interactive
**Padding:** none | sm | md | lg

### Badge Component
**Arquivo:** `src/components/ui/Badge.tsx`
**Tiers:** HOT 🔴 | WARM 🟡 | COOL 🔵 | COLD ⚫

### LeadCard Component
**Arquivo:** `src/components/composite/LeadCard.tsx`
**Callbacks:** `onView`, `onCall`, `onEmail`
**Props:** `deal: DealScore`

### ScoreBreakdown Component
**Arquivo:** `src/components/composite/ScoreBreakdown.tsx`
**Props:** `factors: ScoreFactor[]`, `totalScore?: number`

### SPINSection Component
**Arquivo:** `src/components/composite/SPINSection.tsx`
**Props:** `script: SPINScript`, `accountName?: string`

---

## 🔄 Migration Path

Se você está migrando de componentes antigos:

### Old Pattern
```tsx
<div className="bg-slate-800 rounded-lg border border-slate-700 p-4">
  <p className="text-sm text-slate-400">Label</p>
  <p className="text-3xl font-bold">{value}</p>
</div>
```

### New Pattern (Using Stat)
```tsx
<Stat label="Label" value={value} />
```

---

## 📞 Support

Se encontrar problemas:

1. Verifique o arquivo `REDESIGN_SUMMARY.md` para contexto geral
2. Verifique o arquivo `COMPONENT_ARCHITECTURE.md` para estrutura
3. Verifique os backups: `DashboardPage.backup.tsx`, `DealDetailPage.backup.tsx`
4. Rodar `npm run lint` para identificar issues
5. Rodar `npm run build` para validar build

---

## ✅ Validação Final

Antes de fazer deploy, certifique-se de:

```bash
# Type checking
npx tsc --noEmit

# Linting
npm run lint

# Build
npm run build

# Preview
npm run preview
```

Todos devem passar com 0 errors!

---

## 🎉 Parabéns!

Seu Lead Scorer agora tem uma UI/UX focada em ação, com uma biblioteca de componentes reutilizáveis. O redesign estabelece uma base sólida para futuras features e garante consistência visual em todo o projeto.

**Próximas missões:**
- [ ] Integrar callbacks nos CTA buttons
- [ ] Testar em devices reais (mobile, tablet)
- [ ] Coletar feedback de vendedores
- [ ] Iterar baseado em feedback

Boa sorte! 🚀

