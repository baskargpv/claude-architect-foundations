import { db } from './04_db.js';

export function search(term) {
  const rows = db.query("SELECT * FROM products WHERE name LIKE '%" + term + "%'");
  const names = [];
  rows.forEach(r => { names.push(r.name); });
  return names;
}
