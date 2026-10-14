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
  const context = vm.createContext({ firebase: f.firebase, document: d.document, navigator: { clipboard: { writeText: async () => {} } }, console });
  vm.runInContext(source, context);
  await Promise.resolve(); await Promise.resolve();
  return { ...f, ...d, context, click: () => d.button.listeners.click() };
}
const historical = () => ({ likes: { 'travel-japan': { count: 4, note: 'historical', users: Object.fromEntries([1, 2, 3, 4].map(i => ['other-' + i, { liked: true, timestamp: i }])) } } });
test('Atomic like/unlike preserves four existing contributions and unrelated fields', async () => {
  const f = await setup({ data: historical() }); await f.click();
  assert.equal(f.data.likes['travel-japan'].count, 5); assert.equal(f.button.getAttribute('aria-pressed'), 'true');
  await f.click(); assert.equal(f.data.likes['travel-japan'].count, 4);
  assert.equal(f.data.likes['travel-japan'].note, 'historical'); assert.equal(Object.keys(f.data.likes['travel-japan'].users).length, 4);
  assert.deepEqual(f.operations.map(x => [x.type, x.path, x.applyLocally]), [['transaction', 'likes/travel-japan', false], ['transaction', 'likes/travel-japan', false]]);
});
test('Failure before commit cannot leave a partial user marker; retry keeps intended action', async () => {
  const f = await setup({ data: historical(), mode: { failBefore: true } }); await f.click();
  assert.equal(f.data.likes['travel-japan'].count, 4); assert.equal(f.data.likes['travel-japan'].users['fixture-user'], undefined);
  assert.match(f.status.textContent, /Retry/); f.mode.failBefore = false; await f.click();
  assert.equal(f.data.likes['travel-japan'].count, 5); assert.equal(f.button.getAttribute('aria-pressed'), 'true');
});
test('Lost acknowledgement then retry is idempotent for both like and unlike', async () => {
  const f = await setup({ data: historical(), mode: { ackLoss: true } }); await f.click();
  assert.equal(f.data.likes['travel-japan'].count, 5); f.mode.ackLoss = false; await f.click(); assert.equal(f.data.likes['travel-japan'].count, 5);
  f.mode.ackLoss = true; await f.click(); assert.equal(f.data.likes['travel-japan'].count, 4);
  f.mode.ackLoss = false; await f.click(); assert.equal(f.data.likes['travel-japan'].count, 4);
});
test('Concurrent distinct users and repeated same-user intents remain consistent under retries', async () => {
  const f = await setup({ data: historical(), mode: { conflicts: 3 } });
  const run = (uid, liked) => f.ref('likes/travel-japan').transaction(current => f.context.updateLikeRecord(current, uid, liked), undefined, false);
  await Promise.all(Array.from({ length: 20 }, (_, i) => run('new-' + i, true)));
  assert.equal(f.data.likes['travel-japan'].count, 24);
  await Promise.all(Array.from({ length: 10 }, () => run('same-user', true))); assert.equal(f.data.likes['travel-japan'].count, 25);
  await Promise.all(Array.from({ length: 10 }, () => run('same-user', false))); assert.equal(f.data.likes['travel-japan'].count, 24);
  await Promise.all(Array.from({ length: 20 }, (_, i) => run('new-' + i, false))); assert.equal(f.data.likes['travel-japan'].count, 4);
});
test('Pending network write disables repeat activation and resumes once', async () => {
  const f = await setup({ data: historical(), mode: { hold: true } }); const pending = f.click();
  assert.equal(f.button.disabled, true); assert.equal(f.button.getAttribute('aria-busy'), 'true'); await f.click(); assert.equal(f.operations.length, 1);
  f.resume(); await pending; assert.equal(f.data.likes['travel-japan'].count, 5); assert.equal(f.button.disabled, false);
});
test('Permission denial fails closed; authentication/read failures keep sharing usable', async () => {
  const f = await setup({ data: historical(), mode: { deny: true } }); await f.click();
  assert.equal(f.data.likes['travel-japan'].count, 4); assert.match(f.status.textContent, /Could not confirm/);
  for (const mode of [{ authFail: true }, { readFail: true }]) {
    const g = await setup({ mode }); assert.equal(g.button.disabled, true);
    await g.context.sharePost('https://zachmccray.github.io/travel/japan/', 'travel-japan');
    assert.match(g.status.textContent, /Link copied/);
  }
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
  const g = await setup({ mode: { ackLoss: true } }); await g.context.logShareToFirebase('travel-japan');
  assert.equal(g.data.shares['travel-japan'].count, 1); assert.equal(g.operations.length, 1);
});
test('Invalid existing counts fail without destructive repair', async () => {
  const f = await setup({ data: { likes: { 'travel-japan': { count: 'unknown', users: { old: { liked: true } } } } } });
  await f.click(); assert.equal(f.data.likes['travel-japan'].count, 'unknown'); assert.equal(f.data.likes['travel-japan'].users['fixture-user'], undefined);
});

test('Like child validation rejects both changes together; mixed same-user intents preserve the invariant', async () => {
  for (const failChild of ['/count', '/users/']) {
    const f = await setup({ data: historical(), mode: { failChild } }); await f.click();
    assert.equal(f.data.likes['travel-japan'].count, 4);
    assert.deepEqual(f.data.likes['travel-japan'].users, historical().likes['travel-japan'].users);
    f.mode.failChild = null; await f.click(); assert.equal(f.data.likes['travel-japan'].count, 5);
  }
  const f = await setup({ data: historical(), mode: { conflicts: 2 } });
  await Promise.all(Array.from({ length: 30 }, (_, i) => f.ref('likes/travel-japan').transaction(
    current => f.context.updateLikeRecord(current, 'racing-user', i % 2 === 0), undefined, false)));
  const record = f.data.likes['travel-japan'];
  assert.equal(record.count, 4 + (record.users['racing-user'] ? 1 : 0));
  for (const [uid, value] of Object.entries(historical().likes['travel-japan'].users)) assert.deepEqual(record.users[uid], value);
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

test('Legacy partial-write markers fail closed without decrementing existing contributions', async () => {
  const data = historical(); data.likes['travel-japan'].users['fixture-user'] = { liked: true, timestamp: 99 };
  const f = await setup({ data }); await f.click();
  assert.equal(f.data.likes['travel-japan'].count, 4);
  assert.deepEqual(f.data, data); assert.match(f.status.textContent, /Could not confirm/);
  const missing = historical(); delete missing.likes['travel-japan'].count;
  const g = await setup({ data: missing }); await g.click(); assert.deepEqual(g.data, missing);
});
