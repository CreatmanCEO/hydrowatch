import { test, expect } from "@playwright/test";

test.describe("Depression cone layer", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/");
    await page.waitForSelector(".maplibregl-canvas", { timeout: 15000 });
    await page.waitForTimeout(3000);
  });

  test("toggle reveals time slider, mode toggle, and legend", async ({ page }) => {
    const errors: string[] = [];
    page.on("pageerror", (e) => errors.push(e.message));

    const checkbox = page.getByRole("checkbox", { name: /depression cone/i });
    await checkbox.check();
    await expect(checkbox).toBeChecked();

    // TimeSlider buttons (1d/7d/30d/90d)
    await expect(page.getByRole("button", { name: "1d" })).toBeVisible();
    await expect(page.getByRole("button", { name: "7d" })).toBeVisible();
    await expect(page.getByRole("button", { name: "30d" })).toBeVisible();
    await expect(page.getByRole("button", { name: "90d" })).toBeVisible();

    // Mode toggle
    await expect(page.getByRole("button", { name: "Selected" })).toBeVisible();
    await expect(page.getByRole("button", { name: "All active" })).toBeVisible();

    // Legend (heading text contains the current t_days; default 30)
    await expect(page.getByText(/Drawdown after \d+d/i)).toBeVisible();

    expect(errors).toEqual([]);
  });

  test("changing time preset updates the legend label", async ({ page }) => {
    const checkbox = page.getByRole("checkbox", { name: /depression cone/i });
    await checkbox.check();
    await expect(page.getByText(/Drawdown after 30d/i)).toBeVisible();

    await page.getByRole("button", { name: "90d" }).click();
    await expect(page.getByText(/Drawdown after 90d/i)).toBeVisible();
  });

  test("overlays disappear when layer is toggled off", async ({ page }) => {
    const checkbox = page.getByRole("checkbox", { name: /depression cone/i });
    await checkbox.check();
    await expect(page.getByRole("button", { name: "30d" })).toBeVisible();

    await checkbox.uncheck();
    await expect(page.getByRole("button", { name: "30d" })).toBeHidden();
  });
});
