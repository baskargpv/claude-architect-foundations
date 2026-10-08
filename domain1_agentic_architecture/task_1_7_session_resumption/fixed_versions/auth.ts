import { timingSafeEqual } from "crypto";

export function checkPassword(password: string, stored: string): boolean {
  return timingSafeEqual(Buffer.from(password), Buffer.from(stored));
}
