import { expect, test } from "@playwright/test";
import path from "node:path";

const screenshotNames: Record<string, string> = {
  "/": "01-executive-overview.png",
  "/quality": "02-data-quality.png",
  "/journeys": "03-journey-explorer.png",
  "/graph": "04-journeygraph.png",
  "/watchlist": "05-watchlist.png",
  "/experiments": "06-experiment-lab.png",
  "/governance": "07-governance.png"
};

const routes = ["/", "/quality", "/journeys", "/graph", "/watchlist", "/experiments", "/governance", "/demo", "/methodology"];

for (const route of routes) {
  test(`${route} carrega sem falhas de dados locais`, async ({ page }, testInfo) => {
    const consoleErrors: string[] = [];
    const failedRequests: string[] = [];
    page.on("console", (message) => { if (message.type() === "error") consoleErrors.push(message.text()); });
    page.on("requestfailed", (request) => failedRequests.push(request.url()));
    await page.goto(route);
    await expect(page.locator("main")).toBeVisible();
    await expect(page.getByText("Demonstração histórica local")).toBeVisible();
    expect(consoleErrors).toEqual([]);
    expect(failedRequests.filter((url) => url.includes("/data/"))).toEqual([]);
    if (route === "/graph") {
      await expect(page.getByRole("img", { name: /Visualização JourneyGraph/ })).toBeVisible({ timeout: 20_000 });
      await expect(page.getByText(/explicitamente truncada/)).toBeVisible();
    }
    if (testInfo.project.name === "desktop" && screenshotNames[route]) {
      await page.emulateMedia({ reducedMotion: "reduce" });
      await page.screenshot({ path: path.resolve(process.cwd(), "../reports/screenshots", screenshotNames[route]), fullPage: true });
    }
  });
}

test("demonstração guiada avança", async ({ page }) => {
  await page.goto("/demo");
  await expect(page.getByText("O problema")).toBeVisible();
  await page.getByRole("button", { name: "Próxima" }).click();
  await expect(page.getByText("Qualidade antes da interpretação")).toBeVisible();
});

test("fila de revisão abre detalhe governado", async ({ page }) => {
  await page.goto("/watchlist");
  await page.getByRole("button", { name: "Ver evidência" }).first().click();
  await expect(page.getByText("Revisão humana obrigatória: Sim")).toBeVisible();
  await expect(page.getByText("Intervenção automática: Não permitida")).toBeVisible();
  await expect(page.getByRole("dialog")).not.toContainText(/acct_[0-9a-f]+/i);
});

test("detalhe do experimento abre com status não testado", async ({ page }) => {
  await page.goto("/experiments");
  await page.getByRole("button", { name: /Abrir detalhes do experimento/ }).first().click();
  await expect(page.getByText("Hipótese não testada", { exact: true })).toBeVisible();
  await expect(page.getByText("Nenhum experimento foi executado. Nenhum cliente foi contatado, atribuído a grupo ou exposto a uma intervenção.", { exact: true })).toBeVisible();
});
