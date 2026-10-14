// Actual site helper functions + SDK 9.22.1 + enforced proposed rules. No mock rules.
const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');const path=require('node:path');const vm=require('node:vm');
const {webcrypto}=require('node:crypto');
const {initializeTestEnvironment,assertFails,assertSucceeds}=require('@firebase/rules-unit-testing');
const firebase=require('firebase/compat/app');require('firebase/compat/database');
const SV=firebase.database.ServerValue;
const ROOT=path.join(__dirname,'../..');const post='travel-japan';
const sdkDatabase=Object.assign(()=>({}),{ServerValue:SV});
const source=vm.createContext({crypto:webcrypto,Uint8Array,setTimeout,console,
 document:{readyState:'complete',querySelectorAll:()=>[]},
 firebase:{initializeApp(){},database:sdkDatabase,auth:()=>({signInAnonymously:()=>new Promise(()=>{})})}});
vm.runInContext(fs.readFileSync(path.join(ROOT,'assets/js/travel.js'),'utf8'),source);
const seed=()=>({count:4,note:'preserve',users:Object.fromEntries([1,2,3,4].map(i=>['other-'+i,{liked:true,timestamp:i}]))});
async function scenario(work){
 const env=await initializeTestEnvironment({projectId:'demo-website-reliability',database:{host:'127.0.0.1',port:9008,rules:fs.readFileSync(path.join(ROOT,'_firebase/database.rules.json'),'utf8')}});
 try{await env.clearDatabase();await work(env);}finally{await env.cleanup();}
}
const db=(env,uid='me')=>env.authenticatedContext(uid).database();
async function seedAt(env,type,record){await env.withSecurityRulesDisabled(c=>c.database().ref(type+'/'+post).set(record));}
async function read(env,type='likes'){let value;await env.withSecurityRulesDisabled(async c=>{value=(await c.database().ref(type+'/'+post).get()).val()});return value;}
const state=(database,uid='me')=>source.confirmedLikeState(database,uid,post);
const intent=(before,liked)=>source.newLikeIntent(before,liked);
const save=(database,action,uid='me')=>source.saveLikeIntent(database,uid,post,action);
async function click(database,liked,uid='me'){return save(database,intent(await state(database,uid),liked),uid)}
const omitTechnical=record=>({count:record.count,note:record.note,users:record.users});
test('Production rules: public counts, private own records, denied root/user maps and unauthenticated writes',{timeout:20000},()=>scenario(async e=>{
 await seedAt(e,'likes',seed());const a=db(e);const anon=e.unauthenticatedContext().database();
 for(const p of ['', 'likes','likes/'+post,'likes/'+post+'/users','likes/'+post+'/users/other-1','likes/'+post+'/receipts/other-1','likes/'+post+'/actions/other-1','shares/'+post+'/users/other-1'])await assertFails(a.ref(p || "/").get());
 await assertSucceeds(anon.ref('likes/'+post+'/count').get());await assertSucceeds(a.ref('likes/'+post+'/users/me').get());
 await assertFails(anon.ref('likes/'+post+'/count').set(99));await assertFails(a.ref('likes/'+post).transaction(x=>x));
}));
test('Actual client like/unlike: atomic transitions, existing text/markers, no-op intents and duplicate retries',{timeout:20000},()=>scenario(async e=>{
 await seedAt(e,'likes',seed());const a=db(e);
 const action=intent(await state(a),true);await save(a,action);assert.equal((await read(e)).count,5);
 await save(a,action);assert.equal((await read(e)).count,5);
 await click(a,true);assert.equal((await read(e)).count,5);
 const unlike=intent(await state(a),false);await save(a,unlike);await save(a,unlike);
 assert.deepEqual(omitTechnical(await read(e)),{...seed(),users:seed().users});
}));
test('Lost acknowledgement after intervening opposite intent never resurrects the old like',{timeout:20000},()=>scenario(async e=>{
 await seedAt(e,'likes',seed());const a=db(e);const b=db(e);
 const old=intent(await state(a),true);await save(a,old); // original result deliberately discarded
 await click(b,false);assert.equal((await read(e)).count,4);
 const retry=await save(a,old);assert.equal(retry.state.liked,false);assert.equal((await read(e)).count,4);
}));
test('Concurrent opposite intents use revision CAS; stale intent is superseded without rebasing',{timeout:20000},()=>scenario(async e=>{
 await seedAt(e,'likes',seed());const a=db(e),b=db(e);const before=await state(a);
 const like=intent(before,true),unlike=intent(before,false);
 const results=await Promise.all([save(a,like),save(b,unlike)]);
 assert.equal(results.filter(r=>r.superseded).length,1);
 const record=await read(e);assert.equal(record.count,4+(record.users.me?1:0));
 assert.equal(Object.keys(record.actions.me).length,1);
}));
test('20 distinct clients: contention preserves counts and all other users',{timeout:30000},()=>scenario(async e=>{
 await seedAt(e,'likes',seed());
 const clients=Array.from({length:20},(_,i)=>({database:db(e,'new-'+i),uid:'new-'+i}));
 await Promise.all(clients.map(c=>click(c.database,true,c.uid)));assert.equal((await read(e)).count,24);
 await Promise.all(clients.map(c=>click(c.database,false,c.uid)));const after=await read(e);assert.equal(after.count,4);assert.deepEqual(after.users,seed().users);
}));
test('Ten same-UID clients cannot increment one like repeatedly',{timeout:30000},()=>scenario(async e=>{
 await seedAt(e,'likes',seed());const clients=Array.from({length:10},()=>db(e));
 await Promise.all(clients.map(c=>click(c,true)));const r=await read(e);assert.equal(r.count,5);assert.equal(Object.keys(r.users).length,5);
}));
test('Forged counts, split writes, cross-user edits, fake proofs and receipt deletion fail atomically',{timeout:20000},()=>scenario(async e=>{
 await seedAt(e,'likes',seed());const a=db(e);await click(a,true);const original=await read(e);const ref=a.ref('likes/'+post);
 const malicious=[{count:999},{count:-1},{count:null},{'users/me':null},{'users/other-1':null,count:3},{'receipts/me':null},{'actions/me/11111111111111111111111111111111':{revision:99,liked:true}},{note:'overwrite'}];
 for(const changes of malicious){await assertFails(ref.update(changes));assert.deepEqual(await read(e),original)}
 const key=Object.keys(original.actions.me)[0];await assertFails(ref.update({['actions/me/'+key]:null}));await assertFails(ref.update({['actions/me/'+key+'/liked']:false}));
}));
test('Historical under/overcounts retain their offsets; zero underflow and missing/malformed counts fail without repair',{timeout:20000},()=>scenario(async e=>{
 const a=db(e);
 const over=seed();over.count=20;await seedAt(e,'likes',over);await click(a,true);assert.equal((await read(e)).count,21);await click(a,false);assert.equal((await read(e)).count,20);
 const legacy=seed();legacy.users.me={liked:true,timestamp:99};await seedAt(e,'likes',legacy);
 await click(a,false);const after=await read(e);assert.equal(after.count,3);assert.deepEqual(after.users,seed().users);
 for(const count of [0,'bad',-1,1.5,Number.MAX_SAFE_INTEGER+1,null]){
  const bad={count,users:{me:{liked:true,timestamp:99}}};if(count===null)delete bad.count;
  await seedAt(e,'likes',bad);await assert.rejects(click(a,false));const r=await read(e);assert.equal(r.count,bad.count);assert.deepEqual(r.users,bad.users);
 }
}));
test('Offline queue plus a newer opposite action: queued stale write cannot overwrite the confirmed state',{timeout:20000},()=>scenario(async e=>{
 await seedAt(e,'likes',seed());const a=db(e),b=db(e);const action=intent(await state(a),true);
 a.goOffline();const pending=save(a,action);await new Promise(r=>setImmediate(r));assert.equal((await read(e)).count,4);
 await click(b,true);await click(b,false);a.goOnline();const result=await pending;
 assert.equal(result.superseded,true);assert.equal(result.state.liked,false);assert.equal((await read(e)).count,4);
}));
test('Shares: 20 same-user concurrent completions, duplicates and lost results each count once; extra marker fields stay',{timeout:30000},()=>scenario(async e=>{
 await seedAt(e,'shares',{count:7,note:'preserve',users:{me:{shared:true,timestamp:1,extra:'preserve'},other:{shared:true,timestamp:1}}});
 const ids=Array.from({length:20},()=>source.counterActionId());
 await Promise.all(ids.map(id=>source.saveShareAction(db(e),'me',post,id)));let r=await read(e,'shares');assert.equal(r.count,27);assert.equal(r.users.me.extra,'preserve');
 await Promise.all(ids.map(id=>source.saveShareAction(db(e),'me',post,id)));r=await read(e,'shares');assert.equal(r.count,27);assert.equal(Object.keys(r.actions.me).length,20);
 const a=db(e);await assertFails(a.ref('shares/'+post+'/count').set(999));await assertFails(a.ref('shares/'+post+'/users/other').get());
 const before=await read(e,'shares');await assertFails(a.ref('shares/'+post+'/actions/me/'+ids[0]).remove());assert.deepEqual(await read(e,'shares'),before);
}));
test('Fresh empty articles initialize on an actual like/share without reconstructing historical data',{timeout:20000},()=>scenario(async e=>{
 const a=db(e);await click(a,true);assert.equal((await read(e)).count,1);
 await click(a,false);assert.equal((await read(e)).count,0);
 await source.saveShareAction(a,'me',post,source.counterActionId());assert.equal((await read(e,'shares')).count,1);
}));
test('Final rules reject old split clients and new client against old supplied rules fails without partial data',{timeout:20000},()=>scenario(async e=>{
 await seedAt(e,'likes',seed());const a=db(e);
 await assertFails(a.ref('likes/'+post+'/users/me').set({liked:true,timestamp:SV.TIMESTAMP}));
 await assertFails(a.ref('likes/'+post+'/count').transaction(v=>v+1));
 assert.deepEqual(await read(e),seed());
 const old=await initializeTestEnvironment({projectId:'demo-website-reliability',database:{host:'127.0.0.1',port:9008,rules:fs.readFileSync(path.join(__dirname,'provided.rules.json'),'utf8')}});
 try{await old.clearDatabase();await seedAt(old,'likes',seed());await assert.rejects(click(db(old),true));assert.deepEqual(await read(old),seed())}finally{await old.cleanup()}
}));
test('Share forgery, multi-proof batches, unknown IDs and missing legacy counters reject whole writes',{timeout:20000},()=>scenario(async e=>{
 const a=db(e);const id=source.counterActionId();const extra=source.counterActionId();
 const changes={count:SV.increment(1),['users/me/shared']:true,['users/me/timestamp']:SV.TIMESTAMP,'receipts/me':{actionId:id},['actions/me/'+id]:true,['actions/me/'+extra]:true};
 await assertFails(a.ref('shares/'+post).update(changes));assert.equal(await read(e,'shares'),null);
 await assertFails(a.ref('likes/travel-not-published/count').set(1));
 const legacy={users:{old:{shared:true,timestamp:1}},note:'preserve'};await seedAt(e,'shares',legacy);
 await assert.rejects(source.saveShareAction(a,'me',post,id));assert.deepEqual(await read(e,'shares'),legacy);
}));
test('Cutover boundary preserves an already-committed legacy marker and denies its late split count write',{timeout:20000},async()=>{
 let e=await initializeTestEnvironment({projectId:'demo-website-reliability',database:{host:'127.0.0.1',port:9008,rules:fs.readFileSync(path.join(__dirname,'provided.rules.json'),'utf8')}});
 try{await e.clearDatabase();await seedAt(e,'likes',seed());await db(e).ref('likes/'+post+'/users/me').set({liked:true,timestamp:SV.TIMESTAMP})}finally{await e.cleanup()}
 e=await initializeTestEnvironment({projectId:'demo-website-reliability',database:{host:'127.0.0.1',port:9008,rules:fs.readFileSync(path.join(ROOT,'_firebase/database.rules.json'),'utf8')}});
 try{await assertFails(db(e).ref('likes/'+post+'/count').transaction(v=>v+1));const r=await read(e);assert.equal(r.count,4);assert.equal(r.users.me.liked,true);assert.equal(Object.keys(r.users).length,5)}finally{await e.cleanup()}
});
test('Private maintenance rules deny writes, retain own/count reads, and cannot expose root or another user',{timeout:20000},async()=>{
 const e=await initializeTestEnvironment({projectId:'demo-website-reliability',database:{host:'127.0.0.1',port:9008,rules:fs.readFileSync(path.join(ROOT,'_firebase/maintenance.rules.json'),'utf8')}});
 try{await e.clearDatabase();await seedAt(e,'likes',seed());const a=db(e);await assertSucceeds(a.ref('likes/'+post+'/count').get());await assertFails(a.ref('/').get());await assertFails(a.ref('likes/'+post+'/users/other-1').get());await assert.rejects(click(a,true));assert.deepEqual(await read(e),seed())}finally{await e.cleanup()}
});
test('Malformed nonnumeric count values are not publicly exposed as aggregates',{timeout:20000},()=>scenario(async e=>{
 await seedAt(e,'likes',{count:{private:'legacy malformed'},users:{old:{liked:true}}});
 await assertFails(e.unauthenticatedContext().database().ref('likes/'+post+'/count').get());
 await assertFails(db(e).ref('likes/'+post+'/count').get());assert.deepEqual((await read(e)).count,{private:'legacy malformed'});
}));
test('A mismatched historical private receipt cannot falsely acknowledge state or rewrite markers',{timeout:20000},()=>scenario(async e=>{
 const record={...seed(),receipts:{me:{revision:0,actionId:'initial',liked:true}}};await seedAt(e,'likes',record);
 await assert.rejects(state(db(e)));assert.deepEqual(await read(e),record);
}));
