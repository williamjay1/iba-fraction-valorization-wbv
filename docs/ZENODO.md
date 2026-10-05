# Archiving this release in Zenodo

The default publication sequence is to push the reviewed code and data to this repository, let the authors enable Zenodo, and then publish a GitHub Release. A code push or a release draft does not demonstrate that an archival DOI exists. No active CITATION.cff or .zenodo.json is supplied while the actual creators are unconfirmed. See [publication metadata](PUBLICATION_METADATA.md) and the [repository README](../README.md).

Choose **one** initial deposit route for the selected snapshot.

## A. Enable Zenodo, then publish a GitHub Release

1. Confirm the actual creators, resource title, version and permissions. Add valid citation metadata when those details are known. Keep source attribution and third-party licences with the release.
2. The author signs in to Zenodo, links GitHub, opens the GitHub integration page, selects **Sync now**, and enables this public repository. Organisation repositories may need organisation approval.
3. After enabling the integration, select the reviewed tag/commit in GitHub and click **Publish release**. Wait for Zenodo processing, open the resulting record, and check its creators, files, version and licences.
4. Copy the actual version DOI and concept DOI from the record. Update citation metadata and the README only after checking the archived files against the release manifest.

Zenodo documents automatic ingestion of **new releases after connection**. Do not assume that enabling a repository backfills old releases. For an existing snapshot, use route B or publish a new release after enabling the integration. This is the documented workflow; current official guidance does not promise historical backfill. Do not assume every separately attached GitHub Release asset is archived: check the actual Zenodo Files list.

Official instructions: [enable a repository](https://help.zenodo.org/docs/github/enable-repository/), [archive a GitHub release](https://help.zenodo.org/docs/github/archive-software/github-upload/), [GitHub releases](https://docs.github.com/en/repositories/releasing-projects-on-github/managing-releases-in-a-repository).

## B. Manually upload the reviewed ZIP

The author can instead download the selected source/release ZIP and use Zenodo **New upload**. Record the commit SHA, upload the reviewed public package, fill in the actual creators and licence scope, preview the record, and publish it personally. Complete the deposit form; do not assume citation files inside a ZIP fill it automatically. This route works without GitHub integration and can archive an already published GitHub snapshot.

Manual drafts can reserve a DOI, but it is registered only when published. GitHub integration cannot pre-reserve one. Do not run both routes for the same initial snapshot and create unrelated duplicate records. Source archives contain a snapshot, rather than the full Git history; identify the fixed commit used.

Official instructions: [new upload](https://help.zenodo.org/docs/deposit/create-new-upload/), [DOI pre-reservation FAQ](https://support.zenodo.org/help/en-gb/24-github-integration/73-can-i-pre-reserved-a-doi-before-a-github-release), [source archives](https://docs.github.com/en/repositories/working-with-files/using-files/downloading-source-code-archives).

## DOI and metadata checks

The first publication creates a version DOI and a concept DOI covering all versions. Cite the **version DOI** for manuscript reproducibility; identify the concept DOI separately as the project-wide identifier. Each subsequent version receives its own version DOI. Never substitute an article DOI for a software/data DOI or invent a DOI suffix.

If both metadata files exist, Zenodo uses **.zenodo.json only**; it does not merge missing fields from CITATION.cff. GitHub still uses CITATION.cff for its citation display. A valid CFF alone is sufficient when Zenodo-specific metadata is unnecessary. Preserve each third-party licence; the record-level licence does not extend your rights to external materials.

Official guidance: [DOI versioning](https://support.zenodo.org/help/en-gb/1-upload-deposit/97-what-is-doi-versioning), [Zenodo metadata](https://help.zenodo.org/docs/github/describe-software/), [mixed licences](https://help.zenodo.org/docs/deposit/describe-records/licenses/). Guidance checked on 5 October 2026; no Zenodo action was performed when preparing these documents.
