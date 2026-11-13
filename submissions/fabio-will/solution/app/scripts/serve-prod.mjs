// Serves out/ the way Vercel will: same headers from vercel.json, clean URLs, trailing slash, gzip.
// Used to run the pentest and Lighthouse against production behaviour before any deploy.
// Usage: node scripts/serve-prod.mjs [port]
import { createReadStream } from 'node:fs'
import { readFile, stat } from 'node:fs/promises'
import { createServer } from 'node:http'
import { extname, join, normalize } from 'node:path'
import { createGzip } from 'node:zlib'

const ROOT = new URL('../out/', import.meta.url).pathname
const PORT = Number(process.argv[2] ?? 4180)
const config = JSON.parse(await readFile(new URL('../vercel.json', import.meta.url), 'utf8'))
const TYPES = {
  '.html': 'text/html; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.txt': 'text/plain; charset=utf-8',
  '.svg': 'image/svg+xml',
  '.ico': 'image/x-icon',
  '.woff2': 'font/woff2',
  '.png': 'image/png',
}
const rules = config.headers.map((r) => ({ re: new RegExp(`^${r.source.replace(/\(\.\*\)/g, '.*')}$`), headers: r.headers }))

async function resolve(urlPath) {
  const clean = normalize(decodeURIComponent(urlPath)).replace(/^(\.\.[/\\])+/, '')
  const base = join(ROOT, clean)
  if (!base.startsWith(ROOT.replace(/\/$/, '')) || clean.split(/[\\/]/).some((p) => p.startsWith('.') && p.length > 1)) return null
  for (const candidate of [base, join(base, 'index.html'), `${base}.html`]) {
    try {
      if ((await stat(candidate)).isFile()) return candidate
    } catch {}
  }
  return null
}

createServer(async (req, res) => {
  const path = new URL(req.url ?? '/', 'http://local').pathname
  for (const rule of rules) if (rule.re.test(path)) for (const h of rule.headers) res.setHeader(h.key, h.value)
  const file = await resolve(path)
  if (!file) {
    res.statusCode = 404
    res.setHeader('Content-Type', TYPES['.html'])
    createReadStream(join(ROOT, '404.html')).pipe(res)
    return
  }
  res.setHeader('Content-Type', TYPES[extname(file)] ?? 'application/octet-stream')
  if (/\bgzip\b/.test(req.headers['accept-encoding'] ?? '') && !/\.(woff2|png|ico)$/.test(file)) {
    res.setHeader('Content-Encoding', 'gzip')
    res.setHeader('Vary', 'Accept-Encoding')
    createReadStream(file).pipe(createGzip()).pipe(res)
  } else {
    createReadStream(file).pipe(res)
  }
}).listen(PORT, () => console.log(`serve-prod: http://localhost:${PORT} (headers from vercel.json)`))
