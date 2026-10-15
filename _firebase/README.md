# Private, anonymous Travel interactions — PR #19

The complete proposed production rules are **[database.rules.json](database.rules.json)**.
They are standard Realtime Database rules, tested with Firebase SDK 9.22.1 and the
real Auth/RTDB emulators. They are not deployed by Jekyll or GitHub Pages. This
underscore directory is excluded from the website build. Do not publish the older
`_tests/firebase-rules/private-*.rules.json` investigation fixtures.

Visitors retain automatic Firebase Anonymous Authentication. They provide no name,
email, password, verification or CAPTCHA, and see no authentication UI. Like/unlike
is one button activation, with background saving feedback. Native sharing and
copy-link complete independently of analytics/authentication availability. Voluntary
native-dialog dismissal is normal and creates no share event.

## Data and integrity

Existing `likes/<post-id>/count`, `users/<uid>`, share records, post identifiers and
unrelated fields stay in place. No count is reset/reconstructed and no records are
migrated. Like removal deletes only that visitor's marker as the existing behavior
requires. Share updates retain additional fields on an existing own-user marker.

New **private technical receipts** are created lazily:

| Path within an existing article record | Purpose |
| --- | --- |
| `receipts/<uid>` for likes | Current state, monotonically increasing revision and action ID. Initial revision 0 mirrors the existing marker without changing it or the count. |
| `actions/<uid>/<random-action-id>` for likes | Immutable `{revision, liked}` proof that a specific intent committed. |
| `receipts/<uid>` for shares | Identifies the new completion in its atomic update. |
| `actions/<uid>/<random-action-id>` for shares | Immutable `true` proof of that completion; repeated shares use distinct IDs. |

Only the authenticated owner can read these records. Clients never read other users
or the article parent. Rule evaluation sees the necessary before/after data on the
server. Numeric count leaves remain intentionally public; malformed object/string values
are not exposed through that grant. Root reads and user-map/list reads
are denied; a child denial cannot revoke a root `.read:true`, so that root grant is
removed entirely. All other ungranted database paths default to denied.

Like changes atomically write the count delta, own marker when its presence changes,
new receipt and immutable proof. The rules couple count delta to marker presence,
require the next own revision and one new action, and reject changes to other users,
unknown fields, invalid/noninteger/negative/overflowed counts, deletions of receipts
or proofs and arbitrary counter overwrites. Published writes are limited to the
nine existing Travel IDs. Add a future article's exact ID to the whitelist expressions
and rerun the enforced tests before publishing that article; do not rename old IDs.

SDK cached snapshots/value events can be optimistic. The client confirms receipt
state with an acknowledged, rules-validated no-op, and only an existing immutable
proof can acknowledge an uncertain action. Resending the original mutation cannot
allocate that proof again. A newer same-user revision supersedes a stale intent;
the old intent is never rebased over it. Simultaneous opposite intents use the first
accepted revision; another tab's current state is shown. Distinct users proceed
independently. Controls keep their desired action on retry and prevent double
activation while pending; keyboard focus returns when no other control took focus.

Share logging atomically increments exactly once for each new completion ID, writes
its proof/pointer and updates only the own marker's `shared`/`timestamp` leaves.
Repeated shares by the same UID still count separately, including concurrent tabs.
A replay is acknowledged through its existing proof without another increment.
Missing/rejected analytics delivery does not hold the native/copy control disabled.

Proofs must remain immutable and retained while they could be retried. This PR adds
no automatic cleanup, TTL or data migration. Receipt storage grows with accepted
interactions. No new runtime library/framework/server or Blaze billing is needed;
existing Spark storage, bandwidth, connection and auth quotas still apply. Monitor
usage; the rules do not promise unlimited free operation.

## Historical records and security limits

| Existing condition | Behavior |
| --- | --- |
| Empty record, no count or users | First real interaction initializes the count; no historical users/count are inferred. |
| Valid integer count with a historical undercount or overcount | Normal presence-based deltas preserve the arithmetic offset. No aggregate reconstruction or attribution is attempted. |
| Count 4 with five markers, own marker removed | Becomes count 3 with four markers. The old undercount persists; the client cannot know whether that legacy marker ever contributed to the count. |
| Zero count with an existing own marker | Unlike is rejected atomically to prevent a negative count; marker/count remain intact. Other visitors can still like, using normal deltas. |
| Missing count with existing user markers, malformed/negative/fractional count or malformed receipt | Mutation fails without repair. Only affected records need owner review; sharing itself remains usable if its analytics record is invalid. |
| Very large count/revision at the safe-integer limit | Overflowing operation is rejected, without clamping/resetting. |

These rules establish forward integrity, not historical correctness. They cannot
identify every phantom legacy marker or prove historic contribution ownership. An
unlike against a positive undercount can decrement a contribution that was never
actually recorded for that marker. Strict protection against that historical case
would require an anonymous authenticated trusted endpoint that can inspect private
records, refuse known undercounts and follow an owner-approved reconciliation policy.
Even a backend cannot recover unknown history from aggregates alone. No backend or
historic repair is introduced here.

Anonymous identifiers are not one-person proofs: clearing storage, using another
browser or scripted anonymous signups can create additional voters. Anyone with a
valid UID can submit well-formed own actions. Rules reject forged numeric overwrites,
not malicious actions that satisfy the protocol. Native APIs do not provide a
server-verifiable external-share receipt; a client can fabricate distinct share
completions. No login, CAPTCHA, interactive App Check or personal identity requirement
is added. Firebase auth rate limits/quotas, network/CDN blocking and unavailable
browser APIs can still affect service. SDK offline queues are memory-only; closing
an offline page can lose an uncommitted action or best-effort share metric. Accepted
operations remain protected by their durable proofs.

## Manual production deployment — owner only

**Production activation is pending. No rules, billing, website deployment or database
records have been changed by this work.** The owner-provided rules were reproduced
locally; current deployed rules were not retrieved/verified. Rules publication does
not modify stored data. GitHub Pages was checked read-only: it builds the root of
`gh-pages` with legacy Pages hosting at `https://zachmccray.github.io/`.

Before the PR is safe to merge:

1. Review this ruleset and the PR. Run the documented emulator/served UI tests, both
   Jekyll builds and preservation checks. Test locally against the emulators: the
   unmodified application config still points to production Firebase, so ordinary
   local browsing can sign in anonymously and attempt visitor actions there.
2. In Firebase Console select **website-blog-e4350 → Build → Realtime Database →
   website-blog-e4350-default-rtdb**. Check current database status. The earlier
   inactivity email does not establish deactivation; reactivate manually if needed.
   Confirm **Authentication → Sign-in method → Anonymous** remains enabled. No
   additional provider, verification or billing change is needed.
3. Save a secure local copy of the current rules; optionally take a private read-only
   data backup in Console. Inspect the nine count leaves for type/nonnegative
   integers. Do not reconstruct, delete or reset counts/users. Any changed project
   rules/other application consumers since the supplied copy need review before
   replacing the complete ruleset. Keep backups/private UIDs out of the repository.
4. Schedule the short compatibility window described below. In the Database
   **Rules** editor replace the entire rules JSON with `database.rules.json`, review
   Console validation, then **Publish**. Do not leave root `.read:true` alongside
   these rules. No script in this PR publishes rules.
5. Use Console's rules playground to check denied root/other-user reads and allowed
   public count/own-marker reads with anonymous-auth context. The emulator tests
   cover multi-location writes; a playground parent `set` is not the same operation
   as the client's atomic child `update`. Inspect the published editor JSON and
   confirm it matches the reviewed file. Deployed verification remains the owner's
   responsibility.
6. Test the new client from the reviewed branch locally with the published rules,
   or a separately isolated test project. For a controlled production visitor check,
   one anonymous like/unlike must return the count/marker to its prior state; new
   private action receipts remain, as designed. Normal share/copy must work even if
   analytics is denied. These are deliberate visitor actions, not a repair/migration.
   Check no login/verification UI, correct pressed state/count, and no unexplained
   console/network permission errors. Do not merge while those checks fail.
7. **Only the owner** merges PR #19 into `gh-pages` after review/testing. Wait for the
   GitHub Pages build to finish. Confirm newly served Travel HTML loads
   `travel-atomic-receipts-1.js` and the new script, using a fresh/private browser.
   The version avoids reusing a cached old script on updated pages; advance it with
   future incompatible counter-client releases. Verify normal
   one-click interactions and private permissions again. Keep rules private during
   the entire cutover; do not temporarily reopen reads/writes to make old JS work.

### Compatibility window and rollback

Final rules first is the privacy-first sequence. Until the new Pages build propagates,
the old production split-write client cannot like/log shares under them. Old open
pages continue using old JS until navigation/reload; CDN-cached old HTML can also
persist briefly. Sharing/copy still completes, although the old client can await a
rejected analytics request. The updated client works with final rules; it fails
closed under the supplied old rules because private receipt writes are not granted.
There is no safe rule that simultaneously permits the old unsafe split mutations
and guarantees the new atomic invariant. Do not describe this as a zero-downtime or
fully compatible rollout. No visitor account/verification step is involved.

An old split write whose marker committed **before** publication can have its second
count write denied **after** publication. The cutoff cannot make an already-started
legacy operation atomic. No such marker is automatically repaired; preserve it for
owner review. Test fixtures explicitly reproduce this boundary. Publish promptly in
a quiet window, then deploy the compatible client; monitor without resetting data.

For a safe pause/rollback, **[maintenance.rules.json](maintenance.rules.json)** retains
private reads/public counts and denies all writes. Sharing/copy remains usable with
the new client, while likes/metrics temporarily fail closed. Correct the paired
client/rules and restore the reviewed final rules before normal use. Never restore
root public reads, numeric-only writes, delete proofs or roll back to split writes.
GitHub Pages/client and Firebase rules deployments are separate manual actions.
