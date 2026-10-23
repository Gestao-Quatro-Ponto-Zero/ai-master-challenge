// Tempo ativo de cada sessão a partir dos timestamps dos transcripts do Claude Code (.jsonl).
// Uso: node tempo_ativo.mjs <limite_min> <desde ISO> [--ate <ISO>] <arquivo.jsonl>... [--principal <arquivo.jsonl>...]
//
// Junta os instantes de todos os eventos (sessão principal, forks, subagentes, workers),
// remove repetidos (os forks copiam eventos com o mesmo timestamp) e soma só os
// intervalos entre eventos consecutivos que não passam de <limite_min>. Um intervalo
// maior conta como parado (ninguém interagindo e nenhum agente gravando nada).
// Com --principal, mede também só a sessão principal (o coordenador, inclusive o trabalho autônomo dele).
// Com --ate, ignora eventos depois desse instante: a medição fica reproduzível mesmo com as transcrições crescendo.
import { createReadStream } from 'node:fs';
import { createInterface } from 'node:readline';

const [limiteMin, desde, ...args] = process.argv.slice(2);
const j = args.indexOf('--ate');
const ate = j < 0 ? null : args[j + 1];
const resto = j < 0 ? args : [...args.slice(0, j), ...args.slice(j + 2)];
const i = resto.indexOf('--principal');
const todos = i < 0 ? resto : resto.slice(0, i);
const principal = i < 0 ? [] : resto.slice(i + 1);
const limiteMs = Number(limiteMin) * 60_000;
const desdeMs = Date.parse(desde);
const ateMs = ate ? Date.parse(ate) : Infinity;

async function instantes(arquivos) {
  const set = new Set();
  for (const f of arquivos) {
    const rl = createInterface({ input: createReadStream(f, 'utf8'), crlfDelay: Infinity });
    for await (const linha of rl) {
      const m = linha.match(/"timestamp":"([^"]+)"/);   // só o campo de tempo; o conteúdo não é lido
      if (!m) continue;
      const t = Date.parse(m[1]);
      if (t >= desdeMs && t <= ateMs) set.add(t);
    }
  }
  return [...set].sort((a, b) => a - b);
}

function medir(ts) {
  let ativo = 0, pausas = 0;
  for (let k = 1; k < ts.length; k++) {
    const d = ts[k] - ts[k - 1];
    if (d <= limiteMs) ativo += d; else pausas++;
  }
  const relogio = ts.length ? ts[ts.length - 1] - ts[0] : 0;
  return { inicio: new Date(ts[0]).toISOString(), fim: new Date(ts[ts.length - 1]).toISOString(), relogio, ativo, pausas };
}

const fmt = ms => `${Math.floor(ms / 3_600_000)} h ${String(Math.round(ms / 60_000) % 60).padStart(2, '0')} min`;
const linha = (nome, r) => console.log(`${nome}: ${r.inicio} → ${r.fim} · relógio ${fmt(r.relogio)} · ativo ${fmt(r.ativo)} · ${r.pausas} pausas > ${limiteMin} min`);

linha('tudo (principal + agentes + workers)', medir(await instantes(todos)));
if (principal.length) linha('só a sessão principal', medir(await instantes(principal)));
