import { getUser } from './01_users.js';

export function profileHeader(id) {
  const user = getUser(id);
  return `Profile #${user.id} <${user.email}>`;
}
