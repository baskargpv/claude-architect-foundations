export function loginRoute(app: App) {
  app.post("/login", handleLogin);
}
