const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
  const p = await b.newPage({ viewport:{width:940,height:700}, deviceScaleFactor:2 });
  await p.goto('file://' + __dirname + '/budget-card.html');
  await p.waitForTimeout(2500);
  const box = await (await p.$('.card')).boundingBox();
  await p.screenshot({ path:'budget.png', clip:{x:box.x-28,y:box.y-28,width:box.width+56,height:box.height+56} });
  await b.close();
})();
