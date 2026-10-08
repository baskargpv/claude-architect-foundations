export function cartOwner(carts, userId) {
  const cart = carts.find(c => c.userId === userId);
  return cart.owner.name;
}
