// Saúde dos dados: verifica uma exportação de tickets antes de usá-la para decidir.
// Mesmo código no navegador (upload) e no Node (gera o resultado padrão do Dataset 1).

function parseCSV(text) {
  const rows = [];
  let row = [], field = "", inQuotes = false;
  for (let i = 0; i < text.length; i++) {
    const ch = text[i];
    if (inQuotes) {
      if (ch === '"') {
        if (text[i + 1] === '"') { field += '"'; i++; } else inQuotes = false;
      } else field += ch;
    } else if (ch === '"') inQuotes = true;
    else if (ch === ",") { row.push(field); field = ""; }
    else if (ch === "\n" || ch === "\r") {
      if (ch === "\r" && text[i + 1] === "\n") i++;
      row.push(field); rows.push(row); row = []; field = "";
    } else field += ch;
  }
  if (field !== "" || row.length) { row.push(field); rows.push(row); }
  const header = rows.shift();
  return { header, rows: rows.filter((r) => r.length === header.length) };
}

function runChecks({ header, rows }) {
  const col = (re) => header.findIndex((h) => re.test(h));
  const iStatus = col(/status/i), iPrio = col(/priority|prioridade/i);
  const iFirst = col(/first response/i), iRes = col(/time to resolution|resolution time|resolved/i);
  const iDesc = col(/description|descri/i), iCsat = col(/satisfaction|csat/i);
  const iOpen = col(/created|opened|open date|abertura|creation|submitted/i);
  const n = rows.length;
  const out = [];
  const pc = (x) => (x * 100).toFixed(1).replace(".", ",") + "%";

  out.push({ title: "Volume do arquivo", status: "info", value: n.toLocaleString("pt-BR") + " tickets",
    detail: "Compare com o volume que a operação declara para o período." });

  out.push(iOpen >= 0
    ? { title: "Data de abertura do ticket", status: "ok", value: "presente", detail: `Coluna "${header[iOpen]}".` }
    : { title: "Data de abertura do ticket", status: "critico", value: "ausente",
        detail: "Sem a hora de abertura não existe tempo de resolução nem tempo de espera. Qualquer \"gargalo de tempo\" calculado com este arquivo é inválido." });

  if (iFirst >= 0 && iRes >= 0) {
    let both = 0, neg = 0, min = Infinity, max = -Infinity;
    for (const r of rows) {
      const a = Date.parse(r[iFirst]), b = Date.parse(r[iRes]);
      if (!isNaN(a)) { min = Math.min(min, a); max = Math.max(max, a); }
      if (!isNaN(a) && !isNaN(b)) { both++; if (b < a) neg++; }
    }
    const share = both ? neg / both : 0;
    out.push({ title: "Resolução antes da primeira resposta", status: share > 0.02 ? "critico" : "ok",
      value: pc(share) + " dos fechados", detail: `${neg.toLocaleString("pt-BR")} de ${both.toLocaleString("pt-BR")} tickets têm horário de resolução anterior ao da primeira resposta. É impossível numa operação real.` });
    const spanH = (max - min) / 36e5;
    out.push({ title: "Janela dos horários registrados", status: spanH < 72 && n > 1000 ? "critico" : "ok",
      value: spanH.toFixed(0) + " horas",
      detail: `Todas as primeiras respostas cabem em ${spanH.toFixed(0)} h. Em uma operação com milhares de tickets, isso indica que os campos de tempo são horários soltos, não durações.` });
  }

  if (iDesc >= 0) {
    const ph = rows.filter((r) => /\{[a-z_]+\}/.test(r[iDesc])).length;
    out.push({ title: "Texto com campos de modelo não preenchidos", status: ph / n > 0.05 ? "critico" : "ok",
      value: pc(ph / n), detail: "Descrições com marcadores como {product_purchased} indicam texto gerado por modelo, não escrito por clientes. Não servem para treinar IA." });
  }

  if (iCsat >= 0) {
    const counts = [1, 2, 3, 4, 5].map((v) => rows.filter((r) => Number(r[iCsat]) === v).length);
    const filled = counts.reduce((a, b) => a + b, 0);
    const mean = filled / 5;
    const flat = counts.every((c) => Math.abs(c - mean) / mean < 0.1);
    out.push({ title: "Distribuição da satisfação", status: flat ? "alerta" : "ok",
      value: counts.join(" / "), detail: (flat ? "As notas 1 a 5 aparecem quase na mesma quantidade. Notas reais costumam se concentrar nos extremos ou no topo. " : "") + `Preenchida em ${pc(filled / n)} dos tickets.` });
  }

  if (iStatus >= 0 && iPrio >= 0) {
    const rate = (p) => { const s = rows.filter((r) => r[iPrio] === p); return s.length ? s.filter((r) => /^open$/i.test(r[iStatus])).length / s.length : NaN; };
    const crit = rate("Critical"), low = rate("Low");
    if (!isNaN(crit) && !isNaN(low)) out.push({ title: "Efeito da prioridade", status: Math.abs(crit - low) < 0.03 ? "alerta" : "ok",
      value: `Critical ${pc(crit)} × Low ${pc(low)}`, detail: "Percentual de tickets ainda sem primeira resposta. Se Critical e Low são iguais, ou a triagem por urgência não acontece ou não é registrada." });
  }
  return out;
}

if (typeof module !== "undefined") module.exports = { parseCSV, runChecks };
