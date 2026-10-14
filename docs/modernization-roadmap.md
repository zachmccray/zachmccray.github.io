# Website modernization roadmap

The workflow is implementation, testing and one coherent review PR per request.
Routine technical decisions do not require a separate proposal. Production merges
and new substantive feature directions remain subject to owner review.

- Completed: URLs/navigation/SEO corrections; CSS organization; website-wide
  typography/spacing/semantic roles; Homepage/Academics, Coursework and 64 posts;
  remaining content/Travel articles; approved Photography collage, Blog/Travel/Media
  components; initial UI/UX polish (PRs #13–18 and preceding maintenance).
- Current review: PR #19 performance/core reliability—on-demand native search,
  readiness/error/retry and exact-data session reuse; private, anonymous one-click
  likes/unlikes and receipt-enforced share logging; mobile focus exit; direct fonts/
  scoped icons; pinned dependencies and portable enforced/browser regressions.
  Option A is implemented. Owner publication of the complete private rules and
  coordinated Pages deployment remain required before normal production use.
  See `_firebase/README.md`; no production writes, billing changes or migrations.
  Finish owner review/activation before the next visual work.
- Next image and visual-interaction PR: less intrusive Photography hover/focus
  summary with full existing metadata in the viewer; mobile/touch/keyboard parity;
  Blog Timeline thumbnail gutters and vertical rhythm, including the known major
  thumbnail link issue; carousel copy count, readiness/centering, responsive geometry
  and discoverable controls. Preserve image order/paths, original facts and media
  interactions. Use actual asset dimensions when available; maintain native ratios
  and appropriate above-fold priority. Keep these approved improvements together
  rather than multiplying planning subphases.
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
