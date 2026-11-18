/**
 * Marked charts for the deck (D44). Run: bun run marcados-test.
 * Runs on a throwaway app DB: validation refuses active SVG, re-marking refreshes instead of
 * duplicating, the order is the marking order, and the origin names screen and filters.
 * The presentation built from the marks is tested in deck-marcados-test (D45).
 */
import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";

const dir = mkdtempSync(path.join(tmpdir(), "marcados-"));
process.env.APP_DB_PATH = path.join(dir, "app.sqlite");

let failed = 0;
function check(name: string, cond: boolean, detail = ""): void {
  process.stdout.write(`${cond ? "✓" : "✗"} ${name}${detail ? ` — ${detail}` : ""}\n`);
  if (!cond) failed++;
}

(async () => {
  const m = await import("../src/engine/marcados");
  // 1×1 transparent PNG.
  const png = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=";
  const svg = '<svg xmlns="http://www.w3.org/2000/svg" width="400" height="200"><rect width="100%" height="100%" fill="#121218"/></svg>';
  const base = { rota: "/tela/2", filtros: "", titulo: "Churn por indústria", nota: "% das contas com churn", svg, png, largura: 400, altura: 200, sql: [] as string[] };
  const u = "teste";

  check("recusa SVG com script", m.validarMarcado({ ...base, chave: "a", svg: '<svg><script>alert(1)</script></svg>' }) !== null);
  check("recusa SVG com evento", m.validarMarcado({ ...base, chave: "a", svg: '<svg onload="x()"></svg>' }) !== null);
  check("recusa tela desconhecida", m.validarMarcado({ ...base, chave: "a", rota: "/tela/4" }) !== null);
  check("recusa PNG que não é PNG", m.validarMarcado({ ...base, chave: "a", png: "data:text/html,oi" }) !== null);
  check("aceita um gráfico válido", m.validarMarcado({ ...base, chave: "a" }) === null);

  m.marcar(u, { ...base, chave: "/tela/2|Churn por indústria|" });
  m.marcar(u, { ...base, chave: "/tela/2|Churn por indústria|setor=FinTech", filtros: "setor=FinTech" });
  m.marcar(u, { ...base, chave: "/|Idade média|", rota: "/", titulo: "Idade média", largura: 800 });
  m.marcar(u, { ...base, chave: "/tela/2|Churn por indústria|", nota: "nota nova" });
  const lista = m.listarMarcados(u);
  check("recusa SQL que não é lista", m.validarMarcado({ ...base, chave: "a", sql: "SELECT 1" as unknown as string[] }) !== null);
  check("remarcar atualiza em vez de duplicar (3 marcas)", lista.length === 3, String(lista.length));
  check("a cópia remarcada guarda a nota nova", lista[0].nota === "nota nova");
  check("ordem = ordem em que foram marcados", lista.map((x) => x.titulo).join("|") === "Churn por indústria|Churn por indústria|Idade média");
  check("mesmo gráfico com outro filtro é outra marca", lista[1].filtros === "setor=FinTech");
  const o = m.origemMarcado(lista[1]);
  check("origem nomeia a tela e o filtro", o.tela === "Tela 2 · O que causa o churn" && o.filtros === "FinTech", `${o.tela} / ${o.filtros}`);
  check("sem filtro diz 'sem filtros'", m.origemMarcado(lista[0]).filtros === "sem filtros");
  check("outro usuário não vê as marcas", m.listarMarcados("outro").length === 0);

  check("desmarcar remove", m.desmarcar(u, "/|Idade média|") && m.listarMarcados(u).length === 2);
  check("remover por id só remove do dono", !m.removerMarcado("outro", lista[0].id) && m.removerMarcado(u, lista[0].id));

  rmSync(dir, { recursive: true, force: true });
  process.stdout.write(failed === 0 ? "\nMARCADOS OK\n" : `\n${failed} FAILED\n`);
  process.exit(failed === 0 ? 0 : 1);
})();
