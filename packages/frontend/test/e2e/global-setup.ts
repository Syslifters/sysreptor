import { chromium, type FullConfig } from '@playwright/test';
import { downloadDemoData, importDemoData } from './util/import_demodata';
import { integrationLogin, integrationSuperuser, selfPromotion } from './util/integration_flows';

async function globalSetup(config: FullConfig) {
  const projectConfig = config.projects[0]?.use;
  if (!projectConfig) {
    throw new Error('Project configuration is undefined');
  }
  const { storageState, baseURL } = projectConfig;
  const browser = await chromium.launch();
  const page = await browser.newPage();
  await integrationLogin(page, baseURL);
  await integrationSuperuser(page);
  await selfPromotion(page);
  await downloadDemoData();
  await importDemoData(page);
  // Let the demo data import...
  await page.context().storageState({ path: storageState as string });
}

export default globalSetup;
