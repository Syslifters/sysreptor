import { expect, test } from '@playwright/test';

const userUsername = 'myuser';
const userPassword = 'Test123!@';
const userNewPassword = 'Test123!@456789'
const userFirstName = 'John';
const userLastName = 'Doe';
const userEmail = 'myuser@example.com'


test('A Admin User can create a new User', async ({ page }) => {
  await page.goto('/users/');

  // Create a User
  await page.getByTestId('create-button').click();
  await page.getByLabel('Username').fill(userUsername);
  await page.getByLabel('Password', { exact: true }).fill(userPassword);
  await page.getByLabel('Password (confirm)').fill(userPassword);
  await page.getByLabel('First Name').fill(userFirstName);
  await page.getByLabel('Last Name').fill(userLastName);
  await page.getByLabel('Email').fill(userEmail);
  await page.getByRole('button', { name: 'Create' }).click();

  // Check if user was created
  await page.goto('/users/');
  await page.getByTestId(`user-${userUsername}`).waitFor();
  expect(await page.isVisible(`text=${userUsername}`)).toBeTruthy();
});

test('A created User can login', async ({ page, context }) => {
  await context.clearCookies();

  await page.goto('/login/local/');
  await page.getByLabel('Username').fill(userUsername);
  await page.getByLabel('Password').fill(userPassword);
  await page.getByRole('button', { name: 'Login' }).click();
  await page.getByLabel('New Password', { exact: true }).fill(userNewPassword);
  await page.getByLabel('New Password (confirm)').fill(userNewPassword);
  await page.getByRole('button', { name: 'Change Password' }).click();
  await page.getByTestId('mfa-setup-skip').click();
  await page.getByRole('heading', { name: 'Projects' }).waitFor();
});

test('A Admin User can delete a User', async ({ page }) => {
  await page.goto('/users/');
  // Delete User
  await page.getByTestId(`user-${userUsername}`).click();
  await page.getByTestId('edittoolbar-contextmenu').click();
  await page.getByTestId('edittoolbar-delete').click();
  // Confirm Delete
  await page.getByTestId('confirm-input').getByRole('textbox').fill(userUsername);
  await page.getByTestId('confirm-button').click();
  await page.getByText('User deleted').waitFor();
});

