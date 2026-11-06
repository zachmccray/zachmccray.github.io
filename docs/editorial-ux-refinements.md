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
