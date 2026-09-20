const { chromium } = require('../dentalpin-main/frontend/node_modules/playwright-core');
const path = require('path');
const fs = require('fs');

async function run() {
  const outputDir = path.resolve(__dirname, '../docs_marketing_assets');

  const browser = await chromium.launch({
    executablePath: 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe',
    headless: true
  });

  const context = await browser.newContext({
    viewport: { width: 1600, height: 1000 },
    deviceScaleFactor: 2,
    locale: 'ar-EG'
  });

  const page = await context.newPage();

  console.log('Navigating to Patient Clinical tab...');
  await page.goto('http://127.0.0.1:7070/patients/cdcab8c4-3c03-4c40-98c4-8e39548f3788?tab=clinical', { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(3000);

  // Activate diagnosis/treatment mode
  const newCasesBtn = await page.$('text=تسجيل حالات جديدة') || await page.$('text=وضع التشخيص');
  if (newCasesBtn) await newCasesBtn.click({ force: true });
  await page.waitForTimeout(1000);

  // Click tooth 46
  const tooth46 = await page.$('text=46') || await page.$('text="46"');
  if (tooth46) await tooth46.click({ force: true });
  await page.waitForTimeout(1000);

  // Click "ترميمي ومحافظ" tab
  const restorativeTab = await page.$('button:has-text("ترميمي ومحافظ")') || await page.$('text=ترميمي ومحافظ');
  if (restorativeTab) {
    await restorativeTab.click({ force: true });
    await page.waitForTimeout(1000);
  }

  // Click "حشوة ضوئية كومبوزيت"
  console.log('Clicking composite button...');
  const compositeBtn = await page.$('button:has-text("كومبوزيت")') || await page.$('text=حشوة ضوئية كومبوزيت') || await page.$('[aria-label*="كومبوزيت"]');
  if (compositeBtn) {
    await compositeBtn.click({ force: true });
    await page.waitForTimeout(2000);
  }

  const shotSurface = path.join(outputDir, 'marketing_05_surface_selector_modal.png');
  await page.screenshot({ path: shotSurface, fullPage: false });
  console.log('Saved surface selector shot:', shotSurface);

  await browser.close();
}

run().catch(console.error);
