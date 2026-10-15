# Visual/media components (PR #21)

This document is internal. `_config.yml` excludes it and all other maintainer
documents from site output, navigation, native search and the sitemap probe.

## Photography

Keep `_data/photography.yml` as the single ordered source of photo facts. The tile
include supplies an accessible image link, a small aria-hidden visual summary and
the full accessible description. GLightbox receives that same description on
slide load, retaining both the original label and separate description. The title
is escaped before being passed to the library. No parallel gallery DOM is built.

The CSS columns retain the previous 6px gaps, natural ratios, four-column cap,
two-column mobile layout and one column at 360px and below. Rendered-height
observation hides the secondary summary below 100px and the entire summary below
80px. These are presentation thresholds, not invented intrinsic dimensions.
Full metadata is always available through the normal viewer, touch included.

Caption text is 15px/1.6, its title 18px/1.4 and facts 14px/1.5. The caption scrolls
within min(40dvh, 320px), with a vh fallback. Focus cycles through visible current
slide controls and caption; background is inert while open, Escape closes and
focus returns without scrolling. The library still owns loading, zoom, swipe,
navigation and effects. Reduced-motion overrides its mobile slide effect as well.
Unavailable originals keep their references; the viewer reports the failure.

## Blog Timeline

Major and minor entries share one grid: desktop media slot 96px/gutter 16px;
mobile slot 80px/gutter 12px. Minor images are 72px/56px, aligned against the text
side of the shared slot. Titles and rail-marker centers align; rows retain 24px
separation. Filtering uses `hidden` instead of overriding the grid display mode.
Only major thumbnails gain links, matching their existing title destinations.
Failed and absent images retain a stable neutral slot without replacement URLs.

## Native carousels

`assets/js/infinite-scroll.js` owns one instance per existing strip in a WeakMap.
Repeated `ImageCarousels.init()` refreshes geometry without adding controls,
observers or listeners. Original items retain DOM order and IDs. There are no new
dependencies, scroll-snap rules or per-scroll geometry measurements.

The shared responsive image frame is clamp(180px, 30vw, 280px) high; auto image
width and contain fitting preserve natural ratios. A pending image reserves a
temporary 180px-wide frame until actual geometry arrives. Missing images retain
that neutral frame and their alt text/reference. Layout observes container and
original item sizes, preserves the selected image/fraction and uses the previous
viewport geometry across resize. Collections remain finite while images load.

After readiness, at least three images and a source period over two viewports
enable looping. Each end buffer covers two viewports, copying each original at
most once per side: at most 3N total images, usually N plus a few buffer items.
Short collections stay finite; fitting collections are centered without controls.
Finite overflow includes end padding so its first and last images can be centered.
Copies have no IDs, are inert/aria-hidden and cannot add keyboard stops.

Native touch/trackpad/wheel scrolling runs freely. Equivalent-position wrapping
happens at scrollend or after 180ms quiet, never while pointer contact remains.
Document-level release/cancel and window blur prevent a stuck held-pointer state.
Fractional image widths can round the equivalent position by less than one CSS
pixel. There is no instantaneous correction during an active fling; a very long
gesture may reach the finite physical buffer before it settles and wraps. This
is the deliberate trade-off for bounded DOM and native momentum, rather than
intercepting gestures or creating unbounded copies. Real-device feel still needs
owner validation. Arrow/Home/End keys and 44px Previous/Next buttons select photos;
the polite position status updates at rest rather than every scroll event.

## Delivery and preservation

Four tiny Liquid entry points publish the exact maintained CSS/JS under new asset
names: `custom-visual-media-1.css`, `photography-portfolio-1.js`,
`blog-controls-2.js`, `image-carousel-1.js`. They include the source at build time;
there are no duplicated implementations or runtime extra fetches. Update the
entry-point name and HTML reference together for a future incompatible release.
Existing HTML may retain old references until reload/cache expiry; new HTML
cannot mix the previous component code with the new styles. The independently
versioned Travel client is unchanged. Publication tests verify compiled bytes,
single/deferred/scoped loading and all 82 public routes in three build profiles.

The standard theme search generator is unchanged. All 80 document identities and
destinations remain; 79 records are byte-identical. Photography's one natural
snippet changes with its revised instructions and newly accessible description.
All 45 course fragments, SEO, article bodies, photo facts and Firebase code/rules
remain unchanged. See the PR evidence for the byte/content comparisons.

## Deferred work and rollback

No original image files are present locally; representative production image
requests return 404. Dimensions, EXIF, responsive sources and selective lazy
loading therefore remain deferred. `decoding="async"` is safe; the source images
remain eager to establish reliable geometry. Controlled SVG proportions and
explicitly labeled optional camera values exist only in temporary test builds.
Synthetic timing is not production Core Web Vitals or decoded-image/GPU memory.

Rollback: revert the single PR implementation commit through a review PR against
`gh-pages`, rebuild and check the 82-route/public-surface manifest. That restores
the matching previous HTML, styles and controllers together. No data migration,
counter reset, Firebase deployment or rule rollback is involved. Do not revert
the private database rules or PR #20's exclusions/versioned Travel client.
