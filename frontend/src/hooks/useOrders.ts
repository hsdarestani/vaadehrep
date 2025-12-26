import { useEffect, useState } from "react";

import { endpoints } from "../api/endpoints";
import type { Order } from "../api/types";

export function useOrders(enabled = true) {
  const [orders, setOrders] = useState<Order[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<unknown>();

  useEffect(() => {
    let isMounted = true;
    if (!enabled) {
      setOrders([]);
      setIsLoading(false);
      return () => {
        isMounted = false;
      };
    }

    setIsLoading(true);
    endpoints
      .orders()
      .then((res) => {
        if (!isMounted) return;
        setOrders(res.data);
      })
      .catch((err) => {
        if (!isMounted) return;
        setError(err);
      })
      .finally(() => {
        if (isMounted) setIsLoading(false);
      });

    return () => {
      isMounted = false;
    };
  }, [enabled]);

  return { orders, isLoading, error };
}
