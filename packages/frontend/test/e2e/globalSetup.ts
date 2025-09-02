import { chromium, expect, type FullConfig } from '@playwright/test';
import { getIntegrationAdmin } from "./util/admin";
import { downloadDemoData, importDemoData } from './util/import_demodata';

export default async function globalSetup(config: FullConfig) {
  const projectConfig = config.projects[0]?.use;
  const browser = await chromium.launch(); 
  const page = await browser.newPage();

  // Login
  await page.goto(projectConfig.baseURL + '/login/local/');
  await expect(page).toHaveTitle(/Login | SysReptor.*/, { timeout: 60 * 1000 });
  const adminUser = getIntegrationAdmin();
  await page.getByLabel('Username').fill(adminUser.username);
  await page.getByLabel('Password').fill(adminUser.password);
  await page.getByTestId('login-submit').click();
  await page.getByTestId('mfa-setup-skip').click();
  await expect(page).toHaveTitle(/Projects | SysReptor.*/);
  // eslint-disable-next-line no-console
  console.log('Logged in successfully');

  // Enable superuser permissions
  await page.getByTestId('profile-button').click();
  await page.getByTestId('profile-menu-modal').waitFor({ state: 'visible' });
  await page.getByTestId('enable-superuser').click();
  await page.getByLabel('Password').fill(adminUser.password);
  await page.getByTestId('login-submit').click();
  // eslint-disable-next-line no-console
  console.log('Enabled superuser permissions');

  // Goes to User Settings and gives user all permissions
  await page.getByTestId('users-tab').click();
  await page.getByTestId('test-reptor').click();
  await page.getByLabel('First Name').fill('User');
  await page.getByLabel('Last Name').fill('User');
  await page.getByLabel('Email').fill('user@example.com');
  await page.getByTestId('template-editor-checkbox').getByRole('checkbox').check();
  await page.getByTestId('designer-checkbox').getByRole('checkbox').check();
  await page.getByTestId('user-manager-checkbox').getByRole('checkbox').check();
  await page.getByTestId('global-archiver-checkbox').getByRole('checkbox').check();
  await page.getByTestId('project-admin-checkbox').getByRole('checkbox').check();
  await page.getByTestId('save-toolbar').click();
  // eslint-disable-next-line no-console
  console.log('User permissions updated');

  // Save cookies
  await page.context().storageState({ path: projectConfig.storageState as string });

  // Import demo data
  await downloadDemoData();
  await importDemoData(page, projectConfig.baseURL!);
}

