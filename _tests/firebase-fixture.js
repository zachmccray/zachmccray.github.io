// Isolated in-memory model of RTDB atomic transactions/updates. No credentials,
// network or production writes. Rules and transport behavior require integration testing.
(function (root) {
  function firebaseFixture(options = {}) {
    const data = structuredClone(options.data || {});
    const mode = { ...options.mode };
    const operations = [];
    const reads = [];
    const listeners = [];
    const held = [];
    let queue = Promise.resolve();
    const copy = value => value == null ? value : structuredClone(value);
    function get(path) {
      return path.split('/').filter(Boolean).reduce((node, key) => node?.[key], data);
    }
    function put(path, value) {
      const parts = path.split('/').filter(Boolean);
      const key = parts.pop();
      let node = data;
      parts.forEach(part => { node = node[part] ||= {}; });
      if (value == null) delete node[key]; else node[key] = value;
    }
    const snapshot = (value) => ({ val: () => copy(value), exists: () => value != null,
      child: path => snapshot(path.split('/').reduce((node, key) => node?.[key], value)) });
    function notify() { listeners.forEach(({ path, callback }) => callback(snapshot(get(path)))); }
    function serialize(work) {
      const result = queue.then(work);
      queue = result.catch(() => {});
      return result;
    }
    async function gate(path) {
      if (mode.hold) await new Promise(resolve => held.push(resolve));
      if (mode.deny || mode.failBefore) throw Object.assign(new Error('fixture permission/network failure'), {
        code: mode.deny ? 'PERMISSION_DENIED' : 'NETWORK_ERROR'
      });
    }
    function resolveValues(value, old) {
      if (value && typeof value === 'object') {
        if (value['.sv'] === 'timestamp') return 1700000000000;
        if (value['.sv']?.increment) return (old || 0) + value['.sv'].increment;
        return Object.fromEntries(Object.entries(value).map(([key, item]) => [key, resolveValues(item, old?.[key])]));
      }
      return value;
    }
    function ref(path = '') {
      return {
        child: child => ref([path, child].filter(Boolean).join('/')),
        on: (event, callback, error) => {
          reads.push(path);
          if (mode.readFail || (mode.readFailPath && path.includes(mode.readFailPath))) {
            error?.(Object.assign(new Error('fixture read denied'), { code: 'PERMISSION_DENIED' })); return;
          }
          listeners.push({ path, callback }); callback(snapshot(get(path)));
        },
        once: async () => { if (mode.readFail) throw new Error('fixture read denied'); return snapshot(get(path)); },
        transaction: async (update, complete, applyLocally) => {
          operations.push({ type: 'transaction', path, applyLocally });
          // RTDB can initially call with a cold local null snapshot; discard this
          // speculative calculation and retry against the committed server value.
          update(null);
          await gate(path);
          return serialize(() => {
            const current = copy(get(path));
            for (let i = 0; i < (mode.conflicts || 0); i++) update(copy(current));
            const next = update(current);
            if (mode.failChild && [path + '/count', path + '/users/'].some(child => child.includes(mode.failChild))) throw new Error('fixture child validation denied');
            if (next === undefined) return { committed: false, snapshot: snapshot(current) };
            put(path, resolveValues(next, current)); notify();
            if (mode.ackLoss) throw new Error('fixture committed but acknowledgement lost');
            return { committed: true, snapshot: snapshot(get(path)) };
          });
        },
        update: async changes => {
          operations.push({ type: 'update', path, changes: copy(changes) });
          await gate(path);
          return serialize(() => {
            const entries = Object.entries(changes).map(([key, value]) => {
              const full = [path, key].filter(Boolean).join('/');
              if (mode.failChild && full.includes(mode.failChild)) throw new Error('fixture child validation denied');
              return [full, resolveValues(value, get(full))];
            });
            entries.forEach(([full, value]) => put(full, value)); notify();
            if (mode.ackLoss) throw new Error('fixture committed but acknowledgement lost');
          });
        }
      };
    }
    const database = () => ({ ref });
    database.ServerValue = { TIMESTAMP: { '.sv': 'timestamp' }, increment: n => ({ '.sv': { increment: n } }) };
    const firebase = { initializeApp() {}, database, auth: () => ({
      signInAnonymously: () => mode.authFail ? Promise.reject(Object.assign(new Error('fixture auth denied'), { code: 'auth/operation-not-allowed' }))
        : Promise.resolve({ user: { uid: options.uid || 'fixture-user' } })
    }) };
    return { firebase, data, mode, operations, reads, ref, resume() { mode.hold = false; held.splice(0).forEach(resolve => resolve()); } };
  }
  if (typeof module !== 'undefined') module.exports = firebaseFixture;
  else root.firebaseFixture = firebaseFixture;
})(typeof window !== 'undefined' ? window : globalThis);
