import { rateLimit } from "./ratelimit";

export function loginRoute(app: App) {
  app.post("/login", rateLimit({ perMinute: 5 }), handleLogin);
}
