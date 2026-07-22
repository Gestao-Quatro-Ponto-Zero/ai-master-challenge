import { loadData } from "@/lib/data";
import { DataFreshness, SectionHeader } from "@/components/ui";
import { GuidedDemo } from "@/components/GuidedDemo";

interface Story { demo_accounts: string[]; steps: Array<{ step: number; route: string }> }
interface Metadata { data_cutoff: string }
const copy = [
  ["O problema", "Eventos fragmentados ocultam a jornada do cliente.", "35.586 eventos processados", "Fontes brutas exigem governança antes da interpretação.", "Somente snapshot histórico."],
  ["Qualidade antes da interpretação", "A qualidade é controlada, não escondida.", "13.927 eventos utilizáveis", "Alertas permanecem visíveis e a quarentena continua excluída.", "A população principal inclui eventos com alerta."],
  ["Reconstruir a jornada", "Eventos tornam-se linhas do tempo delimitadas e explicáveis.", "4.221 jornadas", "Perfis anônimos mostram diferentes desfechos observados.", "Exemplos de conta não são estimativas representativas."],
  ["Encontrar caminhos recorrentes", "Sequências repetidas são contadas por conta.", "435 padrões promovíveis", "Suporte e denominador aparecem juntos.", "Ordenação no mesmo dia não é evidência causal."],
  ["Organizar evidências no grafo", "Um grafo reduzido conecta eventos, padrões, achados e revisões.", "43 transições promovíveis", "Somente relações analíticas governadas são exibidas.", "Relações do grafo são descritivas."],
  ["Construir uma fila de revisão humana", "Regras priorizam a investigação sem pontuação individual.", "7 filas de revisão", "Comportamento e qualidade permanecem visualmente separados.", "Intervenção automática não é permitida."],
  ["Converter observações em hipóteses testáveis", "O Laboratório de Experimentos separa observação de teste causal.", "8 desenhos não testados", "A viabilidade amostral aparece antes da promoção.", "Nenhum experimento foi executado."],
  ["Preservar a governança", "Cada camada expõe restrições e decisões humanas autorizadas.", "97 decisões registradas", "Reprodutibilidade e privacidade são características do produto.", "A demo não é um plano de controle de produção."]
] as const;

export default async function DemoPage() {
  const [story, metadata] = await Promise.all([loadData<Story>("demo_story.json"), loadData<Metadata>("metadata.json")]);
  const steps = story.steps.map((step, index) => ({ ...step, title: copy[index][0], sentence: copy[index][1], metric: copy[index][2], insight: copy[index][3], limitation: copy[index][4] }));
  const profiles = ["Perfil A — sem churn observado", "Perfil B — churn recorrente", "Perfil C — reativação e retorno de uso"];
  return <div><SectionHeader eyebrow="Demonstração guiada" title="Oito etapas dos dados brutos às decisões governadas." description="Uma narrativa concisa para avaliação: um visual, uma métrica, um insight e uma limitação em cada etapa." /><DataFreshness cutoff={metadata.data_cutoff} /><div className="mt-7"><GuidedDemo steps={steps} duration="2–4" /></div><section className="mt-7 panel p-5"><p className="eyebrow">Perfis anônimos da demonstração</p><div className="mt-4 flex flex-wrap gap-3">{story.demo_accounts.map((account, index) => <span className="rounded-lg border border-line bg-slate-50 px-3 py-2 text-xs font-semibold" key={account}>{profiles[index]}</span>)}</div></section></div>;
}
