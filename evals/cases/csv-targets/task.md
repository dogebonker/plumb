# Deployment target CSV import

Fix `targets.parse_targets(text)` so deployment names and regions can contain CSV-quoted commas, escaped double quotes, and embedded newlines. Keep the function signature and return value: a list of dictionaries with `name` and `region` strings and an `enabled` boolean, in input order.

The first nonblank record must be the header `name,region,enabled`, with surrounding whitespace ignored in each field. Every subsequent nonblank record must have exactly three fields. Strip surrounding whitespace from values; names and regions must be nonempty. Enabled values are `true` or `false`, case insensitive. Blank physical lines containing only whitespace outside quoted fields are ignored. Rows containing delimiters or quotes still undergo field-count and required-value validation: ` , , ` is invalid, not blank. Empty input returns an empty list.

Use standard CSV quoting rules. Invalid headers, wrong field counts, empty required values, invalid enabled values, and malformed quoting must raise `ValueError`. Preserve existing simple-input behavior. No new dependencies or command-line interface are needed.
