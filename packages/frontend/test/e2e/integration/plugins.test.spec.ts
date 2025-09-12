// I guess for now this can be used to test plugins in the future.
// import { expect, test } from '@playwright/test';

// test('A User can use CyberChef', async ({ page }) => {
//   await page.goto(`/`);

//   await page.getByRole('heading', { name: 'Projects' }).waitFor();
//   await page.getByRole('listitem', { name: 'CyberChef' }).click();
//   await page.locator('iframe').contentFrame().locator('#preloader').waitFor({state: 'hidden'});
//   const buffer1 = await page.screenshot();
//   console.log(buffer1.toString('base64'));
//   await page.locator('iframe').contentFrame().locator('#input-text').getByRole('textbox').waitFor({ state: 'visible' });
//   await page.locator('iframe').contentFrame().locator('#input-text').getByRole('textbox').fill('SGVsbG8gV29ybGQ=');
//   await page.locator('iframe').contentFrame().locator('#preloader').waitFor({state: 'hidden'});
//   await page.locator('iframe').contentFrame().locator('#magic').click();
//   await page.locator('iframe').contentFrame().locator('#preloader').waitFor({state: 'hidden'});
//   expect(await page.locator('iframe').contentFrame().locator('#output-text').getByRole('textbox').textContent()).toBe('Hello World');
// });
