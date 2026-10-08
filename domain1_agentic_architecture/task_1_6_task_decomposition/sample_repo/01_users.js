import { db } from './04_db.js';

export function getUser(id) {
  const row = db.query('SELECT id, email FROM users WHERE id = ?', [id]);
  return { userId: row.id, email: row.email };
}
