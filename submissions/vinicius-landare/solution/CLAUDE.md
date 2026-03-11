# Social Metrics - Sistema de Análise de Métricas de Mídias Sociais

## Stack
- **Framework**: Next.js 15 (App Router, Turbopack)
- **Linguagem**: TypeScript
- **UI**: Tailwind CSS v4 + shadcn/ui
- **ORM**: Prisma (PostgreSQL)
- **Gráficos**: Recharts (via shadcn/ui chart)
- **Auth**: NextAuth.js v5 (beta)
- **Validação**: Zod
- **Ícones**: Lucide React
- **Datas**: date-fns

## Estrutura do Projeto
```
src/
├── app/              # Rotas (App Router)
│   ├── api/          # API Routes
│   └── dashboard/    # Páginas do dashboard
├── components/
│   └── ui/           # Componentes shadcn/ui
├── generated/prisma/ # Prisma Client (gerado)
├── hooks/            # Custom hooks
├── lib/              # Utilitários (prisma, utils)
└── types/            # Tipos TypeScript
prisma/
└── schema.prisma     # Schema do banco de dados
```

## Comandos
- `npm run dev` - Servidor de desenvolvimento
- `npx prisma migrate dev` - Criar/aplicar migrações
- `npx prisma generate` - Gerar Prisma Client
- `npx prisma studio` - UI para explorar o banco

## Convenções
- Usar português para nomes de variáveis de negócio quando fizer sentido
- Componentes em PascalCase
- Arquivos em kebab-case
- API routes retornam JSON padronizado
- Sempre validar input com Zod nas API routes
