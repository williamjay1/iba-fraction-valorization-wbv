# Fixed reference tables

`reference_tables.json` contains the header and data rows of the four finalized main tables and five supplementary tables. It preserves the original strings, rounding, approximate shares and benchmark labels. It was extracted once from the finalized v113 Markdown sources, independently of generated CSVs. Source hashes, table row counts and the JSON hash are recorded in `reference_tables_provenance.json`; the full manuscript is not included.

`verify_analysis.py` reads these fixed cells as transcription references and separately reconstructs arithmetic from source caches or generated primitive quantities. Table 1 documents units and boundaries; it is not a numerical oracle. The verifier checks numerical content of Tables 2–4 and S1–S5 at the original display tolerances. Input and output file hashes are handled by the public runner.
