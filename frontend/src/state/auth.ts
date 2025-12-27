import { create } from "zustand";

import { endpoints } from "../api/endpoints";
import type { UserProfile } from "../api/types";

const loadStoredUser = (): UserProfile | null => {
  if (typeof window === "undefined") {
    return null;
  }
  const raw = localStorage.getItem("vaadeh_user");
  if (!raw) {
    return null;
  }
  try {
    return JSON.parse(raw) as UserProfile;
  } catch {
    localStorage.removeItem("vaadeh_user");
    return null;
  }
};

const ensureDeviceId = (): string | undefined => {
  if (typeof window === "undefined") {
    return undefined;
  }
  const existing = localStorage.getItem("vaadeh_device_id");
  if (existing) {
    return existing;
  }
  const newId =
    typeof crypto !== "undefined" && "randomUUID" in crypto
      ? crypto.randomUUID()
      : Math.random().toString(36).slice(2, 12);
  localStorage.setItem("vaadeh_device_id", newId);
  return newId;
};

type AuthState = {
  user?: UserProfile | null;
  loading: boolean;
  requestOtp: (phone: string) => Promise<void>;
  verifyOtp: (phone: string, code: string) => Promise<void>;
  logout: () => void;
};

export const useAuth = create<AuthState>((set) => ({
  user: loadStoredUser(),
  loading: false,
  requestOtp: async (phone: string) => {
    set({ loading: true });
    try {
      await endpoints.requestOtp(phone);
    } finally {
      set({ loading: false });
    }
  },
  verifyOtp: async (phone: string, code: string) => {
    set({ loading: true });
    try {
      const device_id = ensureDeviceId();
      const device_title = typeof navigator !== "undefined" ? navigator.userAgent.slice(0, 120) : undefined;
      const { data } = await endpoints.verifyOtp({ phone, code, device_id, device_title });

      localStorage.setItem("vaadeh_access", data.access);
      localStorage.setItem("vaadeh_refresh", data.refresh);
      localStorage.setItem("vaadeh_user", JSON.stringify(data.user));
      set({ user: data.user });
    } finally {
      set({ loading: false });
    }
  },
  logout: () => {
    localStorage.removeItem("vaadeh_access");
    localStorage.removeItem("vaadeh_refresh");
    localStorage.removeItem("vaadeh_user");
    set({ user: null });
  },
}));
