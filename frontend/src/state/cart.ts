import { create } from "zustand";

import { endpoints } from "../api/endpoints";

export type CartItem = {
  productId: number;
  title: string;
  price: number;
  quantity: number;
  options: unknown[];
};

type CartState = {
  items: CartItem[];
  add: (item: CartItem) => void;
  updateQty: (productId: number, quantity: number) => void;
  remove: (productId: number) => void;
  clear: () => void;
};

export const useCart = create<CartState>((set) => ({
  items: [],
  add: (item) =>
    set((state) => {
      const existing = state.items.find((i) => i.productId === item.productId);
      if (existing) {
        return {
          items: state.items.map((i) =>
            i.productId === item.productId ? { ...i, quantity: i.quantity + item.quantity } : i,
          ),
        };
      }
      return { items: [...state.items, item] };
    }),
  updateQty: (productId, quantity) =>
    set((state) => ({
      items: state.items.map((i) => (i.productId === productId ? { ...i, quantity } : i)),
    })),
  remove: (productId) => set((state) => ({ items: state.items.filter((i) => i.productId !== productId) })),
  clear: () => set({ items: [] }),
}));

type CheckoutState = {
  loading: boolean;
  total: number;
  submitOrder: (payload: { addressId: string; paymentMethod: "ONLINE" | "COD" }) => Promise<void>;
};

export const useCheckout = create<CheckoutState>((set, get) => ({
  loading: false,
  total: 0,
  submitOrder: async ({ addressId, paymentMethod }) => {
    set({ loading: true });
    const items = getCartItems();
    const total = items.reduce((sum, item) => sum + item.price * item.quantity, 0);
    try {
      await endpoints.createOrder({
        delivery_address: addressId,
        payment_method: paymentMethod,
        items: items.map((item) => ({
          product: item.productId,
          quantity: item.quantity,
          modifiers: item.options,
        })),
        total_amount: total,
      });
      useCart.getState().clear();
    } finally {
      set({ loading: false, total });
    }
  },
}));

function getCartItems() {
  return useCart.getState().items;
}
