import { processLegacyOrder } from "./orders/OrderProcessor";

export function replay(order: Order) {
  return processLegacyOrder(order);
}
