import { useEffect, useState } from "react";

import { endpoints } from "../api/endpoints";
import type { Address } from "../api/types";

export function useAddressBook(enabled = true) {
  const [addresses, setAddresses] = useState<Address[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<unknown>();

  const load = async () => {
    if (!enabled) {
      setAddresses([]);
      setIsLoading(false);
      return;
    }
    setIsLoading(true);
    try {
      const res = await endpoints.addresses();
      setAddresses(res.data);
    } catch (err) {
      setError(err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    void load();
  }, [enabled]);

  const createAddress = async (payload: Partial<Address>) => {
    const res = await endpoints.createAddress(payload);
    setAddresses((prev) => [res.data, ...prev]);
    return res.data;
  };

  const updateAddress = async (id: number, payload: Partial<Address>) => {
    const res = await endpoints.updateAddress(id, payload);
    setAddresses((prev) => prev.map((addr) => (addr.id === id ? res.data : addr)));
    return res.data;
  };

  const removeAddress = async (id: number) => {
    await endpoints.deleteAddress(id);
    setAddresses((prev) => prev.filter((addr) => addr.id !== id));
  };

  return { addresses, isLoading, error, createAddress, updateAddress, removeAddress };
}
