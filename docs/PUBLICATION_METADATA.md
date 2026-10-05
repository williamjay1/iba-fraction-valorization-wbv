# Publication metadata and availability statements

The authors must confirm publication identities and declarations before an archival release. A GitHub login identifies a repository account; it does not establish research authorship. This public package supplies no active CITATION.cff or .zenodo.json while the actual creators remain unconfirmed, and contains no invented DOI. Follow the [Zenodo workflow](ZENODO.md) and the [repository README](../README.md).

## Author confirmation checklist

| Information | What must be confirmed |
|---|---|
| Resource creators | Actual people or organisations responsible for this software/data resource, their citation order, and their agreed names. Zenodo requires creators; it permits both people and organisations. |
| Manuscript authors | The agreed research author list, affiliations, corresponding author and contact details. Repository maintainers are not automatically manuscript authors. |
| ORCID | Verified identifiers only. Omit an unconfirmed ORCID; never copy an example identifier. |
| Funding | Actual funder, grant and project information. State no specific funding only if the authors confirm that declaration. |
| Competing interests | Each author's applicable declaration. Do not infer an absence of conflicts. |
| Contributions | Agreed CRediT roles or the journal's requested contribution statement, reflecting work actually performed. |
| AI assistance | An accurate account of the assistance actually used, reviewed against the journal's policy. Do not invent human authors or limit the disclosure to activities that were not the actual scope. |
| Rights | Authority to release original code/data, the applicable licence scope, and retained third-party attribution and permissions. |

Zenodo's [creator documentation](https://help.zenodo.org/docs/deposit/describe-records/creators/) defines the required field. GitHub's [citation documentation](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-citation-files) describes the root-level CITATION.cff display. Springer Nature's [editorial policies](https://www.springernature.com/gp/policies/editorial-policies) cover authorship, contributions, competing interests and AI accountability. These documents do not supply the missing identities or declarations.

## Citation metadata after confirmation

Use the actual resource title, creators, software/data type, release version, release date, licence and repository URL. If both citation formats are added, keep their authors, version and licence consistent: Zenodo prioritises .zenodo.json entirely, while GitHub displays CITATION.cff. Add a DOI only when it is actually assigned; add a published-paper relation only when that paper and identifier exist. Use the archive's version DOI for the specific reproducibility release. See [Zenodo metadata formats](https://help.zenodo.org/docs/github/describe-software/).

## Manuscript availability templates

Replace every brace-delimited field with a verified public value before copying a template into a manuscript. These are prose templates, not active deposit metadata. Use the first only **after the GitHub repository is publicly accessible**; the prepared package alone does not establish public availability. The statement describes the public package, rather than an internal working directory.

**After public GitHub push, before a Zenodo DOI is available:**

> The analysis code, publicly redistributable data inputs, and derived outputs supporting this study are available at {REPOSITORY_URL}, commit {COMMIT_SHA}. The repository documents source provenance, applicable licences, and reproduction instructions. External source materials are cited and their access conditions are recorded. A versioned Zenodo deposit is planned; a DOI has not yet been issued.

**After the selected snapshot is published in Zenodo:**

> The analysis code, publicly redistributable data inputs, and derived outputs supporting this study are archived in Zenodo as version {RELEASE_VERSION} at https://doi.org/{VERSION_DOI}. The corresponding repository is available at {REPOSITORY_URL}, commit {COMMIT_SHA}. Source provenance, applicable licences, and reproduction instructions accompany the archive. External source materials are cited and their access conditions are recorded.

Check that every input claimed as shared is actually present and permitted for redistribution. If a necessary input requires access from its original provider, describe that specific access route. Springer Nature's [secondary-data guidance](https://support.springernature.com/en/support/solutions/articles/6000237604-data-my-journal-expects-me-to-share) recommends citing secondary sources rather than simply republishing them. A project licence does not relicense third-party articles, data or software; Zenodo supports [mixed-licence uploads](https://help.zenodo.org/docs/deposit/describe-records/licenses/).

For later substantive file changes, publish a new archival version and update the manuscript citation to the version actually used. Keep the concept DOI separate from the version-specific citation. Official [DOI versioning guidance](https://support.zenodo.org/help/en-gb/1-upload-deposit/97-what-is-doi-versioning); checked on 5 October 2026.
