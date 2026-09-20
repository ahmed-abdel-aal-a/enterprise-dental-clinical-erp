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

  // 1. Odontogram - Restorative Tab
  console.log('1. Odontogram - opening restorative category...');
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
    await page.waitForTimeout(1500);
  }

  const shotRestorative = path.join(outputDir, 'marketing_01_odontogram_restorative.png');
  await page.screenshot({ path: shotRestorative, fullPage: false });
  console.log('Saved restorative shot:', shotRestorative);

  // 2. Odontogram - Endodontics Tab
  console.log('2. Odontogram - opening endo category...');
  const endoTab = await page.$('button:has-text("علاج العصب والجذور")') || await page.$('text=علاج العصب والجذور');
  if (endoTab) {
    await endoTab.click({ force: true });
    await page.waitForTimeout(1500);
  }

  const shotEndo = path.join(outputDir, 'marketing_02_odontogram_endo.png');
  await page.screenshot({ path: shotEndo, fullPage: false });
  console.log('Saved endo shot:', shotEndo);

  // 3. Payments & Quick Ledger Tab
  console.log('3. Navigating to Payments & Quick Ledger...');
  await page.goto('http://127.0.0.1:7070/patients/cdcab8c4-3c03-4c40-98c4-8e39548f3788?tab=administration', { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(3000);

  // Click "الدفعات والمقبوضات" tab
  const paymentsSubTab = await page.$('button:has-text("الدفعات والمقبوضات")') || await page.$('text=الدفعات والمقبوضات');
  if (paymentsSubTab) {
    await paymentsSubTab.click({ force: true });
    await page.waitForTimeout(2000);
  }

  const shotLedger = path.join(outputDir, 'marketing_03_quick_ledger_payments.png');
  await page.screenshot({ path: shotLedger, fullPage: false });
  console.log('Saved ledger shot:', shotLedger);

  // Try to click "تحصيل سريع" or "سداد دفعة" if present to show the modal!
  const collectBtn = await page.$('button:has-text("تحصيل")') || await page.$('button:has-text("قبض")') || await page.$('button:has-text("تسجيل دفعة")');
  if (collectBtn) {
    await collectBtn.click({ force: true });
    await page.waitForTimeout(1500);
    const shotCollectModal = path.join(outputDir, 'marketing_04_quick_collect_modal.png');
    await page.screenshot({ path: shotCollectModal, fullPage: false });
    console.log('Saved collect modal shot:', shotCollectModal);
  }

  await browser.close();
  console.log('All detailed clinical and financial shots captured!');
}

run().catch(console.error);
