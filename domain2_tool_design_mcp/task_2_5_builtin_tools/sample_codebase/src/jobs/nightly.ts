import { submitLegacyOrder } from "../utils";

export function runNightly(queue: Order[]) {
  queue.forEach((o) => submitLegacyOrder(o));
}
