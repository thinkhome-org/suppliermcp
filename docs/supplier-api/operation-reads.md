# Reading a supplier operation

Use a reviewed operation ID from the operation inventory. Send the supplier arguments under the names and types in its contract. The server injects credentials. For eD document lists supply an ISO start date. The optional end date defaults to today in Prague. The interval can cover up to 31 dates. Off-stock eD full catalogue exports need a nonempty commodity or another filter supported by the selected method.

For public eD transformed price lists, use `EDLINKOLDXML` with `XML`, `EDLINKOLDCSV` with `CSV`, or `EDLINKXLS` with `XLS`. Invoice downloads support `INVOICEOLD`, `ISDOC_5` and `ISDOC_6`.

## Reading the next page

The result includes the operation ID, supplier output schema and an ordered list of fields. Each field has a supplier XML path, text value and zero-based Unicode character offset within that value. Square brackets distinguish siblings in source order. An attribute path ends in `/@name`. The service preserves supplier codes and decimals as text. Join fragments with the same path in offset order. For a binary export, join fragments of each `base64[n]` field, decode each field independently, and append its bytes. ZIP member prefixes distinguish files inside the same archive.

When `next_cursor` has a value, repeat the original operation and arguments with that cursor. Use the `cursor` argument in Python or MCP, or the `X-Read-Cursor` header on the REST operation route. Stop when `next_cursor` is null. The response's `truncated` flag reports whether another page exists. `stable_pagination: false` means the supplier does not guarantee a persistent snapshot.

The service re-reads the source for each page and verifies its digest before returning data. A changed source raises `source_snapshot_changed`. Restart from the first page to read the new snapshot. A cursor expires after the configured result TTL and requires the original subject, client, arguments and supplier credentials. No document data is stored for pagination. Network or expansion limits, supplier service windows, and permissions still apply to every request. An oversized export may require a targeted or filtered operation instead.

## Account windows and catalog scope

Set the 100MEGA service login/password in the supplier environment and run `python -m suppliermcp.suppliers.mega.capabilities /secure/path/source-contracts.json` before starting the server. This refreshes the named account's export names and windows from its authenticated capability table, preserves other settings and writes the result atomically. Point `SUPPLIERMCP_SOURCE_CONTRACTS_PATH` at that file. Refresh it and restart services after an account change. The server intersects the local account's window with the reviewed operation window. An absent export has no verified capability.

A catalog-only response sets `catalog_projection` to true and returns only scalar fields accepted at reviewed XML paths. The checked-in projection covers eD WSDL results, documented native catalog downloads and 94 100MEGA export names. The two X-HOG variants lack a reviewed field schema. Those exports and opaque CSV/XLS transforms return `catalog_projection_unavailable` for catalog-only clients. A caller authorized for both scopes can read those outputs. The 100MEGA projection uses 89 product XDRs and verified native XML layouts for the two presentation-tree formats, the two shop formats and product safety information. The latter exposes manufacturer ID and name under catalog scope.

## Authenticated probe matrix

Run `python scripts/probe_operations.py --output audit.json` with the installation's credentials and capability file. The command calls only reviewed reads and writes UTC timestamps, results, limits and input categories. It does not retain supplier payloads, arguments, document IDs, URLs or continuation tokens. The default uses each operation's minimum scope, a 2 MiB network limit and an 8 MiB expansion limit. Use `--both-scopes` to evaluate a separately authorized client. Provide a separate output for that scope.

Use `--operation 'ed_private.*'` or a full operation ID to select a source or mode. Repeat `--operation` to combine selections. Use `--wire-mib` and `--expanded-mib` to set bounds for the selected operations. To rerun after the recorded UTC opening, pass `--status outside_supplier_window` with the same output file. The command checks current windows again. When a known document or catalog selector is available, pass a protected local `--arguments-file` mapping full operation IDs to argument objects. Generated dummy detail selectors can verify an empty response but cannot establish business-record coverage.

Both the worker and on-demand reads check the account window against the reviewed operation on each HTTP attempt. The generated account fingerprint binds it to the configured 100MEGA login. A v1 installation must regenerate its unbound capability file for the same supplier account before enabling v2 reads. Refreshing from a file bound to another login is rejected. Use a separate output and freshly verified offer mappings for a different account.
