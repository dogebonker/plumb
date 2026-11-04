from code.events.publisher import publish_closed

def close_account(actor, account, bus):
    if actor.account_id != account.id or not actor.can_close_account:
        raise PermissionError("closure denied")
    account.closed = True
    publish_closed(bus, account.id)
