import { defineVitestConfig } from 'nuxt-vitest/config'

export default defineVitestConfig({
  test: {
    environment: 'happy-dom',
    dir: 'test',
    reporters: ['default', 'junit'],
    outputFile: '../test-reports/junit.xml'
  }
});
