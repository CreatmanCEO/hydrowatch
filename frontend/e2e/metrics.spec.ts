import { test, expect } from "@playwright/test";

test.describe("Metrics", () => {
  test.beforeEach(async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 720 });
    await page.goto("/");
    await page.waitForTimeout(1000);
    await page.getByRole("button", { name: "Metrics" }).click();
  });

  test("metrics panel loads with data", async ({ page }) => {
    await expect(page.getByText("Model Evaluation")).toBeVisible();
    await expect(page.getByText("Sample data")).toBeVisible();
  });

  test("metrics table has model rows", async ({ page }) => {
    // Should show at least one model name
    // Table should have accuracy percentages
    await expect(page.getByText("%").first()).toBeVisible({ timeout: 5000 });
  });

  test("key insights cards visible", async ({ page }) => {
    await expect(page.getByText("Best Accuracy")).toBeVisible();
    await expect(page.getByText("Fastest")).toBeVisible();
    await expect(page.getByText("Cheapest")).toBeVisible();
  });

  test("Run Eval button visible", async ({ page }) => {
    await expect(page.getByRole("button", { name: "Run Eval" })).toBeVisible();
  });
});
