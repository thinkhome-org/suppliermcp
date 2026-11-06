# Promote SupDB 2.0.0

RC tags publish candidate packages with RC versions. For stable promotion, prepare a staging commit with version `2.0.0` in the Python package, lockfile and both plugin manifests. Include all intended code, tests, workflows and operator documentation in that commit. Push a fresh `v2.0.0-stage.N` tag on it. The candidate workflow runs CI, builds the stable-version packages and multi-architecture image, smoke-tests the GHCR digest, and attaches the packages and `image-reference.txt` to a GitHub prerelease. This staging path publishes the image by digest only.

1. Download the staging prerelease assets and verify `sha256sum -c SHA256SUMS`. Record the SHA-256 of the checksum file and the peeled source commit from `git rev-parse 'v2.0.0-stage.N^{commit}'`.
2. Deploy the exact reference in `image-reference.txt` to an isolated Portainer stack with its own storage. Rehearse restart, backup, restore and rollback to v1, including an authenticated lookup. Verify the running image and retain sanitized timestamped receipts outside Git.
3. On the permitted supplier network, run the staged commit's `scripts/probe_operations.py` **inside a container started from that image reference**. Mount the script read-only and a fresh output directory writable. Set the protected account configuration locally. Pass `--image-reference "$image" --output /evidence/operations.json` on every invocation, including retries with legitimate inputs and permitted time windows. Use `--both-scopes` for operations requiring the personal operator grants. Every reviewed read and mode must return a verified nonempty result or a valid, confirmed empty response. Investigate ambiguous truncated responses and supplier errors. Reviewer checks the preserved per-operation timestamp, registered scope, mode and outcome against the protected run.
4. Against that stack, complete actual Codex and personal ChatGPT web OAuth sign-in, a live catalog read and a live document read in each. Also record Python service reads, the REST catalog success and ordinary-client document denial, and fixed-revision catalog selection, relevance and performance checks. Keep protected receipts for each check. Include enough provenance in each receipt to identify the tested digest, date, tool, account class and observed results.
5. Create `docs/releases/2.0.0/operations.json` from the fresh probe results. Write `docs/releases/2.0.0/acceptance.json` with these fields:

| Field | Required value |
| --- | --- |
| `version`, `stage_tag`, `source_commit` | `2.0.0`, stage tag, full staged Git commit |
| `image`, `checksums_sha256` | Exact GHCR digest reference and SHA-256 of the staging release's `SHA256SUMS` file |
| `checks` | One entry for each check listed below. Each entry contains `outcome` set to `passed`, the tested `image`, a timezone-qualified `observed_at` and the SHA-256 of the protected receipt in `receipt_sha256`. |

Required check IDs are `portainer_restart`, `portainer_backup_restore_and_v1_rollback`, `actual_codex_oauth_catalog_and_documents`, `personal_chatgpt_web_oauth_catalog_and_documents`, `rest_catalog_and_document_denial`, `python_catalog_and_documents` and `catalog_selection_relevance_and_performance`.

6. Run `uv run --locked python scripts/verify_promotion.py docs/releases/2.0.0 /path/to/staging-assets "$source_commit"`. Have the operator review the two records and the underlying receipt contents. The automated gate validates coverage, outcome, provenance fields and asset hashes. The reviewer verifies the actual live observations. Keep customer data, credentials and browser transcripts out of the repository.
7. Commit only the two acceptance records on top of the staged revision and tag that reviewed commit `v2.0.0`. Push the tag. The stable workflow verifies the Git ancestry and tree differences, compares the release assets and evidence, checks the staged container version and source revision, and applies the stable GHCR tag to the same digest. It attaches the already-built wheel and plugin archives to the stable release. The operator schedules production deployment separately.

If any code, dependencies, packaging or workflow changes after staging, create a fresh stage tag and repeat acceptance on its digest. Incomplete evidence leaves the version at prerelease.
