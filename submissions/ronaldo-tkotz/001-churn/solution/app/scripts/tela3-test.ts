/**
 * Screen 3 — support and product usage (D43) — against the RavenStack database. Run: bun run tela3-test.
 * Each number must match an independent query; filters and the alert filter must reach every block.
 */
import {
  indicadores3,
  mensal3,
  ticketsPorPrioridade,
  notasSatisfacao,
  faixasResolucao,
  faixasResposta,
  recursosMaisUsados,
  recursosErros,
} from "../src/engine/tela3";
import { lerFiltros } from "../src/engine/filtros";
import { runQuery } from "../src/engine/warehouse";

let failed = 0;
function check(name: string, cond: boolean, detail = ""): void {
  process.stdout.write(`${cond ? "✓" : "✗"} ${name}${detail ? ` — ${detail}` : ""}\n`);
  if (!cond) failed++;
}
const one = (sql: string) => Number(Object.values(runQuery(sql).rows[0])[0]);
const soma = (xs: number[]) => xs.reduce((a, b) => a + b, 0);
const somaS = (s: { dados: { value: number }[] }) => soma(s.dados.map((d) => d.value));
const f = lerFiltros({});

// Headline numbers.
const k = indicadores3(f);
check("2.000 tickets em 492 contas", k.tickets === 2000 && k.contasComTicket === 492, `${k.tickets} / ${k.contasComTicket}`);
check("95 escalados", k.escalados === 95);
check("satisfação média = consulta independente (3,98)", k.satisfacao === one("SELECT round(avg(satisfaction_score), 2) FROM support_tickets") && k.satisfacao === 3.98);
check("41,3% sem nota (825 de 2.000)", k.semNotaPct === 41.3, String(k.semNotaPct));
check("usos = soma de usage_count", k.usos === one("SELECT sum(usage_count) FROM feature_usage"), String(k.usos));
check("erros = soma de error_count", k.erros === one("SELECT sum(error_count) FROM feature_usage"));
check("taxa de erro = erros / usos", k.taxaErroPct === Math.round((10000 * k.erros) / k.usos) / 100, String(k.taxaErroPct));

// Month by month.
const m = mensal3(f);
check("24 meses, de 2023-01 a 2024-12", m.meses.length === 24 && m.meses[0] === "2023-01" && m.meses[23] === "2024-12");
check("tickets por mês somam 2.000", soma(m.tickets) === 2000, String(soma(m.tickets)));
check("escalados por mês somam 95", soma(m.escalados) === 95);
check("usos por mês somam o total", soma(m.usos) === k.usos);
check("dez/2024: 98 tickets", m.tickets[23] === 98 && m.tickets[23] === one("SELECT count(*) FROM support_tickets WHERE substr(submitted_at, 1, 7) = '2024-12'"));

// How the tickets split.
check("prioridades somam 2.000, urgente primeiro", somaS(ticketsPorPrioridade(f)) === 2000 && ticketsPorPrioridade(f).dados[0].label === "Urgente");
const notas = notasSatisfacao(f);
check("notas somam 2.000, 'Sem nota' = 825", somaS(notas) === 2000 && notas.dados.find((d) => d.label === "Sem nota")?.value === 825);
check("faixas de resolução somam 2.000", somaS(faixasResolucao(f)) === 2000);
check("faixas de 1ª resposta somam 2.000", somaS(faixasResposta(f)) === 2000);

// Features.
const top = recursosMaisUsados(f);
check("10 recursos mais usados, em ordem", top.dados.length === 10 && top.dados.every((d, i) => i === 0 || d.value <= top.dados[i - 1].value));
const r = recursosErros(f);
check("recursos: 40 × (estável, beta) = 80 pontos", r.recursos.length === 80);
check("usos dos pontos somam o total", soma(r.recursos.map((x) => x.usos)) === k.usos);

// Filters and alerts.
const sem = indicadores3(lerFiltros({ alerta: "sem" }));
check("sem alertas: 923 tickets (sem os T08)", sem.tickets === 923, String(sem.tickets));
check("sem alertas: menos usos (sem T06/E13)", sem.usos < k.usos);
const fin = indicadores3(lerFiltros({ setor: "FinTech" }));
check("FinTech: tickets = consulta independente", fin.tickets === one("SELECT count(*) FROM support_tickets WHERE account_id IN (SELECT account_id FROM accounts WHERE industry = 'FinTech')"), String(fin.tickets));
const proUsos = one("SELECT sum(u.usage_count) FROM feature_usage u JOIN subscriptions s ON s.subscription_id = u.subscription_id WHERE s.plan_tier = 'Pro'");
check("plano Pro: usos pelo plano da assinatura", indicadores3(lerFiltros({ plano: "Pro" })).usos === proUsos, String(proUsos));

process.stdout.write(failed === 0 ? "\nTELA 3 OK\n" : `\n${failed} FAILED\n`);
process.exit(failed === 0 ? 0 : 1);
