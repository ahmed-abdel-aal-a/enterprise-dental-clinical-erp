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

  // Click on tooth 46
  const t46 = await page.$('text=46');
  if (t46) await t46.click({ force: true });
  await page.waitForTimeout(1500);

  // In modal, click M and O surfaces
  const mBtn = await page.$('button:has-text("إنسي")') || await page.$('text=إنسي');
  if (mBtn) await mBtn.click({ force: true });
  await page.waitForTimeout(500);

  const oBtn = await page.$('button:has-text("إطباقي")') || await page.$('text=إطباقي');
  if (oBtn) await oBtn.click({ force: true });
  await page.waitForTimeout(1000);

  // Screenshot modal with surfaces selected
  const shotSurfacesSelected = path.resolve(__dirname, '../docs_marketing_assets/marketing_07_surfaces_selected_mo.png');
  await page.screenshot({ path: shotSurfacesSelected });
  console.log('Saved surfaces selected shot:', shotSurfacesSelected);

  // Click confirm button
  const confirmBtn = await page.$('button:has-text("تأكيد")');
  if (confirmBtn) await confirmBtn.click({ force: true });
  await page.waitForTimeout(2000);

  // Screenshot showing tooth 46 updated with MO composite and treatment listed below!
  const shotConfirmed = path.resolve(__dirname, '../docs_marketing_assets/marketing_08_odontogram_treatment_recorded.png');
  await page.screenshot({ path: shotConfirmed });
  console.log('Saved recorded treatment shot:', shotConfirmed);

  await browser.close();
}
run().catch(console.error);
