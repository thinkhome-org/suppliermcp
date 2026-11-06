# Reading a supplier operation

Use a reviewed operation ID from the operation inventory. Send the supplier arguments under the names and types in its contract. The server injects credentials. For eD document lists supply both ISO dates within a 31-day interval. Off-stock eD full catalogue exports need a nonempty commodity or another filter supported by the selected method.

For public eD transformed price lists, use `EDLINKOLDXML` with `XML`, `EDLINKOLDCSV` with `CSV`, or `EDLINKXLS` with `XLS`. Invoice downloads support `INVOICEOLD`, `ISDOC_5` and `ISDOC_6`.

## Reading the next page

The result includes the operation ID, supplier output schema and an ordered list of fields. Each field has a supplier XML path, text value and zero-based Unicode character offset within that value. Square brackets distinguish siblings in source order. An attribute path ends in `/@name`. The service preserves supplier codes and decimals as text. Join fragments with the same path in offset order. For a binary export, join fragments of each `base64[n]` field, decode each field independently, and append its bytes. ZIP member prefixes distinguish files inside the same archive.

When `next_cursor` has a value, repeat the original operation and arguments with that cursor. Use the `cursor` argument in Python or MCP, or the `X-Read-Cursor` header on the REST operation route. Stop when `next_cursor` is null. The response's `truncated` flag reports whether another page exists. `stable_pagination: false` means the supplier does not guarantee a persistent snapshot.

The service re-reads the source for each page and verifies its digest before returning data. A changed source raises `source_snapshot_changed`. Restart from the first page to read the new snapshot. A cursor expires after the configured result TTL and requires the original subject, client, arguments and supplier credentials. No document data is stored for pagination. Network or expansion limits, supplier service windows, and permissions still apply to every request. An oversized export may require a targeted or filtered operation instead.
