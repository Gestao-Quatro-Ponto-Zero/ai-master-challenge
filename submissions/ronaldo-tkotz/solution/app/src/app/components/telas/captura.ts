/**
 * Faithful copy of a chart panel for the deck (D44). The panel's content is part SVG (the
 * chart) and part HTML (legends, labels). This turns all of it into ONE self-contained SVG at
 * the size it has on screen: each chart SVG is cloned with its computed styles written inline,
 * each HTML box with a background or border becomes a rect, and each piece of HTML text becomes
 * an SVG text at its on-screen position. The PNG is drawn from that SVG at 3× in the browser.
 */
const NS = "http://www.w3.org/2000/svg";

/** SVG presentation properties copied from the computed style (classes do not travel). */
const PROPS = [
  "fill", "fill-opacity", "stroke", "stroke-width", "stroke-opacity", "stroke-dasharray", "stroke-linecap",
  "stroke-linejoin", "opacity", "font-family", "font-size", "font-weight", "font-style", "letter-spacing",
  "text-anchor", "dominant-baseline", "visibility", "display",
];

const ESCALA_PNG = 3;
/** Breathing room around the content, like the panel padding (the legend dots sit on the edge). */
const MARGEM = 12;

const transparente = (c: string) => !c || c === "transparent" || /rgba\([^)]*,\s*0\)$/.test(c);

function inlineEstilos(original: Element, copia: Element): void {
  const cs = getComputedStyle(original);
  const estilo = PROPS.map((p) => `${p}:${cs.getPropertyValue(p)}`).join(";");
  copia.setAttribute("style", estilo);
  copia.removeAttribute("class");
}

function copiarSvg(svg: SVGSVGElement, base: DOMRect): SVGSVGElement {
  const r = svg.getBoundingClientRect();
  const copia = svg.cloneNode(true) as SVGSVGElement;
  inlineEstilos(svg, copia);
  const orig = svg.querySelectorAll("*");
  const dest = copia.querySelectorAll("*");
  orig.forEach((el, i) => inlineEstilos(el, dest[i]));
  copia.setAttribute("x", String(r.left - base.left));
  copia.setAttribute("y", String(r.top - base.top));
  copia.setAttribute("width", String(r.width));
  copia.setAttribute("height", String(r.height));
  return copia;
}

function raio(cs: CSSStyleDeclaration, w: number, h: number): number {
  const v = cs.borderTopLeftRadius;
  if (v.endsWith("%")) return (Math.min(w, h) * parseFloat(v)) / 100;
  return Math.min(parseFloat(v) || 0, Math.min(w, h) / 2);
}

function caixa(el: HTMLElement, cs: CSSStyleDeclaration, base: DOMRect, destino: SVGElement): void {
  const r = el.getBoundingClientRect();
  if (r.width === 0 || r.height === 0) return;
  const fundo = cs.backgroundColor;
  const bw = parseFloat(cs.borderTopWidth) || 0;
  const borda = bw > 0 && cs.borderTopStyle !== "none" && !transparente(cs.borderTopColor);
  if (transparente(fundo) && !borda) return;
  const rect = document.createElementNS(NS, "rect");
  rect.setAttribute("x", String(r.left - base.left + bw / 2));
  rect.setAttribute("y", String(r.top - base.top + bw / 2));
  rect.setAttribute("width", String(Math.max(0, r.width - bw)));
  rect.setAttribute("height", String(Math.max(0, r.height - bw)));
  const rx = raio(cs, r.width, r.height);
  if (rx > 0) rect.setAttribute("rx", String(rx));
  rect.setAttribute("fill", transparente(fundo) ? "none" : fundo);
  if (borda) {
    rect.setAttribute("stroke", cs.borderTopColor);
    rect.setAttribute("stroke-width", String(bw));
    if (cs.borderTopStyle === "dashed") rect.setAttribute("stroke-dasharray", `${bw * 3} ${bw * 2}`);
    if (cs.borderTopStyle === "dotted") rect.setAttribute("stroke-dasharray", `${bw} ${bw}`);
  }
  destino.appendChild(rect);
}

/** HTML text, one SVG text per rendered line (words grouped by their line). */
function texto(no: Text, base: DOMRect, destino: SVGElement): void {
  const conteudo = no.textContent ?? "";
  if (!conteudo.trim()) return;
  const pai = no.parentElement;
  if (!pai) return;
  const cs = getComputedStyle(pai);
  const range = document.createRange();
  const linhas: { top: number; left: number; bottom: number; palavras: string[] }[] = [];
  const re = /\S+/g;
  let m: RegExpExecArray | null;
  while ((m = re.exec(conteudo))) {
    range.setStart(no, m.index);
    range.setEnd(no, m.index + m[0].length);
    const r = range.getBoundingClientRect();
    if (r.width === 0 && r.height === 0) continue;
    const linha = linhas.find((l) => Math.abs(l.top - r.top) < r.height / 2);
    if (linha) linha.palavras.push(m[0]);
    else linhas.push({ top: r.top, left: r.left, bottom: r.bottom, palavras: [m[0]] });
  }
  const upper = cs.textTransform === "uppercase";
  for (const l of linhas) {
    const t = document.createElementNS(NS, "text");
    t.setAttribute("x", String(l.left - base.left));
    t.setAttribute("y", String((l.top + l.bottom) / 2 - base.top));
    t.setAttribute("dominant-baseline", "central");
    t.setAttribute("fill", cs.color);
    t.setAttribute("font-family", cs.fontFamily);
    t.setAttribute("font-size", cs.fontSize);
    t.setAttribute("font-weight", cs.fontWeight);
    if (cs.letterSpacing !== "normal") t.setAttribute("letter-spacing", cs.letterSpacing);
    if (cs.fontVariantNumeric.includes("tabular")) t.setAttribute("style", "font-variant-numeric:tabular-nums");
    const s = l.palavras.join(" ");
    t.textContent = upper ? s.toUpperCase() : s;
    destino.appendChild(t);
  }
}

function percorrer(el: Element, base: DOMRect, destino: SVGElement): void {
  for (const filho of Array.from(el.childNodes)) {
    if (filho.nodeType === Node.TEXT_NODE) {
      texto(filho as Text, base, destino);
      continue;
    }
    if (!(filho instanceof Element)) continue;
    if (filho instanceof SVGSVGElement) {
      destino.appendChild(copiarSvg(filho, base));
      continue;
    }
    if (!(filho instanceof HTMLElement)) continue;
    const cs = getComputedStyle(filho);
    if (cs.display === "none" || cs.visibility === "hidden" || cs.opacity === "0") continue;
    if (filho.dataset.semCaptura !== undefined) continue;
    caixa(filho, cs, base, destino);
    percorrer(filho, base, destino);
  }
}

export interface Captura {
  svg: string;
  png: string;
  largura: number;
  altura: number;
}

/** The panel content `el` as one SVG plus a 3× PNG, on the panel's own background. */
export async function capturar(el: HTMLElement, fundo: string): Promise<Captura> {
  const r = el.getBoundingClientRect();
  const base = new DOMRect(r.left - MARGEM, r.top - MARGEM, r.width + 2 * MARGEM, r.height + 2 * MARGEM);
  const largura = Math.round(base.width);
  const altura = Math.round(base.height);
  const svg = document.createElementNS(NS, "svg");
  svg.setAttribute("xmlns", NS);
  svg.setAttribute("width", String(largura));
  svg.setAttribute("height", String(altura));
  svg.setAttribute("viewBox", `0 0 ${largura} ${altura}`);
  const bg = document.createElementNS(NS, "rect");
  bg.setAttribute("width", "100%");
  bg.setAttribute("height", "100%");
  bg.setAttribute("fill", fundo);
  svg.appendChild(bg);
  percorrer(el, base, svg);
  const texto = new XMLSerializer().serializeToString(svg);

  const url = URL.createObjectURL(new Blob([texto], { type: "image/svg+xml" }));
  try {
    const img = new Image();
    img.src = url;
    await img.decode();
    const canvas = document.createElement("canvas");
    canvas.width = largura * ESCALA_PNG;
    canvas.height = altura * ESCALA_PNG;
    const ctx = canvas.getContext("2d");
    if (!ctx) throw new Error("canvas indisponível");
    ctx.scale(ESCALA_PNG, ESCALA_PNG);
    ctx.drawImage(img, 0, 0, largura, altura);
    return { svg: texto, png: canvas.toDataURL("image/png"), largura, altura };
  } finally {
    URL.revokeObjectURL(url);
  }
}
