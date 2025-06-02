import { defineVitestConfig } from '@nuxt/test-utils/config';
export default defineVitestConfig({
  test: {
    environment: 'happy-dom',
    dir: 'test',
    include: ['**/*.test.ts'],
    reporters: ['default', 'junit'],
    outputFile: '../test-reports/junit.xml',
  },
});
