import { expect, test } from '@playwright/test';
import { DemoDataState } from '../util/demo_data';
import { createProject } from '../util/helpers';

const projectName = 'Updated Project Name';

test('A User can create an Project with a Name', async ({ page }) => {
  const oldProjectName = 'My Test Project'
  await createProject(page, { projectName: oldProjectName, designId: new DemoDataState().designs[0]!, designName: 'Demo Calzone' });

  // Verify Project Name
  await expect(page.getByText(oldProjectName)).toBeVisible();

  await page.getByTestId('project-settings-tab').click();
  await page.getByLabel('Name').waitFor();
  await page.getByLabel('Name').fill(projectName);
  await page.getByLabel('Tags').fill('Updated Tags');
  await page.keyboard.press('Enter');
  await page.getByTestId('save-toolbar').click();
  await page.getByText('Everything Saved').waitFor();
});

test('A User can delete a Project', async ({ page }) => {
  await page.goto('/projects');
  await page.waitForSelector('text=Projects');
  await page.getByText(projectName).click();
  await page.getByTestId('project-settings-tab').click();
  await page.getByTestId('edittoolbar-contextmenu').click();
  await page.getByTestId('edittoolbar-delete').click();
  await page.getByTestId('confirm-input').getByRole('textbox').fill(projectName);
  await page.getByTestId('confirm-button').click();
  await page.waitForSelector('text=Projects');
});
