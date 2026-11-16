/**
 * Runs once when the server process starts (Next `register` hook): ensures the data dirs
 * exist and seeds the evaluator login — guarded to the Node runtime so the edge `proxy`
 * bundle never pulls in fs.
 */
export async function register() {
  if (process.env.NEXT_RUNTIME === "nodejs") {
    const { ensureDataDirs } = await import("./engine/seed");
    const { seedJudgeUser } = await import("./engine/appdb");
    ensureDataDirs();
    await seedJudgeUser();
  }
}
