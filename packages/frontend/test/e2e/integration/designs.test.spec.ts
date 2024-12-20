import { expect, test } from '@playwright/test';
import { DemoDataState, DemoDataType } from '../util/demo_data';

const designName = 'My Test Design';
test('A User can create an Design with a Name', async ({ page }) => {
  await page.goto('/designs');

  // Navigate to Design Tab 
  await expect(page).toHaveTitle("Designs | SysReptor");

  // Create New Design Modal
  await page.getByTestId('create-button').click();
  await page.getByTestId('copy-existing-design').getByRole('textbox').fill(designName);
  await page.locator('circle').nth(1).waitFor({state: 'hidden'});
  await page.keyboard.press('Escape');
  await page.getByTestId('submit-design').waitFor();
  await page.getByTestId('submit-design').click();

  // Enter Design Name
  await page.getByLabel('Name').waitFor();
  // Save Design Id
  const url = page.url();
  const designId = url.split('/').pop();
  const testState = new DemoDataState();
  testState.addId(DemoDataType.Design, designId);
  await page.getByLabel('Name').fill(designName);

  // Save Design
  await page.getByTestId('save-toolbar').click();

  // Open PDF Designer
  await page.getByText('Report Fields').click();
  await page.getByText('Executive Summary').click();
  await page.getByText('**TODO: write executive').fill('This is a test executive summary');
  await page.getByTestId('save-toolbar').click();
  await page.getByText('Everything saved').waitFor();
  await page.getByText('Finding Fields').click();
  await page.getByText('Finding Ordering').waitFor();
  await page.getByText('title').first().click();
  await page.getByTestId('default-value').getByRole('textbox').clear()
  await page.getByTestId('default-value').getByRole('textbox').fill('My Test Finding Title');
  await page.getByTestId('save-toolbar').click();
  await page.getByText('Everything saved').waitFor();
});

test('Design Settings are reflected in a Project', async ({ page }) => {
  const testState = new DemoDataState();
  await page.goto('/projects');
  await page.waitForSelector('text=Projects');
  await page.getByTestId('create-button').click();
  await page.getByLabel('Name').fill('My Design Test Project');
  await page.getByTestId('project-type').getByRole('textbox').fill(designName);
  await page.getByTestId('page-loader').waitFor({ state: 'hidden' });
  await page.getByText('No data found').waitFor({ state: 'hidden' });
  const designId = testState.designs.at(testState.designs.length - 1);
  await page.getByTestId(`design-${designId}`).click();
  await page.getByTestId('submit-project').click();
  await page.getByRole('link', { name: 'Executive Summary' }).click();
  await page.getByLabel('Assignee', { exact: true }).waitFor();
  expect(await page.getByRole('textbox').getByText('This is a test executive summary').isVisible()).toBeTruthy();
  await page.getByTestId('create-finding-button').click();
  await page.getByRole('button', { name: 'Create Empty Finding' }).click();
  await page.getByTestId('create-finding-dialog').waitFor({ state: 'hidden' });
  await page.getByTestId('title').getByRole('textbox').waitFor();
  expect(await page.getByTestId('title').getByRole('textbox').getByText('My Test Finding Title').isVisible()).toBeTruthy();
});
