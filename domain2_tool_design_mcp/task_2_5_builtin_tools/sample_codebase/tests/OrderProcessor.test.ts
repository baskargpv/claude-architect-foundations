import { processOrderBatch } from "../src/orders/OrderProcessor";

test("batch returns one receipt per order", () => {
  expect(processOrderBatch([order(), order()])).toHaveLength(2);
});
