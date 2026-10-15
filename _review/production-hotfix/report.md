# Urgent production hotfix: Travel asset delivery and internal documentation

Base: `0daaf0d3c98496bea4b178036b131f749e0d57f2` on `gh-pages`.
Branch: `hotfix/production-assets-docs`. No merge, rule deployment, billing change,
production authentication or database write was performed. Visual work remains paused.

## Confirmed findings

**Travel:** GitHub Pages API and its successful deployment action both identify
`0daaf0d`. Fresh production HTML loads exactly one Travel client,
`/assets/js/travel.js?v=atomic-receipts-1`, after the three deferred Firebase SDKs.
Both the query-string and plain asset URLs return the exact merged current source:
SHA-256 `bd584bf25d8a3180dd67d1d281fa314868bfd8df8a2bb2372a70fb0e85a6d78c`.
Observed HTML/JS headers: `Cache-Control: max-age=600`, `Age: 0`, edge cache MISS,
Last-Modified October 14 2026 23:47:25 UTC. The theme pin has no consumer for the
legacy nested `just_the_docs.custom_js` setting; neither live HTML nor reproduced
builds load a duplicate. No service worker is registered by this source.

The exact reported message exists in pre-PR19 commit `19973eb`, not in the deployed
current client. The owner reports Incognito likes/unlikes work. This establishes a
stale regular-browser client/state rather than a currently stale fresh CDN response
or a demonstrated current-client Firebase failure. Cached HTML, cached JS and an
already-open page cannot be distinguished without that affected profile's DevTools.
Query-string cache busting has **not** been proven ineffective: fresh requests work.
An enforced emulator reenactment of `19973eb` produces the exact reported error
without changing the seeded records.

**Documentation:** Pages automatically adds optional front matter, default layouts
and titles from headings. The four `docs/*.md` files became public pages, sidebar
entries and search records. The Pages publishing-plugin reproduction generated
86 HTML routes / 84 search records, with its entire search JSON equal to the actual
live index. Normal local Jekyll generated only 82 / 80, explaining the escaped test.
Raw documentation was also copied into the normal build. Live checks returned HTTP
200 for documentation pages and Markdown, 404 for representative `_firebase`,
`_tests`, `_review` URLs, and 404 for `/sitemap.xml` (no production sitemap).

## Minimal runtime changes

- Rename the current client to `travel-atomic-receipts-1.js`, with **identical bytes**,
  and reference it once, deferred, on Travel only. No counter/auth/share logic changes.
- Remove the unused legacy script configuration. Keep the site-owned include as the
  single source of script loading.
- Explicitly exclude maintainer docs, private/test/review/CI directories, dependency
  subdirectories and root build files. Documentation remains in GitHub. Avoid a broad
  `vendor/` exclusion: it also matches Just the Docs' compression layout.
- Add frozen public-route/asset/search/sitemap assertions, a pinned test-only Pages
  publishing profile, a PR/push CI workflow, and read-only deployed-site checks.
  Firebase tests follow the renamed asset and verify actual browser response bytes.

## Validation

| Check | Result |
| --- | --- |
| Production, localhost serve, Pages-plugin production/local builds | Passed |
| Public output: normal / Pages / local profiles | 253 / 254 / 254 checks passed |
| Content, SEO, assets, routes vs merged baseline | 580 passed; exact main content and SEO retained |
| Native browser search/navigation/responsive suite | 557 passed for Pages output and 557 for real localhost Jekyll |
| Course search | 135 queries and 90 code/title clicks; all 45 destinations; original 80 records preserved |
| Enforced Firebase Node rules | 17 passed |
| Actual Anonymous Auth + SDK browser | 85 passed; stale-client reproduction, nine like/unlike pairs at both widths, share/cancel/clipboard, one current asset with exact bytes |
| Real WebSocket ACK loss/retry/opposite action | 18 passed |
| Isolated Firebase UI/error tests | 11 passed (supplemental, not rule certification) |
| Blog sorting/filtering / navigation+sharing / carousel | 110 / 88 / 64 passed |
| Photography lightbox/keyboard/touch/responsive | 100 passed |
| Unrelated approved content visuals | 36 geometry, typography and pixel comparisons passed |
| Before-fix public-surface check | Expected failures reproduce leaked pages, links and stale asset path |
| Current live HTTP release checker | 84 passed / 86 expected failures: hotfix is not deployed; detects leaked docs and missing new asset |

Responsive checks cover 320, 375, 390, 430, 600, 601, 768, 820, 1024, 1280, 1440,
1920px and eight portrait/landscape profiles. All 82 live public routes currently
return HTTP 200; all 45 live course fragments resolve. Production rules and maintenance
rules are byte-identical to the merged commit. No CSS, photographs, content, Firebase
identifiers or PR20 component redesign changes were made.

The publishing profile uses Jekyll 4.4.1 and the actual relevant Pages plugins, not the
entire legacy Pages dependency stack. Its exact match to the deployed pre-fix search
index is evidence for this specific production difference. CI runs this profile for
both production and localhost origins and rejects unexpected pages in a frozen
82-route manifest. A sitemap plugin is enabled only as a test probe.

## Before/after previews

Controlled synthetic missing-media/font fixtures; navigation before uses the
Pages-plugin reproduction of deployed source. Desktop navigation captures are cropped
to the sidebar and first cards. Firebase screenshots use actual SDK/emulator rules,
with the old client deliberately injected for the before view, then the unmodified
current client served normally for the after view. These are not production DB writes.

| View | Before | After |
| --- | --- | --- |
| Desktop navigation | [Before](before-navigation-1440.png) | [After](after-navigation-1440.png) |
| Mobile navigation | [Before](before-navigation-390.png) | [After](after-navigation-390.png) |
| Desktop stale client/current likes | [Error](before-stale-client-1440.png) | [Working](after-current-client-1440.png) |
| Mobile stale client/current likes | [Error](before-stale-client-390.png) | [Working](after-current-client-390.png) |

## Deployment, limitations and rollback

After owner review/merge, wait for a successful Pages deployment of the hotfix commit.
Run `python _tests/verify-deployed.py --out /tmp/deployed.json`: all routes, sidebar,
internal URLs (404), standard search, course anchors and exact versioned JS must pass.
The production sitemap should remain absent; if present it must exclude internal docs.
Then reload the affected ordinary browser and verify Like/Unlike, native sharing and
copy-link behavior. Check Network shows one versioned Travel script, no old Travel
request, and no auth/permission errors. Already-open pages or cached HTML require a
reload/expiry; observed Pages freshness is ten minutes. This PR cannot invalidate an
already-running document or certify a deployment that has not happened yet.

Owner Incognito success is the live Firebase evidence. Automated writes/authentication
were confined to emulators; neither the deployed rules nor physical devices were
independently certified here. Chromium/Linux with touch emulation was used; Safari,
Firefox, Edge, physical iOS/Android, screen readers and genuine browser 200% zoom were
not run. Native share dialog completion/cancellation is controlled in headless tests.
Missing media remains intentional. Existing upstream Sass deprecation warnings remain.

No data migration or rules action accompanies this hotfix. If delivery must be rolled
back, retain the private rules and documentation exclusions; serve the known-working
`0daaf0d:assets/js/travel.js` bytes under another fresh versioned filename and update
the include in the same reviewed deployment. Do not restore `19973eb`'s split writes
or revert the entire exclusion fix. The CI/test additions can be reverted separately
without affecting visitor behavior. Keep this PR open for local review.

## Exact changed-file list

```text
A	.github/workflows/public-surface.yml
M	_config.yml
M	_firebase/README.md
M	_includes/head_custom.html
A	_review/production-hotfix/after-current-client-1440.png
A	_review/production-hotfix/after-current-client-390.png
A	_review/production-hotfix/after-navigation-1440.png
A	_review/production-hotfix/after-navigation-390.png
A	_review/production-hotfix/before-navigation-1440.png
A	_review/production-hotfix/before-navigation-390.png
A	_review/production-hotfix/before-stale-client-1440.png
A	_review/production-hotfix/before-stale-client-390.png
A	_review/production-hotfix/production-before.json
A	_review/production-hotfix/report.md
A	_review/production-hotfix/validation.json
A	_tests/Gemfile.pages
A	_tests/Gemfile.pages.lock
M	_tests/README.md
M	_tests/firebase-rules/browser.py
M	_tests/firebase-rules/option-a.test.cjs
M	_tests/firebase.test.cjs
A	_tests/pages-parity.yml
A	_tests/public-routes.json
A	_tests/public-surface.py
A	_tests/verify-deployed.py
R100	assets/js/travel.js	assets/js/travel-atomic-receipts-1.js
```

The Travel file is a 100% rename. All other changes are exclusions/loading references,
test infrastructure, maintainer instructions or review evidence.
