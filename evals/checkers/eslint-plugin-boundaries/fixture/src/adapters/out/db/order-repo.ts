import { type Order, total } from "../../../domain/order";

const rows: Order[] = [];

export function saveOrder(order: Order): number {
  rows.push(order);
  return total(rows);
}
