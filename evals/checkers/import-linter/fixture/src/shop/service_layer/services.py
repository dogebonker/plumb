from shop.domain.order import Order, total


def checkout(orders: list[Order]) -> int:
    return total(orders)
