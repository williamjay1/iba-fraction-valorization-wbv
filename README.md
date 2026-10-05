# Incineration bottom ash: fraction composition, release and valorization decisions

Code, attributed analysis inputs, numerical results and publication graphics for
*Linking Fraction Composition, Leaching and Substitution Potential in Municipal
Solid Waste Incineration Bottom Ash Valorization*, prepared for **Waste and
Biomass Valorization**. This repository corresponds to the v113 manuscript
analysis and its Nature-inspired visual revision.

The analysis examines how fraction yield, carbonate phases and joint
strength/release evidence affect conditional valorization decisions. German,
Italian, Spanish and Swedish source cases retain their own materials, functions
and comparison benchmarks. The repository contains secondary analyses of
published measurements and model outputs, with explicitly labelled hypothetical
scenarios.

## Reproduce the numerical results

Use Python **3.12** in a virtual environment. The tested environment is Python
3.12.14, NumPy 2.3.5 and openpyxl 3.1.5 on Windows. Install the two direct
numerical dependencies and run:

```shell
python -m pip install -r requirements.txt
python -X utf8 src/reproduce.py
```

The runner checks every distributed input checksum, copies inputs into a new
work directory, executes seven modules, runs a separately implemented numerical
verifier, and compares all **38 result CSVs byte for byte** against frozen
references. Input files must remain unchanged. No source downloads, licensed LCA
backgrounds, original local archives, or manuscript files are needed. A failed
check returns a nonzero exit code.

Outputs and logs go to a new `temp/reproduction_*` directory. An explicit empty
directory can be selected with `--workdir PATH`; existing results are never
deleted. The supported exact-byte environment is the recorded Windows/Python
configuration. The GitHub workflow uses the available CPython 3.12.10 Windows
build with the same pinned numerical packages. Other platforms can run the algorithms, but cross-platform
byte equality has not been verified. The GitHub workflow runs the same numerical
command and retains its reports.

## Reproduce the figures

```shell
python -m pip install -r requirements-graphics.txt
python -X utf8 src/reproduce.py --figures
```

This additionally produces four main figures and a graphical abstract as
editable **PDF/SVG vectors** and native **1200 dpi PNGs** at fixed physical
dimensions. Vector formats have no inherent DPI. The original SciencePlots
`science`, `no-latex` and `nature` styles are vendored with their MIT licence and
loaded before explicit readability overrides. Arial must be lawfully installed;
font files are not distributed. A missing font or scientific glyph causes a
failure. The figure script checks text collisions, text/line intersections,
clipping and vector content, with positive controls for the detectors.

The reviewed publication assets are in `results/wbv_v113/figures/`, with source
values and complete captions in `results/wbv_v113/figure_data/`. The numerical
and graphic validation report is in `validation/REPRODUCTION_REPORT.json`.

## Repository contents

| Location | Contents |
| --- | --- |
| `src/` | Seven analyses, independent numerical verifier, figure generator and isolated runner |
| `datasets/` | Attributed published-cell caches and paired-response extraction records |
| `public_sources/` | Abis et al. CC BY full-text XML required for source-table checks |
| `results/*.csv` | Two historical derived input tables retained at paths required by the analyses |
| `validation/reference_results/` | Frozen 38-result CSV baseline |
| `validation/reference_tables.json` | Fixed, rounded numerical reference tables extracted from the manuscript |
| `validation/*manifest.json` | Input, reference-result and publication-graphic inventories/checksums |
| `docs/ANALYSIS.md` | Units, equations, exploratory choices and interpretation limits |
| `docs/DATA_DICTIONARY.md` | Input-field conventions and per-file result schemas |
| `docs/SOURCES.md` | Source citations, exact locators, provenance and transformations |
| `DATA_LICENSES.md` | Third-party and original-result licence scopes |
| `docs/ZENODO.md` | Author-operated archival and DOI instructions |

The full manuscript, internal reviews, author identity forms, restricted source
texts, fonts, commercial background inventories and unavailable experimental
replicates are not part of this code/data repository.

## Evidence boundaries

- Italian data comprise **25 linked fractions from five plant composites**.
  Carbonate-adjusted quantities are stoichiometric CO₂ ceilings, with explicit
  rounding sensitivity; actual clinker substitution performance is unmeasured.
- Spanish fractions originate from **one composite**. About 54% of feed meets
  the reported strength benchmark and about 46% meets the mortar molybdenum
  comparator, with an empty intersection. The 0.5 mg/kg Mo comparator concerns
  inert landfill and does not establish construction approval. The whole-mixture
  mortar is a separate formulation, with no additional fraction yield.
- German climate bounds preserve source composition and equivalent clinker
  function. Unknown changes to other exchanges remain in a signed adjustment.
- Swedish processing/eligibility quantities and economic perturbations are
  hypothetical scenarios. Unavailable screening orders and adverse scenarios
  remain in the released results.
- Paired-treatment conditions are nested within source lineages. Descriptive
  proportions are not population prevalence estimates. Technical triplicates
  and modelled probability bounds are not independent plant replication.
- Coefficients are not pooled across countries. A complete same-material
  treatment inventory for a newly demonstrated route is unavailable.

See [the analysis notes](docs/ANALYSIS.md) and source-level limitation fields for
the conditions attached to each result.

## Licences, attribution and AI assistance

Project Python code is licensed under [MIT](LICENSE). Upstream SciencePlots
files retain their original MIT notice. Published input records and source
material retain their source licences and attribution obligations; original
derived outputs and graphics have the scope stated in
[DATA_LICENSES.md](DATA_LICENSES.md). The root code licence does not relicense
third-party data.

AI assisted source discovery/extraction, code generation and revision,
calculation checking, graphics, interpretation and English manuscript drafting.
This release records source locators, checksums, fixed simulation settings and
independent arithmetic checks. AI assistance did not create the underlying
experimental observations. Human authors remain responsible for checking the
research, contributions and final declarations.

## Citation and archival status

**No Zenodo DOI has been generated.** The author will archive a selected version
personally. Use [the Zenodo instructions](docs/ZENODO.md) to choose one archival
path. A GitHub commit or repository URL does not itself provide a Zenodo DOI.

Real research creators and author order have not yet been supplied. Active
`CITATION.cff` and `.zenodo.json` files are therefore deferred until the author
confirms those fields. See [publication metadata](docs/PUBLICATION_METADATA.md)
for the required information and manuscript availability wording. After
archival, cite the actual **version DOI** together with the version and creators.
