from dataclasses import dataclass


@dataclass
class Order:
    id: str
    cents: int


def total(orders: list[Order]) -> int:
    return sum(order.cents for order in orders)
