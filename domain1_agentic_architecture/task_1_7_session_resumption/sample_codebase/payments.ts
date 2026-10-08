export function chargeTotal(items: Item[]) {
  return items.reduce((sum, i) => sum + parseFloat(i.price), 0);
}
