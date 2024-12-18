import { expect, type Page } from '@playwright/test';
import { IntegrationAdmin } from "./admin";

export const integrationLogin = async (page: Page, baseURL: string|undefined) => {
  await page.goto(baseURL + '/login/local/');
  await expect(page).toHaveTitle("Login | SysReptor");
  await page.getByLabel('Username').fill(IntegrationAdmin.username);
  await page.getByLabel('Password').fill(IntegrationAdmin.password);
  await page.getByTestId('login-submit').click();
  await page.getByTestId('mfa-setup-skip').click();
  await expect(page).toHaveTitle("Projects | SysReptor");
}

export const integrationSuperuser = async (page: Page) => {
  await page.getByTestId('profile-button').click();
  await page.getByTestId('profile-menu-modal').waitFor({ state: 'visible' });
  await page.getByTestId('enable-superuser').click();
  await page.getByLabel('Password').fill(IntegrationAdmin.password);
  await page.getByTestId('login-submit').click();
}

// Goes to User Settings and gives user all permissions
export const selfPromotion = async (page: Page, baseURL: string|undefined) => {
  await page.getByTestId('users-tab').click();
  await page.getByTestId('test-reptor').click();
  await page.getByLabel('First Name').fill('User');
  await page.getByLabel('Last Name').fill('User');
  await page.getByTestId('template-editor-checkbox').getByRole('checkbox').check();
  await page.getByTestId('designer-checkbox').getByRole('checkbox').check();
  await page.getByTestId('user-manager-checkbox').getByRole('checkbox').check();
  await page.getByTestId('global-archiver-checkbox').getByRole('checkbox').check();
  await page.getByTestId('project-admin-checkbox').getByRole('checkbox').check();
  await page.getByTestId('save-toolbar').click();
};