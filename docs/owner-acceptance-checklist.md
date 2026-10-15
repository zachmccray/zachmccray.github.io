# Owner acceptance walkthrough

Use this for a normal visitor experience after reviewing/merging the framework PR,
then record the remaining issues for one owner-feedback PR. This document is
maintainer-only and excluded from the public website, navigation and search.

Before merging, you can use the same walkthrough on the development branch with
your Jekyll server. After merging, wait for the Pages deployment to finish and
reload an ordinary browser tab. Compare a fresh/private tab if delivery looks old.
Existing open pages may retain old HTML until reload/cache expiry; this alone is
not evidence of a Firebase problem. Do not change database rules or records to
troubleshoot a browser problem.

## 1. First impression and everyday navigation

Use your usual desktop browser first, without DevTools. Visit About Me, Academics,
Coursework, Blog, Travel, Photography, Volunteering, Hobbies and Media.

- Can you tell where you are, and can you find the next page without guessing?
- Do the typography, spacing, content width and controls feel coherent? Note
  specific pages/roles that feel cramped, oversized or visually inconsistent.
- Open My Courses from Academics. Academics should remain marked as its parent
  section. Blog/Travel should remain marked while reading their individual pages.
- Follow a major Blog title and its thumbnail: both should reach the same post.
  Minor events should remain unlinked. Choose a year and sort, open a post, then
  use Back/Forward: the selected year, visible entries and ordering should agree.
- Open a Travel card, scroll its article and return with Back. Does your original
  position in the index feel preserved? Refresh an article and open its direct URL.
- Try existing external links on Hobbies/Media/Volunteering. Some intentionally
  open a new tab. Check that this is understandable rather than surprising.

Do not judge placeholder article text or absent photographs as new framework bugs.
Do record any newly broken route, changed image reference or malformed layout.

## 2. Search and anchors

Search for `EECS 101`, `ECON 144` and `Calculus I`, on both desktop and phone.

- Do results feel prompt, readable and easy to select? Does clicking land on the
  correct course with its heading visible below the sticky header?
- Try a different query, clear it and search again. Navigate away and back. Use
  the arrow keys and Enter to select results; Escape should dismiss them.
- Tab from the search field into the results region; Page Down/Up should scroll
  that region without unexpectedly moving the article. Shift+Tab returns to the
  input. On mobile, search results use the full header width; Escape returns to
  the navigation menu, then another Escape closes the menu.
- Open `/courses.html#course-econ144` directly, refresh, then use Back/Forward.
- If something fails, capture the query, expected course and actual destination
  URL, including its fragment. Distinguish no results from a wrong destination.

## 3. Real phone/tablet and zoom

Use a physical phone, ideally iOS Safari and Android Chrome. Try portrait and
landscape, a narrow phone and your normal desktop. Also test Firefox/Edge/Safari
where you have them; CI's Linux engines do not replace these real-device checks.

- Open/close the mobile menu on a long page. Search, dismiss results and navigate.
  Menu links and controls should remain usable in short landscape viewports.
- Scroll long articles, rotate while a carousel is selected and return to an
  earlier page. Look for sideways scrolling, clipped text and unexpected jumps.
- Use the browser's actual 200% and 400% zoom. Can you read/reach everything using
  vertical scrolling? Check narrow controls, course headings, the menu and viewer.
- If an issue is device-specific, include browser/version, orientation, zoom and
  screenshot. Avoid substituting a desktop mobile emulator for this step.

## 4. Photography, carousels and missing media

The real photographs are still intentionally absent. Current production 404s are
known; automated visual tests use labeled synthetic proportions. Revisit this
section when real assets are supplied. Do not change image paths or invent metadata.

- The gallery should retain dense masonry, natural ratios and compact gaps.
  Hover/focus shows a small tile-contained summary; normal tap opens full details.
- In the viewer, read the full available fields; scroll long metadata. Try Next,
  Previous, keyboard arrows, touch swipe, Escape and the close control. Focus
  should return to the original photo. Background/offscreen slides should not be
  reachable by Tab or screen-reader navigation while the viewer is open.
- Very short photos may omit the summary; normal activation must still expose
  all provided details. Missing originals should report unavailable and allow
  navigation/closing, without an endless loading spinner.
- On Volunteering and Travel articles, try horizontal wheel/trackpad, touch swipe,
  arrow/Home/End keys and Previous/Next controls. Is the current photo preserved
  on resize/orientation? Are independent strips independent?
- Looping uses finite edge buffers and wraps when scrolling settles. An unusually
  long uninterrupted fling may hit a physical edge before wrapping. Report visible
  discontinuities or poor touch feel; the emulated tests cannot settle that judgment.
- Optional failure check: block GLightbox's CDN request and reload Photography.
  Original-file links should remain, with native Photo details disclosures. If
  JavaScript is disabled entirely, navigation links and content remain available;
  unavailable search/actions are hidden and photo facts remain readable.

## 5. Keyboard and assistive technology

Use only Tab, Shift+Tab, Enter, Space, arrows and Escape for a few minutes.

- The skip link should be reachable first; activation moves into the content.
- Can you see focus on navigation, anchors, course/search controls, cards, images
  and carousel controls? Is the order understandable?
- The mobile menu is a disclosure, not a keyboard trap. Escape returns focus to
  Menu; Tab can leave it and dismiss it. The lightbox is a modal and must contain
  focus until closed. Check both directions with Shift+Tab.
- If available, use VoiceOver, NVDA or TalkBack: listen to page/section context,
  course headings, search results/feedback, photo details and carousel names.
  Only the current lightbox slide should be exposed; its details are scrollable.
- Enable the OS reduced-motion preference and retry gallery/carousel navigation.

Automated axe scans and three browser engines are evidence, not a WCAG certificate.
Screen-reader phrasing, real touch and personal comfort still need your assessment.

## 6. Public Travel likes/sharing

After deployment, test as an ordinary visitor; no account, personal information,
verification or setup prompt should appear. Agents' automated tests use emulators
only; this owner walkthrough is the final real-browser acceptance check.

- One Like click, then one Unlike click, should finish clearly. Check a fresh tab
  and an existing ordinary profile. Avoid repeatedly clicking to diagnose counters.
- The heart's shape and color should indicate liked state. Like/Share icons should
  still be visible if external icon-font/CDN access is blocked.
- Try native sharing; voluntarily canceling it is normal. Try copy-link fallback
  in a supported browser. Analytics logging failure must not prevent the share/copy.
- Historical inconsistent records may need separate owner review. Do not reset
  counts, modify user markers or loosen private rules. Report the article URL,
  visible message and console error code if available; never include user records,
  credentials or private database exports.

## 7. Issue severity and reporting

| Severity | Meaning | Examples |
| --- | --- | --- |
| P0 — urgent | Privacy/data integrity or security risk | Private records readable; unauthorized writes; counter corruption |
| P1 — blocking | An ordinary visitor cannot complete a core task | Navigation/search broken; normal Like fails everywhere; viewer cannot close; unusable mobile menu |
| P2 — important | A significant issue with a workable alternative | A particular viewport clips a control; focus visibility/history problem on one browser |
| P3 — refinement | Preference or minor polish | Spacing, hierarchy, wording of UI feedback or subtle interaction feel |
| Editorial / known media | Deferred owner content rather than framework | Placeholder copy, copied facts/labels, intentional missing photographs |

For P0/P1, stop the affected interaction and report promptly. For other issues,
batch observations after normal use instead of trying to design a solution first.

Copy this template for each issue:

```text
Title:
Severity / editorial:
Page URL (include #fragment if relevant):
Device / OS / browser + version:
Viewport or screen size / orientation / zoom:
Starting state (fresh tab, Back/Forward, selected year/sort, etc.):
Steps:
1.
2.
Expected result:
Actual result:
Reproduces consistently or intermittently:
Screenshot / short recording:
Optional console error code (no credentials or user records):
Optional design preference / why it feels confusing:
```

Capture enough surrounding UI to show the location and crop/redact personal tab,
account and browser data. For motion/history problems, a short screen recording
plus numbered steps is more useful than a single screenshot. Keep one clear issue
per report; the owner-feedback PR can then group related corrections coherently.
