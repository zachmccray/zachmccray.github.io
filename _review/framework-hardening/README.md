# PR #22 — Framework, UX and accessibility hardening

Baseline: merged PR #21, `a33a590bcfaadc8f1aeb3ad9ce3d50a4b2945f04`.
Branch: `hardening/ux-accessibility-framework`. One implementation/review PR;
no production merge, database deployment, content import or photograph import.

## Prioritized findings and implemented corrections

| Priority | Confirmed defect / reproduction | Correction | Evidence |
| --- | --- | --- | --- |
| P1 | Select 2025/Title A–Z, open a Blog article, then Back after the document is rebuilt. The selects restore, but the list still contains 2026/2024 entries and default ordering. | Reconcile native restored controls on pageshow only when their values differ from the last applied state. Disable Timeline scroll anchoring so reordering cannot pull the restored viewport to another entry. No custom history/storage/scroll-restoration system. | Browser flow plus 12 native-HTTP cached-rebuild/BFCache assertions; exact scroll retained in both native paths. Comparator logic is unchanged. |
| P1 in failure state | Block the theme script: the mobile Menu button does not open. Disable JavaScript: no primary navigation links are reachable on mobile. | Site-owned disclosure handling reuses the existing menu and avoids the theme's second toggle. A small stylesheet loaded only through noscript exposes existing links and hides nonfunctional controls. Failed theme search is explicitly unavailable. | Actual request-failure and JavaScript-disabled navigation checks. |
| P2 | Articles/Coursework have no active sidebar context. | Mark their existing Blog/Travel/Academics parent link as the current location; retain exact-page indicators on primary sections. | Generated context checked on every route; actual visitor navigation/Back/Forward/refresh. No new links or menus. |
| P2 | Mobile search leaves a narrow navigation layer visible beside results; Tab dismisses results because the scrollable region cannot receive focus. | Anchor results to the full mobile header, hide competing navigation while results are active, and make the region focusable with a visible outline. Permit focus transitions within search while preserving native engine/keyboard selection. | Full-page axe, Tab/Shift+Tab/Escape, native Page Down, search clicks, 12 widths/eight orientations and short reflow viewports. |
| P2 | Open GLightbox: 28 empty offscreen headings and duplicate Photo details landmarks remain exposed. | Use the existing library's events/public slide index to make inactive slides inert/aria-hidden. Keep current details, controls, Escape and focus return. | Before/after axe and current-slide focus checks. |
| P2 in failure state | Block GLightbox: full facts remain clipped to a 1px source description. | Move the existing metadata into native Photo details disclosures; keep original-file links and IDs, without copying facts or images. Scope definition-list styling to keep narrow fallback columns readable. | Missing-library keyboard/axe/bounds checks and previews. |
| P2 | Two Washington carousels have the same accessible landmark name. | Add an order-derived carousel number to existing labels. Preserve algorithm, image order, native gestures, controls and buffers. | Before/after landmark-unique scans; retained 70-case native carousel stress suite. |
| P2 | Theme-relative heading-anchor targets shrink to 21px on phones. | Minimum 24px target dimensions without changing heading fonts, fragments or content layout. | Axe target-size checks and viewport/anchor tests. |
| P2 in failure state; delivery improvement | Travel action icons require one external stylesheet/two font files; blocking them leaves blank visual controls. | Embed the same licensed icon paths as SVG symbols. Existing Firebase button state selects outline/filled heart, supplementing color. Keep the complete Firebase client/identifiers unchanged. | Visible icons with the font CDN blocked; actual SDK/emulator regressions; paired delivery benchmark. |
| P3 | The theme adds punctuation after labels that already include colons; its generic definition-list grid also distorts fallback metadata. | Narrow caption/fallback/no-script CSS removes duplicate punctuation and preserves readable label/value flow. No factual strings are edited. | Computed pseudo-content, metadata bounds, screenshots and all preserved data/source bytes. |

These are targeted corrections, not a new navigation/design system. No breadcrumb,
recommendation, theme toggle, additional search system or frontend framework was
introduced. The owner acceptance document complements the implementation.

## Review coverage and decisions

Reviewed Homepage, Academics, Coursework, Timeline, major/minor posts, Travel
index/articles (including long and placeholder-heavy pages), Photography,
Volunteering, Hobbies and Media. Evaluated page titles/hierarchy, readability,
spacing, links/footnotes, navigation/discovery, current location, keyboard/focus,
lightbox/carousels, loading/failure states, direct URLs and history.

The existing main typography/layout, dense natural-ratio collage, Timeline and
bounded carousel design remain approved. **22 matched main-content pixel
comparisons** at 390/1440px are unchanged (11 representative pages); native video
paint is masked consistently, its source/attributes preserved. Navigation-context
and error-state differences are intentional. No carousel positions are forced by
capture helpers. Normal viewer changes are limited to accessibility exposure and
removing duplicate label punctuation.

All **82 routes**, all **80 byte-identical search records**, **45 course anchors**,
**64 posts**, **9 Travel articles** and **30 photo data records** remain.
All original links/media/fragment IDs, SEO fields, article text/front matter,
course/photo data and Firebase sources/rules are preserved. Source checks allow
only the declared icon/asset-entry changes in rendered main content. Internal
page/footnote links all resolve; 149 existing missing media link references remain
intentionally unmodified. This is not a claim that unavailable photographs load.

On-demand native search/cache/batching, scoped deferred resources, pinned theme/
GLightbox, private receipt-based counters and PR #20 publication protections are
retained. No bulk unused-CSS or legacy-code removal is justified by conditional
coverage: working components are not rebuilt to make this PR look larger.

## Before/after previews

Actual baseline/candidate HTML, styles and controllers; real Inter, GLightbox and
baseline icon fonts. Photographs are **controlled SVG fixtures**, not new or
restored real media. Copyright/source paths for the inline UI icons are recorded
in `docs/fontawesome-icons-license.txt`; no photographic facts were fabricated.

| Intentional change | Preview |
| --- | --- |
| Parent Blog indicator | [Desktop article](previews/comparison-article-context.jpg) |
| Parent Academics indicator | [Desktop Coursework](previews/comparison-course-context.jpg) |
| Mobile search layering/width | [Search](previews/comparison-search.jpg) |
| Correct state after Blog Back | [Restored controls/results](previews/comparison-history.jpg) |
| Library unavailable | [Native photo details](previews/comparison-no-gallery.jpg) |
| Theme unavailable | [Mobile menu](previews/comparison-no-theme.jpg) |
| JavaScript disabled | [Existing navigation exposed](previews/comparison-no-js.jpg) |
| Icon CDN unavailable | [Visible Travel actions](previews/comparison-icons-unavailable.jpg) |
| Normal Travel appearance | [Same icon shapes](previews/comparison-icons-normal.jpg), [pressed shape feedback](previews/comparison-icons-normal-pressed.jpg) |
| Viewer | [Caption comparison](previews/comparison-viewer.jpg) |

[Matched originals and comparison results](previews/). History screenshots return
to the controls after native Back solely to show control/result agreement; the
independent native-history tests verify the unmodified scroll position.

## Test results

| Suite | Result |
| --- | --- |
| Production, running localhost and Pages-plugin Jekyll builds | Passed; frozen dependencies and pinned theme; known upstream Sass deprecations |
| Publication/public surface | 1,079 normal + 1,080 Pages + 1,079 localhost assertions; 82 routes, parent context, internal links/footnotes, exact current assets and no internal docs/search/sitemap leakage |
| Normal/Pages and normal/localhost parity | 580 + 580 assertions |
| Merged baseline/source preservation | 747 assertions; exact content/links/media/SEO/data plus all 80 search payloads |
| Native search/navigation/Travel UI | 557 production + 557 actual Jekyll-server assertions, including 135 queries and 90 code/title destination clicks |
| Existing visual/media suite | 975 assertions, with focused 446-assertion Timeline rerun after the history correction |
| Carousel native input/stress | 70 assertions; 1/2/5/12/150/180 images, wheel/touch, boundaries, resize, late/missing images, idempotence and independent strips |
| Framework/browser/axe (local Chromium 154) | 268 assertions; 32 full-page/state axe scans, no violations; incomplete/manual-review items retained |
| Native cached history | 12 assertions; actual Chromium persisted=false rebuild and persisted=true BFCache paths, controls, entry state, exact scroll and Forward |
| Enforced Firebase rules | 17 passed |
| Real SDK/Anonymous Authentication UI | 85 passed with local RTDB/Auth emulators |
| Lost-ACK/retry/opposite-intent transport | 18 passed with real SDK/enforced emulator rules |
| Isolated Firebase UI/error cases | 11 passed |
| Unrelated approved appearance | 22/22 matched main-content pixel comparisons |
| Delivery benchmark | 28 paired runs; all samples and trade-offs retained |
| Syntax/whitespace | Maintained/generated JavaScript and git diff checks passed |

The Firefox/WebKit/Chromium GitHub Actions matrix and final publication run are
checked on the PR; CI evidence will be linked here once the run finishes. Local
Firefox/WebKit downloads returned network-policy 403s. They are not claimed as
local tests. The CI workflow installs each actual engine independently on Linux;
Linux WebKit is not macOS/iOS Safari.

Widths: 320/375/390/430/600/601/768/820/1024/1280/1440/1920px, plus the eight
portrait/landscape pairs retained from PR #21. 640×450 and 320×225 CSS content
viewports test 200%/400% reflow equivalence, not actual browser-chrome zoom. The
attempted local zoom preference did not change browser metrics and is recorded
as unsupported, not passed.

The Playwright routed suite disables HTTP cache; its history assertion allows
font reflow while retaining the same visible Timeline context. The separate
native-HTTP test verifies exact scroll with cached assets and real BFCache.
The test-only server maps external font/script URLs locally and enforces a
self-only CSP. No such CSP, proxy or history override is added to production.

All Firebase automation uses fixtures or official isolated emulators; **no real
visitor writes, production rules/auth/billing/analytics changes or data migrations**.
Permission-denied warnings in emulator logs are expected asserted rejection cases.
The physical native share dialog is controlled in headless tests; voluntary cancel
remains normal. Existing private rules are preserved, not recertified remotely.

Machine evidence: [results](results/). Reproduction: [`_tests/README.md`](../../_tests/README.md).
The Pages profile exercises automatic publication plugins on Jekyll 4.4.1, not the
entire legacy Pages dependency stack. Production has no sitemap; sitemap generation
is a test-only exclusion probe. Internal owner docs/results remain unpublished.

## Performance and remaining limitations

[Measured before/after delivery, CPU, DOM and trade-offs](performance.md).
Three icon stylesheet/font requests are removed. Added SVG document/DOM cost is
explicit. Native local HTTP data include real fixture font bytes and the document;
no production CDN latency, photo/R2, decoded-memory or Core Web Vitals improvement
is claimed. Search/Carousel optimizations already shipped remain intact.

- No physical iOS/Android, native Safari/Edge or screen-reader certification.
  Browser engine, viewport and motion emulation complement owner real-device use.
- axe reports 26 incomplete rule instances across the 32 representative scans,
  requiring manual assessment (not automatic passes). Real photo contrast, quality
  of generic alt text, captions and copied facts need actual assets/owner input.
- Original media are still absent. Synthetic loading/error/proportion tests do
  not establish real photographic quality or loading performance. No dimensions,
  EXIF, article text or replacements were guessed. Placeholder/copy inaccuracies
  remain an editorial task; current URLs/references remain intact.
- Very short panoramas can have small natural image hit areas. They retain
  keyboard activation/full-view details; assess real extreme ratios before changing
  the approved collage's ratios/gaps. This PR makes no universal touch-size or
  WCAG-compliance claim for every hypothetical future photograph.
- New HTML references distinct current component filenames. Already-open old HTML
  may persist until reload/expiry; the versioned Travel asset is unchanged.
- The optional cloud setup draft saves only the two needed browser download hosts
  and tested test-tool/start instructions, preserving existing configuration. Local
  Firefox/WebKit activation requires reviewing/saving/publishing environment settings;
  this is separate from the website PR and not a production deployment.

## Owner review, optional later work and rollback

Use [`docs/owner-acceptance-checklist.md`](../../docs/owner-acceptance-checklist.md)
for practical desktop/phone, keyboard/history/search/gallery/counter checks,
severity definitions, screenshots and a reproducible issue template. It is intended
for normal use and subjective review after your local test/merge/deployment.

Larger optional work remains separately approval-gated: discovery/navigation aids
only if owner use demonstrates a need; theme preferences/dark mode; and real-media
R2/responsive-image/SEO work after the content/photo phases. Generic alt/caption,
multilingual pronunciation and ambiguous inline link wording are candidates for
owner/screen-reader feedback, not fabricated editorial changes here.

[Exact changed-file manifest](changed-files.txt). The PR Files changed tab is the
full source/binary diff. No source posts, Travel articles, course/photo data,
Firebase code or security settings changed. Revert the entire PR through a review
PR if rollback is needed; restore its matching HTML/CSS/JS together and rerun the
82-route/public-surface checks. No database rollback, reset or migration is required.
Keep PR #22 open and unmerged for owner review.
