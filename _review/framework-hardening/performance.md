# Travel icon delivery comparison

Baseline: merged PR #21 (`a33a590`). Seven alternating fresh Chromium contexts per
phase at 1× and 4× CPU slowdown (28 runs). Real compiled HTML/CSS/controllers and
Font Awesome 6.5.0 CSS/WOFF2 files are served over local HTTP. Test HTML maps the
external font URLs locally; Inter TTF and synthetic photographs are controlled,
matching inputs. Firebase is a UI fixture; production SDK/analytics are blocked.
No production source is rewritten by the lab.

| Metric, median | Before | After |
| --- | ---: | ---: |
| Icon stylesheet/font requests | 3 | 0 |
| Icon stylesheet/font transfer bytes | 285,438 | 0 |
| All requests including document | 25 | 22 |
| Document transfer bytes | 23,668 | 28,128 |
| All local transfer bytes including document | 1,410,469 | 1,133,240 |
| Renderer DOM nodes | 888 | 993 |

The same icon paths are embedded once as symbols. The document grows, and SVG
instances add DOM nodes; these costs are included above. Removing the remote icon
stylesheet and two font resources saves three requests. This eliminates the font
loading failure mode; it does not make the Firebase backend faster.

| CPU | Phase | JS ms | Layout ms | Style ms | Fixture FCP ms | Fixture CLS |
| ---: | --- | ---: | ---: | ---: | ---: | ---: |
| 1× | before | 6.0 | 42.3 | 9.5 | 136 | 0.000008 |
| 1× | after | 5.3 | 43.6 | 8.7 | 136 | 0.000000 |
| 4× | before | 18.3 | 97.6 | 42.8 | 312 | 0.000008 |
| 4× | after | 17.8 | 83.7 | 40.7 | 252 | 0.000000 |

Browser-reported transfer sizes include local HTTP headers and the document;
resources are uncompressed here. The test Inter TTF is larger than production
WOFF subsets and is identical in both phases. The removed Font Awesome resource
bytes are real fixture files, not fabricated estimates, but these totals are not
production CDN/Brotli transfer sizes. Do not extrapolate them to R2 or restored
photographs. Shared-cloud CPU/paint medians are descriptive: some JS/style costs
increase, extra SVG DOM is explicit, and no universal speedup or production Core
Web Vitals improvement is claimed. No decoded-image/GPU memory was measured.

Search remains on demand with its validated session cache; native search code
and all 80 records are unchanged. PR #21's bounded carousel strategy is retained,
with only unique accessible labels added. No bulk unused-CSS/JS deletion is
justified by this fixture workload, so conditional/legacy behavior is preserved.

[All 28 samples, medians, resources and heap measurements](results/performance.json).
Reproduce using `_tests/framework-performance.py` and `_tests/README.md`.
