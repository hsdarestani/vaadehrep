import { api } from "./client";
import type { Address, Order, Product, Vendor } from "./types";

export const endpoints = {
  vendors: () => api.get<Vendor[]>("/vendors/vendors/"),
  productsByVendor: (vendorId: number) => api.get<Product[]>("/catalog/products/", { params: { vendor: vendorId } }),
  addresses: () => api.get<Address[]>("/addresses/addresses/"),
  createAddress: (payload: Partial<Address>) => api.post<Address>("/addresses/addresses/", payload),
  orders: () => api.get<Order[]>("/orders/orders/"),
  createOrder: (payload: Record<string, unknown>) => api.post("/orders/orders/", payload),
  requestOtp: (phone: string) =>
    api.post("/accounts/login-otps/", {
      phone,
      purpose: "LOGIN",
      code_hash: "placeholder",
      salt: "placeholder",
      expires_at: new Date().toISOString(),
    }),
};
