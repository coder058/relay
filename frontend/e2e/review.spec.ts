import { test, expect } from '@playwright/test';
import { readFile } from 'node:fs/promises';

test('SYNTHETIC: pasted listing reaches real Python review and exports original evidence', async ({ page }) => {
  // SOURCE: isolate only the external board. Review and export use the actual local FastAPI service.
  await page.route('**/jobs/search**', route => route.fulfill({ json: {
    jobs: [], matching_count: 0, scanned_count: 0,
    fetched_at: '2026-09-06T00:00:00Z', source_url: 'https://example.test/SYNTHETIC',
    coverage: 'SYNTHETIC empty board for deterministic UI testing',
  }}));
  await page.goto('/');
  await expect(page.getByRole('button', { name: 'Review evidence', exact: true })).toBeDisabled();
  await page.getByRole('button', { name: 'Paste a listing', exact: true }).click();
  await page.getByLabel('Job title', { exact: true }).fill('SYNTHETIC developer role');
  await page.getByLabel('Company', { exact: true }).fill('SYNTHETIC test company');
  await page.getByLabel('Listing text', { exact: true }).fill('Python required.\nReact.js used for dashboards.');
  await page.getByRole('button', { name: 'Add to review', exact: true }).click();
  await page.getByLabel('Skills to look for', { exact: false }).fill('Python, React, Rust');
  await page.getByRole('button', { name: 'Review evidence', exact: true }).click();
  const results = page.getByRole('region', { name: 'Evidence results' });
  await expect(results).toBeVisible();
  await expect(results.locator('blockquote')).toContainText(['Python required.', 'React.js used for dashboards.']);
  await expect(results.getByRole('cell', { name: 'Not found', exact: true })).toHaveCount(1);
  const downloadReady = page.waitForEvent('download');
  await page.getByRole('button', { name: 'Export Markdown', exact: true }).click();
  const download = await downloadReady;
  const exported = await readFile((await download.path())!, 'utf8');
  expect(exported).toContain('SYNTHETIC developer role');
  expect(exported).toContain('Python required.');
  // Editing inputs must invalidate a previously computed review.
  await page.getByLabel('Skills to look for', { exact: false }).fill('Rust');
  await expect(results).toHaveCount(0);
});
