import { api } from "./client";
import type {
  Address,
  Order,
  Product,
  ServiceabilityResponse,
  SessionResponse,
  Vendor,
  VerifyLoginResponse,
} from "./types";

export const endpoints = {
  vendors: () => api.get<Vendor[]>("/vendors/vendors/"),
  productsByVendor: (vendorId: number) => api.get<Product[]>("/catalog/products/", { params: { vendor: vendorId } }),
  addresses: () => api.get<Address[]>("/addresses/addresses/"),
  createAddress: (payload: Partial<Address>) => api.post<Address>("/addresses/addresses/", payload),
  updateAddress: (id: number, payload: Partial<Address>) => api.patch<Address>(`/addresses/addresses/${id}/`, payload),
  deleteAddress: (id: number) => api.delete(`/addresses/addresses/${id}/`),
  orders: () => api.get<Order[]>("/orders/orders/"),
  createOrder: (payload: Record<string, unknown>) =>
    api.post<Order & { payment_url?: string | null }>("/orders/orders/", payload),
  serviceability: (payload: Record<string, unknown>) =>
    api.post<ServiceabilityResponse>("/orders/serviceability/", payload),
  session: () => api.get<SessionResponse>("/accounts/session/"),
  requestOtp: (phone: string) =>
    api.post("/accounts/login-otps/", {
      phone,
      purpose: "LOGIN",
    }),
  verifyOtp: (payload: { phone: string; code: string; device_id?: string; device_title?: string }) =>
    api.post<VerifyLoginResponse>("/accounts/verify-login/", payload),
};
