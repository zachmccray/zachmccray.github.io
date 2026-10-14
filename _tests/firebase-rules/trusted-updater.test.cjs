const {test}=require('node:test');
const assert=require('node:assert/strict');
const {planLikeChange}=require('./trusted-updater.cjs');
const seed=()=>({count:4,note:'preserve',users:Object.fromEntries([1,2,3,4].map(i=>['other-'+i,{liked:true,timestamp:i}]))});
test('Trusted design prototype changes marker/count together, preserving unknown fields and original records',()=>{
  const before=seed(); const liked=planLikeChange(before,'me',true,123);
  assert.equal(liked.kind,'changed'); assert.equal(liked.next.count,5); assert.deepEqual(before,seed());
  assert.deepEqual(liked.next.users.me,{liked:true,timestamp:123});
  const unlike=planLikeChange(liked.next,'me',false,124); assert.deepEqual(unlike.next,before);
});
test('Trusted design prototype keeps fixed desired intents idempotent after a lost reply',()=>{
  const liked=planLikeChange(seed(),'me',true,123).next;
  const retry=planLikeChange(liked,'me',true,124); assert.equal(retry.kind,'unchanged'); assert.deepEqual(retry.next,liked);
  const unliked=planLikeChange(liked,'me',false,125).next;
  assert.equal(planLikeChange(unliked,'me',false,126).kind,'unchanged');
});
test('Trusted design prototype distinguishes malformed records, counts and legacy undercounts',()=>{
  const cases=[['bad','record-shape'],[{users:[]},'users-shape'],[{count:'bad'},'count-invalid'],[{count:-1},'count-invalid'],[{count:1.5},'count-invalid'],[{count:4,users:{...seed().users,me:{liked:true}}},'legacy-undercount'],[{users:seed().users},'legacy-undercount'],[{count:Number.MAX_SAFE_INTEGER},'count-overflow']];
  for(const [record,reason] of cases){const before=structuredClone(record);assert.deepEqual(planLikeChange(record,'me',true,123),{kind:'invalid',reason});assert.deepEqual(record,before);}
});
test('Trusted design prototype preserves historic overcounts without claiming to reconstruct attribution',()=>{
  const record=seed();record.count=20;const next=planLikeChange(record,'me',true,123).next;
  assert.equal(next.count,21);assert.equal(Object.keys(next.users).length,5);assert.equal(planLikeChange(next,'me',false,124).next.count,20);
});
