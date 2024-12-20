import { expect, test } from '@playwright/test';
import { DemoDataState, DemoDataType } from '../util/demo_data';

test('A User can Create a Template with German and English Translations', async ({ page }) => {
  const testState = new DemoDataState();
  await page.goto('/templates/');
  await page.getByTestId('create-button').click();
  await page.getByTestId('title-en-US').getByRole('textbox').waitFor();
  const templateId = page.url().split('/').at(4);
  testState.addId(DemoDataType.Template, templateId);
  await page.getByTestId('title-en-US').getByRole('textbox').clear();
  await page.getByTestId('title-en-US').getByRole('textbox').fill('My Vulnerability');
  // Add German Translation
  await page.getByRole('tablist').getByRole('button').click();
  await page.getByText('German (de-AT)').click();
  await page.getByTestId('title-de-AT').getByRole('textbox').clear();
  await page.getByTestId('title-de-AT').getByRole('textbox').fill('Meine Schwachstelle');
  await page.getByTestId('save-toolbar').click();
  await page.getByText('Everything saved').waitFor();
});

test('Template Translations are displayed correctly', async ({ page }) => {
  const testState = new DemoDataState();
  const templateId = testState.templates[testState.templates.length - 1];
  await page.goto(`/templates/${templateId}`);
  expect(await page.getByTestId('title-en-US').getByRole('textbox').textContent()).toBe('My Vulnerability');
  await page.getByRole('tab', { name: 'German (de-AT)' }).click();
  expect(await page.getByTestId('title-de-AT').getByRole('textbox').textContent()).toBe('Meine Schwachstelle');
});

test('A User can delete a Template', async ({ page }) => {
  const testState = new DemoDataState();
  const templateId = testState.templates[testState.templates.length - 1];
  await page.goto(`/templates/${templateId}`);
  await page.getByTestId('title-en-US').getByRole('textbox').waitFor();
  if(await page.getByText('It seems like you are editing').isVisible()) {
    await page.getByRole('button', { name: 'Edit Anyway' }).click();
  }
  await page.getByTestId('options-dots').click();
  await page.getByText('Delete').click();
  await page.getByRole('button', { name: 'Delete' }).click();
  await page.getByRole('heading', { name: 'Templates' }).waitFor();
});
