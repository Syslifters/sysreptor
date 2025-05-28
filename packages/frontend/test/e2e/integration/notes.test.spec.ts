import { expect, test } from '@playwright/test';
import { DemoDataState } from '../util/demo_data';
const noteTitle = 'My First Note';
const noteText = 'This is my first note';

test('A User can create, write and delete a Note', async ({ page }) => {
  const projectId = new DemoDataState().projects[0];
  await page.goto(`/projects/${projectId}`);

  // Open Notes Tab
  await page.getByTestId('project-notes-tab').click();

  // Create a Note
  await page.getByTestId('create-note').click();

  await page.getByTestId('note-title').getByRole('textbox').fill(noteTitle);

  await page.getByTestId('note-text').getByRole('textbox').fill(noteText);

  await page.getByTestId('note-title').getByText(noteTitle).waitFor();
  
  await page.getByTestId('note-text').getByRole('textbox').getByText(noteText).waitFor();

  expect(await page.getByTestId('note-title').getByText(noteTitle).isVisible()).toBeTruthy();
  expect(await page.getByTestId('note-text').getByRole('textbox').getByText(noteText).isVisible()).toBeTruthy();

  await page.getByTestId('edittoolbar-contextmenu').click();
  await page.getByTestId('edittoolbar-delete').click();
  await page.getByTestId('confirm-button').click();
  await page.getByTestId('confirm-button').waitFor({ state: 'hidden' });
  expect(await page.getByTestId('note-title').getByText(noteTitle).isVisible()).toBeFalsy();
  expect(await page.getByTestId('note-text').getByRole('textbox').getByText(noteText).isVisible()).toBeFalsy();
  expect(await page.getByText(noteTitle).isVisible()).toBeFalsy();
});


// test('ffasf', async ({ page }) => {
//   await page.goto('/projects');
//   await page.getByTestId('profile-button').click();
//   await page.getByTestId('profile-menu-modal').waitFor({ state: 'visible' });
//   await page.getByTestId('enable-superuser').click();
//   await page.getByLabel('Password').fill(IntegrationAdmin.password);
//   await page.getByTestId('login-submit').click();
// });
