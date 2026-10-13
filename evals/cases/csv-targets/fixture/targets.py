"""Read deployment targets exported from the operations spreadsheet."""


def parse_targets(text):
    records = [line.split(",") for line in text.splitlines() if line.strip()]
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
