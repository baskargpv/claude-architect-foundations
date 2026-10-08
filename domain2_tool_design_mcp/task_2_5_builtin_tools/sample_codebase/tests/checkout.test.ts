import { checkout } from "../src/checkout";

test("checkout returns a receipt", () => {
  expect(checkout(cart())).toBeDefined();
});
