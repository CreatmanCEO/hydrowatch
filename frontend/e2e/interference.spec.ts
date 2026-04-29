import { test, expect } from "@playwright/test";

test.describe("Interference layer", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/");
    await page.waitForSelector(".maplibregl-canvas", { timeout: 15000 });
    await page.waitForTimeout(3000);
  });

  test("interference toggle activates without console errors", async ({ page }) => {
    const errors: string[] = [];
    page.on("pageerror", (e) => errors.push(e.message));
    page.on("console", (msg) => {
      if (msg.type() === "error") errors.push(msg.text());
    });

    const checkbox = page.getByRole("checkbox", { name: /interference/i });
    await checkbox.check();
    await expect(checkbox).toBeChecked();

    // Allow fetch + render to settle
    await page.waitForTimeout(2500);

    // No top-level page or console errors during the toggle.
    const fatal = errors.filter((e) => !/Failed to load resource/i.test(e));
    expect(fatal).toEqual([]);
  });

  test("interference toggle is reversible", async ({ page }) => {
    const checkbox = page.getByRole("checkbox", { name: /interference/i });
    await checkbox.check();
    await expect(checkbox).toBeChecked();
    await checkbox.uncheck();
    await expect(checkbox).not.toBeChecked();
  });
});
