# Approved editorial UI/UX refinements — review evidence

Implementation source: `bd006c9` on `design/editorial-ux-refinements`, based on
merged `gh-pages` `3422234`. Production has not been modified or merged.
The GitHub API is blocked by the current runtime egress policy; PR creation is a
remaining gate. The branch is published and the exact [PR body](PR.md) is ready.
The actual creation attempt was rejected before reaching GitHub: `Tunnel connection
failed: 403 Forbidden`. Apply the saved runtime allowlist for `api.github.com`,
`cdn.playwright.dev`, `playwright.download.prss.microsoft.com` and
`storage.googleapis.com` to finish creation and the remaining local tests.
[Final report-exclusion check](evidence/review-publication-surface.json): 1,246 passed.

## Prioritized changes

1. Corrected the 80→78 baseline CI discrepancy in separate commit `e95ca17`.
   Standard H2 grouping explains the change. All topic/gear/book/language text is
   still indexed; old fragments remain. Thirteen real Hobbies queries/clicks
   verify discoverability and reveal closed supporting lists. Course data, its
   135 queries/90 destination clicks and all 45 course URLs remain intact.
2. Bare 44px carousel controls; one-photo clicks, cancelable holds and accessible
   enlargement using the existing GLightbox. Original-only viewer sequences,
   inert clone mapping, native gestures, reduced motion, loading retry/cancellation
   and focus restoration are covered. Keyboard help is assistive-only.
3. Compact **thumbnail-based** minor Timeline entries; major prominence and links
   retained. All 64 records, descriptions, metadata and filter/sort/history logic
   remain. Minor entries remain nonlinked.
4. Three-column natural-ratio Photography with a smaller flat inset, full original
   metadata in the viewer, no visible normal instructions and usable missing-media
   states. No photo files or facts are imported or invented.
5. Conservative, independently reversible Travel CSS; no Firebase change.
6. Editorial Hobbies groups/five disclosures, compact Media rows and reusable
   inline navigation across Hobbies/Media/Volunteering and article templates.
   Short Volunteering labels preserve full accessible organization names.

[Exact changed source files](CHANGED_FILES.md) · [source diff](source.patch) ·
[implementation/navigation/rollback guide](NAVIGATION_AND_ROLLBACK.md)

## Before/after desktop and mobile

[Comparison viewer](comparisons.html) contains all pairs. All media are clearly
labeled synthetic geometry fixtures; these are not real-photo rendering claims.
The visible wording and metadata belong to the unchanged source records.

| Component | Desktop | Mobile |
| --- | --- | --- |
| Carousels | [before](screenshots/carousels-before-1440.png) / [after](screenshots/carousels-after-1440.png) | [before](screenshots/carousels-before-390.png) / [after](screenshots/carousels-after-390.png) |
| Blog Timeline | [before](screenshots/blog-before-1440.png) / [after](screenshots/blog-after-1440.png) | [before](screenshots/blog-before-390.png) / [after](screenshots/blog-after-390.png) |
| Photography | [before](screenshots/photography-before-1440.png) / [after](screenshots/photography-after-1440.png) | [before](screenshots/photography-before-390.png) / [after](screenshots/photography-after-390.png) |
| Travel | [before](screenshots/travel-before-1440.png) / [after](screenshots/travel-after-1440.png) | [before](screenshots/travel-before-390.png) / [after](screenshots/travel-after-390.png) |
| Hobbies | [before](screenshots/hobbies-before-1440.png) / [after](screenshots/hobbies-after-1440.png) | [before](screenshots/hobbies-before-390.png) / [after](screenshots/hobbies-after-390.png) |
| Media | [before](screenshots/media-before-1440.png) / [after](screenshots/media-after-1440.png) | [before](screenshots/media-before-390.png) / [after](screenshots/media-after-390.png) |
| Volunteering | [before](screenshots/volunteering-before-1440.png) / [after](screenshots/volunteering-after-1440.png) | [before](screenshots/volunteering-before-390.png) / [after](screenshots/volunteering-after-390.png) |
| Short Blog article | [before](screenshots/article-short-before-1440.png) / [after](screenshots/article-short-after-1440.png) | [before](screenshots/article-short-before-390.png) / [after](screenshots/article-short-after-390.png) |
| Multi-day Travel | [before](screenshots/article-days-before-1440.png) / [after](screenshots/article-days-after-1440.png) | [before](screenshots/article-days-before-390.png) / [after](screenshots/article-days-after-390.png) |

Enlargement: [desktop](screenshots/carousel-viewer-1440.png) /
[mobile](screenshots/carousel-viewer-390.png).
Full camera/long-description fixture: [mobile viewer](screenshots/fixture-long-metadata-390.png).
Hobbies supporting lists expanded: [desktop](screenshots/hobbies-details-open-1440.png) /
[mobile](screenshots/hobbies-details-open-390.png).

The shared navigation uses existing H2 IDs and actual Day labels, omits empty lists,
keeps more than twelve sections in a compact native expansion, and reveals targets
inside disclosures. No heading IDs are guessed. Seven copied placeholder Travel
outlines opt out until authored; the five legacy Washington labels/dates remain.
Current short Blog bodies have no fabricated TOC. A copied test post with 17
synthetic sections verifies future long articles and native details.

## Validation

| Check | Result |
| --- | --- |
| production publication | 1,245 passed |
| Pages publication | 1,246 passed |
| localhost publication | 1,246 passed |
| Pages parity | 580 passed |
| localhost parity | 580 passed |
| content/source preservation | 504 passed |
| real search/navigation | 557 passed |
| framework/browser/axe | 272 passed |
| editorial text/navigation | 620 passed |
| carousel interactions | 63 passed |
| gallery/Timeline/media stress | 996 passed |
| native carousel stress | 70 passed |
| native cached/BFCache history | 12 passed |
| controlled comparisons | 52 passed |
| Isolated Firebase client tests | 11 passed |
| Production / Pages-plugin / localhost Jekyll builds | Passed |
| Public routes / course targets | 82 / 45 preserved |
| Unexpected pages, internal docs/nav/search/sitemap entries | None |

Framework and editorial axe scans have zero violations; incomplete/manual cases
are retained in their evidence JSON. This is not WCAG certification. The established
twelve widths/eight orientations and 200%/400% equivalent reflow viewports pass.
Actual browser-chrome zoom, screen readers, physical iOS/Android/Edge, native share
dialogs and real-photo loading/contrast/memory are not certified. New tests were
executed in Chromium 154. Firefox/WebKit downloads returned HTTP 403. Current
enforced Firebase emulator tests could not start because its official JAR download
returned HTTP 403. The 11 isolated tests and UI fixture are **not** a substitute for
enforced-rule certification. No production Firebase rules/data were accessed or
changed. The unchanged client/rules/data sources are checked byte-for-byte.

CI now runs the new interactions in Chromium/Firefox/WebKit and runs current private
rules on demo Firebase emulators. Those required hosted results must pass before
merge; they have not been certified from this blocked environment. API and download
hosts are already in the saved environment draft, but the current runtime still
denies them even after a turn-level network grant.

All earlier exploratory failures were investigated: a new fragment helper initially
handled skip-to-main and deferred focus into search. It now handles only article-body
targets synchronously; the unchanged original focus assertion and full 557-check
suite pass. Cancellation cannot issue a trailing advance; CSS-only viewer failures
retry properly; canceled/competing lazy openings cannot steal focus. No assertions
were removed to hide those failures.

## Computed design values and reversibility

Body remains Inter **15px / 24px**, with 12px paragraph spacing. H1 is 28px desktop /
24px mobile; H2 22px / 20px; main subsections 18px. Navigation is 13px desktop /
14px mobile with 20px line height and 28px/32px link targets, native inline wrapping,
no boxes or borders. Gallery title/secondary text is 13px/12px desktop and 14px/13px
mobile, with 17px/16px and 18px line heights. Full measurements are in
[computed components](evidence/computed-components.json) and the editorial text JSON.
Supporting controls are explicit compact roles; no global typography reset occurs.

The two Photography variables `--gallery-column-width:220px` and
`--gallery-column-count:3` can independently return to `170px` / `4`. The three-column
choice makes desktop photographs larger and the gallery longer. Panoramas keep
their source ratio and at least a 24px activation area; unfit overlay lines move
to the viewer instead of covering adjacent photos. Missing-image targets are 44px.

The single marked Travel CSS block changes border `#dedee5→#e4e4ea`, date margin
`8→6px`, excerpt margin `12→10px`, tabular counter figures, transparent action-hover
borders, `#ece9f8` press feedback, related-title hover underlining and an inset cover
focus outline. Typography sizes, grid, padding, image ratios, source content and all
Like/Share logic remain. Removing that block restores exact baseline Travel pixels
at both widths. Ten unrelated desktop/mobile views are also pixel-identical.

## Performance comparison

Native local HTTP lab: seven alternating fresh contexts per phase at 1×/4× CPU,
1/2/5/12/150/180 source images. Controlled SVGs, no real media or CDN timing.
The controller-only lab includes its CSS/DOM work, but not loading the shared viewer
adapter or first opening; its byte cost and first-use behavior are listed separately.
Timing variation on shared hardware is material; no production speedup is claimed.

| CPU / originals | Rendered images, before→after | Initialization callbacks | Retained DOM nodes |
| --- | --- | --- | --- |
| 1× / 12 | 21 → 21 | 18.1 → 17.8ms | 111 → 135 |
| 1× / 150 | 159 → 159 | 26.1 → 23.2ms | 939 → 1101 |
| 1× / 180 | 189 → 189 | 35.3 → 20.8ms | 1119 → 1311 |
| 4× / 12 | 21 → 21 | 56.8 → 50.4ms | 111 → 135 |
| 4× / 150 | 159 → 159 | 52.8 → 63.1ms | 939 → 1101 |
| 4× / 180 | 189 → 189 | 53.9 → 66.4ms | 1119 → 1311 |

Bounded image counts and unique source transfers remain. Fallback links add one
anchor per rendered item, plus constant control/help nodes. This is a real DOM/JS
cost; repeated resize/scroll work also rises in some large-set samples. The full
[168-sample lab](evidence/carousel-performance-performance.json) retains CPU/layout/
heap/resource/repeated-use results. No decoded-image/GPU-memory saving is claimed.
Hold callbacks stop at release; no idle hold animation loop remains.

The paired [Travel lab](evidence/travel-performance.json) retains 22 requests,
993 DOM nodes and zero controlled layout shift in each phase. CSS transfer grows;
timing changes are not evidence of a user-visible performance win. Inter TTF fixture
bytes differ from production WOFF subsets. Firebase SDK/network and analytics were
blocked or replaced, so production service timing is not measured.

| Current artifact | Raw bytes, baseline→after | Computed gzip bytes |
| --- | ---: | ---: |
| `assets/css/custom-editorial-1.css` | 38,681 → 46,381 | 7,855 → 9,443 |
| `assets/js/image-carousel-3.js` | 11,420 → 19,794 | 3,608 → 5,669 |
| `assets/js/photography-portfolio-3.js` | 7,465 → 3,075 | 2,478 → 1,232 |
| `assets/js/image-viewer-1.js` | 0 → 6,572 | 0 → 2,216 |
| `assets/js/section-navigation-1.js` | 0 → 5,155 | 0 → 1,932 |

Gzip figures describe artifacts, not measured CDN responses. Carousel pages fetch
no GLightbox before activation. First use adds two requests (56,343B JS + 13,749B CSS
in the pinned fixture); warm openings reuse them. Photography already used that
library. No new library or framework is introduced. Empty Blog bodies do not load
the section-navigation enhancement.

## Review / rollback boundary

Do not merge until the remaining browser/emulator gates and owner local visual
checks pass. No Firebase Console, billing, R2, media migration or deployment-rule
action is required. Do not restore public database reads or an old Travel client.

Travel can be reversed by removing its isolated block; Photography's cap by its
two variables. Full rollback should use a PR around feature commits, retain the
baseline test correction, and retain versioned entry points/compatibility assets
while cached HTML can reference them. New HTML loads the current distinct assets
exactly once. The unchanged atomic Travel client retains its versioned safeguard.
