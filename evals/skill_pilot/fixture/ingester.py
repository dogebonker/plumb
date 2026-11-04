def accept(items, store):
    # shortcut: materialize finite requests; use bounded consumption for streaming ingress.
    items = list(items)
    if len(items) > 5:
        raise ValueError("requests may contain at most five items")
    count = 0
    for item in items:
        store.append(item)
        count += 1
    return count
