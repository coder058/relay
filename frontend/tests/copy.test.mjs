import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

const html = readFileSync(new URL('../index.html', import.meta.url), 'utf8');
const desk = readFileSync(new URL('../src/components/JobDesk.tsx', import.meta.url), 'utf8');

test('page introduces the task without unsupported licensing or hiring claims', () => {
  assert.match(html, /Relay — Job requirement review/);
  assert.doesNotMatch(html, /open-source|not a match score/);
  assert.match(desk, /Add a listing, enter the skills you want to find/);
  assert.match(desk, /Do not paste your CV or private messages/);
});

test('board counts are optional while search and review remain available', () => {
  assert.match(desk, /<details className="desk-panel summary-panel">/);
  assert.match(desk, /<summary>Skill mentions on the public board<\/summary>/);
  assert.match(desk, /aria-label="Find listings"/);
  assert.match(desk, /aria-label="Review queue"/);
  assert.match(desk, /onClick=\{\(\) => void review\(\)\}/);
});
