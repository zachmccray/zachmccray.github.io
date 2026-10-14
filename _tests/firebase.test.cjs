const test = require('node:test');
const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');
const fixture = require('./firebase-fixture');
const source = fs.readFileSync(require('node:path').join(__dirname, '../assets/js/travel.js'), 'utf8');
function dom() {
  const status = { textContent: '' };
  const count = { textContent: '', setAttribute() {} };
  const attributes = { 'data-id': 'travel-japan', 'aria-pressed': 'false' };
  const button = { dataset: { id: 'travel-japan' }, disabled: true, title: '', listeners: {},
    classList: { toggle() {} }, getAttribute: key => attributes[key],
    setAttribute: (key, value) => { attributes[key] = value; },
    addEventListener(event, callback) { this.listeners[event] = callback; },
    parentElement: { querySelector: () => count }, closest: () => card };
  const share = { dataset: { id: 'travel-japan' }, getAttribute: key => key === 'data-id' ? 'travel-japan' : null, disabled: false, parentElement: { querySelector: () => ({ textContent: '', setAttribute() {} }) }, closest: () => card };
  const card = { querySelector: query => query === '.travel-card-title' ? { textContent: 'Tokyo, Japan' } : status };
  const document = { readyState: 'complete', title: 'Travel | Zachary McCray',
    querySelectorAll: query => query === '.like-button' ? [button] : [share] };
  return { button, share, status, count, document };
}
async function setup(options = {}) {
  const f = fixture(options); const d = dom();
  const warnings = [];
  const crypto = require('node:crypto').webcrypto;
  const context = vm.createContext({ crypto, setTimeout, firebase: f.firebase, document: d.document, navigator: { clipboard: { writeText: async () => {} } }, console: { warn: (...args) => warnings.push(args) } });
  vm.runInContext(source, context);
  await Promise.resolve(); await Promise.resolve();
  return { ...f, ...d, context, warnings };
}
const historical = () => ({ likes: { 'travel-japan': { count: 4, note: 'historical', users: Object.fromEntries([1, 2, 3, 4].map(i => ['other-' + i, { liked: true, timestamp: i }])) } } });
test('One-click like/unlike updates atomically without reading other users',async()=>{
 const f=await setup({data:historical()});assert.equal(f.button.disabled,false);
 await f.button.listeners.click();assert.equal(f.data.likes['travel-japan'].count,5);assert.equal(f.button.getAttribute('aria-pressed'),'true');
 await f.button.listeners.click();assert.equal(f.data.likes['travel-japan'].count,4);assert.equal(f.button.getAttribute('aria-pressed'),'false');
 assert.equal(f.data.likes['travel-japan'].note,'historical');assert.deepEqual(f.data.likes['travel-japan'].users,historical().likes['travel-japan'].users);
 assert.ok(f.reads.filter(p=>p.startsWith('likes/')).every(p=>p.endsWith('/count')||p.includes('/users/fixture-user')||p.includes('/receipts/fixture-user')));
 assert.ok(f.operations.every(o=>o.type==='update'));
});
test('Acknowledgement loss preserves fixed like/unlike intents and does not increment twice',async()=>{
 const f=await setup({data:historical()});f.mode.ackLossAtomic=true;await f.button.listeners.click();
 assert.equal(f.data.likes['travel-japan'].count,5);assert.equal(f.status.textContent,'Liked.');
 f.mode.ackLossAtomic=true;await f.button.listeners.click();assert.equal(f.data.likes['travel-japan'].count,4);assert.equal(f.status.textContent,'Like removed.');
});
test('Pending write prevents repeat activation and preserves counts until acknowledgement',async()=>{
 const f=await setup({data:historical(),mode:{hold:true}});const pending=f.button.listeners.click();
 assert.equal(f.button.disabled,true);assert.equal(f.button.getAttribute('aria-busy'),'true');await f.button.listeners.click();f.resume();await pending;
 assert.equal(f.data.likes['travel-japan'].count,5);assert.equal(f.button.disabled,false);
});
test('Legacy markers and counts are not reconstructed on initialization',async()=>{
 const data=historical();data.likes['travel-japan'].users['fixture-user']={liked:true,timestamp:99};
 const f=await setup({data});assert.equal(f.button.getAttribute('aria-pressed'),'true');assert.deepEqual(f.data,data);assert.deepEqual(f.operations,[]);
});
test('Invalid historic counts have distinct feedback and are never repaired', async () => {
  for (const count of ['unknown',-1,1.5,Number.MAX_SAFE_INTEGER+1]) {
    const data=historical(); data.likes['travel-japan'].count=count;
    const f=await setup({data}); assert.equal(f.count.textContent,'—'); assert.match(f.status.textContent,/count needs review/);
    assert.deepEqual(f.data,data); assert.deepEqual(f.operations,[]);
  }
});
test('Authentication, own-marker read and count-read errors are distinguished without private logging', async () => {
  for (const [mode,stage,message] of [
    [{authFail:true},'authentication',/temporarily unavailable/],
    [{readFailPath:'/users/'},'own-like-read',/Your like state/],
    [{readFailPath:'likes\/travel-japan\/count'},'like-count-read',/like count/]
  ]) {
    const f=await setup({data:historical(),mode}); assert.equal(f.button.disabled,true); assert.match(f.status.textContent,message);
    assert.equal(f.warnings[0][1].stage,stage); assert.ok(f.warnings[0][1].code);
    assert.ok(!JSON.stringify(f.warnings).includes('fixture-user')); assert.deepEqual(f.operations,[]);
    await f.context.sharePost('https://zachmccray.github.io/travel/japan/','travel-japan'); assert.match(f.status.textContent,/Link copied/);
  }
});
test('Missing SDK leaves navigation/sharing usable and like controls disabled', async () => {
  const d=dom(); const copied=[];
  const context=vm.createContext({document:d.document,navigator:{clipboard:{writeText:async value=>copied.push(value)}},console});
  vm.runInContext(source,context); assert.equal(d.button.disabled,true);
  await context.sharePost('https://zachmccray.github.io/travel/japan/','travel-japan'); assert.equal(copied.length,1);
});
test('Voluntary native-share cancellation is normal and does not log a share', async () => {
  const f=await setup(); f.context.navigator.share=async()=>{throw Object.assign(new Error('dismissed'),{name:'AbortError'})};
  await f.context.sharePost('https://zachmccray.github.io/travel/japan/','travel-japan');
  assert.equal(f.status.textContent,'Sharing canceled.'); assert.equal(f.share.disabled,false); assert.deepEqual(f.operations,[]);
});
test('Shares atomically update existing paths and count every completed share', async () => {
  const f = await setup({ data: { shares: { 'travel-japan': { count: 7, users: { other: { shared: true } }, note: 'keep' } } } });
  await Promise.all(Array.from({ length: 20 }, () => f.context.logShareToFirebase('travel-japan')));
  assert.equal(f.data.shares['travel-japan'].count, 27); assert.equal(f.data.shares['travel-japan'].note, 'keep');
  assert.equal(f.data.shares['travel-japan'].users.other.shared, true);
  assert.equal(f.operations.length, 20); assert.ok(f.operations.every(x => x.type === 'update' && x.path === 'shares/travel-japan'));
});
test('Rejected share child cannot leave either half committed; no implicit replay', async () => {
  const f = await setup({ mode: { failChild: '/count' } }); await f.context.logShareToFirebase('travel-japan');
  assert.equal(f.data.shares, undefined); assert.match(f.status.textContent, /count update could not be confirmed/);
  const g = await setup({ mode: { ackLossAtomic: true } }); await g.context.logShareToFirebase('travel-japan');
  assert.equal(g.data.shares['travel-japan'].count, 1); assert.equal(g.operations.filter(o=>o.changes?.count!=null).length,1);
});
test('Queued share logging keeps controls responsive and counts each completion on reconnection', async () => {
  const f = await setup({ mode: { hold: true } });
  await f.context.sharePost('https://zachmccray.github.io/travel/japan/', 'travel-japan');
  assert.equal(f.share.disabled, false); assert.match(f.status.textContent, /Link copied/);
  await f.context.sharePost('https://zachmccray.github.io/travel/japan/', 'travel-japan');
  assert.equal(f.operations.length, 2); assert.equal(f.share.disabled, false);
  f.resume(); await new Promise(resolve => setImmediate(resolve));
  assert.equal(f.data.shares['travel-japan'].count, 2);
});
