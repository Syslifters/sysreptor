import { expect, test } from '@playwright/test';
import { DemoDataState } from '../util/demo_data';
const projectName = 'My Test Project';
test('A User can create an Project with a Name', async ({ page }) => {
  await page.goto('/projects');
  await page.waitForSelector('text=Projects');

  expect(await page.title()).toBe('Projects | SysReptor');
  // Create New Design Modal
  await page.getByTestId('create-button').click();
  // Create New Design Modal
  await page.getByLabel('Name').fill(projectName);
  const designId = new DemoDataState().designs[0];

  await page.getByTestId('project-type').getByRole('textbox').fill('Demo Matrix');
  await page.getByTestId('page-loader').waitFor({ state: 'hidden' });
  await page.getByText('No data found').waitFor({ state: 'hidden' });
  await page.getByTestId('design-' + designId).locator('nth=0').click();
  await page.getByTestId('submit-project').click();

  // Verify Project Name
  await expect(page.getByText(projectName)).toBeVisible();

  await page.getByTestId('project-settings-tab').click();
  await page.getByLabel('Name').waitFor();
  await page.getByLabel('Name').fill('Updated Project Name');
  await page.getByLabel('Tags').fill('Updated Tags');
  await page.keyboard.press('Enter');
  await page.getByRole('button', { name: 'Badge' }).click();
  await page.getByText('Everything Saved').waitFor();
});

test('A User can delete a Project', async ({ page }) => {
  await page.goto('/projects');
  await page.waitForSelector('text=Projects');
  await page.getByRole('link', { name: 'Updated Project Name' }).click();
  await page.getByTestId('project-settings-tab').click();
  await page.getByTestId('options-dots').click();
  await page.getByText('Delete').click();
  await page.getByTestId('confirm-input').getByRole('textbox').fill('Updated Project Name');
  await page.getByRole('button', { name: 'Delete' }).click();
  await page.waitForSelector('text=Projects');
  
});
