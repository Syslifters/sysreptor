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
  await page.getByTestId(`user-${adminUser.username}`).click();
  await page.getByLabel('First Name').fill('User');
  await page.getByLabel('Last Name').fill('User');
  await page.getByLabel('Email').fill('user@example.com');
  for (const roleName of ['Template Editor', 'Designer', 'User Manager', 'Global Archiver', 'Project Admin']) {
    await page.getByTestId('roles-select').click();
    const option = page.getByRole('option', { name: roleName, exact: true });
    if (await option.getAttribute('aria-selected') !== 'true') {
      await option.click();
    }
  }
  await page.keyboard.press('Escape');
  await page.getByTestId('save-toolbar').click();
  // eslint-disable-next-line no-console
  console.log('User permissions updated');

  // Save cookies
  await page.context().storageState({ path: projectConfig.storageState as string });

  // Import demo data
  await downloadDemoData();
  await importDemoData(page, projectConfig.baseURL!);
}

