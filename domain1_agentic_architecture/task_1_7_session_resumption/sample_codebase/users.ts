export function updateEmail(req: Request) {
  return saveEmail(req.user.id, req.body.email);
}
