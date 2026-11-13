import { NavHeader } from '../components/nav-header'
import { Info, Database, Brain, ShieldCheck, AlertTriangle, Code2, User, Layers } from 'lucide-react'
import { Badge } from '@/components/ui/badge'

export default function SobrePage() {
  return (
    <div className="min-h-screen">
      <NavHeader />
      <main className="mx-auto max-w-[1200px] px-4 py-8">
        <div className="mb-8">
          <div className="flex items-center gap-3">
            <Info className="h-8 w-8 text-primary" />
            <div>
              <h1 className="font-display text-2xl font-bold tracking-tight text-foreground sm:text-3xl">
                Sobre o Sistema
              </h1>
              <p className="mt-1 text-sm text-muted-foreground">
                Contexto, arquitetura e decisões metodológicas
              </p>
            </div>
          </div>
        </div>

        <div className="space-y-6">
          {/* Contexto */}
          <Card>
            <SectionTitle icon={<User className="h-5 w-5 text-primary" />} title="Contexto do Challenge" />
            <p className="text-sm leading-relaxed text-foreground">
              Este protótipo foi desenvolvido como parte do <strong>G4 AI Master Challenge — Desafio 002: Redesign de Suporte</strong>, 
              por <strong>Leonardo Candido Lopes</strong>.
            </p>
            <p className="mt-2 text-sm leading-relaxed text-foreground">
              O desafio propõe o redesign da operação de suporte ao cliente utilizando inteligência artificial 
              para triagem automática de chamados, classificação por categoria e prioridade, e roteamento inteligente 
              para as filas de atendimento adequadas.
            </p>
            <div className="mt-3 flex flex-wrap gap-2">
              <Badge variant="secondary">G4 Educação</Badge>
              <Badge variant="secondary">AI Master Challenge</Badge>
              <Badge variant="secondary">Desafio 002</Badge>
              <Badge variant="secondary">Protótipo</Badge>
            </div>
          </Card>

          {/* Arquitetura */}
          <Card>
            <SectionTitle icon={<Layers className="h-5 w-5 text-primary" />} title="Arquitetura do Sistema" />
            <p className="mb-4 text-sm text-muted-foreground">
              O sistema é composto por 3 pilares principais:
            </p>
            <div className="grid gap-4 md:grid-cols-3">
              <PillarCard
                icon={<Brain className="h-6 w-6 text-blue-600" />}
                title="1. Classificador ML"
                items={[
                  'TF-IDF + LinearSVC calibrado (CalibratedClassifierCV)',
                  'F1-macro: 0.84 no conjunto de teste',
                  '8 categorias IT: Hardware, Access, HR Support, etc.',
                  'Pipeline sklearn com preprocessamento de texto',
                ]}
              />
              <PillarCard
                icon={<ShieldCheck className="h-6 w-6 text-emerald-600" />}
                title="2. Regras de Segurança"
                items={[
                  '8 regras explícitas (não ML) em cadeia de prioridade',
                  'Detecção de comprometimento de conta → ESCALATE',
                  'Admin rights → sempre revisão humana',
                  'Thresholds empíricos: 0.70 (auto) e 0.55 (assistido)',
                ]}
              />
              <PillarCard
                icon={<Database className="h-6 w-6 text-orange-600" />}
                title="3. Detecção de Domínio"
                items={[
                  'Classificador binário (IT vs. não-IT)',
                  'Detecta: financeiro/comercial, fora do escopo, indeterminado',
                  'Tickets não-IT → sempre revisão humana',
                  'Limitação: validação com negativos sintéticos',
                ]}
              />
            </div>
          </Card>

          {/* Datasets */}
          <Card>
            <SectionTitle icon={<Database className="h-5 w-5 text-primary" />} title="Datasets Utilizados" />
            <div className="space-y-3">
              <DatasetItem
                name="D1 — Customer Support Ticket Dataset (Kaggle)"
                desc="~48K tickets sintéticos de TI corporativa. Base principal de treinamento."
                limitation="Dados sintéticos, em inglês, sem prioridade real confiável."
              />
              <DatasetItem
                name="D2 — IT Support Tickets Dataset (Kaggle)"
                desc="Dataset complementar para diversidade de vocabulário."
                limitation="Distribuição de categorias diferente de cenários reais."
              />
              <DatasetItem
                name="Negativos sintéticos"
                desc="Exemplos financeiros, comerciais e fora do escopo para treinar o detector de domínio."
                limitation="Negativos fabricados, não representam diversidade real de inputs não-IT."
              />
            </div>
          </Card>

          {/* Decisões */}
          <Card>
            <SectionTitle icon={<Code2 className="h-5 w-5 text-primary" />} title="Decisões Metodológicas" />
            <ul className="space-y-2 text-sm text-foreground">
              <li className="flex items-start gap-2">
                <span className="mt-1 h-1.5 w-1.5 shrink-0 rounded-full bg-primary" />
                <span><strong>LinearSVC sobre modelos mais complexos:</strong> melhor F1-macro com menor tempo de treino. Modelo leve e rápido para inferência em tempo real.</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="mt-1 h-1.5 w-1.5 shrink-0 rounded-full bg-primary" />
                <span><strong>Calibração isotônica:</strong> para obter probabilidades confiáveis do SVM, necessárias para os thresholds de decisão.</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="mt-1 h-1.5 w-1.5 shrink-0 rounded-full bg-primary" />
                <span><strong>Prioridade por regras, não ML:</strong> os datasets não têm rótulos de prioridade confiáveis. Regras são auditáveis e ajustáveis pelo time de operações.</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="mt-1 h-1.5 w-1.5 shrink-0 rounded-full bg-primary" />
                <span><strong>Sistema pode se abster:</strong> confiança insuficiente encaminha para revisão humana, em vez de arriscar classificação incorreta.</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="mt-1 h-1.5 w-1.5 shrink-0 rounded-full bg-primary" />
                <span><strong>Nenhum roteamento automático ativo:</strong> a regra R9 mantém confirmação humana em todos os casos enquanto o detector de domínio não tiver validação representativa.</span>
              </li>
            </ul>
          </Card>

          {/* Limitações */}
          <div className="rounded-lg border border-amber-200 bg-amber-50 p-5 dark:border-amber-800/50 dark:bg-amber-950/20" style={{ boxShadow: 'var(--shadow-sm)' }}>
            <SectionTitle icon={<AlertTriangle className="h-5 w-5 text-amber-700 dark:text-amber-400" />} title="Limitações Conhecidas" />
            <ul className="space-y-1.5 text-sm text-amber-800 dark:text-amber-300">
              <li>• Modelo treinado em dataset público de chamados internos de TI, em inglês; sua representatividade para uma operação específica não foi validada.</li>
              <li>• 3 de 15 casos da suíte final falharam — documentados na página de métricas e no resultado pós-R9.</li>
              <li>• Detector de domínio <strong>não validado</strong> (treinado apenas com negativos sintéticos) — não é uma proteção confiável e não garante a exclusão de chamados externos.</li>
              <li>• A similaridade com o treino <strong>não comprova</strong> pertencimento ao domínio e não é usada como critério de decisão.</li>
              <li>• <strong>Nenhum roteamento 100% automático está ativo:</strong> na ausência de sinal de domínio validado, todo caso recebe ao menos confirmação humana (assistida).</li>
              <li>• Suporta apenas inglês. Texto em português é encaminhado para revisão humana.</li>
              <li>• Protótipo demonstrável — não projetado para ambiente de produção.</li>
              <li>• Sem persistência de dados — cada análise é stateless.</li>
            </ul>
          </div>

          {/* Footer */}
          <div className="border-t border-border/60 pt-4 text-center">
            <p className="text-xs text-muted-foreground">
              Desenvolvido por Leonardo Candido Lopes para o G4 AI Master Challenge — Novembro 2026
            </p>
          </div>
        </div>
      </main>
    </div>
  )
}

function Card({ children }: { children: React.ReactNode }) {
  return (
    <div className="rounded-lg border border-border/60 bg-card p-5" style={{ boxShadow: 'var(--shadow-sm)' }}>
      {children}
    </div>
  )
}

function SectionTitle({ icon, title }: { icon: React.ReactNode; title: string }) {
  return (
    <div className="mb-3 flex items-center gap-2">
      {icon}
      <h3 className="font-display text-base font-semibold tracking-tight text-foreground">{title}</h3>
    </div>
  )
}

function PillarCard({ icon, title, items }: { icon: React.ReactNode; title: string; items: string[] }) {
  return (
    <div className="rounded-md border border-border/40 bg-muted/30 p-4">
      <div className="mb-2 flex items-center gap-2">
        {icon}
        <span className="text-sm font-semibold text-foreground">{title}</span>
      </div>
      <ul className="space-y-1">
        {items.map((item: string, i: number) => (
          <li key={i} className="flex items-start gap-1.5 text-xs text-muted-foreground">
            <span className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-muted-foreground/40" />
            {item}
          </li>
        ))}
      </ul>
    </div>
  )
}

function DatasetItem({ name, desc, limitation }: { name: string; desc: string; limitation: string }) {
  return (
    <div className="rounded-md border border-border/40 bg-muted/20 px-4 py-3">
      <div className="text-sm font-medium text-foreground">{name}</div>
      <div className="mt-0.5 text-xs text-muted-foreground">{desc}</div>
      <div className="mt-1 text-xs text-amber-700 dark:text-amber-400">⚠ {limitation}</div>
    </div>
  )
}
