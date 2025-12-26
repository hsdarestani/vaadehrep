import { useEffect, useState } from "react";

import { endpoints } from "../api/endpoints";
import type { Address } from "../api/types";

export function useAddressBook() {
  const [addresses, setAddresses] = useState<Address[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<unknown>();

  const load = async () => {
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
  }, []);

  const createAddress = async (payload: Partial<Address>) => {
    const res = await endpoints.createAddress(payload);
    setAddresses((prev) => [res.data, ...prev]);
  };

  return { addresses, isLoading, error, createAddress };
}
