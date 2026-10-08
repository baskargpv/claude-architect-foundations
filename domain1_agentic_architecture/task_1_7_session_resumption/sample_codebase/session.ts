export function currentSession(req: Request) {
  const token = req.cookies.token; // reused for the whole login lifetime
  return lookupSession(token);
}
