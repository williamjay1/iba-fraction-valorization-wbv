# Data, source text and figure licences

The repository's MIT licence applies to original software. It does not replace the licences or copyright notices of third-party data, articles, supplementary tables or software. The source identities, original locators and evidence for the permissions below are documented in [docs/SOURCES.md](docs/SOURCES.md). Rights were checked on 5 October 2026.

## Attributed source records

The numerical inputs are transcriptions, reformatted tables and previously calculated factual records from the eleven cited research works. Their upstream works use [Creative Commons Attribution 4.0 International (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/). Preserve attribution to the source authors, the publication/DOI, supplied copyright and licence notices, and the description of changes when redistributing the records. The licence and its disclaimer are available in the [official legal code](https://creativecommons.org/licenses/by/4.0/legalcode.en). Publisher-specific exclusions for third-party material still apply.

This permission statement concerns the included records. It does not extend an article's licence to independently licensed background databases or to unpublished source measurements. Facts, calculations and source text are distinguished in the source ledger; we do not rely on a claim that all publicly accessible material or all table transcriptions are free of rights.

| Included record | Source authors and upstream licence |
|---|---|
| `datasets/published_output_cells/german_source_cells.csv` | Zacharopoulos and Geldermann (2026), CC BY 4.0; 173 published workbook cells with worksheet and cell locators |
| `datasets/published_output_cells/swedish_source_table_cells.json` | Esguerra and Johansson (2026), CC BY 4.0; supplementary Tables B1 and C1, reformatted as JSON |
| `datasets/published_output_cells/source_cache_manifest.json` | Repository provenance metadata identifying the two preceding sources and their hashes; not an original workbook or inventory |
| `datasets/same_material_v114/mantovani_cell_cache.json` | Mantovani et al. (2023), CC BY 4.0; supplementary Tables 1–4, reformatted as JSON |
| `datasets/same_material_v114/marco_gibert2026_table_2_tables.json` | Marco-Gibert et al. (2026), CC BY 4.0; original article Table 2, reformatted as JSON |
| `datasets/same_material_v114/marco_gibert2026_table_3_tables.json` | Marco-Gibert et al. (2026), CC BY 4.0; original article Table 3, reformatted as JSON |
| `datasets/same_material_v114/marco_gibert2026_table_4_tables.json` | Marco-Gibert et al. (2026), CC BY 4.0; original article Table 4, reformatted as JSON |
| `datasets/same_material_v114/marco_gibert2026_table_5_tables.json` | Marco-Gibert et al. (2026), CC BY 4.0; original article Table 5, reformatted as JSON |
| `datasets/treatment_synthesis/abis2021_ec_leachate_pairs_v106.csv` | Abis et al. (2021), CC BY 4.0; transcribed Table 3 conductivity pairs. Historical country labels for Plant B are superseded by the next record |
| `datasets/treatment_synthesis/abis2021_ec_leachate_pairs_v111_metadata_corrected.csv` | Abis et al. (2021), CC BY 4.0; Plant B country corrected to Sweden; numerical values unchanged |
| `datasets/treatment_synthesis/audoye_paired_leachate_responses_v103_2026-09-28.csv` | Audoye et al. (2026), CC BY 4.0; supplementary numerical pairs with sample/table keys and calculated changes |
| `results/paired_response_dataset_v98_2026-09-28.csv` | Abis et al. (2021), Destefanis et al. (2020), Mezni et al. (2026), Vateva and Laner (2020), Simon and Scholz (2023), Schnabel et al. (2021); each upstream work CC BY 4.0. Preserve row-level DOI, citation, locator and evidence status |
| `results/ionic_pte_matched_conditions_v108_text_direction_sensitivity_2026-09-30.csv` | The six preceding sources plus Audoye et al. (2026), each upstream work CC BY 4.0; repository-derived matched-condition directions and source locators |
| `public_sources/abis2021_public_fulltext_20261001.xml` | Abis et al. (2021), CC BY 4.0; original public article XML, obtained through Europe PMC, with its embedded authors' copyright and licence statements retained |

The XML is source text, not a newly authored dataset. Its copyright notice reads “© 2021 by the authors.” The original XML is supplied unchanged. The other source records change representation, link conditions or calculate responses; they do not reproduce original article PDFs or figure images. No claim is made that these transcriptions are the original raw experimental data.

## New derived results and graphics

The repository contributors make their original contributions to the derived numerical outputs and newly drawn graphics available under CC BY 4.0. Attribute this repository and its contributors, identify the version or commit used, and retain the upstream source attribution whenever the output contains or depends on source records. This applies to the seven analysis modules' 38 CSV outputs, their baseline copies under `validation/reference_results`, and the repository's original figure data and drawings. It grants rights only in the contributors' own contributions and does not claim ownership of the original studies or relicense their underlying material.

Some output tables retain published numbers as anchors alongside calculations. Those anchors retain the original-source notices above. Conditional grids, test-order comparisons, sensitivity outputs and simulated technical-variability summaries are derived calculations; they are not new experimental observations or independent field validation. Citation of the repository should not replace citation of the scientific sources.

Repository-authored provenance metadata and documentation are available under CC BY 4.0, subject to their identified source quotations and notices. Do not attribute the published research to repository maintainers or list an AI system as a research author. Actual resource creators and manuscript authors must be confirmed as described in [docs/PUBLICATION_METADATA.md](docs/PUBLICATION_METADATA.md).

## Other components and exclusions

The vendored SciencePlots style files retain their upstream MIT licence and copyright notice in `results/wbv_v113/third_party/scienceplots/LICENSE`. The upstream authors are not authors of this reanalysis. No font software is distributed.

The package excludes commercial ecoinvent/background LCI databases, unavailable raw experimental replicates, restricted publisher or author PDF copies, and the Song et al. (2026) full text. Song's public author PDF has an all-rights-reserved notice; reading or linking it does not establish permission to redistribute it. That work is a contextual comparator, not an input to the distributed numerical analyses.

Marco-Gibert's Spanish article has a verified CC BY 4.0 notice. It must not be confused with the separate Song author PDF. Licence findings are based on the stated article notices, publisher metadata and inspected supplements; they are not a guarantee that every possible reuse or third-party element is covered.
