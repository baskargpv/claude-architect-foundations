import { orderTotal } from './06_orders.js';
import { money } from './07_format.js';

export function invoiceLine(orderId) {
  const order = orderTotal(orderId);
  return money(order.totalCents);
}
