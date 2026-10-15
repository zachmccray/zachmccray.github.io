# Website modernization roadmap

The workflow is implementation, testing and one coherent review PR per request.
Routine technical decisions do not require a separate proposal. Production merges
and new substantive feature directions remain subject to owner review.

- Completed: URLs/navigation/SEO corrections; CSS organization; website-wide
  typography/spacing/semantic roles; Homepage/Academics, Coursework and 64 posts;
  remaining content/Travel articles; approved Photography collage, Blog/Travel/Media
  components; initial UI/UX polish (PRs #13–18 and preceding maintenance).
- Completed: PR #19 performance/core reliability—on-demand native search,
  readiness/error/retry and exact-data session reuse; private, anonymous one-click
  likes/unlikes and receipt-enforced share logging; mobile focus exit; direct fonts/
  scoped icons; pinned dependencies and portable enforced/browser regressions.
  The owner published the private rules and merged/deployed this work. PR #20
  repaired stale Travel asset delivery and excluded maintainer documents from
  Pages publication, navigation and search. Keep its production-parity checks.
- Current PR #21, awaiting owner review: less intrusive Photography hover/focus
  summary with full existing metadata in the viewer; mobile/touch/keyboard parity;
  Blog Timeline thumbnail gutters and vertical rhythm, including the known major
  thumbnail link issue; carousel copy count, readiness/centering, responsive geometry
  and discoverable controls. Bounded viewport buffers replace six complete image
  sets; small collections remain finite. Retain natural ratios, source order,
  metadata, image paths and PR #19/#20 behavior. Camera/exposure details belong in
  the enlarged viewer; ordinary touch opens it directly. See `visual-media.md`
  and `_review/visual-media/README.md` for implementation, evidence and limitations.
  Real intrinsic dimensions and selective loading remain deferred until actual
  assets can be verified. No guessed dimensions or synthetic production metadata.
- Later editorial/readiness and discovery work: owner-provided corrections for
  placeholder Blog bodies/descriptions, copied Travel text and legacy Washington
  labels/dates, generic photo alt/descriptive labels and prefix-shaped image URLs.
  Do not fabricate dates, dimensions, destinations, EXIF or replacement content.
  Collection search must be selective rather than indexing every unfinished post.
- Later UI/UX work: prioritize confirmed accessibility/usability defects, then
  evaluate useful discovery/navigation components, cross-device/screen-reader
  testing, theme preferences/dark mode and performance with real restored media.
  Avoid optional complexity or unnecessary redesign of approved pages.
- Separate future projects: R2 delivery/responsive image integration with real asset
  metadata, deployed Firebase rules/backend changes if needed, and a dedicated SEO
  audit. Preserve current routes and SEO until justified improvements are reviewed.

Validate intentional visual improvements against the approved design, not pixel
identity with superseded designs. For unrelated pages continue content, route,
functionality and controlled visual preservation checks. Never merge automatically.
