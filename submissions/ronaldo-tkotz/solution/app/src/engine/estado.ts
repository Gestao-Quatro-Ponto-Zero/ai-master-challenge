/**
 * Remote state for the deploy (D46.4). Vercel functions have no lasting disk and run in several
 * instances, so the app DB (users, conversations, marks, custom screens, decks) is kept as ONE
 * encrypted SQLite snapshot in a private Vercel Blob store:
 *
 * - before a request uses the app DB, the instance checks the snapshot's ETag and loads it when
 *   another instance wrote a newer one;
 * - after the request, if the DB changed, the instance uploads a new snapshot.
 *
 * The snapshot is AES-256-GCM encrypted with STATE_KEY, so even the private blob holds no readable
 * data. Locally (no BLOB_READ_WRITE_TOKEN / STATE_KEY) none of this runs and the DB is the file.
 * Known limit: two instances writing at the same moment — the later upload wins.
 */
import { createCipheriv, createDecipheriv, createHash, randomBytes } from "node:crypto";
import { get, put } from "@vercel/blob";
import { appdb, appdbMudancas, estadoRemoto, seedJudgeUser, substituirAppDb } from "./appdb";

let versao: string | null = null; // ETag of the snapshot this instance holds
let persistidas = 0; // appdbMudancas() at the last load or upload
let checagem: Promise<void> | null = null; // one ETag check shared by concurrent requests
let gravacao: Promise<void> | null = null; // the upload in progress

function chave(): Buffer {
  return createHash("sha256").update(process.env.STATE_KEY ?? "").digest();
}
/** The blob path: derived from the key, so it is not guessable either. */
function caminho(): string {
  return `estado/app-${createHash("sha256").update(`caminho:${process.env.STATE_KEY ?? ""}`).digest("hex").slice(0, 24)}.bin`;
}

export function cifrar(dados: Buffer): Buffer {
  const iv = randomBytes(12);
  const c = createCipheriv("aes-256-gcm", chave(), iv);
  const corpo = Buffer.concat([c.update(dados), c.final()]);
  return Buffer.concat([Buffer.from("RS1"), iv, c.getAuthTag(), corpo]);
}

export function decifrar(pacote: Buffer): Buffer {
  if (pacote.subarray(0, 3).toString() !== "RS1") throw new Error("estado remoto em formato desconhecido");
  const iv = pacote.subarray(3, 15);
  const tag = pacote.subarray(15, 31);
  const d = createDecipheriv("aes-256-gcm", chave(), iv);
  d.setAuthTag(tag);
  return Buffer.concat([d.update(pacote.subarray(31)), d.final()]);
}

async function baixar(): Promise<void> {
  // A conditional GET (~80 ms, 304 when unchanged) instead of head() (~550 ms on the Blob API).
  const r = await get(caminho(), { access: "private", useCache: false, ...(versao && versao !== "novo" ? { ifNoneMatch: versao } : {}) });
  if (!r) {
    // First boot of the deploy: an empty DB with the evaluator login, uploaded at once.
    if (versao === null) {
      substituirAppDb(null);
      await seedJudgeUser();
      persistidas = -1;
      versao = "novo";
      await enviar();
    }
    return;
  }
  if (r.statusCode === 304 || !r.stream || r.blob.etag === versao) {
    if (r.stream) await r.stream.cancel().catch(() => {});
    return;
  }
  const buf = Buffer.from(await new Response(r.stream).arrayBuffer());
  substituirAppDb(decifrar(buf));
  versao = r.blob.etag;
  persistidas = appdbMudancas();
  // The evaluator password may have changed in the environment.
  await seedJudgeUser();
}

async function enviar(): Promise<void> {
  const n = appdbMudancas();
  if (n === persistidas) return;
  const snapshot = appdb().serialize();
  const r = await put(caminho(), cifrar(snapshot), {
    access: "private",
    allowOverwrite: true,
    addRandomSuffix: false,
    contentType: "application/octet-stream",
  });
  versao = r.etag;
  persistidas = n;
}

/** Loads the newest snapshot before the request touches the app DB (no-op locally). */
export async function prepararEstado(): Promise<void> {
  if (!estadoRemoto()) return;
  // Requests that arrive together (a page and its API calls) share one check.
  if (checagem) return checagem;
  checagem = (async () => {
    while (gravacao) await gravacao;
    await baixar();
  })().finally(() => {
    checagem = null;
  });
  return checagem;
}

/** Uploads a snapshot when the request changed the app DB (no-op locally or when nothing changed). */
export async function persistirEstado(): Promise<void> {
  if (!estadoRemoto()) return;
  while (gravacao) await gravacao;
  if (checagem) await checagem;
  gravacao = enviar()
    .catch((e) => console.error("[estado] falha ao gravar o estado remoto:", e))
    .finally(() => {
      gravacao = null;
    });
  return gravacao;
}

/**
 * Wraps a route handler that writes: the snapshot is uploaded BEFORE the response goes out, so the
 * next request — maybe on another instance — already sees the write (a new screen opens at once).
 */
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export function gravando<T extends (...args: any[]) => Promise<Response>>(fn: T): T {
  return (async (...args: Parameters<T>) => {
    const r = await fn(...args);
    await persistirEstado();
    return r;
  }) as T;
}
