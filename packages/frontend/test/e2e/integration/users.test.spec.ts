import { chromium, expect, test } from '@playwright/test';
import fs from 'fs';
const userUsername = 'MyUser';
const userPassword = 'Test123!@';
const userNewPassword = 'Test123!@456789'
const userFirstName = 'John';
const userLastName = 'Doe';


test('A Admin User can create a new User', async ({ page }) => {
  await page.goto('/users/');

  // Create a User
  await page.getByTestId('create-button').click();
  await page.getByLabel('Username').fill(userUsername);
  await page.getByLabel('Password', { exact: true }).fill(userPassword);
  await page.getByLabel('Password (confirm)').fill(userPassword);
  await page.getByLabel('First Name').fill(userFirstName);
  await page.getByLabel('Last Name').fill(userLastName);
  await page.getByRole('button', { name: 'Create' }).click();

  // Check if user was created
  await page.goto('/users/');
  await page.getByRole('link', { name: userUsername }).waitFor();
  expect(await page.isVisible(`text=${userUsername}`)).toBeTruthy();
});

test('A created User can login', async ({ page }) => {
  const browser = await chromium.launch();
  // create temporary storage state (so we can login as the user and not loose the admin session)
  fs.writeFileSync('../state2.json', "{}");
  const context1 = await browser.newContext({
    storageState: '../state2.json'
  });
  const page1 = await context1.newPage();
  await page1.goto('/login/local');
  await page1.getByLabel('Username').fill(userUsername);
  await page1.getByLabel('Password').fill(userPassword);
  await page1.getByRole('button', { name: 'Login' }).click();
  await page1.getByLabel('New Password', { exact: true }).fill(userNewPassword);
  await page1.getByLabel('New Password (confirm)').fill(userNewPassword);
  await page1.getByRole('button', { name: 'Change Password' }).click();
  await page1.getByTestId('mfa-setup-skip').click();
  await page1.getByRole('heading', { name: 'Projects' }).waitFor();
  await browser.close();
  // delete storage state
  fs.unlinkSync('../state2.json');
});

test('A Admin User can delete a User', async ({ page }) => {
  await page.goto('/users/');
  // Delete User
  await page.getByRole('link', { name: userUsername }).click();
  await page.getByTestId('options-dots').click();
  await page.getByText('Delete').click();
  // Confirm Delete
  await page.getByTestId('confirm-input').getByRole('textbox').fill(userUsername);
  await page.getByTestId('confirm-button').click();
  await page.getByText('User deleted').waitFor();
});

