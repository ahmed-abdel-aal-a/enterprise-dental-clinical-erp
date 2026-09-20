import http from 'http';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { spawn } from 'child_process';
import { chromium } from '../dentalpin-main/frontend/node_modules/playwright/index.mjs';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const publicDir = path.resolve(__dirname, '../dentalpin-main/frontend/.output/public');

// 1. Start PHP built-in server on 127.0.0.1:8888 for chat.php
console.log('Starting PHP server on port 8888 for chat.php ...');
const phpServer = spawn('php', ['-S', '127.0.0.1:8888', '-t', publicDir], {
  cwd: path.resolve(__dirname, '..'),
  stdio: 'ignore'
});

await new Promise(r => setTimeout(r, 1500));

// 2. MIME Types map
const mimeTypes = {
  '.html': 'text/html; charset=utf-8',
  '.js': 'application/javascript; charset=utf-8',
  '.mjs': 'application/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.svg': 'image/svg+xml',
  '.woff2': 'font/woff2',
  '.ttf': 'font/ttf',
  '.webmanifest': 'application/manifest+json'
};

// 3. Node Static HTTP Proxy Server on 4173 serving /dentapex/
const server = http.createServer((req, res) => {
  let reqUrl = req.url.split('?')[0];

  // Proxy /dentapex/api/copilot/chat.php to PHP server
  if (reqUrl.includes('/api/copilot/chat.php') || reqUrl.includes('/api/copilot/chat')) {
    const proxyReq = http.request({
      hostname: '127.0.0.1',
      port: 8888,
      path: '/api/copilot/chat.php',
      method: req.method,
      headers: req.headers
    }, (proxyRes) => {
      res.writeHead(proxyRes.statusCode, proxyRes.headers);
      proxyRes.pipe(res);
    });
    proxyReq.on('error', (err) => {
      res.writeHead(500, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ error: err.message }));
    });
    req.pipe(proxyReq);
    return;
  }

  // Strip /dentapex prefix for static file resolution
  let filePath = reqUrl;
  if (filePath.startsWith('/dentapex')) {
    filePath = filePath.slice('/dentapex'.length);
  }
  if (filePath === '' || filePath === '/') {
    filePath = '/index.html';
  }

  let fullPath = path.join(publicDir, filePath);
  if (!fs.existsSync(fullPath) || fs.statSync(fullPath).isDirectory()) {
    const htmlPath = fullPath.replace(/\/$/, '') + '/index.html';
    if (fs.existsSync(htmlPath)) {
      fullPath = htmlPath;
    } else {
      fullPath = path.join(publicDir, 'index.html');
    }
  }

  const ext = path.extname(fullPath).toLowerCase();
  const contentType = mimeTypes[ext] || 'application/octet-stream';

  try {
    const data = fs.readFileSync(fullPath);
    res.writeHead(200, { 'Content-Type': contentType });
    res.end(data);
  } catch (err) {
    res.writeHead(404);
    res.end('Not Found');
  }
});

await new Promise((resolve) => server.listen(4173, '127.0.0.1', resolve));
console.log('Static server listening on http://127.0.0.1:4173/dentapex/');

// 4. Launch Playwright Chrome / Edge
console.log('Launching Playwright Chrome / Edge...');
const browser = await chromium.launch({
  headless: true,
  channel: 'msedge'
});
const context = await browser.newContext({
  viewport: { width: 1366, height: 850 },
  locale: 'ar-EG'
});

const page = await context.newPage();

const consoleErrors = [];
page.on('console', msg => {
  if (msg.type() === 'error') {
    consoleErrors.push(msg.text());
  }
});

try {
  console.log('Navigating to http://127.0.0.1:4173/dentapex/copilot ...');
  await page.goto('http://127.0.0.1:4173/dentapex/copilot', { waitUntil: 'networkidle' });
  await page.waitForTimeout(2000);

  // Check title
  const title = await page.title();
  console.log('Page Title:', title);

  // Find chat input
  console.log('Finding Copilot chat input...');
  const chatInput = page.locator('textarea, input[placeholder*="مساعد"]').first();
  await chatInput.waitFor({ state: 'visible', timeout: 10000 });

  const testPrompt = 'أعطني نظرة عامة على جدول مواعيد اليوم';
  console.log('Typing prompt:', testPrompt);
  await chatInput.fill(testPrompt);
  await page.waitForTimeout(500);

  // Click Send or press Enter
  console.log('Sending message to Copilot AI...');
  await page.keyboard.press('Enter');

  // Wait for response to stream
  console.log('Waiting for AI streaming response from allam-2-7b...');
  await page.waitForTimeout(6000);

  // Extract all text messages
  const messageTexts = await page.locator('.prose, [class*="message"], p').allInnerTexts();
  const joinedText = messageTexts.join('\n');
  console.log('\n--- EXTRACTED PAGE TEXT ---');
  console.log(joinedText.slice(0, 800));

  // Verify that the error message is NOT present
  const hasError = joinedText.includes('تعذر الاتصال بخدمة الذكاء الاصطناعي');
  console.log('\nDid the error message appear?', hasError ? 'YES (FAILED)' : 'NO (PASSED)');

  // Take screenshot
  const screenshotPath = 'C:/Users/Spider Store/.gemini/antigravity/brain/6e4f4880-bbfe-4109-81ae-a9a5d7dd0fca/ai_copilot_allam_verified.png';
  await page.screenshot({ path: screenshotPath, fullPage: true });
  console.log('Screenshot saved to:', screenshotPath);

  console.log('\nTotal Console Errors:', consoleErrors.length);
  if (consoleErrors.length > 0) {
    console.log('Errors:', consoleErrors);
  }

} finally {
  await browser.close();
  server.close();
  phpServer.kill();
  console.log('All servers stopped.');
}
