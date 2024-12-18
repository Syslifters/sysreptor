import { defineVitestConfig } from '@nuxt/test-utils/config';
export default defineVitestConfig({
  test: {
    environment: 'happy-dom',
    dir: 'test',
    exclude: ['**/*.spec.ts'],
    reporters: ['default', 'junit'],
    outputFile: '../test-reports/junit.xml',
  },
});
