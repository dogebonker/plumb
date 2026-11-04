TOPIC = "account.closed.v1"

def consume_closed(event, archive):
    archive.append(event["account_id"], retention_days=30)
