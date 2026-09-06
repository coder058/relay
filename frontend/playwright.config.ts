import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './e2e',
  // SOURCE: one deterministic browser journey; no parallel test traffic.
  workers: 1,
  use: { baseURL: 'http://127.0.0.1:5173', browserName: 'chromium' },
  webServer: [
    {
      command: 'python -m uvicorn app.main:app --host 127.0.0.1 --port 8000',
      cwd: '../backend', url: 'http://127.0.0.1:8000/health',
      env: { SQLITE_DB_PATH: 'SYNTHETIC-e2e.db' },
    },
    { command: 'npm run dev -- --host 127.0.0.1 --port 5173', url: 'http://127.0.0.1:5173' },
  ],
});
