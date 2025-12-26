import { create } from "zustand";

import { endpoints } from "../api/endpoints";
import type { UserProfile } from "../api/types";

type AuthState = {
  user?: UserProfile | null;
  loading: boolean;
  requestOtp: (phone: string) => Promise<void>;
  verifyOtp: (phone: string, code: string) => Promise<void>;
  logout: () => void;
};

export const useAuth = create<AuthState>((set) => ({
  user: undefined,
  loading: false,
  requestOtp: async (phone: string) => {
    set({ loading: true });
    try {
      await endpoints.requestOtp(phone);
    } finally {
      set({ loading: false });
    }
  },
  verifyOtp: async (phone: string, _code: string) => {
    // TODO: replace with real verify endpoint. For now, just store the phone as session placeholder.
    localStorage.setItem("vaadeh_access", "demo-token");
    set({ user: { id: phone, phone }, loading: false });
  },
  logout: () => {
    localStorage.removeItem("vaadeh_access");
    set({ user: null });
  },
}));
