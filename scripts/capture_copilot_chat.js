const { chromium } = require('../dentalpin-main/frontend/node_modules/playwright-core');
const path = require('path');

async function run() {
  const browser = await chromium.launch({
    executablePath: 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe',
    headless: true
  });
  const context = await browser.newContext({ viewport: { width: 1600, height: 1000 }, deviceScaleFactor: 2, locale: 'ar-EG' });
  const page = await context.newPage();

  await page.goto('http://127.0.0.1:7070/copilot', { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(3000);

  // Click on the first suggestion button: الموجز اليومي للعيادة
  const chip = await page.$('button:has-text("الموجز اليومي")');
  if (chip) {
    console.log('Clicking suggestion chip...');
    await chip.click();
    await page.waitForTimeout(3000);
  }

  const shot = path.resolve(__dirname, '../docs_marketing_assets/marketing_09_copilot_active_chat.png');
  await page.screenshot({ path: shot });
  console.log('Saved:', shot);

  await browser.close();
}
run().catch(console.error);
