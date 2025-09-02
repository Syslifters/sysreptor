import { defineConfig, devices } from '@playwright/test'
import type { ConfigOptions } from '@nuxt/test-utils/playwright'
import { isCI } from 'std-env'

export default defineConfig<ConfigOptions>({
  testDir: './test/e2e',
  globalSetup: './test/e2e/globalSetup',

  use: {
    baseURL: 'http://localhost:3000',
    // Collect trace when retrying the failed test.
    trace: 'on-first-retry',
    storageState: './test/e2e/state.json',
  },
  projects: [
    {
      name: 'chromium',
      use: devices['Desktop Chrome'],
    },
  ],
  webServer: {
    command: 'echo "starting webserver" && npm run dev',
    url: 'http://localhost:3000',
    reuseExistingServer: true,
    stdout: "pipe",
  },

  reporter: [
    ['junit', {  outputFile: 'test-reports/junit.xml' }]
  ],
  outputDir: './test-reports',
  

  // Fail the build on CI if you accidentally left test.only in the source code.
  forbidOnly: !!isCI,

  // Retry on CI only.
  retries: isCI ? 2 : 0,

  // Opt out of parallel tests on CI.
  workers: 1,
  fullyParallel: false,

  // Modified timeouts
  timeout: 60 * 1000,
  expect: {
    timeout: 10 * 1000,
  },
});
