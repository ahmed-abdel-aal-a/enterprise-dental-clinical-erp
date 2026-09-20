const { chromium } = require('../dentalpin-main/frontend/node_modules/playwright-core');
const path = require('path');
const fs = require('fs');

async function run() {
  const outputDir = path.resolve(__dirname, '../docs_marketing_assets');
  if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
  }

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

  console.log('1. Navigating to Patient Clinical tab (?tab=clinical)...');
  await page.goto('http://127.0.0.1:7070/patients/cdcab8c4-3c03-4c40-98c4-8e39548f3788?tab=clinical', { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(4000);

  const odontogramFull = path.join(outputDir, '01_dentapex_clinical_odontogram_full.png');
  await page.screenshot({ path: odontogramFull, fullPage: false });
  console.log('Saved:', odontogramFull);

  // Click on "تسجيل حالات جديدة" or "وضع التشخيص" to activate interactive editing
  console.log('2. Activating treatment/diagnosis mode...');
  const newCasesBtn = await page.$('text=تسجيل حالات جديدة') || await page.$('text=وضع التشخيص') || await page.$('button:has-text("تسجيل")');
  if (newCasesBtn) {
    await newCasesBtn.click({ force: true });
    await page.waitForTimeout(2000);
  }

  // Click on tooth 46 / 16
  console.log('3. Clicking tooth on odontogram...');
  const tooth46 = await page.$('text=46') || await page.$('text="46"');
  if (tooth46) {
    await tooth46.click({ force: true });
    await page.waitForTimeout(2000);
  }

  const toothInteractive = path.join(outputDir, '02_dentapex_tooth_molar_active.png');
  await page.screenshot({ path: toothInteractive, fullPage: false });
  console.log('Saved:', toothInteractive);

  // 3. Navigating to Administration tab (?tab=administration) for Quick Cashier / Ledger
  console.log('4. Navigating to Administration / Ledger tab (?tab=administration)...');
  await page.goto('http://127.0.0.1:7070/patients/cdcab8c4-3c03-4c40-98c4-8e39548f3788?tab=administration', { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(3000);

  const cashierShot = path.join(outputDir, '05_dentapex_quick_cashier_ledger.png');
  await page.screenshot({ path: cashierShot, fullPage: false });
  console.log('Saved Cashier:', cashierShot);

  await browser.close();
  console.log('All marketing assets updated successfully!');
}

run().catch(console.error);
