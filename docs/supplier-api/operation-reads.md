# Reading a supplier operation

Use a reviewed operation ID from the operation inventory. Send the supplier arguments under the names and types in its contract. The server injects credentials. For eD document lists supply an ISO start date. The optional end date defaults to today in Prague. The interval can cover up to 31 dates. Off-stock eD full catalogue exports need a nonempty commodity or another filter supported by the selected method.

For public eD transformed price lists, use `EDLINKOLDXML` with `XML`, `EDLINKOLDCSV` with `CSV`, or `EDLINKXLS` with `XLS`. Invoice downloads support `INVOICEOLD`, `ISDOC_5` and `ISDOC_6`.

## Reading the next page

The result includes the operation ID, supplier output schema and an ordered list of fields. Each field has a supplier XML path, text value and zero-based Unicode character offset within that value. Square brackets distinguish siblings in source order. An attribute path ends in `/@name`. The service preserves supplier codes and decimals as text. Join fragments with the same path in offset order. For a binary export, join fragments of each `base64[n]` field, decode each field independently, and append its bytes. ZIP member prefixes distinguish files inside the same archive.

When `next_cursor` has a value, repeat the original operation and arguments with that cursor. Use the `cursor` argument in Python or MCP, or the `X-Read-Cursor` header on the REST operation route. Stop when `next_cursor` is null. The response's `truncated` flag reports whether another page exists. `stable_pagination: false` means the supplier does not guarantee a persistent snapshot.

The service re-reads the source for each page and verifies its digest before returning data. A changed source raises `source_snapshot_changed`. Restart from the first page to read the new snapshot. A cursor expires after the configured result TTL and requires the original subject, client, arguments and supplier credentials. No document data is stored for pagination. Network or expansion limits, supplier service windows, and permissions still apply to every request. An oversized export may require a targeted or filtered operation instead.

## Account windows and catalog scope

Set the 100MEGA service login/password in the supplier environment and run `python -m suppliermcp.suppliers.mega.capabilities /secure/path/source-contracts.json` before starting the server. This refreshes the named account's export names and windows from its authenticated capability table, preserves other settings and writes the result atomically. Point `SUPPLIERMCP_SOURCE_CONTRACTS_PATH` at that file. Refresh it and restart services after an account change. The server intersects the local account's window with the reviewed operation window. An absent export has no verified capability.

A catalog-only response sets `catalog_projection` to true and returns only scalar fields accepted at reviewed XML paths or tabular columns. The checked-in projection covers eD WSDL results, documented native catalog downloads and 94 100MEGA export names. The two X-HOG variants accept the observed empty `Result/StoItem/SPresentTree` structure. Any attribute, non-whitespace value or unknown element fails with `catalog_projection_unavailable` until a nonempty field schema is reviewed. The 100MEGA projection uses 89 product XDRs and verified native XML layouts for the two presentation-tree formats, the two shop formats and product safety information. The latter exposes manufacturer ID and name under catalog scope.

For catalog-only eD CSV reads, request UTF-8. Columns are matched by header name, with a 64 KiB row limit. Catalog-only XLS reads require Linux and the native BIFF8 workbook with the single visible sheet `Part 1` and its reviewed 17-column header. The repeated `Skladem` column is returned as `SklademText` for the textual stock state. Direct and single-file ZIP downloads return `Product[n]/column` fields. Both scopes together retain the raw non-XML download.

Each XLS page parses the workbook again in a separate process using xlrd. The worker reads cached cell values without executing formulas or macros. Limits per workbook are 16 MiB input, 32 MiB temporary output, 256 MiB virtual address space, 15 CPU seconds and 20 elapsed seconds. Malformed or unsupported workbooks return an error without releasing partial rows.

## Authenticated probe matrix

Run `python scripts/probe_operations.py --output audit.json` with the installation's credentials and capability file. The command calls only reviewed reads and writes UTC timestamps, results, limits and input categories. It does not retain supplier payloads, arguments, document IDs, URLs or continuation tokens. The default uses each operation's minimum scope, a 2 MiB network limit and an 8 MiB expansion limit. Use `--both-scopes` to evaluate a separately authorized client. Provide a separate output for that scope.

Use `--operation 'ed_private.*'` or a full operation ID to select a source or mode. Repeat `--operation` to combine selections. Use `--wire-mib` and `--expanded-mib` to set bounds for the selected operations, up to 1024 MiB and 2048 MiB respectively. The configured installation limits also apply. To rerun after the recorded UTC opening, pass `--status outside_supplier_window` with the same output file. The command checks current windows again. When a known document or catalog selector is available, pass a protected local `--arguments-file` mapping full operation IDs to argument objects. Generated dummy detail selectors can verify an empty response but cannot establish business-record coverage.

Both the worker and on-demand reads check the account window against the reviewed operation on each HTTP attempt. The generated account fingerprint binds it to the configured 100MEGA login. A v1 installation must regenerate its unbound capability file for the same supplier account before enabling v2 reads. Refreshing from a file bound to another login is rejected. Use a separate output and freshly verified offer mappings for a different account.

Read cursors use a random 256-bit process signing key by default. Restarting the process invalidates its cursors. For multiple replicas or continuity across restarts, set the same protected `SUPPLIERMCP_READ_CURSOR_KEY` on every API/MCP process. Generate an independent secret with `openssl rand -base64 32`. Rotating that secret or the supplier credentials invalidates previous read cursors.

## Account evidence on 6 November 2026

The [per-operation matrix](v2-read-probes.json) covers all 326 reviewed read IDs for the ThinkHome account. Each row records its UTC observation time, privilege, bound and input category. The summary favors an observed business result over an empty result, then the more recent observation. Additional attempts on the same operation remain under `other_attempts`. An empty result means the operation returned no business fields in the tested privilege and selector. A verified page can still have a continuation. The matrix tests the reader library. See the [candidate acceptance record](v2-acceptance.md) for separately observed REST, MCP and deployment checks.

The first pass used a freshly authenticated table of 120 export names and the minimum scope for each read. Most checks used a 2 MiB transport limit and an 8 MiB expanded limit. Separate follow-ups used narrower legitimate selectors or larger bounds as recorded in each row. Window and catalog-projection denials occurred before supplier invocation. A size denial or upstream timeout does not establish successful parsing of a complete supplier stream. The matrix began before the independent cursor signing key and account-fingerprint changes. Those changes have separate regression tests. Candidate deployment smoke tests must identify their own build.

Additional document-scope checks used real eD invoice references obtained from the account's 30-day invoice list. The three official invoice formats returned nonempty fields. A separate continuation request returned a second verified page of the same invoice. Real 100MEGA delivery-address IDs obtained in memory from its account export produced nonempty responses from both the single-ID and ID-list methods.

Both-scope tests also read the documented binary variants of the public price list in direct and ZIP form. The ZIP CSV contained tab-separated data and the XLS member had an OLE workbook signature. Where the matrix includes another scope or variant under `other_attempts`, its outcome applies only to that tested combination.

The 100MEGA Order service reported an unknown order for `GetStatus` using the supplier guide’s absent-order example. A one-year change-list read returned no orders from which to obtain a valid ID. The operator knows of no other usable order for this account. Successful GetStatus acceptance is therefore blocked by a missing legitimate input. All three `GetXCompany` operations explicitly denied access and cited a missing parameter, including the date-based operation with its documented argument supplied. The same responses occurred over SOAP, HTTP GET and form POST. Licensing and the exact account setting remain unverified. The two `X-ASM-StiRelation` delta export variants returned HTTP 500 and explicitly reported an invalid SQL column with both documented HTTP methods and date-only inputs. Each affected matrix row records the checks without storing upstream text or identifiers.

For a current snapshot of item relationships, both `mega.X-ASM-StiRelation.full` and `mega.X-ASM-StiRelation_El.full` returned business data. Refreshing the corresponding full snapshot can recover the current state when a delta fails. It cannot recover a historical change interval.

## Bounded RC6 blocker recheck, 7 November 2026

The production Portainer worker identified package `2.0.0rc6` and image `ghcr.io/thinkhome-org/suppliermcp@sha256:39119ec4ac5bbc77bb75813d582a924fc489832b6ac363c93844b2488b82b134`. Sequential reader-library probes at **01:56:58–01:57:07 UTC (02:56:58–02:57:07 Europe/Prague)** used each operation's minimum scope, a 1 MiB wire limit, a 2 MiB expansion limit and an 8 KiB response bound.

| Reviewed operations | Observed result |
| --- | --- |
| `mega_order.GetXCompany`, `mega_order.GetXCompanyListChanged`, `mega_order.GetXCompanyListId` | `supplier_soap_server_application_fault` |
| `mega.X-ASM-StiRelation.delta`, `mega.X-ASM-StiRelation_El.delta` | `supplier_http_5xx` in an allowed account window, using a one-minute change interval |
| `mega_order.GetStatusListChanged` | Valid empty response for the preceding 365 days |

The firm detail/list selectors were synthetic. The order status detail still needs a legitimate order ID. The earlier SQL diagnosis and successful relationship full-snapshot reads retain their historical provenance. This run made no eD calls or full-catalogue downloads. The six small reads do not establish acceptance of all 326 operations on this image. Sanitized receipts retain timestamps, package, image, scope, bounds and outcome, excluding supplier payloads, URLs, credentials, arguments and cursors.

The follow-up requirements remain tracked in [export issue #3](https://github.com/thinkhome-org/suppliermcp/issues/3) and [SOAP issue #4](https://github.com/thinkhome-org/suppliermcp/issues/4). Stable promotion still requires the complete reviewed evidence for the exact staged stable image.
