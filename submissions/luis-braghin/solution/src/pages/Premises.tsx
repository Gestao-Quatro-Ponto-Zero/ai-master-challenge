import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  AlertTriangle, Target, TrendingUp, BarChart3, Award, Clock,
  AlertCircle, Shield, Lightbulb, CheckCircle2, Info
} from "lucide-react";

/* ─── Sub-components ─── */
function WeightItem({ icon: Icon, color, weight, title, description }: {
  icon: React.ElementType; color: string; weight: string; title: string; description: string;
}) {
  return (
    <div className="flex items-start gap-3 p-3 rounded-lg bg-muted/50">
      <Icon className={`h-4 w-4 mt-0.5 shrink-0 ${color}`} />
      <div className="flex-1">
        <div className="flex items-center gap-2">
          <span className="text-sm font-semibold text-foreground">{title}</span>
          <Badge variant="secondary" className="text-xs">{weight}</Badge>
        </div>
        <p className="text-xs text-muted-foreground mt-1">{description}</p>
      </div>
    </div>
  );
}

function CategoryItem({ emoji, label, description, count }: {
  emoji: string; label: string; description: string; count: number;
}) {
  return (
    <div className="flex items-center gap-3 p-3 rounded-lg bg-muted/50">
      <span className="text-lg">{emoji}</span>
      <div className="flex-1">
        <span className="text-sm font-semibold text-foreground">{label}</span>
        <p className="text-xs text-muted-foreground">{description}</p>
      </div>
      <Badge variant="secondary" className="text-xs">{count.toLocaleString("pt-BR")}</Badge>
    </div>
  );
}

function AlertTypeItem({ emoji, title, description }: {
  emoji: string; title: string; description: string;
}) {
  return (
    <div className="flex items-start gap-3 p-3 rounded-lg bg-muted/50">
      <span className="text-lg">{emoji}</span>
      <div>
        <span className="text-sm font-semibold text-foreground">{title}</span>
        <p className="text-xs text-muted-foreground mt-1">{description}</p>
      </div>
    </div>
  );
}

function ConceptItem({ title, description }: { title: string; description: string }) {
  return (
    <div className="border-l-2 border-primary/30 pl-4">
      <h4 className="text-sm font-semibold text-foreground">{title}</h4>
      <p className="text-xs text-muted-foreground mt-1">{description}</p>
    </div>
  );
}

function BacktestCard({ label, winRate, color }: { label: string; winRate: string; color: string }) {
  return (
    <div className="text-center p-4 rounded-lg bg-muted/50">
      <p className={`text-2xl font-bold ${color}`}>{winRate}</p>
      <p className="text-xs text-muted-foreground mt-1">{label}</p>
    </div>
  );
}

/* ─── Main Page ─── */
export default function Premises() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Premissas</h1>
        <p className="text-sm text-muted-foreground">Metodologia, conceitos e validação do sistema de scoring</p>
      </div>

      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Target className="h-5 w-5 text-primary" />
            <CardTitle className="text-base">Score (0-100)</CardTitle>
          </div>
          <p className="text-sm text-muted-foreground">
            O score combina 5 dimensões para estimar a probabilidade de fechamento de cada deal.
          </p>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <h4 className="text-sm font-semibold mb-3 text-foreground">Pesos — Deals em Engaging</h4>
            <div className="grid gap-3">
              <WeightItem icon={Award} color="text-primary" weight="40%" title="Afinidade Agente-Produto" description="Win rate histórico do vendedor com este produto específico. É o preditor mais forte — win rates variam de 14% a 90% para o mesmo produto dependendo do vendedor." />
              <WeightItem icon={TrendingUp} color="text-success" weight="20%" title="Valor do Deal" description="Valor monetário em escala logarítmica. Diferencia prioridade entre deals de $550 e $4.821, não apenas entre $55 e $26.768." />
              <WeightItem icon={Clock} color="text-warning" weight="20%" title="Pipeline Velocity" description="Tempo no pipeline. Sweet spot histórico: 14-30 dias (73% win rate). Deals acima de 138 dias (máximo histórico) recebem penalidade progressiva." />
              <WeightItem icon={Shield} color="text-chart-3" weight="15%" title="Qualidade da Conta" description="Revenue tier da empresa + histórico de deals com a conta." />
              <WeightItem icon={BarChart3} color="text-muted-foreground" weight="5%" title="Fit Produto-Setor" description="Win rate histórico da combinação produto × setor. Peso baixo porque setor é um preditor fraco (spread de apenas 3-4pp)." />
            </div>
          </div>
          <div className="border-t pt-4">
            <h4 className="text-sm font-semibold mb-3 text-foreground">Pesos — Deals em Prospecting</h4>
            <div className="grid gap-3">
              <WeightItem icon={Award} color="text-primary" weight="40%" title="Afinidade Agente-Produto" description="Mesmo critério de Engaging." />
              <WeightItem icon={TrendingUp} color="text-success" weight="20%" title="Valor do Deal" description="Mesmo critério de Engaging." />
              <WeightItem icon={Shield} color="text-chart-3" weight="20%" title="Qualidade da Conta" description="Peso maior em Prospecting — a conta importa levemente mais quando o deal é novo." />
              <WeightItem icon={BarChart3} color="text-muted-foreground" weight="10%" title="Fit Produto-Setor" description="Peso maior que Engaging para compensar falta de dados de velocity." />
              <WeightItem icon={Lightbulb} color="text-warning" weight="10%" title="Janela de Oportunidade" description="Estima se engajar agora resultaria em fechamento num mês de push (fim de trimestre)." />
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <BarChart3 className="h-5 w-5 text-primary" />
            <CardTitle className="text-base">Categorias</CardTitle>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid gap-3">
            <CategoryItem emoji="🟢" label="HOT (80-100)" description="Prioridade máxima — alta afinidade + timing favorável. Ação imediata." count={2} />
            <CategoryItem emoji="🟡" label="WARM (60-79)" description="Ótima oportunidade — manter engajamento ativo e acompanhar de perto." count={175} />
            <CategoryItem emoji="🟠" label="COOL (40-59)" description="Oportunidade mediana — analisar e decidir próximo passo." count={1076} />
            <CategoryItem emoji="🔴" label="COLD (20-39)" description="Baixa probabilidade e/ou retorno — combinação de fatores desfavoráveis. Avaliar se vale o tempo investido." count={816} />
            <CategoryItem emoji="💀" label="DEAD (0-19)" description="Praticamente inviável — pipeline inflado. Considere fechar como Lost e liberar energia pra deals melhores." count={20} />
          </div>
        </CardContent>
      </Card>


      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Lightbulb className="h-5 w-5 text-chart-3" />
            <CardTitle className="text-base">Conceitos-chave</CardTitle>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4">
            <ConceptItem title="Esperança Matemática / Expected Value" description="Expected Value = (Score ÷ 100) × Preço do Produto. O score é usado como proxy de probabilidade de fechamento — um deal com score 60 é tratado como tendo ~60% de chance. O backtest com 6.711 deals históricos valida essa relação: deals COLD (score 20-39) tiveram 43% de win rate real, COOL (40-59) 60%, WARM (60-79) 73%, HOT (80-100) 88%. A relação não é 1:1 mas é consistentemente crescente." />
            <ConceptItem title="Viés de Sobrevivência" description="Deals com >90 dias no pipeline que ainda estão ativos tendem a ter win rate MAIOR que deals de 30-60 dias. Os deals fracos já morreram — os que sobrevivem são os mais promissores." />
            <ConceptItem title="Pipeline Inflado" description="83,6% dos deals em Engaging têm mais de 130 dias no pipeline. O máximo histórico de fechamento no dataset é 138 dias — ou seja, a grande maioria dos deals ativos já ultrapassou o tempo máximo em que qualquer deal foi fechado com sucesso. Deals acima de 138 dias recebem penalidade progressiva no score." />
            <ConceptItem title="Sazonalidade Trimestral" description="Fim de trimestre (mar/jun/set/dez) tem ~80% win rate vs ~53% nos outros meses. Diferença de 27pp confirmada para todos os produtos e managers. Nota: este padrão é forte nos dados históricos, mas não é usado como dimensão do score para deals em Engaging (porque o snapshot dos dados é de fim de trimestre, o que tornaria a dimensão constante para todos). Para deals em Prospecting, o conceito é capturado pela dimensão &quot;Janela de Oportunidade&quot;." />
            <ConceptItem title="Especialização de Vendedores" description="O insight mais forte dos dados. Win rates variam de 14% a 90% para o mesmo produto dependendo do vendedor. A ferramenta usa isso como dimensão principal do scoring (40% do peso)." />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <CheckCircle2 className="h-5 w-5 text-success" />
            <CardTitle className="text-base">Validação (Backtest)</CardTitle>
          </div>
          <p className="text-sm text-muted-foreground">Scoring validado contra 6.711 deals históricos.</p>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <BacktestCard label="COLD (20-39)" winRate="43%" color="text-destructive" />
            <BacktestCard label="COOL (40-59)" winRate="60%" color="text-warning" />
            <BacktestCard label="WARM (60-79)" winRate="73%" color="text-chart-3" />
            <BacktestCard label="HOT (80-100)" winRate="88%" color="text-success" />
          </div>
          <p className="text-sm text-muted-foreground mt-4">Score mais alto = probabilidade de fechamento mais alta. O modelo funciona.</p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Info className="h-5 w-5 text-muted-foreground" />
            <CardTitle className="text-base">Limitações</CardTitle>
          </div>
        </CardHeader>
        <CardContent>
          <ul className="space-y-2 text-sm text-muted-foreground">
            {[
              "Scoring é rule-based com heurísticas, não machine learning",
              "Dados estáticos (snapshot de 28/12/2017, sem integração CRM real-time)",
              "68% dos deals sem nome de conta — Account Quality usa defaults nesses casos",
              "GTK 500 tem apenas 25 deals históricos — métricas desse produto têm baixa confiabilidade",
              "Sem dados de interação (emails, calls, reuniões)",
              "Sem dados de concorrência",
              "Score não captura qualidade do relacionamento pessoal",
              "Faixa DEAD no backtest tem amostra muito pequena (3 deals) — resultado não é estatisticamente confiável",
              "Por se tratar de dados fictícios, não foi possível implementar um sistema de agentes de IA (pesquisa de empresa, compliance, geração de mensagens personalizadas para LinkedIn/email) — funcionalidade viável com dados reais de CRM",
            ].map((text, i) => (
              <li key={i} className="flex items-start gap-2">
                <AlertCircle className="h-4 w-4 mt-0.5 shrink-0 text-muted-foreground" />
                {text}
              </li>
            ))}
          </ul>
        </CardContent>
      </Card>
    </div>
  );
}
