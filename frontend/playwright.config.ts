import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false,
  timeout: 30000,
  webServer: [
    {
      command: "cd ../backend && .venv/Scripts/uvicorn main:app --port 8000",
      port: 8000,
      reuseExistingServer: true,
    },
    {
      command: "npm run dev -- --port 3000",
      port: 3000,
      reuseExistingServer: true,
    },
  ],
  use: {
    baseURL: "http://localhost:3000",
    screenshot: "only-on-failure",
  },
  projects: [
    { name: "chromium", use: { browserName: "chromium" } },
  ],
});
