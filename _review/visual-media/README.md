# PR #21 — Photography, Blog Timeline and native carousels

Baseline: merged `gh-pages` **8bd2daa** (PR #20). Implementation continues on the
existing **design/portfolio-timeline-carousels** branch. This is one review PR;
production Firebase, security settings and production content are untouched.

## What changed

- **Photography:** retain all 30 records, natural image ratios, order, four-column
  masonry cap and compact gaps. Replace viewport-fixed full inventories with
  tile-contained title/secondary summaries. Short tiles simplify or omit the
  summary. Ordinary touch/click/Enter opens the full details immediately, without
  a long-hold gesture. The viewer includes the existing description and label,
  date/location, separate body and grouped optional exposure settings; no invented
  fields. Long captions scroll within 40% of viewport height, at most 320px.
  Visible current-slide focus, Escape/return, reduced motion and missing-image
  error/navigation handling use the existing pinned GLightbox.
- **Blog Timeline:** one shared grid aligns titles, image-to-text gutters and
  marker centers while preserving major/minor sizes and the 24px row gap. Major
  thumbnails link to their original articles. Minor entries stay unlinked.
  Filtering preserves grid layout; all four sorting modes remain intact.
  Failed or absent images keep quiet, consistent media slots and original paths.
- **Carousels:** replace six complete sets with original items plus viewport-sized
  edge buffers. At least three images and a ready source period over two
  viewports enable looping; short or loading sets remain finite. Copies cover
  two viewports per edge, each original at most once per side (total <=3N).
  Native scrolling runs without per-event layout work. Quiet/end correction waits
  for pointer release. Preserve selection across image readiness and orientation
  changes; add 44px controls, arrow/Home/End handling and position feedback.
  Multiple strips initialize independently and refresh without accumulating nodes.
- **Delivery:** tiny build-time Liquid aliases give the CSS and three changed
  controllers distinct filenames. Published bytes are checked against their
  maintained source; no extra runtime requests or copied implementations.
  The separately versioned Travel asset is unchanged.

Travel/Volunteering source changes are **decoding="async" only** on existing
carousel images. There are no media URL, prose, front-matter or layout changes to
these pages. `courses.md`, course data, all post sources, Photography data,
`_config.yml`, Firebase/runtime/rules, native search and theme files are unchanged.

## Before/after previews

These are **controlled media fixtures**, using the real baseline/candidate HTML,
CSS, controllers, Inter and GLightbox 3.3.1. SVGs exercise portrait, landscape,
very tall and very wide proportions. They do not represent restored photographs.
The 110-record camera fixture is a separate temporary Jekyll build; values such
as Sony a7R III/1/800s/f/4/ISO100/35mm are labeled test inputs, never production
facts. Blog comparisons deliberately alternate existing major/minor records in
both previews, without changing their text or production ordering.

| View | Before/after |
| --- | --- |
| Desktop compact summary | [Comparison](previews/comparison-summary-1440.jpg) |
| Mobile compact summary | [Comparison](previews/comparison-summary-390.jpg) |
| Enlarged viewer | [Comparison](previews/comparison-viewer-1440.jpg) |
| Long mobile metadata | [Comparison](previews/comparison-long-metadata-390.jpg), [settings after scrolling](previews/after-long-settings-390.png) |
| Full desktop collage | [Before](previews/before-photography-1440.jpg) · [After](previews/after-photography-1440.jpg) |
| Narrow 320px collage | [Before](previews/before-photography-320.jpg) · [After](previews/after-photography-320.jpg) |
| Alternating Timeline, 390px | [Comparison](previews/comparison-blog-390.jpg) |
| Alternating Timeline, 820px | [Comparison](previews/comparison-blog-820.jpg) |
| Alternating Timeline, 1440px | [Comparison](previews/comparison-blog-1440.jpg) |
| Mobile carousel, genuine initial position | [Comparison](previews/comparison-carousel-390.jpg) |
| Desktop carousel, genuine initial position | [Comparison](previews/comparison-carousel-1440.jpg) |

[All matched originals](previews/) include 320/390/820/1440px views and
[computed styles](previews/computed.json). Viewer title is 18px/25.2px;
description 15px/24px; facts 14px/21px. Mobile text is #f5f5f5 over the dark
caption; desktop title #222/body #666 over white. Timeline major title is
18px/24.3px, minor 16px/22.4px, description 15px/24px; dates/location are
14px/20.3px on mobile and 13px/18.85px on desktop. Media slots/gutters are
80px/12px mobile and 96px/16px desktop, with minor photos 24px smaller.

## Validation

| Check | Result |
| --- | --- |
| Production, running localhost Jekyll, Pages-publication-plugin builds | Passed; Jekyll 4.4.1, frozen lockfiles, pinned remote theme |
| Public surface | 667 normal + 668 Pages + 667 localhost assertions; exactly 82 routes; no internal output/navigation/search or sitemap-probe entries; current scoped assets |
| Build parity | 580 normal/Pages + 580 normal/localhost preservation assertions |
| Merged baseline content preservation | 700 assertions: 64 Blog entries, 9 Travel articles, 30 photo records, routes, article bodies, media/links, SEO and protected source bytes |
| Native search/navigation/Travel UI | 557 production + 557 served-localhost assertions: all 135 queries, 90 course-result code/title clicks, 45 course destinations, retry/cache/batching/history/menu and sharing cases |
| Consolidated components | 960 assertions; 12 widths, 8 orientation profiles; 30/60/110-record galleries, all 32 camera combinations, sorting/filtering, multiple carousels |
| Added empty/failed media + real thumbnail activation | 16 assertions; actual Liquid absent-image branches, missing-photo loading recovery/Next/Escape, reduced motion, keyboard link activation/Back |
| Carousel native-input/boundary stress | 70 assertions; 1/2/5/12/150/180 sources, wheel + Chromium touch input, held-pointer release/cancel, repeated refresh, orientation selection, delayed/failed resources |
| Android-UA/touch gallery matrix | 100 assertions; 12 widths + 8 orientations, computed caption typography, 44px visible controls, modal focus and return |
| Retained Blog and navigation/sharing suites | 110 + 88 assertions; actual current asset URLs, approved grid-aware visibility checks; native dialogs controlled |
| Enforced Firebase rules | 17 passed with official local RTDB/Auth emulators |
| Actual SDK + anonymous Travel UI | 85 passed with real local Anonymous Auth/RTDB SDKs and enforced rules |
| WebSocket ACK loss/retry/opposite intents | 18 passed with actual SDK transport and enforced local rules |
| Isolated Firebase UI/error cases | 11 passed |
| Unrelated page appearance | 27 matched geometry/style/pixel comparisons at 390/820/1440px |
| Syntax/diff checks | Node syntax checks for maintained/compiled controllers and git diff whitespace checks passed |

Widths: **320, 375, 390, 430, 600, 601, 768, 820, 1024, 1280, 1440, 1920**.
Orientation profiles: 375×812 / 812×375; 390×844 / 844×390;
768×1024 / 1024×768; 820×1180 / 1180×820.
Unrelated comparisons cover Homepage, Academics, Coursework, Travel index, Media,
Hobbies, two representative posts and the Travel outline. Shared navigation/search
chrome was excluded from pixel comparison and tested separately; native video and
select painting was masked consistently. Their DOM/styles/interaction remain tested.

All 80 standard search identities/URLs remain; **79 records are byte-identical**.
The Photography snippet naturally changes with the revised instruction and full
accessible description. No search generator or result destinations were changed.
Internal docs/results remain repository-only under existing exclusions. Production
has no sitemap; the Pages profile enables a test-only sitemap probe.

The Pages profile reproduces publication plugins (including optional front matter)
using Jekyll 4.4.1, rather than claiming to reproduce the entire legacy GitHub Pages
dependency stack. CI runs the actual three-profile public-surface workflow.

Machine-readable evidence is in [results](results/). Source-content checks use a merged archive, rather than comparing the candidate
to itself. Fixture file hashes identify the exact font/library inputs. The retained suites use only
external test adapters to replace historical asset URLs and the retired split-write
mock with the existing receipt-aware fixture; search/controllers are not mocked.
Permission-denied warnings in the rules log are expected asserted rejection cases;
log trailing whitespace is normalized. All production Firebase/auth/analytics requests were blocked. Nothing here certifies
remote rules or modifies real visitor records.

## Performance

See [the matched seven-repetition measurements](performance.md). Timings include
real component readiness/control behavior, not the earlier unvalidated 2ms fixture.
Image URL reuse means clone removal does not imply equivalent network savings.

## Limitations and remaining issues

- Chromium 154 on headless Linux, Playwright 1.62.0. Touch, orientations, Android UA
  and reduced motion are browser emulations. Physical iOS Safari/Android, Firefox,
  Edge, desktop browser-chrome 200% zoom and screen-reader/device feel are untested.
  This is not a WCAG certification or production Core Web Vitals claim.
- Original media are absent locally. All six representative production photo,
  carousel and Blog image probes returned 404 ([paths](results/real-media-probes.json)).
  The owner must review with real photographs. Do not infer source dimensions,
  EXIF, decoded image/GPU memory, contrast against every actual photograph or R2
  performance from synthetic fixtures. Intrinsic dimensions, responsive sources and
  selective lazy loading are deferred; original images remain eager/async-decoded.
- Very wide/short masonry images deliberately omit the tiny overlay; normal
  activation still exposes every supplied field. Long titles use one-line visual
  truncation in the summary and full text in the accessible description/viewer.
- Bounded native buffers are not an endless physical scroll range. A sufficiently
  long single fling can reach an edge before idle wrapping. No correction fights
  active pointer contact or native momentum. Equivalent boundary positions can
  round fractional geometry by <1 CSS pixel; behavioral tests compare content
  identity/geometry as well as exact pixels where integral.
- Historical generic/copied labels, dates, camera bodies, placeholder posts,
  prefix-like media URLs and the photograph73/photography73 mismatch are preserved.
  Editorial corrections and R2/SEO work remain future owner-directed tasks.
- Source/evidence changes are local until the owner merges and Pages deploys. Old
  open HTML may retain old assets until reload/expiry. New HTML loads the distinct
  current component filenames once; Travel retains its PR #20 pathname.

## Review and rollback

[Exact changed-file manifest](changed-files.txt); the PR's Files changed tab is the
full source/binary diff. Build/test reproduction commands are in
[`_tests/README.md`](../../_tests/README.md), with component rationale in
[`docs/visual-media.md`](../../docs/visual-media.md).

Review locally, especially restored real-image behavior and physical-device touch.
Do not merge automatically. To roll back after any future merge, revert this PR's
single implementation commit through a review PR, rebuild and rerun the public
surface/82-route checks. Revert HTML, CSS and JS together; no database deployment,
record reset, migration or Firebase rule rollback is required. Preserve PRs #19/#20.
