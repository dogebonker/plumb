def accept(items, store):
    count = 0
    for item in items:
        store.append(item)
        count += 1
    return count
