import { useEffect, useState } from "react";

import { endpoints } from "../api/endpoints";
import type { Product, Vendor } from "../api/types";

type CatalogState = {
  vendors?: Vendor[];
  products?: Product[];
  isLoading: boolean;
  error?: unknown;
};

export function useVendorCatalog(vendorId?: number) {
  const [state, setState] = useState<CatalogState>({ isLoading: true });

  useEffect(() => {
    let isMounted = true;
    setState((prev) => ({ ...prev, isLoading: true }));

    async function load() {
      try {
        const [vendorsRes, productsRes] = await Promise.all([
          endpoints.vendors(),
          vendorId ? endpoints.productsByVendor(vendorId) : Promise.resolve({ data: [] as Product[] }),
        ]);
        if (!isMounted) return;
        setState({
          vendors: vendorsRes.data,
          products: productsRes.data,
          isLoading: false,
        });
      } catch (error) {
        if (!isMounted) return;
        setState((prev) => ({ ...prev, isLoading: false, error }));
      }
    }

    load();

    return () => {
      isMounted = false;
    };
  }, [vendorId]);

  return state;
}
