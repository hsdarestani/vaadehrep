import { useCallback, useEffect } from "react";

import { useLocationStore } from "../state/location";

export function useGeolocation(autoRequest = false) {
  const { coords, status, error, setCoords, setStatus } = useLocationStore();

  const requestLocation = useCallback(() => {
    if (typeof navigator === "undefined" || !("geolocation" in navigator)) {
      setStatus("unsupported", "موقعیت مکانی توسط مرورگر پشتیبانی نمی‌شود.");
      return;
    }

    setStatus("prompting");
    navigator.geolocation.getCurrentPosition(
      (position) => {
        setCoords({
          latitude: position.coords.latitude,
          longitude: position.coords.longitude,
          accuracy: position.coords.accuracy,
        });
      },
      (err) => {
        if (err.code === err.PERMISSION_DENIED) {
          setStatus("denied", "دسترسی موقعیت مکانی رد شد.");
          return;
        }
        setStatus("error", "خطا در دریافت موقعیت مکانی.");
      },
      { enableHighAccuracy: true, timeout: 10000 },
    );
  }, [setCoords, setStatus]);

  useEffect(() => {
    if (autoRequest && status === "idle") {
      requestLocation();
    }
  }, [autoRequest, requestLocation, status]);

  return { coords, status, error, requestLocation };
}
