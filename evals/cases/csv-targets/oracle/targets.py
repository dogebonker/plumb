"""Read deployment targets exported from the operations spreadsheet."""

import csv
import io


def parse_targets(text):
    try:
        lines = list(io.StringIO(text, newline=""))
        reader = csv.reader(lines, strict=True)
        records, previous = [], 0
        for record in reader:
            raw = "".join(lines[previous:reader.line_num])
            previous = reader.line_num
            if raw.strip():
                records.append(record)
    except csv.Error as error:
        raise ValueError("invalid CSV") from error
    if not records:
        return []
    if [field.strip() for field in records[0]] != ["name", "region", "enabled"]:
        raise ValueError("invalid header")
    targets = []
    for record in records[1:]:
        if len(record) != 3:
            raise ValueError("expected three fields")
        name, region, enabled = [field.strip() for field in record]
        if not name or not region or enabled.lower() not in {"true", "false"}:
            raise ValueError("invalid target")
        targets.append({"name": name, "region": region, "enabled": enabled.lower() == "true"})
    return targets
