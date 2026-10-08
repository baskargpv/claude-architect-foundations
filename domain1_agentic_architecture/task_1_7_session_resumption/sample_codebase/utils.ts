export function slugify(s: string): string {
  return s.toLowerCase().replace(/\s+/g, "-");
}
