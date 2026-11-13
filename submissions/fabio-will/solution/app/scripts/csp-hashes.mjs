// Post-build: pins every inline <script> of each exported page by SHA-256 in a <meta> CSP.
//
// The static export needs a few inline bootstrap scripts, so the header CSP (vercel.json) has to allow inline
// scripts. A second policy in a <meta> tag is enforced on top of the header one (the browser applies both), and
// it only allows the exact inline scripts the build produced. Anything injected later fails both policies.
// The header keeps what a <meta> CSP cannot carry: frame-ancestors, and the other directives.
import { createHash } from 'node:crypto'
import { readdir, readFile, writeFile } from 'node:fs/promises'
import { join } from 'node:path'

const OUT = new URL('../out/', import.meta.url).pathname
const INLINE_SCRIPT = /<script(?![^>]*\bsrc=)[^>]*>([\s\S]*?)<\/script>/g
const MARKER = 'data-csp="pinned"'

async function htmlFiles(dir) {
  const entries = await readdir(dir, { withFileTypes: true })
  const nested = await Promise.all(entries.map((e) => (e.isDirectory() ? htmlFiles(join(dir, e.name)) : e.name.endsWith('.html') ? [join(dir, e.name)] : [])))
  return nested.flat()
}

let pages = 0
let pinned = 0
for (const file of await htmlFiles(OUT)) {
  const html = await readFile(file, 'utf8')
  if (html.includes(MARKER)) continue // idempotent
  const hashes = [...html.matchAll(INLINE_SCRIPT)].map((m) => `'sha256-${createHash('sha256').update(m[1], 'utf8').digest('base64')}'`)
  const policy = ["script-src 'self'", ...new Set(hashes)].join(' ')
  const meta = `<meta http-equiv="Content-Security-Policy" ${MARKER} content="${policy}"/>`
  // Right after the charset declaration, before any script; the charset stays within the first 1024 bytes.
  const anchor = html.includes('<meta charSet="utf-8"/>') ? '<meta charSet="utf-8"/>' : '<head>'
  if (!html.includes(anchor)) throw new Error(`no <head> in ${file}`)
  await writeFile(file, html.replace(anchor, `${anchor}${meta}`))
  pages += 1
  pinned += hashes.length
}
console.log(`csp-hashes: pinned ${pinned} inline scripts across ${pages} pages`)
