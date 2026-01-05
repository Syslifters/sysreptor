import type { Page } from "@playwright/test";

export async function createProject(page: Page, options: { projectName: string, designId: string, designName: string }) {
  // Click create project button
  await page.goto('/projects');
  await page.waitForSelector('text=Projects');
  await page.getByTestId('create-button').click();

  // Fill project name
  await page.getByLabel('Name').fill(options.projectName);
  
  // Select design
  const designSelection = await page.getByTestId('project-type').locator('css=input[type=text]');
  await designSelection.clear();
  await designSelection.fill(options.designName);
  await page.getByTestId('page-loader').waitFor({ state: 'hidden' });
  await page.getByText('No data found').waitFor({ state: 'hidden' });
  await page.getByTestId(`design-${options.designId}`).click();

  // Create
  await page.getByTestId('submit-project').click();
}


export async function clickListItemLink(page: Page, name: string) {
  await page.getByRole('link', { name }).first().waitFor();
  await page.getByRole('link', { name }).first().click();
}

