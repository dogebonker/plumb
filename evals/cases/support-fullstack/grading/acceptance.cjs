const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');

const {chromium}=require(process.env.PLAYWRIGHT_MODULE);
const base=process.env.BENCHMARK_BASE,checks=[];
let browser;

async function check(name,ids,fn){try{await fn();
checks.push({name,ids,passed:true})}catch(e){checks.push({name,ids,passed:false,error:e.message});
console.error(name+': '+e.stack)}}
function client(initialCookie=''){let cookie=initialCookie;
return async(route,method='GET',body)=>{const response=await fetch(base+route,{method,headers:{'Content-Type':'application/json',Cookie:cookie},body:body===undefined?undefined:JSON.stringify(body),signal:AbortSignal.timeout(5000)});
if(response.headers.get('set-cookie'))cookie=response.headers.get('set-cookie').split(';')[0];
let data;
try{data=await response.json()}catch{data={}}return {code:response.status,data,cookie:response.headers.get('set-cookie')}}}
async function login(email='operator@acme.test'){const call=client();
assert.equal((await call('/api/login','POST',{email,password:'benchmark-pass'})).code,200);
return call}
async function get(call,id='T001'){const r=await call('/api/tickets/'+id);
assert.equal(r.code,200);
return r.data.ticket}
const payload={title:'  Delivery update  ',description:'  Please update our delivery.  '};

async function browserLogin(page,email='operator@acme.test'){await page.goto(base,{timeout:10000});
const ready=page.getByRole('button',{name:'New ticket',exact:true}),emailField=page.getByLabel('Email',{exact:true});
const state=await Promise.any([ready.waitFor({timeout:10000}).then(()=>'ready'),emailField.waitFor({timeout:10000}).then(()=>'login')]);
if(state==='ready')return;
try{await emailField.fill(email)}catch(error){await ready.waitFor({timeout:10000});return}
await page.getByLabel('Password',{exact:true}).fill('benchmark-pass');
await page.getByRole('button',{name:'Log in',exact:true}).click();
await page.getByRole('button',{name:'New ticket',exact:true}).waitFor({timeout:10000})}
const ticketControl=(p,name)=>p.getByRole('button',{name}).or(p.getByRole('link',{name}));
const form=(p,name='New ticket')=>p.getByRole('dialog',{name,exact:true});

async function choose(page,control,value){
if(await control.evaluate(node=>node.tagName)==='SELECT')return control.selectOption(value);
assert.equal(await control.getAttribute('role'),'combobox','Use a labeled select or accessible combobox');
await control.click();
await page.getByRole('option',{name:new RegExp('\\b'+value+'\\b','i')}).click();
}
async function persisted(predicate){
const c=await login(),deadline=Date.now()+5000;
while(Date.now()<deadline){const response=await c('/api/tickets');
assert.equal(response.code,200);
const ticket=response.data.tickets.find(predicate);
if(ticket)return ticket;
await new Promise(resolve=>setTimeout(resolve,50));
}throw Error('UI action did not persist the expected ticket within 5 seconds');
}
async function dismiss(page,dialog){
if(await dialog.isVisible())await page.keyboard.press('Escape');
await dialog.waitFor({state:'hidden'});
}
async function newDraft(page,title='UI delivery'){await page.getByRole('button',{name:'New ticket',exact:true}).click();
const f=form(page);
await f.getByLabel('Title',{exact:true}).fill(title);
await f.getByLabel('Description',{exact:true}).fill('UI description');
return f}
(async()=>{

await check('login_logout',['FR-01','NFR-01'],async()=>{
const c=client();
assert.equal((await c('/api/login','POST',{email:'operator@acme.test',password:'wrong'})).code,401);
const r=await c('/api/login','POST',{email:'operator@acme.test',password:'benchmark-pass'});
assert.equal(r.code,200);
assert.match(r.cookie,/HttpOnly/i);
assert.match(r.cookie,/SameSite=(Lax|Strict)/i);
assert.equal((await c('/api/me')).data.user.role,'operator');
const retiredSession=r.cookie.split(';')[0];
assert.equal((await c('/api/logout','POST',{})).code,200);
assert.equal((await client(retiredSession)('/api/me')).code,401,'Logged-out session must not remain valid');
assert.equal((await c('/api/me')).code,401)});

await check('seed_and_combined_filters',['FR-02'],async()=>{
const c=await login();
const all=(await c('/api/tickets')).data.tickets;
assert.equal(all.length,2);
assert.deepEqual(all.map(t=>t.id).sort(),['T001','T002']);
assert.equal((await c('/api/tickets?q=PASSWORD&status=open&priority=high')).data.tickets.length,1);
assert.equal((await c('/api/tickets?q=PASSWORD&status=pending')).data.tickets.length,0)});

await check('create_and_validation',['FR-03','NFR-03'],async()=>{
const c=await login();
for(const body of [{title:' ',description:'ok'},{title:'ok',description:' '},{title:'x'.repeat(121),description:'ok'}])assert.equal((await c('/api/tickets','POST',body)).code,400);
const r=await c('/api/tickets','POST',payload);
assert.equal(r.code,201);
assert.equal(r.data.ticket.title,'Delivery update');
assert.equal(r.data.ticket.description,'Please update our delivery.');
assert.equal(r.data.ticket.customer,'operator@acme.test');
assert.equal(r.data.ticket.status,'open')});

await check('operator_edit_assignment',['FR-03','NFR-03'],async()=>{
const c=await login(),t=await get(c);
const body={version:t.version,status:'resolved',priority:'low',assignee:'operator@acme.test',title:'Password reset expired',description:t.description};
const r=await c('/api/tickets/T001','PATCH',body);
assert.equal(r.code,200);
assert.equal(r.data.ticket.assignee,'operator@acme.test');
assert.equal(r.data.ticket.status,'resolved');
assert.equal((await c('/api/tickets/T001','PATCH',{version:r.data.ticket.version,status:'invalid'})).code,400);
assert.equal((await get(c)).version,r.data.ticket.version)});

await check('comment_and_history',['FR-04'],async()=>{
const c=await login(),t=await get(c);
const r=await c('/api/tickets/T001/comments','POST',{version:t.version,text:'  Investigating now  '});
assert.equal(r.code,201);
assert.equal(r.data.ticket.comments.at(-1).text,'Investigating now');
for(const type of ['create','edit','comment'])assert.ok(r.data.ticket.history.some(h=>h.type===type));
assert.equal(r.data.ticket.history[0].type,'create');
assert.equal(r.data.ticket.history.at(-1).type,'comment');
assert.equal(r.data.ticket.history.at(-1).actor,'operator@acme.test')});

await check('anonymous_denied',['NFR-01'],async()=>{
const c=client();
for(const [route,method,body]of [['/api/tickets','GET'],['/api/tickets/T001','GET'],['/api/tickets','POST',payload],['/api/tickets/T001','PATCH',{version:1,status:'resolved'}],['/api/tickets/T001/comments','POST',{version:1,text:'x'}]])assert.equal((await c(route,method,body)).code,401)});

await check('tenant_boundaries',['NFR-01'],async()=>{
const c=await login('operator@north.test');
assert.deepEqual((await c('/api/tickets')).data.tickets.map(t=>t.id).sort(),['T101','T102']);
for(const [method,suffix,body]of [['GET',''],['PATCH','',{version:1,status:'resolved'}],['POST','/comments',{version:1,text:'secret'}]]){const r=await c('/api/tickets/T001'+suffix,method,body);
assert.equal(r.code,404);
assert.ok(!JSON.stringify(r.data).includes('Password reset'))}});

await check('customer_privileges_and_ownership',['NFR-01'],async()=>{
const c=await login('customer@acme.test');
assert.deepEqual((await c('/api/tickets')).data.tickets.map(t=>t.id).sort(),['T001','T002']);
const t=await get(c);
assert.equal((await c('/api/tickets/T001','PATCH',{version:t.version,status:'open'})).code,403);
const operator=await login(),privateTicket=(await operator('/api/tickets?q=Delivery%20update')).data.tickets[0];
assert.equal((await c('/api/tickets/'+privateTicket.id)).code,404);
assert.equal((await c('/api/tickets/'+privateTicket.id+'/comments','POST',{version:privateTicket.version,text:'forbidden'})).code,404);
const r=await c('/api/tickets','POST',{title:'Customer created',description:'own ticket'});
assert.equal(r.code,201);
assert.equal(r.data.ticket.customer,'customer@acme.test');
assert.equal((await c('/api/tickets/'+r.data.ticket.id+'/comments','POST',{version:1,text:'hello'})).code,201)});

await check('mass_assignment_rejected',['NFR-01','NFR-03'],async()=>{
const c=await login(),t=await get(c);
for(const key of ['tenant','customer','actor']){assert.equal((await c('/api/tickets','POST',{...payload,[key]:'north'})).code,400);
assert.equal((await c('/api/tickets/T001','PATCH',{version:t.version,[key]:'north'})).code,400)}assert.equal((await get(c)).version,t.version)});

await check('stale_edits_and_comments',['NFR-04'],async()=>{
const a=await login(),b=await login(),t=await get(a,'T002');
assert.equal((await a('/api/tickets/T002','PATCH',{version:t.version,priority:'high'})).code,200);
assert.equal((await b('/api/tickets/T002','PATCH',{version:t.version,status:'resolved'})).code,409);
assert.equal((await b('/api/tickets/T002/comments','POST',{version:t.version,text:'stale'})).code,409);
const saved=await get(a,'T002');
assert.equal(saved.priority,'high');
assert.equal(saved.status,'pending')});

await check('sequential_clients_retain_records',['NFR-04'],async()=>{
const a=await login(),b=await login();
const x=(await a('/api/tickets','POST',{title:'Client A',description:'one'})).data.ticket,y=(await b('/api/tickets','POST',{title:'Client B',description:'two'})).data.ticket;
assert.notEqual(x.id,y.id);
assert.equal((await a('/api/tickets/'+x.id,'PATCH',{version:x.version,priority:'high'})).code,200);
assert.equal((await b('/api/tickets/'+y.id,'PATCH',{version:y.version,status:'pending'})).code,200);
assert.equal((await get(b,x.id)).priority,'high');
assert.equal((await get(a,y.id)).status,'pending')});

await check('local_response_budget',['NFR-06'],async()=>{
const c=await login(),begin=Date.now();
for(let i=0;
i<30;
i++){const start=Date.now();
assert.equal((await c('/api/tickets')).code,200);
assert.ok(Date.now()-start<2000)}assert.ok(Date.now()-begin<15000)});

try{browser=await chromium.launch({headless:true,args:['--no-sandbox']});
const context=await browser.newContext();
context.setDefaultTimeout(2500);
const external=[];
await context.route('**/*',route=>{const u=new URL(route.request().url());
if(u.origin!==base){external.push(u.href);
return route.abort()}return route.continue()});

await check('ui_create_edit_comment',['FR-03','FR-04'],async()=>{
const p=await context.newPage();
await browserLogin(p);
await p.getByLabel('Search tickets',{exact:true}).fill('Delivery update');
await choose(p,p.getByLabel('Status filter',{exact:true}),'open');
await choose(p,p.getByLabel('Priority filter',{exact:true}),'medium');
await p.getByRole('status').filter({hasText:/(^|\D)1(\D|$)/}).waitFor();
await choose(p,p.getByLabel('Priority filter',{exact:true}),'high');
await p.getByRole('status').filter({hasText:/(^|\D)0(\D|$)/}).waitFor();
await p.getByRole('button',{name:'Reset filters',exact:true}).click();
await ticketControl(p,/(?=.*\bT002\b)(?=.*Export stalls)/).waitFor();
const f=await newDraft(p,'UI durable ticket');
await f.getByRole('button',{name:'Create ticket',exact:true}).click();
const created=await persisted(t=>t.title==='UI durable ticket');
await dismiss(p,f);
await browserLogin(p);
const button=ticketControl(p,/UI durable ticket/);
await button.click();
const d=form(p,'Ticket details');
await choose(p,d.getByLabel('Priority',{exact:true}),'high');
await d.getByRole('button',{name:'Save changes',exact:true}).click();
await persisted(t=>t.id===created.id&&t.priority==='high');
await dismiss(p,d);
await browserLogin(p);
await button.click();
await d.getByLabel('Comment',{exact:true}).fill('UI comment saved');
await d.getByRole('button',{name:'Add comment',exact:true}).click();
await persisted(t=>t.id===created.id&&t.comments.some(comment=>comment.text==='UI comment saved'));
await Promise.any([d.getByText(/UI comment saved/).waitFor(),d.waitFor({state:'hidden'})]);
await dismiss(p,d);
await browserLogin(p);
await button.click();
await d.getByText(/UI comment saved/).waitFor();
await p.screenshot({path:path.join(process.env.BROWSER_ARTIFACTS,'desktop-details.png')});
await p.close()});

await check('ui_failed_save_retains_draft_and_retry',['NFR-03'],async()=>{
const p=await context.newPage();
await browserLogin(p);
const f=await newDraft(p,'UI retry exactly once');
await p.route('**/api/tickets',route=>route.request().method()==='POST'?route.fulfill({status:503,contentType:'application/json',body:JSON.stringify({error:'Injected write failure'})}):route.continue());
await f.getByRole('button',{name:'Create ticket',exact:true}).click();
await f.getByRole('alert').filter({hasText:/./}).waitFor();
assert.equal(await f.getByLabel('Title',{exact:true}).inputValue(),'UI retry exactly once');
assert.equal((await (await login())('/api/tickets?q=UI%20retry')).data.tickets.length,0);
await p.unroute('**/api/tickets');
await f.getByRole('button',{name:'Create ticket',exact:true}).click();
await persisted(t=>t.title==='UI retry exactly once');
await dismiss(p,f);
await browserLogin(p);
const c=await login(),saved=(await c('/api/tickets?q=UI%20retry')).data.tickets;
assert.equal(saved.length,1);
await ticketControl(p,/UI retry exactly once/).click();
const d=form(p,'Ticket details');
await d.getByLabel('Description',{exact:true}).fill('Retained edit draft');
await p.route('**/api/tickets/'+saved[0].id,route=>route.request().method()==='PATCH'?route.fulfill({status:503,contentType:'application/json',body:JSON.stringify({error:'Injected edit failure'})}):route.continue());
await d.getByRole('button',{name:'Save changes',exact:true}).click();
await d.getByRole('alert').filter({hasText:/./}).waitFor();
assert.equal(await d.getByLabel('Description',{exact:true}).inputValue(),'Retained edit draft');
assert.equal((await get(c,saved[0].id)).description,saved[0].description);
await p.unroute('**/api/tickets/'+saved[0].id);
await d.getByRole('button',{name:'Save changes',exact:true}).click();
const updated=await persisted(t=>t.id===saved[0].id&&t.description==='Retained edit draft');
await dismiss(p,d);
assert.equal(updated.description,'Retained edit draft');
assert.equal(updated.version,saved[0].version+1);
await p.close()});

await check('ui_stale_conflict_retains_draft',['NFR-04'],async()=>{
const p=await context.newPage();
await browserLogin(p);
await ticketControl(p,/(?=.*\bT002\b)(?=.*Export stalls)/).click();
const d=form(p,'Ticket details');
await d.getByLabel('Title',{exact:true}).fill('My stale title');
const c=await login(),t=await get(c,'T002');
assert.equal((await c('/api/tickets/T002','PATCH',{version:t.version,priority:'low'})).code,200);
await d.getByRole('button',{name:'Save changes',exact:true}).click();
await d.getByRole('alert').filter({hasText:/./}).waitFor();
assert.equal(await d.getByLabel('Title',{exact:true}).inputValue(),'My stale title');
assert.equal((await get(c,'T002')).title,'Export stalls');
await p.close()});

await check('responsive_keyboard_and_local_network',['NFR-05','NFR-06'],async()=>{
const p=await context.newPage();
await browserLogin(p);
for(const width of [360,600,601,1280]){await p.setViewportSize({width,height:900});
await p.getByRole('button',{name:'New ticket',exact:true}).focus();
await p.keyboard.press('Enter');
const d=form(p);
const bounds=await d.boundingBox();
assert.ok(bounds.x>=0&&bounds.x+bounds.width<=width+1);
for(let i=0;
i<12;
i++){await p.keyboard.press('Tab');
assert.equal(await d.evaluate(n=>n.contains(document.activeElement)),true)}await p.keyboard.press('Escape');
assert.equal(await p.getByRole('button',{name:'New ticket',exact:true}).evaluate(n=>n===document.activeElement),true);
assert.equal(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),true);
for(const button of await ticketControl(p,/(?=.*\bT001\b)(?=.*Password reset)/).all()){assert.ok((await button.boundingBox()).width>=120);
const readable=await button.evaluate(node=>{const walker=document.createTreeWalker(node,NodeFilter.SHOW_TEXT);
while(walker.nextNode()){if(walker.currentNode.textContent.trim().length<20)continue;
const range=document.createRange();
range.selectNodeContents(walker.currentNode);
const b=range.getBoundingClientRect();
if(b.width<80||b.height>160)return false}return true});
assert.ok(readable,'Ticket title collapsed or excessively wrapped')}await p.screenshot({path:path.join(process.env.BROWSER_ARTIFACTS,'viewport-'+width+'.png')})}assert.deepEqual(external,[]);
await p.close()});

await context.close();
}catch(e){for(const name of ['ui_create_edit_comment','ui_failed_save_retains_draft_and_retry','ui_stale_conflict_retains_draft','responsive_keyboard_and_local_network'])if(!checks.some(c=>c.name===name))checks.push({name,ids:['NFR-05'],passed:false,error:e.message})}finally{if(browser)await browser.close()}
const result={tests:checks.length,failures:checks.filter(c=>!c.passed).length,errors:0,skipped:0,checks};
console.log('BENCHMARK_GRADE='+JSON.stringify(result));
process.exitCode=result.failures?1:0;

})().catch(e=>{console.error(e.stack);
process.exitCode=1});
