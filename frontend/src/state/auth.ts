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
  user:
    typeof window !== "undefined" && localStorage.getItem("vaadeh_user_phone")
      ? {
          id: localStorage.getItem("vaadeh_user_phone") as string,
          phone: localStorage.getItem("vaadeh_user_phone") as string,
        }
      : null,
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
    set({ loading: true });
    try {
      // TODO: replace with real verify endpoint. For now, just store the phone as session placeholder.
      localStorage.setItem("vaadeh_access", "demo-token");
      localStorage.setItem("vaadeh_user_phone", phone);
      set({ user: { id: phone, phone } });
    } finally {
      set({ loading: false });
    }
  },
  logout: () => {
    localStorage.removeItem("vaadeh_access");
    localStorage.removeItem("vaadeh_user_phone");
    set({ user: null });
  },
}));
