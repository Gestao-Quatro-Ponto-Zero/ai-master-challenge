// Gera docs.generated.json a partir dos .md do repositório (PRD §4.7: "os textos vêm dos .md, lidos no build").
// Fontes: docs/decisions/*.md, process-log/judgment-log.md e process-log/process-log.md.
//
// No deploy da Vercel o root é solution/app, então o JSON gerado fica versionado: se as fontes não estiverem
// acessíveis no build, o script mantém o arquivo existente e sai sem erro.
// Uso (de solution/app): node app/como-foi-feito/_content/generate.mjs
import { existsSync, readdirSync, readFileSync, writeFileSync } from "node:fs"
import { dirname, join, resolve } from "node:path"
import { fileURLToPath } from "node:url"

import { Marked } from "marked"

const here = dirname(fileURLToPath(import.meta.url))
const SUB = resolve(here, "../../../../..") // submissions/daniel-fonseca
const OUT = join(here, "docs.generated.json")

const decisionsDir = join(SUB, "docs/decisions")
const judgmentFile = join(SUB, "process-log/judgment-log.md")
const processFile = join(SUB, "process-log/process-log.md")

if (!existsSync(decisionsDir) || !existsSync(judgmentFile)) {
  console.log(`[como-foi-feito] fontes .md fora do alcance do build; mantido ${existsSync(OUT) ? "o JSON versionado" : "nada (JSON ausente!)"}`)
  process.exit(0)
}

// O repositório é privado: o app mostra o documento transcrito num pop-up. Links externos (http) abrem em nova aba;
// links relativos do repositório viram texto, porque não há destino público para eles.
const md2html = new Marked({
  gfm: true,
  renderer: {
    link({ href, tokens }) {
      const text = this.parser.parseInline(tokens)
      return /^https?:\/\//.test(href) ? `<a href="${href}" target="_blank" rel="noreferrer">${text}</a>` : `<span class="doc-ref">${text}</span>`
    },
    html() {
      return ""
    },
  },
})
const toHtml = (md) => md2html.parse(md)

/** Remove marcação markdown leve (negrito, código, links) para texto corrido. */
const plain = (s) =>
  s
    .replace(/\[([^\]]+)\]\([^)]+\)/g, "$1")
    .replace(/\*\*([^*]+)\*\*/g, "$1")
    .replace(/`([^`]+)`/g, "$1")
    .replace(/\s+/g, " ")
    .trim()

const field = (md, name) => {
  const m = md.match(new RegExp(`^- \\*\\*${name}:\\*\\*\\s*(.+)$`, "m"))
  return m ? plain(m[1]) : null
}

/** Primeira frase de uma seção (Decisão, Proposta…) para o resumo da linha do tempo. */
function summary(md) {
  for (const h of ["Decisão", "Proposta", "Decisão (Daniel)"]) {
    const m = md.match(new RegExp(`^## ${h}[^\\n]*\\n+([\\s\\S]*?)(?=\\n## |(?![\\s\\S]))`, "m"))
    if (!m) continue
    const first = m[1]
      .split("\n")
      .map((l) => l.trim())
      .find((l) => l && !l.startsWith("|") && !l.startsWith("```") && !l.startsWith("#"))
    if (first) {
      const text = plain(first.replace(/^(\d+\.|-)\s*/, ""))
      return text.length > 260 ? `${text.slice(0, 257).replace(/\s+\S*$/, "")}…` : text
    }
  }
  return null
}

/** "Daniel (…) · IA (…)" → quem aparece primeiro e se a origem é compartilhada. */
function originKind(origin) {
  if (!origin) return "ia_daniel"
  const first = origin.trim().toLowerCase()
  const hasIa = /\bia\b/i.test(origin)
  const hasDaniel = /daniel/i.test(origin)
  if (hasDaniel && !hasIa) return "daniel"
  if (first.startsWith("daniel")) return "daniel_ia"
  return hasDaniel ? "ia_daniel" : "ia"
}

const adrs = readdirSync(decisionsDir)
  .filter((f) => /^\d{4}-.+\.md$/.test(f))
  .sort()
  .map((file) => {
    const md = readFileSync(join(decisionsDir, file), "utf8")
    const title = md.match(/^# (\d{4}) — (.+)$/m)
    const status = field(md, "Status") ?? ""
    const origin = field(md, "Origem")
    return {
      number: title ? title[1] : file.slice(0, 4),
      title: title ? plain(title[2]) : file,
      status,
      statusKind: /^aceita/i.test(status) ? "aceita" : /^proposta/i.test(status) ? "proposta" : /^rejeitada/i.test(status) ? "rejeitada" : "outra",
      date: field(md, "Data"),
      origin,
      originKind: originKind(origin),
      summary: summary(md),
      file: `docs/decisions/${file}`,
      // Corpo sem o título (o pop-up mostra o título no cabeçalho).
      html: toHtml(md.replace(/^# .+\n+/, "")),
    }
  })

// Tabela do judgment log: | # | Data | Tipo | O que aconteceu | Quem percebeu | Resultado |
const judgmentMd = readFileSync(judgmentFile, "utf8")
const judgment = judgmentMd
  .split("\n")
  .filter((l) => /^\|\s*\d+\s*\|/.test(l))
  .map((l) => {
    const c = l.split("|").slice(1, -1).map((x) => plain(x))
    return { n: Number(c[0]), date: c[1], type: c[2], what: c[3], who: c[4], result: c[5] }
  })

// Cabeçalhos das sessões: "## Sessão 01 — 2026-11-09 — Claude Code (…) — ~1h"
const sessions = existsSync(processFile)
  ? readFileSync(processFile, "utf8")
      .split("\n")
      .filter((l) => /^## Sessão \d+/.test(l))
      .map((l) => {
        const parts = l.replace(/^## /, "").split(" — ")
        return { name: parts[0], date: parts[1] ?? null, harness: parts[2] ? plain(parts[2]) : null, duration: parts[3] ?? null }
      })
  : []

const data = {
  adrs,
  judgment,
  judgmentHtml: toHtml(judgmentMd.replace(/^# .+\n+/, "")),
  sessions,
}
writeFileSync(OUT, `${JSON.stringify(data, null, 1)}\n`)
console.log(`[como-foi-feito] ${adrs.length} ADRs, ${judgment.length} registros do judgment log, ${sessions.length} sessões → ${OUT}`)
