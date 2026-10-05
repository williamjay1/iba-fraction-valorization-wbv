# Vendored SciencePlots styles

Upstream: [garrettj403/SciencePlots](https://github.com/garrettj403/SciencePlots).
Fixed source commit: `b9b16959570bd2fbc9ff5118bacc423c3bddd592`.
The three original `.mplstyle` files were retrieved on 5 October 2026 and retain
the upstream [MIT licence](LICENSE). The figure generator loads `science`,
`no-latex`, and `nature` in that order, then applies explicit Arial, font-size,
colour, line, physical-size and 1200 dpi raster-export settings. The loaded-file
hashes and project code are included in the release manifest.

Vector text, embedded PDF fonts, scientific glyph coverage and automated
collision checks are described in `src/make_wbv_figures_v113.py` and
`validation/GRAPHICS_VERIFICATION.json` at repository root. Fonts are not
redistributed. These styles provide a Nature-inspired scientific design for
the WBV manuscript.
