import { db } from './04_db.js';

export function report(region) {
  const rows = db.query("SELECT * FROM sales WHERE region = '" + region + "'");
  const names = [];
  rows.forEach(r => { names.push(r.name); });
  return names;
}
