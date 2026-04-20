import { test, expect } from "@playwright/test";

test.describe("Command Bar", () => {
  test.beforeEach(async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 720 });
    await page.goto("/");
    await page.waitForTimeout(2000);
  });

  test("command bar toggle opens dropdown", async ({ page }) => {
    await page.getByText("Quick commands").first().click();
    await expect(page.getByText("Analysis").first()).toBeVisible();
    await expect(page.getByText("Monitoring").first()).toBeVisible();
  });

  test("clicking command sends message", async ({ page }) => {
    await page.getByText("Quick commands").first().click();
    await page.getByText("Region overview").first().click();
    await expect(page.getByText("Complete overview").first()).toBeVisible({ timeout: 5000 });
  });

  test("dropdown closes after command selection", async ({ page }) => {
    await page.getByText("Quick commands").first().click();
    await expect(page.getByText("Scan for anomalies").first()).toBeVisible();
    await page.getByText("Region overview").first().click();
    await page.waitForTimeout(500);
  });
});
