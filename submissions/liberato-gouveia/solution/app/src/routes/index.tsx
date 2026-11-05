import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useMemo, useState } from "react";
import { CalendarDays, AlertTriangle, Search } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "Lead Scorer — Onde focar" },
      { name: "description", content: "Priorização de deals B2B a partir de dados históricos de demonstração." },
      { property: "og:title", content: "Lead Scorer — Onde focar" },
      { property: "og:description", content: "Em quais deals focar: listas, notas e ações prontas de um motor testado." },
    ],
  }),
  component: Index,
});

const URL_DADOS =
  "https://raw.githubusercontent.com/libegouv/ai-master-challenge/refs/heads/submission/liberato-gouveia/submissions/liberato-gouveia/solution/motor/saida/deals_priorizados.json";

type Deal = {
  id: string; vendedor: string; gerente: string; regiao: string; empresa: string | null;
  setor: string; produto: string; preco_usd: number; etapa: string; idade_dias: number | null;
  chance: number | null; valor_esperado_usd: number | null; nota: number | null; lista: string;
  ordem_na_lista: number; acao: string; porque: string; nota_texto: string; aviso: string | null; chance_texto: string | null;
};
type Dados = {
  data_referencia: string; limite_ciclo_dias: number;
  parametros: { valor_minimo_foco_usd: number; valor_deal_grande_usd: number };
  vendedores: { vendedor: string; gerente: string; regiao: string }[];
  curva_chance: { idade_dias: number; chance: number }[];
  validacao_volta_no_tempo: { data_corte: string; captura_top20_nossa_logica: number; captura_top20_so_valor: number };
  deals: Deal[];
};

const LISTAS = ["Foco", "Requalificar ou encerrar", "Iniciar contato", "Automatizar"] as const;
const TODOS = "__todos";

const dataBR = (s: string) => { const [a, m, d] = s.split("-"); return `${d}/${m}/${a}`; };
const usd = (n: number) => "US$ " + Math.round(n).toLocaleString("pt-BR");
const pct = (x: number) => `${Math.round(x * 100)}%`;

const ACAO_COR: Record<string, string> = {
  "Avançar este deal": "bg-act-blue",
  "Ligar para requalificar": "bg-act-orange",
  "Encerrar no CRM": "bg-act-gray",
  "Fazer o primeiro contato": "bg-act-green",
  "Incluir na cadência automática (mensagens em lote)": "bg-act-purple",
};

function Index() {
  const [dados, setDados] = useState<Dados | null>(null);
  const [erro, setErro] = useState(false);
  const [regiao, setRegiao] = useState(TODOS);
  const [gerente, setGerente] = useState(TODOS);
  const [vendedor, setVendedor] = useState(TODOS);
  const [aba, setAba] = useState<string>("Foco");

  useEffect(() => {
    fetch(URL_DADOS).then((r) => { if (!r.ok) throw 0; return r.json(); }).then(setDados).catch(() => setErro(true));
  }, []);

  const vend = dados?.vendedores ?? [];
  const regioes = [...new Set(vend.map((v) => v.regiao))].sort();
  const gerentes = [...new Set(vend.filter((v) => regiao === TODOS || v.regiao === regiao).map((v) => v.gerente))].sort();
  const vendedores = vend
    .filter((v) => (regiao === TODOS || v.regiao === regiao) && (gerente === TODOS || v.gerente === gerente))
    .map((v) => v.vendedor).sort();

  const filtrados = useMemo(
    () => (dados?.deals ?? []).filter((d) =>
      (regiao === TODOS || d.regiao === regiao) && (gerente === TODOS || d.gerente === gerente) && (vendedor === TODOS || d.vendedor === vendedor)),
    [dados, regiao, gerente, vendedor],
  );
  const porLista = useMemo(() => {
    const m = {} as Record<(typeof LISTAS)[number], Deal[]>;
    for (const l of LISTAS) m[l] = filtrados.filter((d) => d.lista === l).sort((a, b) => a.ordem_na_lista - b.ordem_na_lista);
    return m;
  }, [filtrados]);

  if (erro) return <Centro>Não foi possível carregar os dados. Tente recarregar a página.</Centro>;
  if (!dados) return <Centro>Carregando dados…</Centro>;

  const ref = dataBR(dados.data_referencia);
  const somaFoco = porLista["Foco"].reduce((s, d) => s + (d.valor_esperado_usd ?? 0), 0);
  const ligar = porLista["Requalificar ou encerrar"].filter((d) => d.acao === "Ligar para requalificar").length;
  const linhas: Record<string, string> = {
    Foco: `Avançar estes deals · ${usd(somaFoco)} em valor esperado`,
    "Requalificar ou encerrar": `Fora do ciclo histórico · ${ligar} para ligar`,
    "Iniciar contato": "Primeiro contato, por valor",
    Automatizar: "Cadência automática",
  };

  return (
    <div className="min-h-screen bg-background">
      <div className="sticky top-0 z-20 border-b border-warn-border bg-warn px-4 py-2 text-warn-foreground">
        <p className="mx-auto flex max-w-6xl items-center gap-2 text-sm font-medium">
          <CalendarDays className="h-4 w-4 shrink-0" />
          Dados históricos de demonstração: pipeline como estava em {ref}. Não são dados atuais.
        </p>
      </div>
      <main className="mx-auto max-w-6xl space-y-6 px-4 py-6">
        <header>
          <h1 className="text-2xl font-bold tracking-tight sm:text-3xl">Lead Scorer — Onde focar</h1>
          <p className="mt-1 text-muted-foreground">Situação em {ref} · {filtrados.length.toLocaleString("pt-BR")} deals abertos naquela data</p>
        </header>

        <div className="grid gap-3 sm:grid-cols-3">
          <Filtro rotulo="Região" valor={regiao} opcoes={regioes} onChange={(v) => { setRegiao(v); setGerente(TODOS); setVendedor(TODOS); }} />
          <Filtro rotulo="Gerente" valor={gerente} opcoes={gerentes} onChange={(v) => { setGerente(v); setVendedor(TODOS); }} />
          <Filtro rotulo="Vendedor" valor={vendedor} opcoes={vendedores} onChange={setVendedor} />
        </div>

        <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
          {LISTAS.map((l) => (
            <button key={l} onClick={() => setAba(l)} className="text-left">
              <Card className={`h-full transition-colors hover:border-primary ${aba === l ? "border-primary" : ""}`}>
                <CardContent className="p-4">
                  <p className="text-sm font-medium text-muted-foreground">{l}</p>
                  <p className="mt-1 text-3xl font-bold">{porLista[l].length.toLocaleString("pt-BR")}</p>
                  <p className="mt-1 text-xs text-muted-foreground">{linhas[l]}</p>
                </CardContent>
              </Card>
            </button>
          ))}
        </div>

        <Tabs value={aba} onValueChange={setAba}>
          <TabsList className="flex h-auto flex-wrap justify-start">
            {LISTAS.map((l) => <TabsTrigger key={l} value={l}>{l} ({porLista[l].length})</TabsTrigger>)}
            <TabsTrigger value="como">Como a nota funciona</TabsTrigger>
          </TabsList>
          {LISTAS.map((l) => (
            <TabsContent key={l} value={l}>
              <ListaDeals deals={porLista[l]} foco={l === "Foco"} ref_={ref} mostrarVendedor={vendedor === TODOS} />
            </TabsContent>
          ))}
          <TabsContent value="como"><ComoFunciona dados={dados} /></TabsContent>
        </Tabs>
      </main>
    </div>
  );
}

function Centro({ children }: { children: React.ReactNode }) {
  return <div className="flex min-h-screen items-center justify-center p-6 text-center text-muted-foreground">{children}</div>;
}

function Filtro({ rotulo, valor, opcoes, onChange }: { rotulo: string; valor: string; opcoes: string[]; onChange: (v: string) => void }) {
  return (
    <label className="space-y-1">
      <span className="text-sm font-medium">{rotulo}</span>
      <Select value={valor} onValueChange={onChange}>
        <SelectTrigger className="bg-card"><SelectValue /></SelectTrigger>
        <SelectContent>
          <SelectItem value={TODOS}>Todos</SelectItem>
          {opcoes.map((o) => <SelectItem key={o} value={o}>{o}</SelectItem>)}
        </SelectContent>
      </Select>
    </label>
  );
}

function ListaDeals({ deals, foco, ref_, mostrarVendedor }: { deals: Deal[]; foco: boolean; ref_: string; mostrarVendedor: boolean }) {
  const [busca, setBusca] = useState("");
  const [qtd, setQtd] = useState(25);
  useEffect(() => setQtd(25), [busca, deals]);
  const q = busca.trim().toLowerCase();
  const lista = q ? deals.filter((d) => d.id.toLowerCase().includes(q) || (d.empresa ?? "").toLowerCase().includes(q)) : deals;
  const posicao = new Map(deals.map((d, i) => [d.id, i + 1]));

  return (
    <div className="space-y-3 pt-2">
      <div className="relative">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <Input className="bg-card pl-9" placeholder="Buscar por ID do deal ou empresa" value={busca} onChange={(e) => setBusca(e.target.value)} />
      </div>
      {lista.length === 0 && <p className="py-8 text-center text-muted-foreground">Nenhum deal nesta lista para este filtro.</p>}
      {lista.slice(0, qtd).map((d) => <DealCard key={d.id} d={d} foco={foco} ref_={ref_} mostrarVendedor={mostrarVendedor} pos={posicao.get(d.id) ?? 0} />)}
      {qtd < lista.length && (
        <div className="flex justify-center">
          <Button variant="outline" onClick={() => setQtd(qtd + 25)}>Mostrar mais ({lista.length - qtd} restantes)</Button>
        </div>
      )}
    </div>
  );
}

function DealCard({ d, foco, ref_, mostrarVendedor, pos }: { d: Deal; foco: boolean; ref_: string; mostrarVendedor: boolean; pos: number }) {
  const nota = d.nota ?? 0;
  return (
    <Card>
      <CardContent className="flex gap-4 p-4">
        {foco && d.nota !== null ? (
          <div
            className="flex h-14 w-14 shrink-0 items-center justify-center rounded-lg text-xl font-bold text-primary-foreground"
            style={{ backgroundColor: `color-mix(in oklab, var(--act-blue) ${25 + nota * 0.75}%, var(--act-gray))` }}
            aria-label={`Nota ${d.nota}`}
          >{d.nota}</div>
        ) : (
          <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded-lg bg-muted text-xl font-bold text-muted-foreground">—</div>
        )}
        <div className="min-w-0 flex-1 space-y-2">
          <div className="flex flex-wrap items-baseline justify-between gap-2">
            <p className="font-semibold">{d.produto} · {usd(d.preco_usd)}</p>
            <span className="text-xs text-muted-foreground">{pos}º · {d.id}</span>
          </div>
          <p className="text-sm text-muted-foreground">
            {d.empresa ?? "Empresa não cadastrada"} · {d.etapa}
            {d.idade_dias !== null && ` · ${d.idade_dias} dias em ${d.etapa.toLowerCase()} em ${ref_}`}
            {mostrarVendedor && ` · ${d.vendedor}`}
          </p>
          <Badge className={`${ACAO_COR[d.acao] ?? "bg-act-gray"} text-primary-foreground hover:opacity-90`}>{d.acao}</Badge>
          {foco && (
            <p className="text-sm font-medium">
              Valor esperado: {d.valor_esperado_usd !== null ? usd(d.valor_esperado_usd) : "—"} · Chance: {d.chance_texto ?? "—"}
            </p>
          )}
          <p className="text-sm">{d.porque}</p>
          <p className="text-xs text-muted-foreground">{d.nota_texto}</p>
          {d.aviso && (
            <div className="flex gap-2 rounded-md border border-warn-border bg-warn p-2 text-sm text-warn-foreground">
              <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />{d.aviso}
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

function ComoFunciona({ dados }: { dados: Dados }) {
  const curva = dados.curva_chance.map((c) => ({ dias: c.idade_dias, chance: Math.round(c.chance * 1000) / 10 }));
  const chanceEm = (n: number) => Math.round((dados.curva_chance.find((c) => c.idade_dias === n)?.chance ?? 0) * 100);
  const p = dados.parametros, v = dados.validacao_volta_no_tempo;
  const blocos: [string, string][] = [
    ["O que é a nota?", "Para cada deal em negociação, multiplicamos o preço do produto pela chance de ele ser ganho. O resultado é o valor esperado: quanto o deal 'vale' na fila. A nota de 0 a 100 diz qual porcentagem dos outros deals em Foco da empresa tem valor esperado menor. 100 é o maior da empresa."],
    ["De onde vem a chance?", `Só da idade do deal (há quantos dias ele está em negociação), medida no histórico da empresa. Deals novos foram ganhos ${chanceEm(0)}% das vezes; com 90 dias, ${chanceEm(90)}%; com ${dados.limite_ciclo_dias} dias ou mais, nenhum deal da história foi ganho.`],
    ["Por que não usamos produto, setor, região ou vendedor?", "Testamos. As taxas de ganho por esses fatores são praticamente iguais (entre 60% e 65%), e um modelo de machine learning com todos eles acertou só 54% (o chute acerta 50%)."],
    ["As 4 listas.", `Foco: deals em negociação dentro do ciclo histórico, com preço a partir de US$ ${p.valor_minimo_foco_usd.toLocaleString("pt-BR")}. Requalificar ou encerrar: deals em negociação fora do ciclo histórico; a partir de US$ ${p.valor_deal_grande_usd.toLocaleString("pt-BR")}, vale uma ligação antes de encerrar. Iniciar contato: deals em prospecção, ordenados pelo preço, porque não há histórico para estimar a chance. Automatizar: deals dentro do ciclo, abaixo de US$ ${p.valor_minimo_foco_usd.toLocaleString("pt-BR")}, para cadência automática.`],
  ];
  return (
    <div className="grid gap-4 pt-2">
      {blocos.map(([t, x]) => (
        <Card key={t}><CardHeader className="pb-2"><CardTitle className="text-lg">{t}</CardTitle></CardHeader><CardContent><p>{x}</p></CardContent></Card>
      ))}
      <Card>
        <CardHeader className="pb-2"><CardTitle className="text-lg">Chance de ganho pela idade do deal</CardTitle></CardHeader>
        <CardContent className="h-72">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={curva} margin={{ left: 8, right: 8, bottom: 20 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
              <XAxis dataKey="dias" label={{ value: "dias em negociação", position: "insideBottom", offset: -12 }} />
              <YAxis label={{ value: "chance de ser ganho (%)", angle: -90, position: "insideLeft", style: { textAnchor: "middle" } }} />
              <Tooltip formatter={(val: number) => [`${val}%`, "Chance"]} labelFormatter={(l) => `${l} dias`} />
              <Line type="monotone" dataKey="chance" stroke="var(--act-blue)" strokeWidth={2} dot={false} isAnimationActive={false} />
            </LineChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
      <Card>
        <CardHeader className="pb-2"><CardTitle className="text-lg">Teste de volta no tempo</CardTitle></CardHeader>
        <CardContent><p>Em {dataBR(v.data_corte)}, os 20% de deals com maior nota nesta lógica concentravam {pct(v.captura_top20_nossa_logica)} da receita ganha nos meses seguintes. Ordenando só pelo preço, seriam {pct(v.captura_top20_so_valor)}.</p></CardContent>
      </Card>
      <p className="text-sm text-muted-foreground">O app não recalcula notas, chances nem listas: tudo vem de um motor testado (testes automáticos, incluindo um teste contra o uso de informação do futuro).</p>
    </div>
  );
}
