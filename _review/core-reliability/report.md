# Performance and core reliability review

Branch: `perf/core-reliability`, based on latest merged `gh-pages` `19973eb`.
One PR for local review; production remains unmodified and the PR must stay unmerged.

**Option A is implemented and locally verified; production activation remains pending
the owner's private rules publication and coordinated Pages deployment.** Normal
like/unlike controls are writable through one click and automatic Anonymous Auth.
No login, personal details, CAPTCHA, Cloud Function or billing change is added.
See the [complete rules, historical limits and exact manual rollout](../../_firebase/README.md).
No production rules/data or merge were changed. Keep PR #19 open for owner review.

## Implementation

- Native Just the Docs search loads Lunr/data on demand, replays early/pasted input,
  provides loading/error/keyboard retry, and restores session indexes only against
  the exact retrieved data and matching builder/Lunr versions. Corrupt/disabled/stale
  storage falls back to the native builder. All 80 standard records and 45 course
  destination anchors remain unchanged; no generator override or placeholder indexing.
- The pinned theme exposes no lifecycle hook. Its 53-line head and runtime have a
  guarded integration: deferred scripts, initialization delegation, no forced page
  scroll, and cancellation of native result batches only when the query changes.
  Full-result tests verify all 18 EECS 101 matches after real typing/focus return;
  associations alone would miss an interrupted batch. Native ranking, snippets,
  highlighting, result URLs and Arrow/Enter/Escape handlers remain in use.
- Accessible suggestions use the native list as a listbox inside a named region;
  retry stays an ordinary button outside it. Tab exits suggestions, arrow keys choose
  a result, and Enter follows its unchanged URL. Error-button Escape works in one
  press. Mobile retry uses the original event path so replacing feedback does not
  dismiss the menu. Retry text computes to Inter 15px/24px with a 44px minimum target
  and the established 3px purple focus outline; input remains 16px.
- Likes/unlikes use private immutable action proofs, current-state receipts and
  rules-coupled atomic count/marker changes. Cached snapshots alone never confirm
  success; acknowledged no-ops establish state/proof. Same-user revision conflicts
  supersede stale intents without rebasing. A lost acknowledgement cannot resurrect
  an old like after an opposite action. Initial legacy records are mirrored without
  changing their markers/counts; historical totals are not reconstructed.
- Shares retain native/copy behavior independently of analytics. Each completion has
  an immutable proof; repeated/concurrent shares count separately and resends count
  once. Only the own marker's shared/timestamp leaves change, preserving extra fields.
  Cancellation is normal. Keyboard focus returns after saving when no other control
  took focus. Authentication errors stay ordinary availability feedback.
- Complete proposed rules remove root public reads, allow numeric public counts and
  private own records, and deny forged/split/cross-user/delete/multi-proof writes.
  Private maintenance rules support rollback. The Travel asset cache version makes
  updated pages fetch the compatible client. Old tabs/HTML and in-flight split writes
  require the documented cutover; there is no zero-downtime compatibility claim.
- Font Awesome loads on Travel only. Inter's original four weights/display=swap move
  directly to the head with preconnect. Pin the audited theme SHA and tested GLightbox
  3.3.1; no dependency upgrade, global typography reset or image changes.

Audit findings implemented: **A1/A2/A3, B1/B4/B6/B7, A6**. Production acceptance
remains gated on owner rules publication, verification and Pages deployment.

## Comparable performance evidence

Recorded on `02839e0`; seven other production files remain byte-identical; the only head_custom change is
a cache token inside its Travel-only branch. Homepage assets/request scheduling are
unchanged, so homepage performance was not remeasured.
Seven fresh contexts per phase/rate, alternating order; Chromium 154, 390×844,
actual compiled JS and standard 80-record JSON from local HTTP. Native functions
are timed with a transparent test-only Proxy. No simultaneous browser regressions
ran during this measurement.

| 4× CPU median | Baseline | Revision |
| --- | ---: | ---: |
| Index build on initial page load | 183.7ms | 0ms |
| Cold native build | 183.7ms (startup) | 178.6ms (first use) |
| Session native Index.load | — | 20.5ms |
| Initial total script duration | 217.8ms | 19.6ms |
| Initial local HTTP transferred bytes, including headers | 290,869 | 215,241 |
| Initial requests, including controlled externals | 12 | 10 |
| Laboratory FCP | 300ms | 244ms |

Initial local transfer drops by 75,628 bytes.
The earlier audit's 182ms construction is reproduced at 183.7ms;
its new range is 142.7–192.3ms.
Cold first use still pays construction/network cost; this moves work to visitors
using search rather than promising instant first-use search. Session Index.load
excludes storage/JSON parsing, UI rendering and network time.

The separately removed Font Awesome stylesheet is 102,526 decoded bytes (21,865
estimated gzip), omitted on 81/82 routes. This CDN payload is excluded from the local
HTTP totals above. Synthetic font/media transfers are also excluded. Google font
WOFF2 payloads/cache headers and live production were inaccessible, so no actual
font-byte or production Core Web Vitals claims are made. FCP ranges and all 28 raw
samples are in [performance-results.json](performance-results.json).

## Validation of this revision

- Production/local Jekyll builds succeed, 580 preservation checks each; all **82 HTML
  routes**, exact content/SEO, assets, IDs, 80 standard search records and 45 course
  anchors retained. Existing upstream Sass warnings remain. `_firebase`, `_tests`
  and `_review` are excluded from the website output.
- **557** real served-browser checks: 135 course queries/90 destination clicks,
  native loading/error/cache/keyboard/history, 12 widths/eight orientations and all
  nine one-click keyboard like/unlike/share controls. No browser exceptions.
- **17 enforced scenarios** run the actual client helpers with Firebase 9.22.1 and
  RTDB emulator 4.11.2: private ownership, atomic/no-op/replay intents, opposite intents,
  20 distinct/ten same-UID clients, forged/split/cross-user/delete/multi-proof writes,
  empty counters, under/overcounts and malformed/overflow records, offline/newer
  opposite state, 20 concurrent same-UID shares/replays, old/new compatibility, an
  already-committed legacy split marker at cutover, maintenance policy and malformed
  public-count/private-receipt protection. Expected denials:
  [firebase-enforced.log](firebase-enforced.log).
- **75 actual served UI/SDK checks** at 390/1440 with real Anonymous Auth and Database
  emulators: no login/verification UI, persistent anonymous UID, all nine one-click
  likes/unlikes, exact original counts/markers, normal cancellation and real clipboard
  success despite denied analytics. [Results](firebase-browser-results.json).
- **18 real transport checks** drop successful WebSocket ACKs, close/reconnect and
  observe SDK resends plus immutable proof acknowledgements. Like/unlike state/count
  survives, a newer opposite action in a second tab remains, and a share is counted
  once. [Results](firebase-transport-results.json). No mocked counter engine/rules.
- **11** isolated UI/error cases supplement integration tests. Retained Blog: **110**;
  Travel IDs/URLs/sharing/navigation/like/unlike: **88**; carousel/navigation: **64**.
- **36** unrelated main-content DOM/style/pixel pairs at 390/820/1440 remain unchanged
  with controlled fonts/media and consistent chrome/native-paint masks. No new
  horizontal overflow; healthy browser flows have no exceptions. Seven other runtime
  source files remain byte-identical to `02839e0`; head_custom keeps every successful
  feature and only versions the Travel script.

Earlier initial-PR gallery/performance evidence remains historical under `prior_suites`;
it is not claimed as rerun. Current source/rule hashes and results:
[validation.json](validation.json). Commands: [testing README](../../_tests/README.md).

## Before/after screenshots

[Homepage desktop](homepage-desktop.png) · [Homepage mobile](homepage-mobile.png) ·
[Mobile keyboard focus exit](mobile-keyboard.png) ·
[Mobile search failure](search-failure-390.png) · [Desktop search failure](search-failure-1440.png).

Travel failure → working anonymous one-click interactions (actual Auth/DB emulators,
cached Inter/icons, neutral missing media): [Mobile before](travel-like-before-390.png) ·
[Mobile working](travel-like-working-390.png) · [Desktop before](travel-like-before-1440.png) ·
[Desktop working](travel-like-working-1440.png). Older read-only snapshots remain
historical evidence of the temporary containment; they are not the current design.

Homepage presentation stays intact. The menu now dismisses when Tab reaches main
content, and search failure has readable, keyboard-accessible feedback.

## Limits and remaining work

The supplied rules explain the original failure/privacy warning; no current deployed
rules were remotely verified. The complete proposed policy must be manually published
before normal production use. See the [manual guide](../../_firebase/README.md) for
Console steps, merge checks, old-client/cached-HTML incompatibility and private rollback.
A new script cache token covers updated pages; it cannot rewrite already-open old tabs.
An old marker accepted before publication can lose its late split count write afterward;
no old data is silently reconciled. Do not reopen reads or permit split writes for rollout.

Historical numeric under/overcounts retain their offset; their contribution attribution
is unknown. Underflow/malformed/missing historical counters fail without repair. Rules
cannot prevent anonymous multi-account abuse or prove an external share occurred.
Durable private proofs grow with interactions; no cleanup/migration is added. Offline
page closure can lose uncommitted/best-effort events. These limits do not impose visitor
identity/verification or billing/backend requirements.

Linux Chromium is available; physical iOS/Android, Safari, Firefox, Edge, real screen
readers and genuine 200% browser zoom remain unverified. Public website/CDN access
was blocked in this cloud. No full WCAG conformance or live performance certification.

Image dimensions/lazy priority changes are deferred because no actual referenced
photograph dimensions are available; never write fixture dimensions into source or
blindly lazy-load above-fold photos. Next: Photography overlay summary, Timeline
rhythm/gutters/major thumbnail link, carousel copies/readiness/geometry/controls,
then actual R2 metadata and selective discovery/editorial readiness work. Broader
SEO/dark mode remain separate. See [updated roadmap](../../docs/modernization-roadmap.md).

## Exact changed files

Runtime changes in this revision: `assets/js/travel.js`, and
`_includes/head_custom.html` for the Travel-only cache token. Proposed private rules/
manual rollout are in `_firebase`. Seven other production files from reviewed PR19
remain unchanged. Test, policy and review directories are excluded from Jekyll output.

This revision from `d25ed7e`:

- `_firebase/README.md`
- `_firebase/database.rules.json`
- `_firebase/maintenance.rules.json`
- `_includes/head_custom.html`
- `_review/core-reliability/firebase-browser-results.json`
- `_review/core-reliability/firebase-enforced.log`
- `_review/core-reliability/firebase-transport-results.json`
- `_review/core-reliability/report.md`
- `_review/core-reliability/travel-like-working-1440.png`
- `_review/core-reliability/travel-like-working-390.png`
- `_review/core-reliability/validation.json`
- `_tests/README.md`
- `_tests/browser.py`
- `_tests/firebase-fixture.js`
- `_tests/firebase-rules/browser.py`
- `_tests/firebase-rules/firebase.json`
- `_tests/firebase-rules/option-a.test.cjs`
- `_tests/firebase-rules/transport.py`
- `_tests/firebase.test.cjs`
- `assets/js/travel.js`
- `docs/core-reliability.md`
- `docs/modernization-roadmap.md`
- `docs/travel-like-reliability.md`

Complete PR against `gh-pages`:

- `_config.yml`
- `_firebase/README.md`
- `_firebase/database.rules.json`
- `_firebase/maintenance.rules.json`
- `_includes/head.html`
- `_includes/head_custom.html`
- `_review/core-reliability/firebase-browser-results.json`
- `_review/core-reliability/firebase-enforced.log`
- `_review/core-reliability/firebase-transport-results.json`
- `_review/core-reliability/homepage-desktop.png`
- `_review/core-reliability/homepage-mobile.png`
- `_review/core-reliability/mobile-keyboard.png`
- `_review/core-reliability/performance-results.json`
- `_review/core-reliability/report.md`
- `_review/core-reliability/search-failure-1440.png`
- `_review/core-reliability/search-failure-390.png`
- `_review/core-reliability/travel-like-before-1440.png`
- `_review/core-reliability/travel-like-before-390.png`
- `_review/core-reliability/travel-like-readonly-1440.png`
- `_review/core-reliability/travel-like-readonly-390.png`
- `_review/core-reliability/travel-like-working-1440.png`
- `_review/core-reliability/travel-like-working-390.png`
- `_review/core-reliability/validation.json`
- `_tests/.gitignore`
- `_tests/README.md`
- `_tests/browser.py`
- `_tests/course-queries.json`
- `_tests/firebase-fixture.js`
- `_tests/firebase-rules/browser.py`
- `_tests/firebase-rules/emulator.test.cjs`
- `_tests/firebase-rules/firebase.json`
- `_tests/firebase-rules/option-a.test.cjs`
- `_tests/firebase-rules/package.json`
- `_tests/firebase-rules/private-backend.rules.json`
- `_tests/firebase-rules/private-coupled.rules.json`
- `_tests/firebase-rules/provided.rules.json`
- `_tests/firebase-rules/transport.py`
- `_tests/firebase-rules/trusted-updater.cjs`
- `_tests/firebase-rules/trusted-updater.test.cjs`
- `_tests/firebase.test.cjs`
- `_tests/performance.py`
- `_tests/preservation.py`
- `_tests/requirements.txt`
- `assets/css/custom.css`
- `assets/js/just-the-docs.js`
- `assets/js/search.js`
- `assets/js/site-ui.js`
- `assets/js/travel.js`
- `docs/core-reliability.md`
- `docs/just-the-docs-license.txt`
- `docs/modernization-roadmap.md`
- `docs/travel-like-reliability.md`
- `photography.md`

## Rollback

Before merge, close/discard this branch; production is untouched. After an approved
merge, revert its merge commit in a separately reviewed PR and rebuild Pages. No
migration or data reset needs reversal. If reverting only performance work, restore
head/runtime/controller/site-ui/font integration together and retain the paired
private counter client/rules; use the private maintenance policy for a temporary pause.
A complete revert would restore the old split-write defect. Session entries are
ignored by the old runtime and need no purge. Do not merge automatically.
