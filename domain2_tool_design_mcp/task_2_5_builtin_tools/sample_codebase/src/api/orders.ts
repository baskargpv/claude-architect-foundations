import { submitLegacyOrder } from "../utils";

export function postOrder(req: Request) {
  return submitLegacyOrder(req.body);
}
