import { db } from './04_db.js';

export function orderTotal(orderId) {
  const row = db.query('SELECT total_cents FROM orders WHERE id = ?', [orderId]);
  return { totalCents: row.total_cents };
}
