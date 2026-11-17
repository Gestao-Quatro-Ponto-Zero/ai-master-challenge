/**
 * Remote state (D46.4). Without Blob credentials: the cipher round-trips and tampering is caught.
 * With BLOB_READ_WRITE_TOKEN + STATE_KEY (a test key, never production's): a write in one
 * "instance" is uploaded and a second, fresh process loads it.
 *   ETAPA=gravar  → seeds, creates a custom screen, uploads
 *   ETAPA=ler     → loads the snapshot and finds that screen
 */
import assert from "node:assert/strict";

(async () => {
  const e = await import("../src/engine/estado");
  process.env.STATE_KEY ??= "teste-local";
  const dado = Buffer.from("SQLite format 3\u0000 qualquer coisa");
  assert.deepEqual(e.decifrar(e.cifrar(dado)), dado);
  const adulterado = e.cifrar(dado);
  adulterado[adulterado.length - 1] ^= 1;
  assert.throws(() => e.decifrar(adulterado));
  console.log("ESTADO cifra OK");
  if (!process.env.BLOB_READ_WRITE_TOKEN || !process.env.ETAPA) return;

  const t = await import("../src/engine/telasUsuario");
  const { getUserByEmail, judgeEmailFromEnv } = await import("../src/engine/appdb");
  await e.prepararEstado();
  const u = getUserByEmail(judgeEmailFromEnv());
  assert.ok(u, "login do avaliador semeado no estado remoto");
  if (process.env.ETAPA === "gravar") {
    t.criarTela(u.id, `teste-${process.env.MARCA}`);
    await e.persistirEstado();
    console.log("ESTADO gravado");
  } else {
    const nomes = t.listarTelas(u.id).map((x) => x.nome);
    assert.ok(nomes.includes(`teste-${process.env.MARCA}`), `tela não encontrada: ${nomes.join(", ")}`);
    console.log(`ESTADO lido por outro processo OK (${nomes.length} telas)`);
  }
})().catch((err) => {
  console.error(err);
  process.exit(1);
});
