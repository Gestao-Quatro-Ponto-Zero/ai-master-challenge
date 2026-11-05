import { jsPDF } from "jspdf";
import autoTable from "jspdf-autotable";
import * as XLSX from "xlsx-js-style";
import type { Deal } from "@/hooks/useDeals";
import type { ResumoVendedor } from "@/hooks/useResumoVendedores";
import type { Filters } from "@/lib/filters";
import { formatDate, formatNumber, formatPct, formatUSD } from "@/lib/format";
import { pctParado, sortFocar, sortProspectar, sortRequalificar, type Indicadores } from "@/lib/metrics";

/** Paleta G4 (equivalentes RGB dos tokens oklch do app). */
const NAVY: [number, number, number] = [31, 42, 58];
const GOLD: [number, number, number] = [201, 162, 39];
const GOLD_SOFT: [number, number, number] = [247, 240, 222];
const GRAY: [number, number, number] = [110, 116, 128];

const NAVY_HEX = "1F2A3A";
const GOLD_HEX = "C9A227";
const GOLD_SOFT_HEX = "F7F0DE";

export function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 30_000);
}

function hoje(): string {
  return new Date().toISOString().slice(0, 10);
}

function filtroLabel(f: Filters): string {
  const parte = (label: string, v: string) => `${label}: ${v || "Todos"}`;
  return `${parte("Região", f.regiao)} · ${parte("Manager", f.manager)} · ${parte("Vendedor", f.vendedor)}`;
}

function cabecalhoPdf(doc: jsPDF, titulo: string, filtros: string) {
  const w = doc.internal.pageSize.getWidth();
  doc.setFillColor(...NAVY);
  doc.rect(0, 0, w, 22, "F");
  doc.setFillColor(...GOLD);
  doc.circle(12, 11, 2.2, "F");
  doc.setFont("helvetica", "bold");
  doc.setFontSize(14);
  doc.setTextColor(255, 255, 255);
  doc.text(titulo, 18, 12.5);
  doc.setFont("helvetica", "normal");
  doc.setFontSize(9);
  doc.setTextColor(...GOLD_SOFT);
  doc.text(filtros, 18, 18);
  doc.setTextColor(...GRAY);
  doc.text("Retrato do CRM em 31/12/2017", w - 14, 18, { align: "right" });
}

function rodapePdf(doc: jsPDF) {
  const w = doc.internal.pageSize.getWidth();
  const h = doc.internal.pageSize.getHeight();
  const total = doc.getNumberOfPages();
  for (let i = 1; i <= total; i++) {
    doc.setPage(i);
    doc.setFontSize(8);
    doc.setTextColor(...GRAY);
    doc.text(`Lead Scorer · gerado em ${formatDate(hoje())} · página ${i} de ${total}`, w / 2, h - 6, { align: "center" });
  }
}

type LinhaDeal = {
  Score: number | null;
  Oportunidade: string;
  Produto: string;
  Conta: string;
  Vendedor: string;
  Manager: string;
  Região: string;
  "Idade (dias)": number | null;
  Estágio: string;
  "Chance de ganho": number | null;
  "Valor esperado (US$)": number | null;
  "Preço de lista (US$)": number | null;
  "Prazo limite": string;
  "Dias até o limite": number | null;
  Momento: string;
  "Sem conta": string;
  "Possível duplicata": string;
};

function dealToRow(d: Deal): LinhaDeal {
  return {
    Score: d.score,
    Oportunidade: `${d.opportunity_id ?? ""} ${d.product ?? ""}`.trim(),
    Produto: d.product ?? "",
    Conta: d.account ?? "",
    Vendedor: d.sales_agent ?? "",
    Manager: d.manager ?? "",
    Região: d.regional_office ?? "",
    "Idade (dias)": d.idade_dias,
    Estágio: d.deal_stage ?? "",
    "Chance de ganho": d.p_ganho,
    "Valor esperado (US$)": d.valor_esperado,
    "Preço de lista (US$)": d.sales_price,
    "Prazo limite": formatDate(d.prazo_limite),
    "Dias até o limite": d.dias_ate_limite,
    Momento: d.momento ?? "",
    "Sem conta": d.sem_conta ? "sim" : "",
    "Possível duplicata": d.possivel_duplicata ? "sim" : "",
  };
}

function filasDeals(deals: Deal[]) {
  return {
    focar: deals.filter((d) => d.fila === "focar").sort(sortFocar),
    requalificar: deals.filter((d) => d.fila === "requalificar").sort(sortRequalificar),
    prospectar: deals.filter((d) => d.fila === "prospectar").sort(sortProspectar),
  };
}

const headerStyle = {
  font: { bold: true, color: { rgb: "FFFFFF" }, sz: 11 },
  fill: { patternType: "solid", fgColor: { rgb: NAVY_HEX } },
  alignment: { vertical: "center" },
};

function sheetFromRows(rows: LinhaDeal[]) {
  const ws = XLSX.utils.json_to_sheet(rows);
  const range = XLSX.utils.decode_range(ws["!ref"] ?? "A1");
  for (let c = range.s.c; c <= range.e.c; c++) {
    const addr = XLSX.utils.encode_cell({ r: 0, c });
    if (ws[addr]) ws[addr].s = headerStyle;
  }
  ws["!cols"] = Object.keys(rows[0] ?? { v: 1 }).map((k) => ({ wch: Math.max(12, Math.min(28, k.length + 4)) }));
  ws["!rows"] = [{ hpt: 20 }];
  return ws;
}

function salvarXlsx(wb: XLSX.WorkBook, nome: string) {
  const out = XLSX.write(wb, { bookType: "xlsx", type: "array" });
  downloadBlob(new Blob([out], { type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" }), nome);
}

// ---------- Meu pipeline ----------

export function exportPipelineXlsx(deals: Deal[], filters: Filters) {
  const { focar, requalificar, prospectar } = filasDeals(deals);
  const wb = XLSX.utils.book_new();
  const resumo = [
    { Campo: "Filtros", Valor: filtroLabel(filters) },
    { Campo: "Retrato do CRM", Valor: "31/12/2017" },
    { Campo: "Deals para focar", Valor: focar.length },
    { Campo: "Parados para requalificar", Valor: requalificar.length },
    { Campo: "Prospectar", Valor: prospectar.length },
  ];
  const wsResumo = XLSX.utils.json_to_sheet(resumo);
  const r = XLSX.utils.decode_range(wsResumo["!ref"] ?? "A1");
  for (let c = r.s.c; c <= r.e.c; c++) {
    const addr = XLSX.utils.encode_cell({ r: 0, c });
    if (wsResumo[addr]) wsResumo[addr].s = headerStyle;
  }
  wsResumo["!cols"] = [{ wch: 28 }, { wch: 80 }];
  XLSX.utils.book_append_sheet(wb, wsResumo, "Resumo");
  XLSX.utils.book_append_sheet(wb, sheetFromRows(focar.map(dealToRow)), "Focar agora");
  XLSX.utils.book_append_sheet(wb, sheetFromRows(requalificar.map(dealToRow)), "Requalificar ou encerrar");
  XLSX.utils.book_append_sheet(wb, sheetFromRows(prospectar.map(dealToRow)), "Prospectar");
  salvarXlsx(wb, `lead-scorer-pipeline-${hoje()}.xlsx`);
}

export function exportPipelinePdf(deals: Deal[], filters: Filters, ind: Indicadores) {
  const doc = new jsPDF({ orientation: "landscape", unit: "mm", format: "a4" });
  cabecalhoPdf(doc, "Meu pipeline — Lead Scorer", filtroLabel(filters));

  doc.setFontSize(11);
  doc.setTextColor(...NAVY);
  doc.setFont("helvetica", "bold");
  doc.text("Resumo do recorte", 14, 32);
  doc.setFont("helvetica", "normal");
  doc.setFontSize(9);
  doc.setTextColor(60, 60, 60);
  doc.text(
    `Deals para focar: ${formatNumber(ind.focar)} (${formatUSD(ind.valorEsperadoFocar)} de valor esperado) · ` +
      `Na reta final: ${formatNumber(ind.retaFinal)} · Parados para requalificar: ${formatNumber(ind.requalificar)} ` +
      `(${formatUSD(ind.valorParado)} travado) · Prospectar: ${formatNumber(ind.prospectar)} · Sem conta cadastrada: ${formatNumber(ind.semConta)}`,
    14,
    38,
    { maxWidth: 270 },
  );

  const { focar, requalificar, prospectar } = filasDeals(deals);
  const colunas = ["Score", "Oportunidade", "Conta", "Vendedor", "Manager", "Idade", "Chance", "Valor esperado", "Preço de lista", "Prazo limite"];
  const linhaPdf = (d: Deal) => [
    d.score ?? "—",
    `${d.opportunity_id ?? ""}\n${d.product ?? ""}`.trim(),
    d.account ?? (d.sem_conta ? "sem conta" : "—"),
    d.sales_agent ?? "—",
    d.manager ?? "—",
    d.idade_dias != null ? `${d.idade_dias}d` : "—",
    formatPct(d.p_ganho),
    formatUSD(d.valor_esperado),
    formatUSD(d.sales_price),
    d.prazo_limite ? `${formatDate(d.prazo_limite)}${d.dias_ate_limite != null ? ` (${d.dias_ate_limite}d)` : ""}` : "—",
  ];

  const secoes: { titulo: string; rows: Deal[] }[] = [
    { titulo: `Focar agora (${focar.length})`, rows: focar },
    { titulo: `Requalificar ou encerrar (${requalificar.length})`, rows: requalificar },
    { titulo: `Prospectar (${prospectar.length})`, rows: prospectar },
  ];

  let y = 46;
  secoes.forEach((sec, i) => {
    if (i > 0) {
      doc.addPage();
      y = 20;
    }
    doc.setFont("helvetica", "bold");
    doc.setFontSize(11);
    doc.setTextColor(...NAVY);
    doc.text(sec.titulo, 14, y);
    autoTable(doc, {
      startY: y + 3,
      head: [colunas],
      body: sec.rows.map(linhaPdf),
      styles: { fontSize: 7.5, cellPadding: 1.4, textColor: [40, 40, 40] },
      headStyles: { fillColor: NAVY, textColor: [255, 255, 255], fontStyle: "bold" },
      alternateRowStyles: { fillColor: GOLD_SOFT },
      columnStyles: { 0: { textColor: GOLD, fontStyle: "bold" } },
      margin: { left: 14, right: 14 },
    });
  });

  rodapePdf(doc);
  downloadBlob(doc.output("blob"), `lead-scorer-pipeline-${hoje()}.pdf`);
}

// ---------- Visão do gestor ----------

export type ResumoRow = ResumoVendedor & { pct_parado: number };

const gestorHeaders = [
  "Vendedor", "Manager", "Região", "Focar", "Valor esperado em foco (US$)", "Reta final",
  "Parados", "Valor parado (US$)", "% do aberto parado", "Sem conta", "Possível duplicata", "Ganhos", "Perdidos",
];

function gestorRowValues(r: ResumoRow): (string | number)[] {
  return [
    r.sales_agent ?? "",
    r.manager ?? "",
    r.regional_office ?? "",
    r.deals_focar ?? 0,
    r.valor_esperado_focar ?? 0,
    r.deals_reta_final ?? 0,
    r.deals_requalificar ?? 0,
    r.valor_parado ?? 0,
    Math.round(r.pct_parado * 100) / 100,
    r.deals_sem_conta ?? 0,
    r.deals_possivel_duplicata ?? 0,
    r.ganhos ?? 0,
    r.perdidos ?? 0,
  ];
}

export function exportGestorXlsx(rows: ResumoRow[], filters: Filters) {
  const wb = XLSX.utils.book_new();
  const dados = [
    { Campo: "Filtros", Valor: filtroLabel(filters) },
    { Campo: "Retrato do CRM", Valor: "31/12/2017" },
    { Campo: "Vendedores no recorte", Valor: rows.length },
  ];
  const wsResumo = XLSX.utils.json_to_sheet(dados);
  const rr = XLSX.utils.decode_range(wsResumo["!ref"] ?? "A1");
  for (let c = rr.s.c; c <= rr.e.c; c++) {
    const addr = XLSX.utils.encode_cell({ r: 0, c });
    if (wsResumo[addr]) wsResumo[addr].s = headerStyle;
  }
  wsResumo["!cols"] = [{ wch: 28 }, { wch: 80 }];
  XLSX.utils.book_append_sheet(wb, wsResumo, "Resumo");

  const ws = XLSX.utils.aoa_to_sheet([gestorHeaders, ...rows.map(gestorRowValues)]);
  const range = XLSX.utils.decode_range(ws["!ref"] ?? "A1");
  for (let c = range.s.c; c <= range.e.c; c++) {
    const addr = XLSX.utils.encode_cell({ r: 0, c });
    if (ws[addr]) ws[addr].s = headerStyle;
  }
  for (let rIdx = 1; rIdx <= rows.length; rIdx++) {
    const row = rows[rIdx - 1]!;
    if (row.pct_parado > 0.7) {
      for (let c = range.s.c; c <= range.e.c; c++) {
        const addr = XLSX.utils.encode_cell({ r: rIdx, c });
        if (ws[addr]) ws[addr].s = { fill: { patternType: "solid", fgColor: { rgb: GOLD_SOFT_HEX } } };
      }
    }
    const pctAddr = XLSX.utils.encode_cell({ r: rIdx, c: 8 });
    if (ws[pctAddr]) ws[pctAddr].z = "0%";
  }
  ws["!cols"] = gestorHeaders.map((h) => ({ wch: Math.max(14, Math.min(30, h.length + 4)) }));
  XLSX.utils.book_append_sheet(wb, ws, "Por vendedor");
  salvarXlsx(wb, `lead-scorer-gestor-${hoje()}.xlsx`);
}

export function exportGestorPdf(rows: ResumoRow[], filters: Filters, ind: Indicadores) {
  const doc = new jsPDF({ orientation: "landscape", unit: "mm", format: "a4" });
  cabecalhoPdf(doc, "Visão do gestor — Lead Scorer", filtroLabel(filters));

  doc.setFont("helvetica", "bold");
  doc.setFontSize(11);
  doc.setTextColor(...NAVY);
  doc.text("Resumo do recorte", 14, 32);
  doc.setFont("helvetica", "normal");
  doc.setFontSize(9);
  doc.setTextColor(60, 60, 60);
  doc.text(
    `Vendedores: ${formatNumber(rows.length)} · Deals para focar: ${formatNumber(ind.focar)} (${formatUSD(ind.valorEsperadoFocar)}) · ` +
      `Parados: ${formatNumber(ind.requalificar)} (${formatUSD(ind.valorParado)} travado) · Sem conta: ${formatNumber(ind.semConta)}`,
    14,
    38,
    { maxWidth: 270 },
  );

  autoTable(doc, {
    startY: 44,
    head: [["Vendedor", "Manager", "Região", "Focar", "Valor em foco", "Reta final", "Parados", "Valor parado", "% parado", "Sem conta", "Duplicata"]],
    body: rows.map((r) => [
      r.sales_agent ?? "—",
      r.manager ?? "—",
      r.regional_office ?? "—",
      formatNumber(r.deals_focar),
      formatUSD(r.valor_esperado_focar),
      formatNumber(r.deals_reta_final),
      formatNumber(r.deals_requalificar),
      formatUSD(r.valor_parado),
      formatPct(r.pct_parado),
      formatNumber(r.deals_sem_conta),
      formatNumber(r.deals_possivel_duplicata),
    ]),
    styles: { fontSize: 8, cellPadding: 1.6, textColor: [40, 40, 40] },
    headStyles: { fillColor: NAVY, textColor: [255, 255, 255], fontStyle: "bold" },
    alternateRowStyles: { fillColor: GOLD_SOFT },
    didParseCell: (data) => {
      if (data.section === "body" && data.column.index === 8) {
        const row = rows[data.row.index];
        if (row && row.pct_parado > 0.7) {
          data.cell.styles.textColor = [146, 106, 22];
          data.cell.styles.fontStyle = "bold";
        }
      }
    },
    margin: { left: 14, right: 14 },
  });

  rodapePdf(doc);
  downloadBlob(doc.output("blob"), `lead-scorer-gestor-${hoje()}.pdf`);
}

export { pctParado };
