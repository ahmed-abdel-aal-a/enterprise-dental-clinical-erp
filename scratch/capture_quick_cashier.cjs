const { chromium } = require('@playwright/test');
const path = require('path');
const fs = require('fs');

async function main() {
  const screenshotDir = path.resolve(__dirname, '../dentalpin-main/docs/screenshots');

  const browser = await chromium.launch({
    headless: true,
    channel: 'msedge'
  });

  const context = await browser.newContext({
    viewport: { width: 1366, height: 850 },
    locale: 'ar-EG'
  });

  const page = await context.newPage();

  console.log('Logging in via API...');
  const loginRes = await page.request.post('http://127.0.0.1:7070/api/v1/auth/login', {
    form: {
      username: 'admin@dental.com',
      password: 'DentApex2026!'
    }
  });

  const loginData = await loginRes.json();
  const token = loginData.access_token;

  await context.addCookies([
    {
      name: 'access_token',
      value: token,
      domain: '127.0.0.1',
      path: '/'
    }
  ]);

  await page.addInitScript((tok) => {
    window.localStorage.setItem('dentapex_access_token', tok);
  }, token);

  const patientsRes = await page.request.get('http://127.0.0.1:7070/api/v1/patients?page=1&page_size=1', {
    headers: { Authorization: `Bearer ${token}` }
  });
  const patientsData = await patientsRes.json();
  const patientId = patientsData.data[0].id;

  // 1. Navigate to patient payments
  await page.goto(`http://127.0.0.1:7070/dentapex/patients/${patientId}?tab=administration&adminMode=payments`);
  await page.waitForTimeout(3000);

  // 2. Open Quick Collect Modal
  console.log('Opening Quick Collect modal: تحصيل نقدية (سداد)...');
  const collectBtn = page.locator('button:has-text("تحصيل نقدية (سداد)")').first();
  if (await collectBtn.isVisible()) {
    await collectBtn.click();
    await page.waitForTimeout(1500);
    const collectPath = path.join(screenshotDir, 'quick_collect_modal.png');
    await page.screenshot({ path: collectPath });
    console.log('Saved:', collectPath);

    // Close modal via Escape
    await page.keyboard.press('Escape');
    await page.waitForTimeout(1000);
  }

  // 3. Open Quick Charge Modal
  console.log('Opening Quick Charge modal: إضافة كشف / خدمة...');
  const chargeBtn = page.locator('button:has-text("إضافة كشف / خدمة")').first();
  if (await chargeBtn.isVisible()) {
    await chargeBtn.click();
    await page.waitForTimeout(1500);
    const chargePath = path.join(screenshotDir, 'quick_charge_modal.png');
    await page.screenshot({ path: chargePath });
    console.log('Saved:', chargePath);

    // Close modal via Escape
    await page.keyboard.press('Escape');
    await page.waitForTimeout(1000);
  }

  // 4. Open Quick Price List Modal
  console.log('Opening Quick Price List modal: تسعيرة العيادة...');
  const priceListBtn = page.locator('button:has-text("تسعيرة العيادة")').first();
  if (await priceListBtn.isVisible()) {
    await priceListBtn.click();
    await page.waitForTimeout(1500);
    const priceListPath = path.join(screenshotDir, 'quick_price_list_modal.png');
    await page.screenshot({ path: priceListPath });
    console.log('Saved:', priceListPath);

    // Close modal via Escape
    await page.keyboard.press('Escape');
    await page.waitForTimeout(1000);
  }

  await browser.close();
  console.log('All modals captured successfully!');
}

main().catch(err => {
  console.error('Error:', err);
  process.exit(1);
});
