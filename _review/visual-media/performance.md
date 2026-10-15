# Carousel performance comparison

Actual merged PR #20 versus final PR #21 component CSS/controller. Seven
alternating fresh Chromium contexts per phase/count, at 1× and 4× CPU slowdown:
168 runs total. Source sets include mixed landscape/portrait proportions.
Native HTTP resources/cache are used, not route-mocked timing. Each repetition
also performs 24 scroll frames and five resizes (390/820/1440/390/1440).

Initialization below is summed instrumented DOMContentLoaded/rAF/ResizeObserver
callback work, including synchronous layout, not wall-clock load time. CDP layout,
script, task, DOM and JS heap measurements are separate. The two phases run on the
same shared cloud host; medians reduce noise but are not a real-device benchmark.
No comparison uses the audit's unvalidated single-set 2ms fixture.

## Image nodes and initialization

| Source images | Before → after image nodes | Reduction | Init at 1×, ms | Init at 4×, ms |
| ---: | ---: | ---: | ---: | ---: |
| 1 | 6 → 1 | 83.3% | 2.0 → 3.8 | 23.2 → 23.0 |
| 2 | 12 → 2 | 83.3% | 12.3 → 3.9 | 22.5 → 19.8 |
| 5 | 30 → 15 | 50.0% | 2.7 → 17.8 | 24.7 → 40.9 |
| 12 | 72 → 21 | 70.8% | 4.0 → 14.2 | 19.2 → 46.1 |
| 150 | 900 → 159 | 82.3% | 22.0 → 21.1 | 90.3 → 55.7 |
| 180 | 1080 → 189 | 82.5% | 31.9 → 25.4 | 114.2 → 51.4 |

For 150 originals the final DOM has **159 image nodes instead of 900** (82.3%
fewer); 180 becomes 189 instead of 1,080 (82.5% fewer). One/two-photo collections
have no copies. Short sets can require up to 3N for the viewport buffers, rather
than a fixed low clone cap that would expose blank edges.

## CPU work under 4× slowdown

All pairs are before → after; medians in milliseconds.

| Sources | Layout | Script | Repeated scroll/resize tasks |
| ---: | ---: | ---: | ---: |
| 1 | 24.7 → 11.7 | 21.6 → 15.6 | 150.6 → 101.3 |
| 2 | 16.7 → 12.4 | 8.7 → 15.8 | 109.1 → 142.7 |
| 5 | 19.4 → 31.7 | 8.6 → 21.7 | 132.5 → 211.8 |
| 12 | 18.8 → 33.8 | 13.7 → 20.4 | 138.7 → 245.5 |
| 150 | 47.6 → 42.4 | 71.5 → 36.6 | 430.1 → 460.1 |
| 180 | 48.7 → 40.6 | 100.7 → 35.9 | 534.2 → 500.8 |

Large-set initialization improves under slowdown, while five/twelve-image startup
costs rise: the replacement adds controls, image readiness, ResizeObservers,
selected-position preservation and bounded-copy setup absent from the old code.
Repeated tasks include the work of rebuilding buffers across five real resizes;
they are **not pure scroll-handler CPU**. The native scroll listener only marks
state and schedules quiet-time work, with no geometry reads/writes per event.
These numbers do not establish universal CPU improvement. The ordinary-speed
150-image result is roughly unchanged; fewer DOM nodes alone do not guarantee
lower layout/heap cost in every case.

## Transfers and memory

| Sources | Unique image resources, both | Image bytes, both | Post-GC DOM nodes (4×), before → after | Initial JS heap MiB (4×), before → after |
| ---: | ---: | ---: | ---: | ---: |
| 1 | 1 | 469 | 28 → 27 | 1.71 → 1.75 |
| 2 | 2 | 938 | 44 → 33 | 1.71 → 1.75 |
| 5 | 5 | 2,345 | 92 → 71 | 1.72 → 1.81 |
| 12 | 12 | 5,628 | 204 → 111 | 1.72 → 1.83 |
| 150 | 150 | 70,350 | 2412 → 939 | 1.28 → 2.00 |
| 180 | 180 | 84,420 | 2892 → 1119 | 1.28 → 2.02 |

Browsers already deduplicate/cache repeated image URLs. **There is no measured
unique-image network saving in this lab.** Fewer image elements and retained DOM
nodes do not prove lower decoded-image/GPU memory; those were not measured. JS
heap can increase with retained controller/observer state and GC timing, despite
the large reduction in DOM. Do not combine DOM and JS heap into a claimed RAM
saving. Real photographs, restored media and R2 delivery need separate profiling.

Every repeated-use run retains <=3N images and one control set; no accumulating
copies. Separate behavioral tests cover 1/2/5/12/150/180 images, missing/slow
resources, native wheel/touch, independent collections, held-pointer release,
orientation selection and boundary continuity. A bounded buffer can reach its
physical end during an unusually long uninterrupted fling; idle wrapping resumes
without fighting native input. Physical-device acceptance remains with the owner.

[All samples and medians](results/carousel-performance.json).
[Behavioral evidence](results/carousel-behavior.json).
Reproduce with `_tests/carousel-performance.py`; see `_tests/README.md`.
