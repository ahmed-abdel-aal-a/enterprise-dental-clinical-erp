const { chromium } = require('../dentalpin-main/frontend/node_modules/playwright-core');
const path = require('path');

async function run() {
  const browser = await chromium.launch({
    executablePath: 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe',
    headless: true
  });
  const context = await browser.newContext({ viewport: { width: 1600, height: 1000 }, deviceScaleFactor: 2, locale: 'ar-EG' });
  const page = await context.newPage();

  await page.goto('http://127.0.0.1:7070/patients/cdcab8c4-3c03-4c40-98c4-8e39548f3788?tab=clinical', { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(3000);

  // Click restorative
  const restTab = await page.$('text=ترميمي ومحافظ');
  if (restTab) await restTab.click({ force: true });
  await page.waitForTimeout(1000);

  // Click composite
  const comp = await page.$('text=حشوة ضوئية كومبوزيت');
  if (comp) await comp.click({ force: true });
  await page.waitForTimeout(1000);

  // Click on tooth 46 SVG or text
  const t46 = await page.$('text=46');
  if (t46) {
    console.log('Clicking 46 after selecting composite...');
    await t46.click({ force: true });
    await page.waitForTimeout(2000);
  }

  const shot = path.resolve(__dirname, '../docs_marketing_assets/marketing_06_tooth_surface_popup.png');
  await page.screenshot({ path: shot });
  console.log('Saved:', shot);

  await browser.close();
}
run().catch(console.error);
