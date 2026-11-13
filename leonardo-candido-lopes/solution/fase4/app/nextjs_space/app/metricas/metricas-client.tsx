'use client'

import { useEffect, useState } from 'react'
import { Loader2, AlertCircle, CheckCircle2, XCircle, TrendingUp, Target, Activity } from 'lucide-react'
import { cn } from '@/lib/utils'
import { Progress } from '@/components/ui/progress'
import { Badge } from '@/components/ui/badge'
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow
} from '@/components/ui/table'

export function MetricasClient() {
  const [metadata, setMetadata] = useState<any>(null)
  const [testData, setTestData] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    Promise.all([
      fetch('/api/model-metadata').then(r => r.ok ? r.json() : null),
      fetch('/api/test-cases').then(r => r.ok ? r.json() : null),
    ])
      .then(([meta, tests]) => {
        setMetadata(meta)
        setTestData(tests)
      })
      .catch((e: any) => setError(e?.message || 'Erro ao carregar dados'))
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    )
  }

  if (error || !metadata) {
    return (
      <div className="flex items-center gap-2 rounded-lg border border-red-200 bg-red-50 px-4 py-3 dark:border-red-800/50 dark:bg-red-950/20">
        <AlertCircle className="h-5 w-5 text-red-600" />
        <p className="text-sm text-red-700 dark:text-red-300">{error || 'Dados não disponíveis. Verifique se o backend está rodando.'}</p>
      </div>
    )
  }

  const testMetrics = metadata?.test_metrics ?? {}
  const perClass = testMetrics?.per_class ?? {}
  const thresholds = metadata?.thresholds ?? {}
  const testResults = testData?.test_results ?? []

  // Sort categories by F1
  const sortedCategories = Object.entries(perClass)
    .map(([name, m]: [string, any]) => ({ name, ...m }))
    .sort((a: any, b: any) => (b?.f1 ?? 0) - (a?.f1 ?? 0))

  const totalPass = testResults.filter((t: any) => t?.test_pass === true).length
  const totalFail = testResults.filter((t: any) => t?.test_pass === false).length

  return (
    <div className="space-y-6">
      {/* KPIs */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <KpiCard
          icon={<Target className="h-5 w-5 text-primary" />}
          label="F1-Macro (Teste)"
          value={`${((testMetrics?.f1_macro ?? 0) * 100).toFixed(1)}%`}
          sub={`${testMetrics?.n ?? 0} amostras`}
        />
        <KpiCard
          icon={<TrendingUp className="h-5 w-5 text-emerald-600" />}
          label="Acurácia"
          value={`${((testMetrics?.accuracy ?? 0) * 100).toFixed(1)}%`}
          sub="conjunto de teste"
        />
        <KpiCard
          icon={<Activity className="h-5 w-5 text-blue-600" />}
          label="ECE (Calibração)"
          value={`${((testMetrics?.ece ?? 0) * 100).toFixed(1)}%`}
          sub="erro de calibração"
        />
        <KpiCard
          icon={<CheckCircle2 className="h-5 w-5 text-amber-600" />}
          label="Testes de Validação"
          value={`${totalPass}/${totalPass + totalFail}`}
          sub={`${totalFail} falha(s)`}
        />
      </div>

      {/* F1 por categoria */}
      <div className="rounded-lg border border-border/60 bg-card p-5" style={{ boxShadow: 'var(--shadow-sm)' }}>
        <h3 className="mb-4 font-display text-base font-semibold tracking-tight text-foreground">F1-Score por Categoria</h3>
        <div className="space-y-3">
          {sortedCategories.map((cat: any) => {
            const f1Pct = Math.round((cat?.f1 ?? 0) * 100)
            return (
              <div key={cat.name} className="flex items-center gap-3">
                <span className="w-36 shrink-0 truncate text-sm font-medium text-foreground">{cat.name}</span>
                <div className="flex-1">
                  <Progress value={f1Pct} className="h-3" />
                </div>
                <span className="w-12 text-right font-mono text-sm font-semibold text-foreground">{f1Pct}%</span>
              </div>
            )
          })}
        </div>
      </div>

      {/* Tabela de métricas detalhada */}
      <div className="rounded-lg border border-border/60 bg-card p-5" style={{ boxShadow: 'var(--shadow-sm)' }}>
        <h3 className="mb-4 font-display text-base font-semibold tracking-tight text-foreground">Métricas Detalhadas por Categoria</h3>
        <div className="overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Categoria</TableHead>
                <TableHead className="text-right">Precision</TableHead>
                <TableHead className="text-right">Recall</TableHead>
                <TableHead className="text-right">F1</TableHead>
                <TableHead className="text-right">Suporte</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {sortedCategories.map((cat: any) => (
                <TableRow key={cat.name}>
                  <TableCell className="font-medium">{cat.name}</TableCell>
                  <TableCell className="text-right font-mono text-sm">{((cat?.precision ?? 0) * 100).toFixed(1)}%</TableCell>
                  <TableCell className="text-right font-mono text-sm">{((cat?.recall ?? 0) * 100).toFixed(1)}%</TableCell>
                  <TableCell className="text-right font-mono text-sm font-semibold">{((cat?.f1 ?? 0) * 100).toFixed(1)}%</TableCell>
                  <TableCell className="text-right font-mono text-sm">{cat?.support ?? 0}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      </div>

      {/* Thresholds */}
      <div className="rounded-lg border border-border/60 bg-card p-5" style={{ boxShadow: 'var(--shadow-sm)' }}>
        <h3 className="mb-2 font-display text-base font-semibold tracking-tight text-foreground">Cobertura e precisão do classificador (pré-R9)</h3>
        <p className="mb-4 text-sm text-muted-foreground">Métricas de classificação por categoria, medidas antes da política operacional final. Não representam roteamento automático: a regra R9 mantém confirmação humana em todos os casos.</p>
        <div className="overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Limiar de confiança da categoria</TableHead>
                <TableHead className="text-right">Threshold</TableHead>
                <TableHead className="text-right">Cobertura</TableHead>
                <TableHead className="text-right">Precisão</TableHead>
                <TableHead className="text-right">Amostras</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              <TableRow>
                <TableCell><Badge variant="outline">Limiar alto (classificador)</Badge></TableCell>
                <TableCell className="text-right font-mono">≥ {thresholds?.threshold_alto ?? 0.7}</TableCell>
                <TableCell className="text-right font-mono">{((thresholds?.test_at_alto?.coverage ?? 0) * 100).toFixed(1)}%</TableCell>
                <TableCell className="text-right font-mono">{((thresholds?.test_at_alto?.precision ?? 0) * 100).toFixed(1)}%</TableCell>
                <TableCell className="text-right font-mono">{thresholds?.test_at_alto?.n ?? 'N/A'}</TableCell>
              </TableRow>
              <TableRow>
                <TableCell><Badge variant="outline">Limiar baixo (classificador)</Badge></TableCell>
                <TableCell className="text-right font-mono">≥ {thresholds?.threshold_baixo ?? 0.55}</TableCell>
                <TableCell className="text-right font-mono">{((thresholds?.test_at_baixo?.coverage ?? 0) * 100).toFixed(1)}%</TableCell>
                <TableCell className="text-right font-mono">{((thresholds?.test_at_baixo?.precision ?? 0) * 100).toFixed(1)}%</TableCell>
                <TableCell className="text-right font-mono">{thresholds?.test_at_baixo?.n ?? 'N/A'}</TableCell>
              </TableRow>
            </TableBody>
          </Table>
        </div>
      </div>

      {/* Limitações */}
      <div className="rounded-lg border border-amber-200 bg-amber-50 p-5 dark:border-amber-800/50 dark:bg-amber-950/20" style={{ boxShadow: 'var(--shadow-sm)' }}>
        <h3 className="mb-3 font-display text-base font-semibold tracking-tight text-amber-900 dark:text-amber-200">⚠ Limitações Conhecidas</h3>
        <ul className="space-y-1.5 text-sm text-amber-800 dark:text-amber-300">
          <li>• Modelo treinado em dados de TI corporativa (inglês). Sem dados B2C reais de qualidade.</li>
          <li>• {totalFail} de {totalPass + totalFail} casos de teste falharam (documentados abaixo).</li>
          <li>• Detector de domínio sem validação independente robusta (negativos sintéticos).</li>
          <li>• Suporta apenas inglês — texto em português é encaminhado para revisão humana.</li>
          <li>• F1-macro real no conjunto de teste: {((testMetrics?.f1_macro ?? 0) * 100).toFixed(1)}%</li>
        </ul>
      </div>

      {/* Casos de teste */}
      <div className="rounded-lg border border-border/60 bg-card p-5" style={{ boxShadow: 'var(--shadow-sm)' }}>
        <h3 className="mb-4 font-display text-base font-semibold tracking-tight text-foreground">Casos de Teste ({totalPass + totalFail} casos)</h3>
        <div className="overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-10">#</TableHead>
                <TableHead>Tipo</TableHead>
                <TableHead className="max-w-[200px]">Texto</TableHead>
                <TableHead>Esperado</TableHead>
                <TableHead>Obtido</TableHead>
                <TableHead className="text-center">Status</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {testResults.map((t: any, idx: number) => (
                <TableRow key={t?.id ?? `test-${idx}`}>
                  <TableCell className="font-mono text-xs">{t?.id}</TableCell>
                  <TableCell>
                    <Badge variant={t?.tipo === 'obrigatorio' ? 'default' : 'secondary'} className="text-[10px]">
                      {t?.tipo === 'obrigatorio' ? 'Obrigatório' : 'Adicional'}
                    </Badge>
                  </TableCell>
                  <TableCell className="max-w-[200px] truncate text-xs" title={t?.input_text}>
                    {(t?.input_text ?? '').length > 60 ? `${(t?.input_text ?? '').slice(0, 60)}...` : t?.input_text}
                  </TableCell>
                  <TableCell className="text-xs">
                    <div>{t?.expected_domain}</div>
                    {t?.expected_category && <div className="text-muted-foreground">{t.expected_category}</div>}
                  </TableCell>
                  <TableCell className="text-xs">
                    <div>{t?.predicted_domain}</div>
                    {t?.predicted_category && <div className="text-muted-foreground">{t.predicted_category}</div>}
                  </TableCell>
                  <TableCell className="text-center">
                    {t?.test_pass ? (
                      <CheckCircle2 className="mx-auto h-5 w-5 text-emerald-600" />
                    ) : (
                      <XCircle className="mx-auto h-5 w-5 text-red-500" />
                    )}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      </div>
    </div>
  )
}

function KpiCard({ icon, label, value, sub }: { icon: React.ReactNode; label: string; value: string; sub: string }) {
  return (
    <div className="rounded-lg border border-border/60 bg-card p-4" style={{ boxShadow: 'var(--shadow-sm)' }}>
      <div className="mb-2 flex items-center gap-2">
        {icon}
        <span className="text-xs font-medium text-muted-foreground">{label}</span>
      </div>
      <div className="font-display text-2xl font-bold tracking-tight text-foreground">{value}</div>
      <div className="mt-0.5 text-xs text-muted-foreground">{sub}</div>
    </div>
  )
}
