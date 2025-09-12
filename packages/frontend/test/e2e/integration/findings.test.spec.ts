import { expect, test } from '@playwright/test';
import { DemoDataState } from '../util/demo_data';

test('A User can Create a Finding an Export an Report', async ({ page }) => {
  const projectId = new DemoDataState().projects[0];
  await page.goto(`/projects/${projectId}`);
  await page.getByText('Reporting').click();
  await page.getByTestId('create-finding-button').click();
  await page.getByLabel('Template (optional)').locator('nth=0').fill('SQL Injection');
  await page.getByText('SQL Injection (SQLi)').locator('nth=0').waitFor()
  await page.getByText('SQL Injection (SQLi)').locator('nth=0').click();
  await page.getByText('Create From Template').click();
  await page.getByRole('textbox').getByText('SQL Injection (SQLi)').waitFor();
  await page.getByRole('textbox').getByText('SQL Injection (SQLi)').fill('My SQL Injection');
  await page.getByText('Publish').click();
  await page.waitForSelector('text=Download');
  expect(await page.getByText('Download').isVisible()).toBeTruthy();
});

test('A User can edit a CVSS Score', async ({ page }) => {
  const projectId = new DemoDataState().projects[0];
  await page.goto(`/projects/${projectId}`);
  await page.getByText('Project Settings').waitFor();
  await page.getByTestId('project-reporting-tab').click();
  await page.getByRole('option', { name: 'Ajla' }).waitFor();
  await page.getByRole('option', { name: 'Ajla' }).click();
  await page.getByLabel('CVSS').waitFor();
  await page.getByRole('button', { name: 'CVSS Editor' }).click();
  await page.waitForSelector('text=CVSS:3.1 Editor');
  await page.getByTestId('cvss-metric-AV-N').click();
  await page.getByTestId('cvss-metric-AC-H').click();
  await page.getByTestId('cvss-metric-PR-L').click();
  await page.getByTestId('cvss-metric-UI-R').click();
  await page.getByTestId('cvss-metric-S-U').click();
  await page.getByTestId('cvss-metric-C-L').click();
  await page.getByTestId('cvss-metric-I-L').click();
  await page.getByTestId('cvss-metric-A-L').click();

  await page.getByTestId('cvss-metric-E-P').click();
  await page.getByTestId('cvss-metric-RL-O').click();
  await page.getByTestId('cvss-metric-RC-C').click();

  expect(await page.getByRole('dialog').getByText('4.2').isVisible()).toBeTruthy();
  await page.getByTestId('cvss-apply').click();
  await page.getByRole('dialog').waitFor({ state: 'hidden' });

  expect(await page.getByLabel('CVSS').textContent(), 'CVSS:3.1/AV:N/AC:H/PR:L/UI:R/S:U/C:L/I:L/A:L/E:P/RL:O/RC:C');

  await page.getByTestId('project-settings-tab').click();
  await page.getByLabel('Name').waitFor();

});

test('Version History correctly displays the changes CVSS changes', async ({ page }) => {
  const projectId = new DemoDataState().projects[0];
  await page.goto(`/projects/${projectId}`);
  await page.getByText('Project Settings').waitFor();
  await page.getByTestId('project-reporting-tab').click();
  await page.getByRole('option', { name: 'Ajla' }).waitFor();
  await page.getByRole('option', { name: 'Ajla' }).click();
  await page.getByLabel('CVSS').waitFor();
  await page.getByTestId('history-button').click();
  await page.locator('circle').nth(1).waitFor({ state: 'hidden'})
  await page.getByText('reptorImported').click();
  await page.getByRole('link', { name: 'Close Version History' }).waitFor();
  expect(await page.locator('#cvss').getByText('4.2').isVisible()).toBeTruthy();
  expect(await page.getByText('10.0').isVisible()).toBeTruthy();
});

test('A User can assign a Finding to a User and change status', async ({ page }) => {
  const projectId = new DemoDataState().projects[0];
  await page.goto(`/projects/${projectId}`);
  await page.getByText('Project Settings').waitFor();
  await page.getByTestId('project-reporting-tab').click();
  await page.getByRole('option', { name: 'Ajla' }).waitFor();
  await page.getByRole('option', { name: 'Ajla' }).click();
  await page.getByLabel('CVSS').waitFor();

  // Happens when test are run out of order
  if(await page.getByLabel('Clear Assignee').isVisible()) {
    await page.getByLabel('Clear Assignee').click();
  }
  await page.getByLabel('Assignee', { exact: true }).click();
  await page.getByText('reptor (User User)', { exact: true }).click();
  await page.getByTestId('status-select').click();
  await page.getByTestId('status-in-progress').waitFor();
  await page.getByTestId('status-in-progress').click();
  await page.keyboard.press('Escape');
  await page.getByTestId('status-in-progress').waitFor({ state: 'hidden' });
  expect(await page.locator('div').filter({ hasText: /^reptor \(User User\)$/ }).first().isVisible()).toBeTruthy();
  expect(await page.getByTestId('status-select').getByText('In progress').isVisible()).toBeTruthy();
});

test('A User create a Template from a Finding', async ({ page }) => {
  const projectId = new DemoDataState().projects[0];
  await page.goto(`/projects/${projectId}`);
  await page.getByText('Project Settings').waitFor();
  await page.getByTestId('project-reporting-tab').click();
  await page.getByRole('option', { name: 'DC', exact: true }).click();
  await page.getByLabel('CVSS').waitFor();
  await page.getByTestId('edittoolbar-contextmenu').click();
  await page.getByText('Save as Template').click();
  await page.getByTestId('title-en-US').getByRole('textbox').waitFor();
  await page.getByTestId('title-en-US').getByRole('textbox').fill('My Template');
  await page.getByTestId('template-status').click();
  await page.getByTestId('status-finished').click();
  await page.keyboard.press('Escape');
  await page.getByRole('main').locator('button').nth(2).click();
  await page.getByRole('button', { name: 'Save' }).click();

  // Check if the template is saved and can be used
  await page.goto(`/projects/${projectId}`);
  await page.getByText('Project Settings').waitFor();
  await page.getByTestId('project-reporting-tab').click();
  await page.getByTestId('create-finding-button').click();
  await page.getByLabel('Template (optional)').locator('nth=0').fill('My Template');
  await page.getByTestId('page-loader').waitFor({ state: 'hidden' });
  await page.getByTestId('select-item-My Template').first().click();
  await page.getByRole('button', { name: 'Create from Template' }).click();
  await page.getByRole('button', { name: 'Create from Template' }).waitFor({ state: 'hidden' });
  await page.getByTestId('create-finding-dialog').waitFor({ state: 'hidden' });
  expect(await page.getByRole('option', { name: 'My Template @reptor' }).first().isVisible()).toBeTruthy();
});
