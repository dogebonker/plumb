export interface Order {
  id: string;
  cents: number;
}

export function total(orders: Order[]): number {
  return orders.reduce((sum, order) => sum + order.cents, 0);
}
