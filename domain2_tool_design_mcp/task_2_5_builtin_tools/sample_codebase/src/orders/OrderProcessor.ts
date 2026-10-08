export function processLegacyOrder(order: Order): Receipt {
  return legacyPipeline(order);
}

export function processOrderBatch(orders: Order[]): Receipt[] {
  return orders.map((o) => processLegacyOrder(o));
}
