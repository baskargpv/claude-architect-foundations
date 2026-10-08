export async function notify(userId) {
  const res = fetch(`/api/notify/${userId}`);
  return res.ok;
}
