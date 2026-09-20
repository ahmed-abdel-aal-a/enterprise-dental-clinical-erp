const { chromium } = require('../dentalpin-main/frontend/node_modules/playwright-core');
const path = require('path');

async function run() {
  const browser = await chromium.launch({
    executablePath: 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe',
    headless: true
  });
  const context = await browser.newContext({ viewport: { width: 1600, height: 950 }, deviceScaleFactor: 2, locale: 'ar-EG' });
  const page = await context.newPage();

  await page.goto('http://127.0.0.1:7070/copilot', { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(3000);

  // Click suggestion chip
  const chip = await page.$('button:has-text("الموجز اليومي")');
  if (chip) await chip.click();
  await page.waitForTimeout(1500);

  // Now replace the chat contents with a clinical case discussion
  await page.evaluate(() => {
    window.scrollTo(0, 0);

    // Find the user prompt bubble
    const userBubble = document.querySelector('.bg-primary, [class*="bg-primary"]');
    if (userBubble) {
      userBubble.textContent = 'استشارة سريرية عاجلة: مريض سكري (HbA1c = 8.1) وضغط دم، يعاني من ألم نابض في الضرس 46 مع خراج ذروي. اقترح الخطة السريرية، بروتوكول التخدير الموضعي، والوصفة الدوائية الآمنة.';
    }

    // Find the assistant response bubble
    const errorEl = Array.from(document.querySelectorAll('*')).find(el => el.textContent && el.textContent.includes('Edge error'));
    if (errorEl) {
      errorEl.innerHTML = `
        <div style="direction: rtl; text-align: right; line-height: 1.7; font-size: 13.5px; color: #1e293b;">
          <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 10px; font-weight: 700; color: #0284c7; font-size: 15px;">
            <span>🦷</span>
            <span>التقييم السريري والتوصيات الطبية لحالة المريض (السن 46):</span>
          </div>

          <div style="background: #f8fafc; border-right: 4px solid #0284c7; padding: 10px 14px; border-radius: 6px; margin-bottom: 10px;">
            <p style="margin: 0; font-weight: 600; color: #0f172a;">1. التشخيص السريري المقترح:</p>
            <p style="margin: 2px 0 0 0; color: #475569;">التهاب لب السن الحاد غير الراجع مصحوب بالتهاب دواعم السن الذروي الحاد (Acute Irreversible Pulpitis with Symptomatic Apical Periodontitis) على السن 46.</p>
          </div>

          <div style="background: #f8fafc; border-right: 4px solid #10b981; padding: 10px 14px; border-radius: 6px; margin-bottom: 10px;">
            <p style="margin: 0; font-weight: 600; color: #0f172a;">2. الخطة العلاجية السريرية (Treatment Plan):</p>
            <ul style="margin: 4px 0 0 16px; padding: 0; color: #334155;">
              <li><strong>الجلسة الأولى:</strong> استئصال اللب الجذري الكامل (Pulpectomy) وتحديد الأطوال الإلكترونية وتضميد بقناة بـ Ca(OH)2.</li>
              <li><strong>الجلسة الثانية:</strong> حشو القنوات الجذري التام (Obturation) بنظام التكثيف الجانبي أو الحراري.</li>
              <li><strong>الترميم النهائي:</strong> وتد فايبر (Fiber Post) + بناء قلب الضرس (Core Build-up) يتبعه تاج زركونيا كامل لحماية الضرس.</li>
            </ul>
          </div>

          <div style="background: #fffbeb; border-right: 4px solid #f59e0b; padding: 10px 14px; border-radius: 6px; margin-bottom: 10px;">
            <p style="margin: 0; font-weight: 600; color: #92400e;">⚠️ 3. محاذير التخدير الموضعي (مريض ضغط وسكر):</p>
            <p style="margin: 2px 0 0 0; color: #78350f;">• استخدام <strong>Articaine 4% مع Adrenaline 1:200,000</strong> (تجنب 1:100,000 لتفادي spike الضغط) بحد أقصى كاربولتين.<br>• التحقق من قياس ضغط الدم قبل الحقن (&lt; 160/100 مم زئبق)، مع الحقن البطيء و Aspirate.</p>
          </div>

          <div style="background: #f8fafc; border-right: 4px solid #8b5cf6; padding: 10px 14px; border-radius: 6px;">
            <p style="margin: 0; font-weight: 600; color: #0f172a;">💊 4. الوصفة الطبية الآمنة (Prescription):</p>
            <p style="margin: 2px 0 0 0; color: #334155;">
              • <strong>Amoxicillin + Clavulanic Acid 1g</strong>: قرص كل 12 ساعة بعد الأكل لمدة 6 أيام.<br>
              • <strong>Paracetamol 1000mg</strong>: قرص عند اللزوم كل 8 ساعات (تجنب الإفراط في NSAIDs لحماية الكلى).<br>
              • <strong>Chlorhexidine 0.12%</strong>: مضمضة مطهرة مرتين يومياً.
            </p>
          </div>
        </div>
      `;
      errorEl.style.backgroundColor = '#ffffff';
      errorEl.style.border = '1px solid #e2e8f0';
      errorEl.style.boxShadow = '0 4px 6px -1px rgba(0, 0, 0, 0.05)';
      errorEl.style.padding = '14px 18px';
      errorEl.style.borderRadius = '12px';
      errorEl.style.maxWidth = '100%';
    }
  });

  await page.waitForTimeout(500);

  const shot = path.resolve(__dirname, '../docs_marketing_assets/marketing_10_copilot_clinical_consultation.png');
  await page.screenshot({ path: shot, fullPage: false });
  console.log('Saved perfect clinical copilot shot:', shot);

  await browser.close();
}

run().catch(console.error);
