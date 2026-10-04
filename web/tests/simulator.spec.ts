import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

async function start(page: import('@playwright/test').Page) {
  await page.addInitScript(() => { if (!localStorage.getItem('marie.theme')) localStorage.setItem('marie.theme', 'light'); });
  await page.goto('/');
  await expect(page.getByRole('button', { name: 'Assemble', exact: true })).toBeEnabled();
}
async function example(page: import('@playwright/test').Page, index: number) {
  await page.getByLabel('Load example (replaces current source)').selectOption(String(index));
  await page.getByRole('button', { name: 'Assemble', exact: true }).click();
  await expect(page.getByRole('button', { name: 'Run', exact: true })).toBeEnabled();
}

test('assemble, step, run, output, inspect, reset, refresh', async ({ page }, info) => {
  const errors: string[] = []; page.on('pageerror', e => errors.push(e.message));
  await start(page); await example(page, 0);
  await page.getByRole('button', { name: 'Step', exact: true }).click();
  await expect(page.locator('.register.accumulator .register-value code')).toHaveText('000C');
  await expect(page.locator('.execution-line')).toContainText('Add');
  await page.getByRole('button', { name: 'Run', exact: true }).click();
  await expect(page.locator('.status')).toContainText('Halted');
  await expect(page.getByRole('region', { name: 'Program output' })).toContainText('0x0014');
  await page.getByRole('button', { name: 'Address 007, hex 0014, decimal 20', exact: true }).click();
  await expect(page.locator('.memory-footer')).toContainText('20 decimal');
  await page.getByRole('button', { name: 'Reset', exact: true }).click();
  await expect(page.locator('.status')).toContainText('Ready');
  await expect(page.getByRole('region', { name: 'Program output' })).not.toContainText('0x0014');
  await page.reload(); await expect(page.locator('.status')).toContainText('Ready');
  await expect(page.getByRole('button', { name: 'Run', exact: true })).toBeEnabled();
  expect(errors).toEqual([]);
  await page.evaluate(() => window.scrollTo(0, 0));
  await page.screenshot({ path: `test-results/${info.project.name}-workspace.png`, fullPage: true });
});

test('input yields, accepts signed value, and resumes explicitly', async ({ page }) => {
  await start(page); await example(page, 1);
  await page.getByRole('button', { name: 'Run', exact: true }).click();
  await expect(page.locator('.status')).toContainText('Waiting for input');
  await page.getByLabel('Your program is waiting for a number').fill('-7');
  await page.getByRole('button', { name: 'Supply input' }).click();
  await expect(page.locator('.status')).toContainText('Paused');
  await page.getByRole('button', { name: 'Run', exact: true }).click();
  await expect(page.locator('.status')).toContainText('Halted');
  await expect(page.getByRole('region', { name: 'Program output' })).toContainText('0xFFF9');
});

test('assembly diagnostics, source persistence, disconnected and expired states', async ({ page }) => {
  await start(page);
  const editor = page.getByRole('textbox', { name: 'MARIE assembly source' });
  await editor.fill('Load Missing\nHalt');
  await page.getByRole('button', { name: 'Assemble', exact: true }).click();
  await expect(page.getByRole('alert')).toContainText('Assembly error · line 1');
  await expect(page.locator('.assembly-error-line')).toContainText('Load Missing');
  await page.reload(); await expect(editor).toContainText('Load Missing');
  await expect(page.getByRole('button', { name: 'Assemble', exact: true })).toBeEnabled();
  await example(page, 0);
  await page.route('**/api/sessions/*', route => route.abort());
  await expect(page.locator('.status')).toContainText('Disconnected');
  await page.unroute('**/api/sessions/*');
  await page.getByRole('button', { name: 'Reconnect', exact: true }).click();
  await expect(page.locator('.status')).toContainText('Ready');
  await page.route('**/api/sessions/*', route => route.fulfill({ status:404, contentType:'application/json', body:JSON.stringify({detail:'Session expired or unavailable.'}) }));
  await expect(page.locator('.status')).toContainText('Session expired');
  await page.unroute('**/api/sessions/*');
  await page.getByRole('button', { name: 'Start a new session' }).click();
  await page.getByRole('button', { name: 'Assemble', exact: true }).click();
  await expect(page.locator('.status')).toContainText('Ready');
});

test('pause a loop, themes, navigation, layout, accessibility', async ({ page }, info) => {
  await start(page);
  await page.getByRole('textbox', { name: 'MARIE assembly source' }).fill('Loop, Jump Loop');
  await page.getByRole('button', { name: 'Assemble', exact: true }).click();
  await page.getByRole('button', { name: 'Run', exact: true }).click();
  await expect(page.getByRole('button', { name: 'Pause', exact: true })).toBeEnabled();
  await page.getByRole('button', { name: 'Pause', exact: true }).click();
  await expect(page.locator('.status')).toContainText('Paused');
  const lightResults = await new AxeBuilder({ page }).withTags(['wcag2a','wcag2aa','wcag21aa']).analyze();
  expect(lightResults.violations).toEqual([]);
  await page.getByRole('button', { name: 'Switch to dark theme' }).click();
  await expect(page.locator('html')).toHaveAttribute('data-theme', 'dark');
  await page.reload(); await expect(page.locator('html')).toHaveAttribute('data-theme', 'dark');
  await expect(page.locator('.status')).toContainText('Paused');
  await page.evaluate(() => window.scrollTo(0, 0));
  await page.screenshot({ path: `test-results/${info.project.name}-dark.png`, fullPage: true });
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  for (const control of ['Assemble','Run','Pause','Step','Reset']) await expect(page.getByRole('button',{name:control,exact:true})).toBeVisible();
  const results = await new AxeBuilder({ page }).withTags(['wcag2a','wcag2aa','wcag21aa']).analyze();
  expect(results.violations).toEqual([]);
  if (info.project.name === 'mobile') await page.getByRole('button', { name:'Toggle navigation' }).click();
  await page.getByRole('button', { name:'Instruction guide', exact:true }).click();
  await expect(page.getByRole('heading', { name:'Meet your little machine.' })).toBeVisible();
  const guideResults = await new AxeBuilder({ page }).withTags(['wcag2a','wcag2aa','wcag21aa']).analyze();
  expect(guideResults.violations).toEqual([]);
});

test('all examples produce expected output', async ({ page }) => {
  await start(page);
  for (const [index, output] of [[2,'0x0001'],[3,'0x002A'],[4,'0x0012']] as const) {
    await example(page,index);
    await page.getByLabel('Execution speed').selectOption('1000');
    await expect(page.getByRole('button', {name:'Run',exact:true})).toBeEnabled();
    await page.getByRole('button', { name:'Run',exact:true }).click();
    await expect(page.locator('.status')).toContainText('Halted');
    await expect(page.getByRole('region',{name:'Program output'})).toContainText(output);
  }
});

test('an expired running session can be assembled again', async ({ page }) => {
  await start(page);
  await page.getByRole('textbox', { name: 'MARIE assembly source' }).fill('Loop, Jump Loop');
  await page.getByRole('button', { name: 'Assemble', exact: true }).click();
  await page.getByRole('button', { name: 'Run', exact: true }).click();
  await expect(page.locator('.status')).toContainText('Running');
  await page.route('**/api/sessions/*', route => route.fulfill({ status:404, contentType:'application/json', body:JSON.stringify({detail:'Session expired or unavailable.'}) }));
  await expect(page.locator('.status')).toContainText('Session expired');
  await page.unroute('**/api/sessions/*');
  await page.getByRole('button', { name: 'Start a new session' }).click();
  await expect(page.getByRole('button', { name:'Assemble',exact:true })).toBeEnabled();
  await page.getByRole('button', { name:'Assemble',exact:true }).click();
  await expect(page.locator('.status')).toContainText('Ready');
});
