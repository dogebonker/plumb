from shop.domain.order import Order


class MemoryRepository:
    def __init__(self) -> None:
        self.rows: list[Order] = []

    def add(self, order: Order) -> None:
        self.rows.append(order)
