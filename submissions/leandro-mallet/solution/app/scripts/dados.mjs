// Traz os dados limpos para dentro do app (data/base.json), para o app rodar sozinho a partir
// da própria pasta (inclusive publicado). Copia também o arquivo de notas, se existir.
//
// Uso:  node scripts/dados.mjs <pasta solution/data>     (padrão: ../data)
import { existsSync, mkdirSync, readFileSync, writeFileSync, copyFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const app = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const origem = resolve(process.argv[2] ?? join(app, "..", "data"));
const clean = join(origem, "clean");
if (!existsSync(join(clean, "deals.csv"))) {
  console.error(`Não achei ${join(clean, "deals.csv")}. Informe a pasta solution/data.`);
  process.exit(2);
}

/** CSV com aspas opcionais (os arquivos limpos não têm quebra de linha dentro de campo). */
function lerCsv(arquivo) {
  const linhas = readFileSync(join(clean, arquivo), "utf8").replace(/\r/g, "").split("\n").filter(Boolean);
  const campos = (l) => {
    const out = [];
    let atual = "";
    let aspas = false;
    for (let i = 0; i < l.length; i++) {
      const c = l[i];
      if (c === '"') {
        if (aspas && l[i + 1] === '"') { atual += '"'; i++; } else aspas = !aspas;
      } else if (c === "," && !aspas) { out.push(atual); atual = ""; } else atual += c;
    }
    out.push(atual);
    return out;
  };
  const nomes = campos(linhas[0]);
  return linhas.slice(1).map((l) => Object.fromEntries(campos(l).map((v, i) => [nomes[i], v])));
}

const vazio = (t) => (t === undefined || t.trim() === "" ? null : t.trim());
const int = (t) => (vazio(t) === null ? null : Math.round(Number(t)));
const num = (t) => (vazio(t) === null ? null : Number(t));

const deals = lerCsv("deals.csv");
const base = {
  dataReferencia: deals.reduce((m, d) => (d.close_date > m ? d.close_date : m), ""),
  equipe: lerCsv("sales_teams.csv").map((r) => ({ vendedor: r.sales_agent, manager: r.manager, regiao: r.regional_office })),
  produtos: lerCsv("products.csv").map((r) => ({ nome: r.product, serie: r.series, preco: int(r.sales_price) })),
  contas: lerCsv("accounts.csv").map((r) => ({
    nome: r.account,
    setor: vazio(r.sector),
    anoFundacao: int(r.year_established),
    receitaMilhoes: num(r.revenue),
    funcionarios: int(r.employees),
    porte: vazio(r.employees_band),
    sede: vazio(r.office_location),
    empresaMae: vazio(r.subsidiary_of),
  })),
  // [id, vendedor, produto, conta, estagio, abertura, fechamento, valor]
  colunasDeals: ["id", "vendedor", "produto", "conta", "estagio", "dataAbertura", "closeDate", "closeValue"],
  deals: deals.map((r) => [r.opportunity_id, r.sales_agent, r.product, vazio(r.account), r.deal_stage, vazio(r.engage_date), vazio(r.close_date), int(r.close_value)]),
};

mkdirSync(join(app, "data"), { recursive: true });
writeFileSync(join(app, "data", "base.json"), JSON.stringify(base) + "\n", "utf8");
console.log(`data/base.json: ${base.deals.length} deals, ${base.contas.length} contas, ${base.equipe.length} vendedores, ${base.produtos.length} produtos; referência ${base.dataReferencia}`);

const notas = join(origem, "scored", "deals_scored.json");
if (existsSync(notas)) {
  copyFileSync(notas, join(app, "data", "deals_scored.json"));
  console.log("data/deals_scored.json copiado (notas do score).");
} else {
  console.log("Sem deals_scored.json: o app mostra \"Sem nota ainda\".");
}
