// SERVER-SIDE DESIGN PROTOTYPE ONLY; not loaded by Jekyll/browser.
// A real authenticated endpoint and its deployment need separate approval.
function planLikeChange(current, uid, liked, timestamp) {
  const invalid = reason => ({ kind: 'invalid', reason });
  if (current != null && (typeof current !== 'object' || Array.isArray(current))) return invalid('record-shape');
  const record = current || {};
  if (record.users != null && (typeof record.users !== 'object' || Array.isArray(record.users))) return invalid('users-shape');
  const users = { ...(record.users || {}) };
  const count = record.count == null ? 0 : record.count;
  if (!Number.isSafeInteger(count) || count < 0) return invalid('count-invalid');
  if (count < Object.values(users).filter(value => value != null).length) return invalid('legacy-undercount');
  if ((users[uid] != null) === liked) return { kind: 'unchanged', next: record };
  if (liked && count === Number.MAX_SAFE_INTEGER) return invalid('count-overflow');
  if (liked) users[uid] = { liked: true, timestamp };
  else delete users[uid];
  return { kind: 'changed', next: { ...record, users, count: count + (liked ? 1 : -1) } };
}
module.exports = { planLikeChange };
