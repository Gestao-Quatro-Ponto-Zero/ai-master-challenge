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

const routes = ["/", "/quality", "/journeys", "/graph", "/watchlist", "/experiments", "/governance", "/demo"];

for (const route of routes) {
  test(`${route} loads without local data failures`, async ({ page }, testInfo) => {
    const consoleErrors: string[] = [];
    const failedRequests: string[] = [];
    page.on("console", (message) => { if (message.type() === "error") consoleErrors.push(message.text()); });
    page.on("requestfailed", (request) => failedRequests.push(request.url()));
    await page.goto(route);
    await expect(page.locator("main")).toBeVisible();
    await expect(page.getByText("Demo · historical observational data")).toBeVisible();
    expect(consoleErrors).toEqual([]);
    expect(failedRequests.filter((url) => url.includes("/data/"))).toEqual([]);
    if (testInfo.project.name === "desktop" && screenshotNames[route]) {
      await page.emulateMedia({ reducedMotion: "reduce" });
      if (route === "/graph") await expect(page.getByRole("img", { name: /JourneyGraph view/ })).toBeVisible({ timeout: 20_000 });
      await page.screenshot({ path: path.resolve(process.cwd(), "../reports/screenshots", screenshotNames[route]), fullPage: true });
    }
  });
}

test("guided demo advances", async ({ page }) => {
  await page.goto("/demo");
  await expect(page.getByText("The problem")).toBeVisible();
  await page.getByRole("button", { name: "Next" }).click();
  await expect(page.getByText("Data quality before prediction")).toBeVisible();
});

test("watchlist opens governed detail", async ({ page }) => {
  await page.goto("/watchlist");
  await page.getByRole("button", { name: "View evidence" }).first().click();
  await expect(page.getByText("Requires human review: Yes")).toBeVisible();
  await expect(page.getByText("Automatic intervention: Not allowed")).toBeVisible();
});

test("experiment detail opens with untested status", async ({ page }) => {
  await page.goto("/experiments");
  await page.getByRole("button", { name: /Open experiment detail/ }).first().click();
  await expect(page.getByText("Untested hypothesis", { exact: true })).toBeVisible();
  await expect(page.getByText(/No experiment has been executed/)).toBeVisible();
});

test("graph loads a bounded view", async ({ page }) => {
  await page.goto("/graph");
  await expect(page.getByRole("img", { name: /JourneyGraph view/ })).toBeVisible({ timeout: 20_000 });
  await expect(page.getByText(/explicitly truncated/)).toBeVisible();
});
