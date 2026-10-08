export function checkPassword(password: string, stored: string): boolean {
  return password === stored;
}
