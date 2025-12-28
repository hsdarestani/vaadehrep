import { create } from "zustand";

import { endpoints } from "../api/endpoints";
import { useAuth } from "./auth";
import { useLocationStore } from "./location";
import { useServiceability } from "./serviceability";

export type CartModifierItem = {
  id: number;
  name: string;
  price_delta_amount: number;
  quantity: number;
};

export type CartModifierGroup = {
  group_id: number;
  group_name: string;
  items: CartModifierItem[];
};

export type CartItem = {
  id: string;
  productId: number;
  title: string;
  price: number;
  quantity: number;
  options: CartModifierGroup[];
};

type CartState = {
  items: CartItem[];
  add: (item: CartItem) => void;
  updateQty: (itemId: string, quantity: number) => void;
  remove: (itemId: string) => void;
  clear: () => void;
};

export const useCart = create<CartState>((set) => ({
  items: [],
  add: (item) => set((state) => ({ items: [...state.items, item] })),
  updateQty: (itemId, quantity) =>
    set((state) => ({
      items: state.items.map((i) => (i.id === itemId ? { ...i, quantity } : i)),
    })),
  remove: (itemId) => set((state) => ({ items: state.items.filter((i) => i.id !== itemId) })),
  clear: () => set({ items: [] }),
}));

type CheckoutState = {
  loading: boolean;
  total: number;
  submitOrder: (payload: {
    addressId?: string;
    addressInput?: { title?: string; full_text?: string; latitude?: number; longitude?: number };
    phone?: string;
    acceptTerms: boolean;
  }) => Promise<Record<string, unknown>>;
};

export const useCheckout = create<CheckoutState>((set, get) => ({
  loading: false,
  total: 0,
  submitOrder: async ({ addressId, addressInput, phone, acceptTerms }) => {
    set({ loading: true });
    const items = getCartItems();
    const total = items.reduce((sum, item) => sum + item.price * item.quantity, 0);
    const coords = useLocationStore.getState().coords;
    const service = useServiceability.getState().data;
    const deliveryFee =
      service?.delivery_type === "IN_ZONE" ? service.delivery_fee_amount ?? 0 : 0;
    const payloadTotal = total + deliveryFee;
    try {
      const res = await endpoints.createOrder({
        vendor: service?.vendor?.id,
        delivery_address: addressId,
        delivery_address_data: !addressId ? addressInput : undefined,
        customer_phone: phone,
        accept_terms: acceptTerms,
        payment_method: "ONLINE",
        items: items.map((item) => ({
          product: item.productId,
          quantity: item.quantity,
          modifiers: item.options,
        })),
        total_amount: payloadTotal,
        delivery_type: service?.delivery_type,
        delivery_fee_amount: deliveryFee,
        customer_location: coords
          ? {
              latitude: coords.latitude,
              longitude: coords.longitude,
              accuracy: coords.accuracy,
            }
          : undefined,
      });
      let paymentUrl = (res.data as { payment_url?: string | null }).payment_url ?? null;
      const orderId = (res.data as { id?: string | null }).id;
      if (!paymentUrl && orderId) {
        try {
          const paymentRes = await endpoints.payForOrder(String(orderId));
          paymentUrl = (paymentRes.data as { payment_url?: string | null }).payment_url ?? paymentUrl;
        } catch {
          // Swallow payment link errors here; caller can decide on next steps.
        }
      }
      useCart.getState().clear();
      if ((res.data as { auth?: { access: string; refresh: string; user: unknown } }).auth) {
        useAuth.getState().applyAuthPayload(res.data.auth as never);
      }
      useAuth.getState().setActiveOrder({
        id: String((res.data as { id?: string }).id || ""),
        short_code: String((res.data as { short_code?: string }).short_code || ""),
        status: String((res.data as { status?: string }).status || "PLACED"),
      });
      return { ...(res.data as Record<string, unknown>), payment_url: paymentUrl };
    } finally {
      set({ loading: false, total: payloadTotal });
    }
  },
}));

function getCartItems() {
  return useCart.getState().items;
}
