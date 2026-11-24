import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import raw from "./mrr.json";
import { Tecnico } from "./charts";
import { dec, int, pct, usd, usdK } from "./format";
import type { Palette } from "./theme";

const A = raw.auditoria;

export function Receita({ pal }: { pal: Palette }) {
  const precos = Object.entries(A.preco_por_assento).sort((a, b) => a[1] - b[1]);
  return (
    <section className="block" id="receita">
      <div className="eyebrow">Qualidade dos dados</div>
      <h2>A receita registrada também não é confiável</h2>
      <p className="lede">A receita mensal de cada serviço parece ser calculada, e não copiada do que foi cobrado. Os clientes aparecem com vários
        serviços ativos ao mesmo tempo, o que infla a soma da receita.</p>
      <div className="grid2">
        <div className="card">
          <h3>Metade dos clientes tem {dec(A.ativas_simult_mediana, 0)} ou mais assinaturas ativas ao mesmo tempo</h3>
          <p className="note" style={{ fontSize: 14 }}>Só <b>{int(A.contas_com_uma)} de {int(A.contas_com_ativas)}</b> clientes têm uma assinatura só. Parece que renovações e
            trocas de plano abrem uma assinatura nova sem fechar a anterior. Por isso a receita mensal somada, <b>{usdK(A.mrr_total_ativo)}</b>,
            provavelmente está inflada e não deve ser usada como valor real.</p>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={A.dist_simultaneas} margin={{ top: 10, right: 8, left: 0, bottom: 14 }} barCategoryGap="14%">
              <CartesianGrid vertical={false} stroke={pal["--grid"]} />
              <XAxis dataKey="n" stroke={pal["--axis"]} tick={{ fill: pal["--muted"], fontSize: 11 }} tickLine={false}
                label={{ value: "assinaturas ativas ao mesmo tempo", position: "insideBottom", offset: -8, fill: pal["--muted"], fontSize: 11 }} />
              <YAxis stroke={pal["--axis"]} tick={{ fill: pal["--muted"], fontSize: 11 }} tickLine={false} axisLine={false} width={36} />
              <Tooltip cursor={{ fill: pal["--grid"], opacity: 0.5 }} content={({ active, payload }) => {
                if (!active || !payload?.length) return null;
                const x = payload[0].payload as { n: number; contas: number };
                return <div className="tt"><b>{x.n} assinatura{x.n > 1 ? "s" : ""} ativa{x.n > 1 ? "s" : ""}</b><div className="row"><span>Clientes</span><span>{int(x.contas)}</span></div></div>;
              }} />
              <Bar dataKey="contas" name="Clientes" radius={[3, 3, 0, 0]} isAnimationActive={false}>
                {A.dist_simultaneas.map((x) => <Cell key={x.n} fill={x.n === 1 ? pal["--s3"] : pal["--s1"]} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
          <p className="foot">Em verde, quem tem uma assinatura só, o esperado para a maioria dos clientes.</p>
        </div>
        <div className="card">
          <h3>A receita é uma conta, não o valor cobrado</h3>
          <p className="note" style={{ fontSize: 14 }}>Em <b>{pct(A.pct_mrr_formula, 0)}</b> das assinaturas, a receita mensal é exatamente o número de usuários contratados
            vezes um preço fixo por usuário:</p>
          <div className="precos">
            {precos.map(([plano, v]) => (
              <div key={plano}><span>{plano}</span><b>{usd(v)}</b><small>por usuário/mês</small></div>
            ))}
          </div>
          <p className="note" style={{ fontSize: 14 }}>Nenhum desconto, nenhuma cobrança proporcional, nenhuma negociação. Na prática, isso quase nunca acontece.</p>
          <h3 style={{ marginTop: 16 }}>E o cadastro não bate com as assinaturas</h3>
          <ul style={{ margin: "6px 0 0", paddingLeft: 18, fontSize: 14, color: pal["--ink-2"] }}>
            <li>O plano anotado na conta coincide com o plano das assinaturas em só <b style={{ color: pal["--ink"] }}>{dec(A.pct_plano_conta_bate * 100, 0)} de cada 100</b> clientes, quase o mesmo que sortear.</li>
            <li>O número de usuários do cadastro não acompanha o das assinaturas ativas.</li>
            <li><b style={{ color: pal["--ink"] }}>{int(A.upgrade_e_downgrade)}</b> assinaturas estão marcadas, ao mesmo tempo, como troca para plano maior e para plano menor.</li>
          </ul>
        </div>
      </div>
      <Tecnico>
        <div className="stats">
          <span><b>{pct(A.pct_mrr_formula, 0)}</b> MRR = assentos × preço de tabela</span>
          <span><b>{pct(A.pct_arr_12x, 0)}</b> ARR = 12 × MRR</span>
          <span><b>mediana {usd(A.mrr_conta_mediana)}</b> MRR ativo por conta (máx. {usd(A.mrr_conta_max)})</span>
          <span><b>ρ = {dec(A.rho_assentos, 2)}</b> assentos da conta × soma dos assentos ativos</span>
        </div>
        <p>Detalhes em docs/auditoria_mrr.md (script 08).</p>
      </Tecnico>
      <div className="verdict"><span className="tag partial">Conclusão</span>
        <span>A receita serve para comparar grupos de clientes entre si, mas o total de receita mensal não deve ser tratado como valor real até
          vir do sistema de cobrança, com uma assinatura ativa por serviço.</span>
      </div>
    </section>
  );
}
