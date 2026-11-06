Refine the existing minimalist presentation with bare carousel controls and accessible enlargement, compact thumbnail-based minor Blog entries, three-column Photography with flat metadata panels, conservative Travel styling, and editorial Hobbies/Media/Volunteering organization. Shared article navigation uses existing headings and reveals supporting details without changing routes, content or Firebase behavior.

The separate baseline commit replaces the obsolete 80-record assertion with an explicit 78-destination contract following the owner's Hobbies grouping. All 82 routes, 45 course targets, original posts/photo facts and protected Firebase/search/history sources are preserved.

Review [before/after images, exact files, measurements, tests and rollback boundaries](https://github.com/zachmccray/zachmccray.github.io/blob/design/editorial-ux-refinements/_review/editorial-ux/README.md) and [navigation behavior](https://github.com/zachmccray/zachmccray.github.io/blob/design/editorial-ux-refinements/docs/editorial-ux-refinements.md).

Validation: production/Pages-plugin/localhost builds and parity, full real search/navigation, browser/axe, native history, gallery/carousel fixtures, content preservation and controlled pixel checks pass locally in Chromium. Firefox/WebKit and enforced Firebase emulator downloads are blocked by the cloud egress policy; required hosted CI and owner local/device checks must pass before merge. No production Firebase changes or deployments were made.

Keep this PR open and unmerged for owner review.
