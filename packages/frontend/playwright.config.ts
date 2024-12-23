import { defineConfig } from '@playwright/test';

export default defineConfig({
  globalSetup: './test/e2e/global-setup',
  reporter: [
    ['junit', {  outputFile: 'test-reports/junit.xml' }]
  ],
  outputDir: './test-reports',
  testDir: './test/e2e',
  // fullyParallel: true,

  // Fail the build on CI if you accidentally left test.only in the source code.
  forbidOnly: !!process.env.CI,

  // Retry on CI only.
  retries: process.env.CI ? 2 : 0,

  // Opt out of parallel tests on CI.
  workers: 1,

  use: {
    baseURL: 'http://localhost:3000',
    // Collect trace when retrying the failed test.
    trace: 'on-first-retry',
    storageState: './test/e2e/state.json',
  },
  webServer: {
    command: 'echo "starting webserver" && npm run dev',
    url: 'http://localhost:3000',
    reuseExistingServer: true,
    stdout: "pipe",
  },
});
