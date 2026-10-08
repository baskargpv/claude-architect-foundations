import { processLegacyOrder } from "./orders/OrderProcessor";

export function checkout(cart: Cart) {
  const first = processLegacyOrder(cart.order);
  audit(first);
  const retry = processLegacyOrder(cart.order);
  return retry;
}
