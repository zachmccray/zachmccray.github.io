# PR #19: Travel likes, privacy and the deployment boundary

## Status

**Release blocked. Likes are read-only on this branch pending an approved safe
write path. This is containment, not a completed like/unlike fix.** Counts and the
current visitor's existing like state remain visible. No parent records are read,
no like writes are attempted, and there is no split-write fallback. Sharing,
search, performance and the approved presentation remain intact.

No production rules, infrastructure, records, counters or identifiers have been
changed. The owner supplied the rules reproduced in
`_tests/firebase-rules/provided.rules.json`. They have not been retrieved from or
verified against the deployed database. Local emulator reproduction is distinct
from production verification.

## Root cause and distinct failure categories

PR #19 originally called `transaction()` at `likes/<article-id>`. The supplied
rules grant `.write` at `users/<authenticated-uid>` and `count`, **not at their
parent**. Child grants do not authorize a parent transaction. This produces
`PERMISSION_DENIED` even for an authenticated user and a perfectly consistent
record. A transaction also needs a parent read; that exposes other users' markers.

| Cause | Evidence / treatment |
| --- | --- |
| Parent write permission | Explained by the supplied rules and reproduced using the actual SDK against those rules locally; it is not a count-repair problem. |
| Authentication | Anonymous sign-in can fail independently. The revised client reports the authentication stage and SDK code, without tokens, IDs or snapshots. No production authentication probe was made. |
| Historical data | Noninteger, negative or malformed counts and marker undercounts are distinct from permission failures. The former client callback aborted these with `committed:false`, then displayed the same generic retry message. Existing undercounts are not proven to exist in production. Fixtures include them; nothing is repaired or reset. |
| Network / database status | An unavailable SDK, denied child read, disconnect, exhausted transaction retries or an inactive database can fail independently. The email's scheduled inactivity notice does not prove that the database is currently inactive. Check its current status/date in the Firebase console; no keepalive writes or reactivation were attempted. |
| Native sharing canceled | A voluntary dismissal produces `AbortError` and “Sharing canceled.” This is normal, leaves sharing enabled, and logs no completed share. |

The previous isolated RTDB model treated a transaction as an authorized atomic
operation. It did not evaluate ancestor/child security rules. Its passing retries
and counter arithmetic therefore never established deployed permissions. New
integration tests use the real Firebase 9.22.1 SDK and RTDB emulator; they explicitly
reproduce both the parent denial and unsafe operations allowed by the supplied
rules.

## Existing privacy and counter-rule problems

Root `.read: true` permits unauthenticated reads of **the entire database**, including
all `likes` and `shares` user markers. Adding `.read: false` below that root does not
revoke its grant. The owner must approve replacing that root grant with explicit
reads on public count leaves and each authenticated user's own marker. Until that
happens, this client's narrower requests do not make the database private.

The supplied count validation accepts *any number* from *any authenticated user*.
A client can overwrite the aggregate or send two increments for one user. An atomic
multi-location `update({count:increment(1), 'users/<uid>':marker})` commits both
leaves together without reading the parent, but **atomicity alone does not prevent
same-user races, duplicate retries or arbitrary count writes under these rules**.
We do not enable that operation against the current rules.

## Option A: private, coupled rules and an atomic client update

`_tests/firebase-rules/private-coupled.rules.json` is an **emulator-only candidate**,
not deployment configuration. It removes root public reads, grants public reads
only on counts and authenticated reads/writes only on one's own marker, and
validates at `likes/<id>` that the new aggregate changes by exactly the caller's
marker transition. Its child write grants allow multi-path updates; they do not
grant parent transactions. Count-only writes, marker-only writes, edits to other
users or unrelated fields, and duplicate increments are rejected atomically.
Existing share paths/write semantics are retained, with count/own-marker reads.

In a corresponding future client, retain a fixed desired state, submit one atomic
marker/increment update, and reconcile an uncertain response using only that user's
marker. A denial must be distinguished from confirmation of an already committed
intent; a cached/offline snapshot is not sufficient confirmation. Offline queues,
reconnects, opposite intents from the same user and acknowledgement loss need
additional endpoint/browser validation before enabling this design.

**Trade-off:** the candidate rules cannot count or attribute every private historical
marker. A fixture with count 4 and five markers can still be decremented to 3 with
four markers: the pre-existing undercount survives. Fixing forward transitions does
not establish whether an old marker ever contributed to the count. An owner-approved
policy for historical inconsistencies is needed if choosing this option. No
reconciliation or migration is included. Share counter authorization remains the
existing numeric-only policy; broader share abuse protection is separate work.

This option has no new hosting service or framework. It would need an explicitly
approved rules change, a completed client update and rule/transport verification.
Ordinary RTDB bandwidth/operation charges still apply under the project's plan.

## Recommended option B: an authenticated trusted endpoint

For PR #19's stronger historical undercount protection, move the atomic operation
into a small trusted endpoint (for example, a callable Cloud Function). Only the
server reads the article's user map. `_tests/firebase-rules/trusted-updater.cjs` is a
**server-design test prototype**, not deployed application code. Its integration test
uses the emulator's privileged test context; an actual Admin SDK/callable endpoint
is not implemented or certified here. It preserves all
existing fields and users, changes only the authenticated caller's marker and count,
uses a fixed desired state, and rejects malformed records/known undercounts. No-op
retries leave the original timestamp and count intact. Historic overcounts remain;
aggregate equality alone cannot establish perfect historic attribution.

The endpoint would:

1. Require authentication; derive the UID from the verified token, never request
   data. Accept only a boolean desired state and an allowed existing Travel ID.
2. Validate IDs against the site's nine existing identifiers; reject arbitrary
   paths, oversized payloads, unknown fields and unauthenticated callers.
3. Run the pure updater in an Admin SDK transaction at the existing record path.
   Use server timestamps; never log user maps/tokens. Transaction callbacks have no
   external side effects. Handle bounded contention retries with the same intent.
4. Return only `{liked, count}` for the caller and a categorized error such as
   `failed-precondition` for invalid historical data. The browser never receives
   another user's record. Repeating an uncertain call repeats its desired state.
5. Restrict client like writes to false and count/own-marker reads as shown in the
   emulator-only `private-backend.rules.json`; keep existing share behavior. Admin
   access bypasses rules, so authentication, input validation and limited service
   account permissions must be implemented and audited in the endpoint.

Deployment requires an approved backend/runtime, project/region selection, function
service account and rules change. Firebase Cloud Functions normally requires the
Blaze billing plan. Low-volume use may fall within current free allowances, but
invocations, compute, database bandwidth, build/artifact storage and egress can incur
charges; no zero-cost guarantee is made. Configure budgets/alerts and bounded
instances/concurrency; consider App Check and abuse limits because anonymous auth
alone does not prevent repeated-account abuse. A budget alert is not a hard spending
cap. Keep minimum instances at zero unless cold-start trade-offs justify otherwise.
GitHub Pages remains a static frontend and cannot itself execute a trusted transaction.
No function, billing change, rules update or production connection is deployed here.

## Approval and rollback

Before re-enabling likes, the owner must choose/approve Option A's rules and historical
policy or Option B's endpoint/rules/hosting. Option B is recommended for retaining
known-undercount protection without client access to other users. The tests and exact
rule candidates are reviewable in this PR; they are **not deployment commands**.
A production-readiness check must then confirm the approved rules are actually
published, test the endpoint/client in an isolated staging environment and verify
retries/reconnects and UI behavior before merging PR #19.

The current containment can be reverted as a commit, but the old parent transaction
will still be denied by the supplied rules and violates the desired client privacy
boundary. Do not merge a reversal merely to restore the generic retry message. Any
future server rollback must keep private reads and deny unsafe direct like writes;
return to the read-only client instead of restoring split writes. Keep PR #19 open.
