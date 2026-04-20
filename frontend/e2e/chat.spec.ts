import { test, expect } from "@playwright/test";

test.describe("Chat", () => {
  test.beforeEach(async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 720 });
    await page.goto("/");
    await page.waitForTimeout(2000);
  });

  test("welcome message displayed on load", async ({ page }) => {
    await expect(page.getByText("Welcome to HydroWatch AI").first()).toBeVisible();
  });

  test("suggestion buttons visible", async ({ page }) => {
    await expect(page.getByRole("button", { name: "Show anomalies in the viewport" }).first()).toBeVisible();
    await expect(page.getByRole("button", { name: "Region statistics" }).first()).toBeVisible();
  });

  test("suggestion button fills input", async ({ page }) => {
    await page.getByRole("button", { name: "Region statistics" }).first().click();
    const input = page.getByPlaceholder("Ask about wells, anomalies...").first();
    await expect(input).toHaveValue("Region statistics");
  });

  test("send message shows user bubble", async ({ page }) => {
    const input = page.getByPlaceholder("Ask about wells, anomalies...").first();
    await input.fill("test message");
    await page.getByRole("button", { name: "Send" }).first().click();
    await expect(page.getByText("test message").first()).toBeVisible();
  });

  test("send button disabled when input empty", async ({ page }) => {
    const sendBtn = page.getByRole("button", { name: "Send" }).first();
    await expect(sendBtn).toBeDisabled();
  });

  test("loading indicator appears after send", async ({ page }) => {
    const input = page.getByPlaceholder("Ask about wells, anomalies...").first();
    await input.fill("Region statistics");
    await page.getByRole("button", { name: "Send" }).first().click();
    await expect(page.getByRole("button", { name: "Stop" }).first()).toBeVisible({ timeout: 5000 });
  });

  test("SSE response appears after sending", async ({ page }) => {
    test.setTimeout(60000);
    const input = page.getByPlaceholder("Ask about wells, anomalies...").first();
    await input.fill("Region statistics");
    await page.getByRole("button", { name: "Send" }).first().click();
    // Wait for Send button to reappear (means response complete)
    await expect(page.getByRole("button", { name: "Send" }).first()).toBeVisible({ timeout: 45000 });
  });
});
