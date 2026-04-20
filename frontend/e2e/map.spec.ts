import { test, expect } from "@playwright/test";

test.describe("Map", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/");
    // Wait for map tiles and wells to load
    await page.waitForSelector(".maplibregl-canvas", { timeout: 15000 });
    await page.waitForTimeout(3000);
  });

  test("map renders with MapLibre canvas", async ({ page }) => {
    const canvas = page.locator(".maplibregl-canvas");
    await expect(canvas).toBeVisible();
  });

  test("navigation controls visible", async ({ page }) => {
    const nav = page.locator(".maplibregl-ctrl-zoom-in");
    await expect(nav).toBeVisible();
  });

  test("layer controls panel visible", async ({ page }) => {
    await expect(page.getByText("Layers", { exact: false }).first()).toBeVisible();
    await expect(page.getByText("Wells").first()).toBeVisible();
    await expect(page.getByText("Depression Cones").first()).toBeVisible();
  });

  test("wells checkbox is checked by default", async ({ page }) => {
    const wellsCheckbox = page.locator("input[type=checkbox]").first();
    await expect(wellsCheckbox).toBeChecked();
  });

  test("depression cones toggle works", async ({ page }) => {
    const conesCheckbox = page.locator("input[type=checkbox]").nth(1);
    await conesCheckbox.check();
    await expect(conesCheckbox).toBeChecked();
    await conesCheckbox.uncheck();
    await expect(conesCheckbox).not.toBeChecked();
  });
});
