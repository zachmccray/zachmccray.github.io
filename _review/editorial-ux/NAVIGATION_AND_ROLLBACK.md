# Editorial UI/UX refinements

## Baseline search correction (separate from visual work)

Baseline: `34222340f367e4222c3a38212425e6bebe399467` on `gh-pages`.
Compared its generated standard search index with `d85ea557` before the owner's
Hobbies/Academics edits. Hobbies previously emitted six H2 topic records plus its
page record; it now emits four H2 group records plus its page record: 80 → 78 total.
The standard pinned-theme generator indexes H1/H2 by default. H3/H4 topic, gear,
book and language text remains in the appropriate parent group's content. No
course destination changed; all 45 remain. Academics snippets also reflect the
owner's separate paragraph edit; that is not responsible for the record count.

Hiking, band, Piano, language, volleyball and Mixology results have lost the old
topic-specific result fragments, but their old HTML anchors remain valid. Keep
the intentional semantic hierarchy and standard generator. Real search checks
must confirm that group destinations reveal the equipment/book lists on arrival,
including same-page searches; directly linked historical anchors must still work.
Do not introduce a copied search generator to reproduce a historical record count.

`_tests/search-destinations.json` freezes all 78 intended document/title/URL
identities, rather than a bare count or the generator's numeric keys. Publication
and parity checks reject missing, duplicate or substituted destinations and still
verify all course fragments against actual generated headings. Intended content
changes must explicitly review this contract. No failing assertion is skipped.

## Approved implementation

- Bare 18px chevrons retain 44px buttons, visible focus and a quiet position
  indicator. A click advances one original; a 350ms hold scrolls at bounded speed.
  Reduced motion uses discrete steps at least 500ms apart. Release, cancellation,
  capture loss, blur, resize and hidden tabs stop the hold.
- Carousel images open pinned GLightbox on demand. A registry keyed by original
  slot, not URL, maps inert buffer copies without extra keyboard stops or slides.
  Native scrolling, mouse dragging and bounded buffers remain. One cached library
  promise supports retries, loading cancellation and competing strip intents.
  Library/CSS failure leaves the existing original-file URL available.
- Minor Timeline records retain real 48px desktop / 40px mobile thumbnail columns,
  15px titles, full 15px/24px descriptions and wrapping metadata. Major titles and
  thumbnails remain linked. Filters, comparators and history logic are unchanged.
- Photography uses three-column natural-ratio masonry and 6px gaps. The flat inset
  is 4px from its tile with 4px/6px padding: no gradient, border, shadow or animation.
  Title/secondary text is 13px/12px desktop, 14px/13px mobile. Only complete lines
  fitting within 40% of the image appear. Very short panoramas use the full viewer
  for details. All supplied facts remain accessible there and in the original
  description. Panoramas retain a 24px activation area; missing files retain 44px
  targets. Source ratios are unchanged. Normal instructions are assistive-only;
  viewer-failure feedback remains visible.
- Hobbies retains every word, heading, language sample, link and old ID. Hiking
  prose stays intact; short outdoor topics form a compact status group; independent
  Music/language topics share responsive columns. Small phones stack the short
  topics consistently. Five secondary lists progressively collapse. All 18 items
  remain visible without JS and in print; narratives are always readable. Native
  search arrivals and old deep links reveal relevant lists.
- Media retains all four links and unfinished text in compact category rows.
  Hobbies, Media and Volunteering share small left-aligned wrapping navigation.
  Short organization labels retain full accessible names. Volunteering's narrative,
  figures, footnotes and media order are unchanged.

Modal focus containment, inactive-slide inertness, Escape, missing-image feedback
and stable focus return now share a small adapter. No new production library,
theme fork, backend or visitor authentication step is introduced.

## Reusable article navigation

`_includes/section-navigation.html` serves the shared post/content layouts. It
links to authored H2 IDs outside indexed `page.content`. Day labels come from actual
Day headings, with full accessible names. No body IDs or days are guessed; duplicate
targets are not emitted. Entities are escaped once. Markdown H2 IDs still come
from the existing renderer. HTML headings without an ID are omitted.

Two useful sections are required. Short/empty Blog bodies and the single-section
Washington article have no empty list. The Southwest itinerary has eight day links.
More than twelve sections use a small native disclosure. Native details containing
a fragment target are revealed. Ordinary links remain functional without JS.

Seven copied placeholder Travel outlines opt out with `section_navigation: false`;
remove that flag when genuine sections are authored. No content is rewritten. The
five copied Washington labels/dates remain legacy metadata, not newly verified facts.
Other content pages can opt in with `section_navigation: true`. Optional
`section_navigation_labels` maps existing IDs to short labels while preserving full
heading names in `aria-label`, as on Volunteering.

The fragment helper excludes the theme's skip-to-main target and changes focus
synchronously. An early regression exposed deferred focus stealing search focus;
the original 557-check suite detected it and passes with the correction. There is
no `pushState`, `replaceState` or global scroll-restoration override. BFCache keeps
its DOM; reconstructed history reveals targets before native scroll restoration.

## Independently reversible presentation

The single marked **Travel refinements** CSS block changes only:

| Property | Baseline → approved |
| --- | --- |
| Card border | `#dedee5` → `#e4e4ea` |
| Date bottom margin | `8px` → `6px` |
| Excerpt bottom margin | `12px` → `10px` |
| Counter digits | proportional → tabular |
| Enabled action hover border | visible neutral → transparent |
| Enabled action press background | existing treatment → `#ece9f8` |
| Cover hover | also underlines its existing title |
| Cover focus outline offset | `3px` → `-3px`, inside the cover |

Fonts, grid/padding, image ratios, wording, links, receipts and confirmed likes
are unchanged. Removing the block restores exact baseline Travel pixels in the
controlled desktop/mobile comparison. Press feedback never implies a Firebase write.

Photography's adjacent CSS variables are `--gallery-column-width: 220px` and
`--gallery-column-count: 3`. Use `170px` / `4` to restore the previous cap without
changing metadata styling. Mobile two/one-column rules remain. Update geometry
acceptance expectations alongside an intentionally changed cap.

Publish CSS/JS changes through a new current pathname and matching publication
guard. Keep old entry points for cached HTML. For full rollback, prepare a rollback
PR around the feature commits, retain the baseline search correction, and retain
compatibility assets while cached HTML can reference them. Do not revert Firebase
rules, counters, data or its unchanged `travel-atomic-receipts-1.js` client. No
Firebase deployment action accompanies this PR.

## Evidence and remaining gates

The excluded `_review/editorial-ux/` report contains exact files, source diff,
desktop/mobile PNGs, computed values, performance samples and results. Images are
labeled synthetic fixtures. Gallery stress uses 110 records and all 32 optional
camera combinations, including long/absent metadata. Production facts are untouched.

Chromium and zero axe violations do not certify physical iOS/Android, screen readers,
native sharing dialogs or browser-chrome zoom. Checks include 200%/400% equivalent
reflow viewports. Complete owner/device review and required CI gates before merge.
CI also exercises Firefox/WebKit and demo Firebase rules. Blocked local downloads
must be reported as unrun, never replaced with mock permission certification.
