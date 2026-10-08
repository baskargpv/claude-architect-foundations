export function findUser(conn: Conn, id: string) {
  return conn.query("SELECT * FROM users WHERE id = $1", [id]);
}
