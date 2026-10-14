// This suite MUST use the actual RTDB emulator; it never falls back to a mock.
const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { initializeTestEnvironment, assertFails, assertSucceeds } = require('@firebase/rules-unit-testing');
const firebase = require('firebase/compat/app');
require('firebase/compat/database');
const { planLikeChange } = require('./trusted-updater.cjs');
const projectId = 'demo-website-reliability';
const post = 'likes/travel-japan';
const SV = firebase.database.ServerValue;
const seed = () => ({ count: 4, note: 'preserve', users: Object.fromEntries([1,2,3,4].map(i => ['other-'+i, { liked: true, timestamp: i }])) });
const changes = (uid, liked) => ({ ['users/'+uid]: liked ? { liked:true, timestamp:SV.TIMESTAMP } : null, count:SV.increment(liked ? 1 : -1) });
async function withRules(name, work) {
  const env = await initializeTestEnvironment({ projectId,
    database: { host:'127.0.0.1', port:9008, rules: fs.readFileSync(path.join(__dirname,name+'.rules.json'),'utf8') } });
  try { await env.clearDatabase(); await work(env); } finally { await env.cleanup(); }
}
async function put(env, record) {
  await env.withSecurityRulesDisabled(ctx => ctx.database().ref(post).set(record));
}
async function read(env) {
  let result;
  await env.withSecurityRulesDisabled(async ctx => { result=(await ctx.database().ref(post).get()).val(); });
  return result;
}
const client = (env, uid='me') => env.authenticatedContext(uid).database();
test('Supplied rules expose user records and deny PR19 parent transaction', {timeout:20000}, async () => {
  await withRules('provided', async env => {
    await put(env, seed()); const db = client(env);
    assert.equal((await env.unauthenticatedContext().database().ref(post+'/users/other-1').get()).val().liked,true);
    await assertFails(db.ref(post).transaction(current => ({...(current||{}), count:5}), undefined,false));
    assert.deepEqual(await read(env),seed());
    await assertSucceeds(db.ref(post).update(changes('me',true)));
    assert.equal((await read(env)).count,5);
    // Current numeric-only count rule does not enforce a marker transition.
    await assertSucceeds(db.ref(post+'/count').set(999));
  });
});
test('Supplied rules permit duplicate same-user increments in atomic updates', {timeout:20000}, async () => {
  await withRules('provided', async env => {
    await put(env,seed()); const a=client(env), b=client(env);
    await Promise.all([a.ref(post).update(changes('me',true)), b.ref(post).update(changes('me',true))]);
    const record=await read(env); assert.equal(record.count,6); assert.equal(Object.keys(record.users).length,5);
  });
});
test('Candidate coupled rules: private reads, atomic like/unlike, fixed-intent retries', {timeout:20000}, async () => {
  await withRules('private-coupled', async env => {
    await put(env,seed()); const db=client(env);
    for (const location of ['', '/users', '/users/other-1']) await assertFails(db.ref(post+location).get());
    await assertSucceeds(db.ref(post+'/count').get()); await assertSucceeds(db.ref(post+'/users/me').get());
    await assertSucceeds(db.ref(post).update(changes('me',true)));
    assert.equal((await read(env)).count,5);
    await assertFails(db.ref(post).update(changes('me',true))); // duplicate increment rejected
    assert.equal((await db.ref(post+'/users/me').get()).exists(),true); // confirm desired state via own marker
    await assertSucceeds(db.ref(post).update(changes('me',false)));
    await assertFails(db.ref(post).update(changes('me',false)));
    assert.deepEqual(await read(env),seed());
    const anonymous=env.unauthenticatedContext().database();
    await assertFails(anonymous.ref(post).update(changes('me',true)));
  });
});
test('Candidate rules reject split writes, forged counts, other users and unrelated fields', {timeout:20000}, async () => {
  await withRules('private-coupled', async env => {
    await put(env,seed()); const db=client(env);
    for (const changeset of [{count:999},{'users/me':{liked:true,timestamp:SV.TIMESTAMP}},{'users/other-1':null,count:SV.increment(-1)},{note:'overwrite'}]) {
      await assertFails(db.ref(post).update(changeset)); assert.deepEqual(await read(env),seed());
    }
  });
});
test('Candidate rules enforce distinct-user and same-user contention', {timeout:30000}, async () => {
  await withRules('private-coupled', async env => {
    await put(env,seed());
    await Promise.all(Array.from({length:20},(_,i)=>client(env,'new-'+i).ref(post).update(changes('new-'+i,true))));
    assert.equal((await read(env)).count,24);
    const race=await Promise.allSettled(Array.from({length:10},()=>client(env,'same').ref(post).update(changes('same',true))));
    assert.equal(race.filter(x=>x.status==='fulfilled').length,1); assert.equal((await read(env)).count,25);
    await Promise.all(Array.from({length:20},(_,i)=>client(env,'new-'+i).ref(post).update(changes('new-'+i,false))));
    assert.equal((await read(env)).count,5);
  });
});
test('Candidate rules reject malformed counts but cannot identify historic marker undercounts', {timeout:20000}, async () => {
  await withRules('private-coupled', async env => {
    const db=client(env);
    for (const count of ['unknown',-1,1.5]) {
      const record={...seed(),count}; await put(env,record);
      await assertFails(db.ref(post).update(changes('me',true))); assert.deepEqual(await read(env),record);
    }
    const record=seed(); record.users.me={liked:true,timestamp:99}; await put(env,record);
    await assertSucceeds(db.ref(post).update(changes('me',false)));
    // The aggregate undercount remains: candidate rules do not establish attribution.
    const after=await read(env); assert.equal(after.count,3); assert.equal(Object.keys(after.users).length,4);
  });
});
test('Trusted prototype: like/unlike, retries and contention without client parent reads', {timeout:30000}, async () => {
  await withRules('private-backend', async env => {
    await put(env,seed());
    const mutate=async(uid,liked)=>{
      let result;
      for (let attempt=0;attempt<3;attempt++) {
        try {
          await env.withSecurityRulesDisabled(async ctx=>{
            result=await ctx.database().ref(post).transaction(current=>{
              const plan=planLikeChange(current,uid,liked,SV.TIMESTAMP);
              return plan.kind==='invalid'?undefined:plan.next;
            },undefined,false);
          });
          return result;
        } catch(error) {
          if (error.message!=='maxretry' || attempt===2) throw error;
        }
      }
    };
    await Promise.all(Array.from({length:20},(_,i)=>mutate('new-'+i,true)));
    assert.equal((await read(env)).count,24);
    await Promise.all(Array.from({length:10},()=>mutate('same',true))); assert.equal((await read(env)).count,25);
    await Promise.all(Array.from({length:10},()=>mutate('same',false))); assert.equal((await read(env)).count,24);
    await Promise.all(Array.from({length:20},(_,i)=>mutate('new-'+i,false))); assert.deepEqual(await read(env),seed());
    await assertFails(client(env).ref(post).get());
    await assertFails(client(env).ref(post).update(changes('me',true)));
    const inconsistent=seed(); inconsistent.users.me={liked:true,timestamp:99}; await put(env,inconsistent);
    const result=await mutate('me',false); assert.equal(result.committed,false); assert.deepEqual(await read(env),inconsistent);
  });
});
test('Real offline queue: optimistic own marker is not confirmation; reconnect commits both leaves once', {timeout:20000}, async () => {
  await withRules('private-coupled', async env => {
    await put(env,seed()); const db=client(env);
    await db.ref(post+'/count').get();
    let own=false; const ref=db.ref(post+'/users/me'); const listener=ref.on('value',s=>{own=s.exists()});
    db.goOffline();
    const pending=db.ref(post).update(changes('me',true));
    await new Promise(resolve=>setImmediate(resolve));
    assert.equal(own,true); assert.deepEqual(await read(env),seed());
    db.goOnline(); await pending;
    assert.equal((await read(env)).count,5);
    await assertFails(db.ref(post).update(changes('me',true)));
    assert.equal((await db.ref(post+'/users/me').get()).exists(),true);
    await db.ref(post).update(changes('me',false)); assert.deepEqual(await read(env),seed());
    ref.off('value',listener);
  });
});
