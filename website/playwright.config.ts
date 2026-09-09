import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./tests",
  fullyParallel: true,
  use: {
    baseURL: "http://127.0.0.1:4321/oh-my-harness/",
    browserName: "chromium",
    viewport: { width: 1440, height: 900 },
  },
  webServer: {
    command: "node scripts/preview.mjs",
    url: "http://127.0.0.1:4321/oh-my-harness/",
    reuseExistingServer: !process.env.CI,
  },
});
