def publish_closed(bus, account_id):
    bus.publish("account.closed.v1", {"account_id": account_id})
