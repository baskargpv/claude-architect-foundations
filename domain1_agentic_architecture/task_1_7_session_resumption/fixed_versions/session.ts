export function currentSession(req: Request) {
  const session = lookupSession(req.cookies.token);
  return rotateSession(session); // new token on every privilege change
}
