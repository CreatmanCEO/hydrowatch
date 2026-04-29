# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: metrics.spec.ts >> Metrics >> metrics panel loads with data
- Location: e2e\metrics.spec.ts:11:7

# Error details

```
Error: expect(locator).toBeVisible() failed

Locator: getByText('Sample data')
Expected: visible
Timeout: 5000ms
Error: element(s) not found

Call log:
  - Expect "toBeVisible" with timeout 5000ms
  - waiting for getByText('Sample data')

```

# Page snapshot

```yaml
- generic [ref=e1]:
  - main [ref=e2]:
    - generic [ref=e4]:
      - generic [ref=e5]:
        - region "Map" [ref=e6] [cursor=pointer]
        - generic:
          - generic [ref=e7]:
            - button "Zoom in" [ref=e8] [cursor=pointer]
            - button "Zoom out" [ref=e10] [cursor=pointer]
            - button "Drag to rotate map, click to reset north" [ref=e12]
          - group [ref=e14]:
            - generic "Toggle attribution" [ref=e15] [cursor=pointer]
            - generic [ref=e16]:
              - link "MapLibre" [ref=e17] [cursor=pointer]:
                - /url: https://maplibre.org/
              - text: "|"
              - link "OpenFreeMap" [ref=e18] [cursor=pointer]:
                - /url: https://openfreemap.org
              - link "© OpenMapTiles" [ref=e19] [cursor=pointer]:
                - /url: https://www.openmaptiles.org/
              - text: Data from
              - link "OpenStreetMap" [ref=e20] [cursor=pointer]:
                - /url: https://www.openstreetmap.org/copyright
      - generic [ref=e22]:
        - heading "Layers" [level=4] [ref=e23]
        - generic [ref=e24]:
          - generic [ref=e25] [cursor=pointer]:
            - checkbox "⬤ Wells" [checked] [ref=e26]
            - generic [ref=e27]: ⬤
            - generic [ref=e28]: Wells
          - generic [ref=e29] [cursor=pointer]:
            - checkbox "◎ Depression Cone" [ref=e30]
            - generic [ref=e31]: ◎
            - generic [ref=e32]: Depression Cone
          - generic [ref=e33] [cursor=pointer]:
            - checkbox "⟷ Interference" [ref=e34]
            - generic [ref=e35]: ⟷
            - generic [ref=e36]: Interference
    - generic [ref=e38]:
      - generic [ref=e39]:
        - generic [ref=e40]:
          - heading "HydroWatch AI" [level=2] [ref=e41]
          - paragraph [ref=e42]: Groundwater monitoring assistant
        - generic [ref=e43]:
          - button "CSV" [ref=e44]
          - button "Metrics" [active] [ref=e45]
      - generic [ref=e47]:
        - generic [ref=e48]:
          - heading "Model Evaluation" [level=2] [ref=e49]
          - generic [ref=e50]:
            - generic [ref=e51]: Eval run
            - button "Run Eval" [ref=e52]
        - table [ref=e54]:
          - rowgroup [ref=e55]:
            - row "Model Accuracy Schema P50 P95 Cost/req Errors" [ref=e56]:
              - columnheader "Model" [ref=e57]
              - columnheader "Accuracy" [ref=e58]
              - columnheader "Schema" [ref=e59]
              - columnheader "P50" [ref=e60]
              - columnheader "P95" [ref=e61]
              - columnheader "Cost/req" [ref=e62]
              - columnheader "Errors" [ref=e63]
          - rowgroup [ref=e64]:
            - row "deepseek unknown 68.8% 39.6% 2862.5ms 10011.75ms $0.00035 0.0%" [ref=e65]:
              - cell "deepseek unknown" [ref=e66]:
                - generic [ref=e67]: deepseek
                - text: unknown
              - cell "68.8%" [ref=e68]
              - cell "39.6%" [ref=e69]
              - cell "2862.5ms" [ref=e70]
              - cell "10011.75ms" [ref=e71]
              - cell "$0.00035" [ref=e72]
              - cell "0.0%" [ref=e73]
        - generic [ref=e74]:
          - generic [ref=e75]:
            - generic [ref=e76]: Best Accuracy
            - generic [ref=e77]: deepseek — 68.8%
          - generic [ref=e78]:
            - generic [ref=e79]: Fastest (P50)
            - generic [ref=e80]: deepseek — 2862.5ms
          - generic [ref=e81]:
            - generic [ref=e82]: Cheapest
            - generic [ref=e83]: deepseek — $0.00035
          - generic [ref=e84]:
            - generic [ref=e85]: Best Schema
            - generic [ref=e86]: deepseek — 39.6%
        - generic [ref=e87]:
          - paragraph [ref=e88]:
            - strong [ref=e89]: Pool A
            - text: "(simple tasks): Gemini Flash ↔ Cerebras Llama (mutual fallback)"
          - paragraph [ref=e90]:
            - strong [ref=e91]: Pool B
            - text: "(complex): Haiku 4.5 → Sonnet 4.5 (upgrade for reasoning)"
      - generic [ref=e93]:
        - generic [ref=e95]:
          - paragraph [ref=e96]: Welcome to HydroWatch AI
          - paragraph [ref=e97]: I am your groundwater monitoring assistant for the Abu Dhabi aquifer network. I can analyze 25 monitoring wells across 4 clusters in real time.
          - paragraph [ref=e98]: "What I can do:"
          - list [ref=e99]:
            - listitem [ref=e100]:
              - generic [ref=e101]: •
              - text: Query wells by location, status, or cluster
            - listitem [ref=e102]:
              - generic [ref=e103]: •
              - text: "Detect anomalies: debit decline, TDS spikes, sensor faults"
            - listitem [ref=e104]:
              - generic [ref=e105]: •
              - text: Analyze time series trends for any parameter
            - listitem [ref=e106]:
              - generic [ref=e107]: •
              - text: Regional statistics for the current viewport
            - listitem [ref=e108]:
              - generic [ref=e109]: •
              - text: Validate uploaded CSV observation files
          - paragraph [ref=e110]: "How to use:"
          - list [ref=e111]:
            - listitem [ref=e112]: • Click a well on the map — I'll see which one you selected
            - listitem [ref=e113]: • Pan/zoom the map — I know your current viewport
            - listitem [ref=e114]: • Toggle layers (Wells, Depression Cones) in the top-right panel
            - listitem [ref=e115]:
              - text: • Upload CSV via the
              - strong [ref=e116]: CSV
              - text: button above
            - listitem [ref=e117]:
              - text: • View model metrics via the
              - strong [ref=e118]: Metrics
              - text: button
        - paragraph [ref=e119]: "Try asking:"
        - generic [ref=e120]:
          - button "Show anomalies in the viewport" [ref=e121]
          - button "Status of well AUH-01-003" [ref=e122]
          - button "Region statistics" [ref=e123]
          - button "Which wells have high TDS?" [ref=e124]
      - button "Quick commands ▾" [ref=e126]:
        - generic [ref=e127]: Quick commands
        - generic [ref=e128]: ▾
      - generic [ref=e130]:
        - textbox "Ask about wells, anomalies..." [ref=e131]
        - button "Send" [disabled] [ref=e132]
  - button "Open Next.js Dev Tools" [ref=e138] [cursor=pointer]:
    - img [ref=e139]
  - alert [ref=e142]
```

# Test source

```ts
  1  | import { test, expect } from "@playwright/test";
  2  | 
  3  | test.describe("Metrics", () => {
  4  |   test.beforeEach(async ({ page }) => {
  5  |     await page.setViewportSize({ width: 1280, height: 720 });
  6  |     await page.goto("/");
  7  |     await page.waitForTimeout(1000);
  8  |     await page.getByRole("button", { name: "Metrics" }).click();
  9  |   });
  10 | 
  11 |   test("metrics panel loads with data", async ({ page }) => {
  12 |     await expect(page.getByText("Model Evaluation")).toBeVisible();
> 13 |     await expect(page.getByText("Sample data")).toBeVisible();
     |                                                 ^ Error: expect(locator).toBeVisible() failed
  14 |   });
  15 | 
  16 |   test("metrics table has model rows", async ({ page }) => {
  17 |     // Should show at least one model name
  18 |     // Table should have accuracy percentages
  19 |     await expect(page.getByText("%").first()).toBeVisible({ timeout: 5000 });
  20 |   });
  21 | 
  22 |   test("key insights cards visible", async ({ page }) => {
  23 |     await expect(page.getByText("Best Accuracy")).toBeVisible();
  24 |     await expect(page.getByText("Fastest")).toBeVisible();
  25 |     await expect(page.getByText("Cheapest")).toBeVisible();
  26 |   });
  27 | 
  28 |   test("Run Eval button visible", async ({ page }) => {
  29 |     await expect(page.getByRole("button", { name: "Run Eval" })).toBeVisible();
  30 |   });
  31 | });
  32 | 
```