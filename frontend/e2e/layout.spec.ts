import { test, expect } from "@playwright/test";

test.describe("Layout", () => {
  test.beforeEach(async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 720 });
    await page.goto("/");
    await page.waitForTimeout(2000);
  });

  test("desktop: map and chat side by side", async ({ page }) => {
    await expect(page.locator(".maplibregl-canvas")).toBeVisible();
    await expect(page.getByText("Groundwater monitoring assistant").first()).toBeVisible();
  });

  test("CSV and Metrics buttons visible", async ({ page }) => {
    await expect(page.getByRole("button", { name: "CSV" }).first()).toBeVisible();
    await expect(page.getByRole("button", { name: "Metrics" }).first()).toBeVisible();
  });

  test("CSV panel opens above chat", async ({ page }) => {
    await page.getByRole("button", { name: "CSV" }).first().click();
    await expect(page.getByText("Drop CSV file here or").first()).toBeVisible();
  });

  test("Metrics panel opens above chat", async ({ page }) => {
    await page.getByRole("button", { name: "Metrics" }).first().click();
    await expect(page.getByText("Model Evaluation").first()).toBeVisible();
  });

  test("Quick commands bar visible", async ({ page }) => {
    await expect(page.getByText("Quick commands").first()).toBeVisible();
  });

  test("command dropdown opens", async ({ page }) => {
    await page.getByText("Quick commands").first().click();
    await expect(page.getByText("Analysis").first()).toBeVisible();
    await expect(page.getByText("Scan for anomalies").first()).toBeVisible();
  });
});
