const fs = require('node:fs');
const http = require('node:http');
const path = require('node:path');
const {chromium} = require('/Users/dan/.nvm/versions/node/v22.15.0/lib/node_modules/@playwright/cli/node_modules/playwright');
const ROOT = '/Users/dan/Work/software-factory/docs/research/dashboard-review';
const KEY = 'support-tickets.v1';
async function main() {
 const browser = await chromium.launch({headless:true});
 const results = [];
 for (const candidate of ['candidate-a','candidate-b']) {
  const server = http.createServer((req,res) => {
   const file=path.join(ROOT,candidate,req.url==='/'?'index.html':req.url);
   fs.readFile(file,(err,data)=>{ if(err)return res.writeHead(404).end();res.setHeader('Content-Type',{'.html':'text/html','.js':'text/javascript','.css':'text/css'}[path.extname(file)]||'text/plain');res.end(data); });
  });
  await new Promise(r=>server.listen(0,'127.0.0.1',r));
  const url=`http://127.0.0.1:${server.address().port}`;
  async function fresh(fn,viewport={width:1280,height:800}){
   const context=await browser.newContext({viewport});
   const page=await context.newPage();const errors=[];page.on('pageerror',e=>errors.push(String(e)));
   await page.goto(url);
   try { results.push({candidate,...await fn(page,context),pageErrors:errors}); } finally { await context.close(); }
  }
  const row=(p,id)=>p.locator('button.ticket').filter({hasText:id});
  const dialog=p=>p.locator('dialog[open]');
  async function create(p,title){await p.getByRole('button',{name:'New ticket',exact:true}).click();for(const [label,value]of [['Title',title],['Customer','Review customer'],['Description','Review description']])await dialog(p).getByLabel(label,{exact:true}).fill(value);await dialog(p).getByRole('button',{name:'Create ticket'}).click();}
  async function edit(p,id,status,priority){await row(p,id).click();if(status)await dialog(p).getByLabel('Status',{exact:true}).selectOption(status);if(priority)await dialog(p).getByLabel('Priority',{exact:true}).selectOption(priority);await dialog(p).getByRole('button',{name:'Save changes'}).click();}
  await fresh(async(p,context)=>{
   const p2=await context.newPage();await p2.goto(url);
   await create(p,'First tab saved');
   const before=await p.evaluate(k=>JSON.parse(localStorage.getItem(k)),KEY);
   await edit(p2,'T002',null,'low');
   const after=await p2.evaluate(k=>JSON.parse(localStorage.getItem(k)),KEY);
   return {probe:'two-tab create then unrelated edit',beforeCount:before.length,afterCount:after.length,retainedNewTicket:after.some(t=>t.title==='First tab saved')};
  });
  await fresh(async(p,context)=>{
   const p2=await context.newPage();await p2.goto(url);
   await create(p,'First tab saved');await create(p2,'Second tab saved');
   const after=await p2.evaluate(k=>JSON.parse(localStorage.getItem(k)),KEY);
   return {probe:'two-tab sequential create',savedTitles:after.slice(12).map(t=>t.title),ids:after.slice(12).map(t=>t.id)};
  });
  await fresh(async(p,context)=>{
   const p2=await context.newPage();await p2.goto(url);
   await row(p,'T002').click();
   await edit(p2,'T002',null,'low');
   const before=await p2.evaluate(k=>JSON.parse(localStorage.getItem(k)).find(t=>t.id==='T002'),KEY);
   await dialog(p).getByLabel('Status',{exact:true}).selectOption('resolved');
   await dialog(p).getByRole('button',{name:'Save changes'}).click();
   const after=await p.evaluate(k=>JSON.parse(localStorage.getItem(k)).find(t=>t.id==='T002'),KEY);
   return {probe:'same-ticket other-tab priority edit while dialog open',before,after};
  });
  await fresh(async(p)=>{
   await p.evaluate(()=>{Storage.prototype.setItem=function(){throw new DOMException('Quota exceeded','QuotaExceededError');};});
   await create(p,'Failed write');
   const before={visible:await row(p,'T013').count(),open:await dialog(p).count(),stored:await p.evaluate(k=>localStorage.getItem(k),KEY)};
   await p.reload();return {probe:'setItem throws on create',before,afterCount:await p.locator('button.ticket').count(),visibleErrors:await p.locator('[role="alert"],.error:not([hidden])').allTextContents()};
  });
  await fresh(async(p)=>{
   await p.evaluate(()=>{Storage.prototype.setItem=function(){throw new DOMException('Quota exceeded','QuotaExceededError');};});
   await edit(p,'T002','resolved','low');const before=await row(p,'T002').locator('..').innerText();
   await p.reload();return {probe:'setItem throws on edit',before,after:await row(p,'T002').locator('..').innerText()};
  });
  await fresh(async(p)=>{
   await create(p,'Retain me');
   await p.evaluate(k=>{const data=JSON.parse(localStorage.getItem(k));data[0].priority='urgent';localStorage.setItem(k,JSON.stringify(data));},KEY);
   await p.reload();const fallbackCount=await p.locator('button.ticket').count();
   const before=await p.evaluate(k=>JSON.parse(localStorage.getItem(k)),KEY);
   await edit(p,'T002',null,'low');const after=await p.evaluate(k=>JSON.parse(localStorage.getItem(k)),KEY);
   return {probe:'one malformed persisted record then unrelated save',fallbackCount,beforeCount:before.length,afterCount:after.length,retainedNewTicket:after.some(t=>t.title==='Retain me')};
  });
  await fresh(async(p)=>{
   await p.getByRole('button',{name:'New ticket',exact:true}).click();for(const [label,value]of [['Title','Double click'],['Customer','Customer'],['Description','Description']])await dialog(p).getByLabel(label,{exact:true}).fill(value);
   await dialog(p).getByRole('button',{name:'Create ticket'}).dblclick();
   return {probe:'double click Create at desktop',openDialogs:await dialog(p).allTextContents(),savedCount:await p.evaluate(k=>JSON.parse(localStorage.getItem(k)).length,KEY)};
  });
  await fresh(async(p)=>{
   await p.getByRole('button',{name:'New ticket',exact:true}).click();
   await dialog(p).getByRole('button',{name:'Create ticket'}).click();
   const ids=await dialog(p).locator('input,select,textarea,button').evaluateAll(els=>els.map(e=>e.id));
   const focus=[];for(let i=0;i<14;i++){await p.keyboard.press('Tab');focus.push(await p.evaluate(()=>document.activeElement.id||document.activeElement.textContent.trim()));}
   return {probe:'mobile invalid create dialog tab walk',ids,focus,overflow:await p.evaluate(()=>document.documentElement.scrollWidth-innerWidth)};
  },{width:360,height:740});
  await fresh(async(p)=>{
   const widths=[];for(const width of [601,620,640,768,1280]){await p.setViewportSize({width,height:800});widths.push(await p.evaluate(()=>{const spans=[...document.querySelectorAll('#tickets li:first-child span')].map(e=>({class:e.className,width:e.getBoundingClientRect().width,height:e.getBoundingClientRect().height,right:e.getBoundingClientRect().right}));return {width:innerWidth,overflow:document.documentElement.scrollWidth-innerWidth,spans};}));}return{probe:'intermediate widths',widths};
  });
  await new Promise(r=>server.close(r));
 }
 await browser.close();fs.writeFileSync('/private/tmp/dashboard-code-review.OeK3ks/results.json',JSON.stringify(results,null,2));console.log(JSON.stringify(results,null,2));
}
main().catch(e=>{console.error(e);process.exitCode=1;});
