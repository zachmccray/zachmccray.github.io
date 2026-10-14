# Performance and core reliability

This work starts from merged `gh-pages` `19973eb`. It addresses audit A1/A2/A3,
B1/B4/B6/B7 and the small A6 native sharing-title correction. It preserves the
approved visual system, all 82 HTML routes, all 80 standard search records,
45 course destinations, article/media content and existing Firebase identifiers.

## Search integration and upgrade boundary

The remote theme is pinned to `9a7e4031a83c115bffbd6b053f319ea74c66859a`,
the revision producing the audited runtime, not the older 0.10.1 gem. GLightbox is
pinned to the already tested 3.3.1; this is not a theme or lightbox upgrade.

`_includes/head.html` follows that pinned theme's 53-line head, changing only
script scheduling. Theme JavaScript is deferred. Lunr and the standard
`assets/js/search-data.json` load concurrently on first search focus/input,
rather than building an unused index on every page visit. No collection indexing,
custom generator, global XHR interception or framework is introduced.

Upstream keeps `initSearch` and `searchLoaded` private and exposes no readiness or
retry API. Consequently `assets/js/just-the-docs.js` is a documented, minimal fork
of the exact pinned source. Only `initSearch` delegates loading to `search.js`,
the batching generation counter advances only on changed queries,
and the three-line forced page-scroll workaround is removed because the approved
search input is already in a persistent header. The remaining native builder,
query/ranking logic, result HTML, highlighting and keyboard/navigation handlers
remain upstream. The batching guard keeps unchanged key/focus events from
canceling later results, including the adapter's input/keyup replay. The redundant site-ui scroll compensation is removed.
The preservation test guards this boundary against the baseline compiled asset;
retain this check and review these focused differences on future theme upgrades.
Upstream's MIT notice is in `docs/just-the-docs-license.txt`.

The lifecycle adapter keeps the input editable, replays early/pasted queries,
shows loading and error/retry feedback, times out requests after 15 seconds,
and exposes combobox expansion, result selection and a polite status region.
The native results list becomes the listbox; loading/error/retry stays in a named
region outside it. Arrow keys/Enter choose results, while Tab leaves suggestions,
following the combobox focus pattern. Escape dismisses retry feedback in one press.
Click dismissal uses the original event path so replacing feedback does not
accidentally close a mobile menu during retry.
It restores a session index only after fetching and comparing the exact retrieved
JSON, builder/tokenizer definitions, cache schema and Lunr version. Shape checks
and native Index.load catch corrupt entries. Changed IDs/data rebuild. Storage
failure or quota exhaustion does not disable search. The roughly 300KB session
entry is local storage only; no larger generated/network index is shipped.
Cold first use still builds the index; on-demand loading moves that cost to a
visitor who actually uses search. Session reuse reduces subsequent construction
work, while preserving current data and all destination associations.

## Firebase safety and release blocker

Owner-supplied rules deny the original parent like transaction and expose all user
records through root `.read: true`. They also lack count/marker transition validation.
The parent transaction has been removed. Likes now read only the count and current
user's marker; mutations are paused until an approved private rules/backend solution
is ready. **This is not a completed like fix; PR #19 remains release-blocked.**

See [Travel like investigation and concrete rules/backend options](travel-like-reliability.md)
for the root cause, local enforcement tests, historical-data limitations, security,
hosting/cost and required approvals. No production rules/data/infrastructure changed.

Share logging retains one multi-path update at `shares/<existing-post-id>` with
ServerValue.increment(1), updating the existing marker and count atomically. Logging
remains independent of the completed native/clipboard action. Native cancellation
is normal feedback and logs no share. No exactly-once transport claim is made.

## Resource loading and intentionally deferred work

Font Awesome 6.5.0 loads only on the Travel index, the only active page using its
icons. Other pages avoid its 102,526-byte decoded stylesheet (21,865 bytes estimated
gzip); actual CDN compression/headers were unavailable. Inter's same four weights
and display=swap load directly from the head, with preconnect, instead of discovery
through custom.css @import. No font substitution or actual WOFF2 byte-saving claim
is made. Deferred/on-demand scripts shorten the render-blocking chain.

No real referenced photographs are available to establish intrinsic dimensions.
Fixture dimensions are never written into source. Broad lazy loading is deferred:
the audit's photo fixtures showed worse LCP/CLS when above-fold images were made
lazy without valid dimensions. Existing asynchronous Photography decoding remains.
Carousel duplication/centering changes, Photography overlay redesign and Timeline
spacing belong to the next coherent visual-interaction PR. This PR preserves them.

## Validation and rollback

Owner-runnable checks are documented in `_tests/README.md`. Production/local builds,
all route/SEO/content/search comparisons, native served search, 135 course queries,
90 destination clicks, keyboard/history, 12 widths/eight orientation profiles,
Firebase fixtures, Gallery/Blog/Travel/carousel regressions and controlled visual
comparisons are summarized in `_review/core-reliability/report.md` and its evidence.
Linux Chromium is the available browser. Physical iOS/Android, Safari, Firefox,
Edge, screen readers and genuine browser 200% zoom remain unverified. Cached
external libraries/fonts and synthetic absent media are controlled fixtures;
local timings are laboratory results, not live-production Core Web Vitals.

Before merge, discard the development branch/PR to roll back. After an approved
merge, revert its merge commit through a separate reviewed PR and rebuild Pages.
No data migration needs reversing. Reverting can reintroduce the old split-write
counter failure, so keep the safe counter changes if rolling back only search/loading.
Session entries are versioned and are ignored by the old runtime; no storage/data
purge is required.
