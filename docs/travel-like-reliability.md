# PR #19: private anonymous Travel counters

Option A is implemented: one-click like/unlike and independent native/copy sharing,
with the existing automatic Anonymous Authentication flow. Normal valid records are
writable; the earlier blanket read-only containment is removed. No Cloud Function,
Blaze change, login, CAPTCHA, personal information or visitor setup is introduced.

See [_firebase/README.md](../_firebase/README.md) for the complete data/security design,
historical limitations, full production rules, exact manual Console/Pages rollout,
compatibility window, merge gates and private rollback rules. **Production activation
remains pending the owner's rule publication and website merge/deployment.**

The original PR19 transaction failed because owner-supplied rules granted only child
writes, not a parent write. Their root `.read:true` exposed all user records. The old
isolated fixture did not enforce rules. The new tests use real SDKs and enforced
Auth/Database emulators, including dropped WebSocket ACKs and reconnects.

The client reads only counts and its own marker/receipt. Atomic state changes carry
immutable private operation proofs. These prevent duplicate counts or resurrection
of an acknowledged-late old intent after an opposite action. Stale revisions are
superseded without rebasing. Share completions retain distinct immutable IDs so
concurrent/repeated shares count separately and retries count once. A cached/offline
snapshot alone never confirms a commit. Existing counts and records are not migrated
or repaired; technical receipts are added lazily during interactions.

Rules preserve presence-based count deltas, not historic attribution. Positive legacy
undercounts/overcounts keep their offset; malformed/missing historical counters and
underflow fail without repair. Anonymous multi-account abuse and fabricated well-
formed share events remain possible. See the precise examples and limits in the
manual guide. Current deployed rules/data were not remotely verified; no production
write tests, rule changes, infrastructure deployment or merge were performed.
