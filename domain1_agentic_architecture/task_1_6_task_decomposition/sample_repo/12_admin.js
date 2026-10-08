export function adminEmail(admins, id) {
  const admin = admins.find(a => a.id === id);
  return admin.email.toLowerCase();
}
