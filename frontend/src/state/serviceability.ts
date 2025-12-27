import { create } from "zustand";

import { endpoints } from "../api/endpoints";
import type { ServiceabilityResponse } from "../api/types";
import { useAuth } from "./auth";
import { useLocationStore } from "./location";

type EvaluateInput = {
  coords?: { latitude: number; longitude: number; accuracy?: number };
  addressId?: number | string;
  vendorId?: number;
  items?: Array<{ vendor?: number }>;
};

type ServiceabilityState = {
  data?: ServiceabilityResponse;
  loading: boolean;
  error?: unknown;
  evaluate: (params?: EvaluateInput) => Promise<void>;
  clear: () => void;
};

export const useServiceability = create<ServiceabilityState>((set) => ({
  data: undefined,
  loading: false,
  error: undefined,
  evaluate: async (params) => {
    set({ loading: true });
    const coords = params?.coords || useLocationStore.getState().coords;
    try {
      const { data } = await endpoints.serviceability({
        location: coords
          ? { latitude: coords.latitude, longitude: coords.longitude, accuracy: coords.accuracy }
          : undefined,
        address_id: params?.addressId,
        vendor: params?.vendorId,
        items: params?.items,
      });
      set({ data, error: undefined });
      if (data.active_order) {
        useAuth.getState().setActiveOrder(data.active_order);
      }
    } catch (error) {
      set({ error });
    } finally {
      set({ loading: false });
    }
  },
  clear: () => set({ data: undefined, error: undefined }),
}));
