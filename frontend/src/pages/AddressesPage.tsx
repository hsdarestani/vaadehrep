import { FormEvent, useMemo, useState } from "react";
import { Navigate, useLocation } from "react-router-dom";

import { useAddressBook } from "../hooks/useAddressBook";
import { LocationPicker } from "../components/LocationPicker";
import { useGeolocation } from "../hooks/useGeolocation";
import { useAuth } from "../state/auth";
import { useLocationStore } from "../state/location";
import { Card } from "../components/common/Card";

export function AddressesPage() {
  const { user, activeOrder } = useAuth();
  const location = useLocation();
  const { addresses, createAddress, isLoading, removeAddress } = useAddressBook(!!user);
  const [title, setTitle] = useState("");
  const [fullText, setFullText] = useState("");
  const { coords, status, requestLocation } = useGeolocation(!!user);
  const setCoords = useLocationStore((state) => state.setCoords);
  const [showMap, setShowMap] = useState(false);
  const canModify = !!user && !activeOrder;

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    const saved = await createAddress({
      title,
      full_text: fullText,
      latitude: coords?.latitude,
      longitude: coords?.longitude,
    });
    if (saved && saved.id) {
      setTitle("");
      setFullText("");
    }
  };

  if (!user) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  }

  const locationStatusText = useMemo(() => {
    if (status === "granted" && coords) {
      return "موقعیت دریافت شد.";
    }
    if (status === "prompting") return "در حال دریافت موقعیت...";
    if (status === "denied") return "اجازه دسترسی به موقعیت داده نشد.";
    if (status === "unsupported") return "مرورگر از موقعیت مکانی پشتیبانی نمی‌کند.";
    if (status === "error") return "دریافت موقعیت با خطا روبه‌رو شد.";
    return "برای ثبت دقیق‌تر آدرس، لطفا موقعیت خود را فعال کنید.";
  }, [coords, status]);

  return (
    <section className="section">
      <div className="container small">
        <div className="section-head" style={{ textAlign: "center" }}>
          <span className="section-eyebrow">دفترچه آدرس</span>
          <h1 className="section-title" style={{ marginBottom: 8 }}>
            آدرس‌های من
          </h1>
          <p className="section-subtitle">آدرس‌های ذخیره‌شده و موقعیت انتخاب‌شده‌ات در این صفحه نمایش داده می‌شوند.</p>
        </div>

        <div className="location-banner">
          <div>
            <p className="muted" style={{ margin: 0, fontWeight: 700 }}>
              موقعیت شما
            </p>
            <strong>{locationStatusText}</strong>
          </div>
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            <button className="secondary-button" type="button" onClick={requestLocation}>
              دریافت موقعیت
            </button>
            <button className="ghost-button" type="button" onClick={() => setShowMap((v) => !v)}>
              {showMap ? "بستن نقشه" : "انتخاب روی نقشه"}
            </button>
          </div>
        </div>

        {showMap ? (
          <div className="stacked-form" style={{ marginTop: 16 }}>
            <LocationPicker
              value={coords ? { latitude: coords.latitude, longitude: coords.longitude } : undefined}
              onChange={(nextCoords) => setCoords(nextCoords)}
            />
            {coords ? (
              <p className="muted" style={{ margin: 0 }}>
                مختصات انتخاب‌شده: {coords.latitude.toFixed(6)}, {coords.longitude.toFixed(6)}
              </p>
            ) : (
              <p className="muted" style={{ margin: 0 }}>
                برای ذخیره موقعیت، روی نقشه کلیک کنید.
              </p>
            )}
          </div>
        ) : null}

        <form onSubmit={handleSubmit} className="stacked-form">
          <label>
            <span className="muted">عنوان</span>
            <input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="خانه / محل کار"
              required
              className="input-field"
              disabled={!canModify}
            />
          </label>
          <label>
            <span className="muted">آدرس کامل</span>
            <textarea
              value={fullText}
              onChange={(e) => setFullText(e.target.value)}
              required
              rows={3}
              className="input-field"
              disabled={!canModify}
            />
          </label>
          <button type="submit" className="primary-button" style={{ width: "100%" }} disabled={!canModify}>
            ذخیره آدرس
          </button>
          {!canModify ? (
            <p className="muted" style={{ margin: 0 }}>
              تا زمانی که سفارش فعالی دارید امکان تغییر یا حذف آدرس وجود ندارد.
            </p>
          ) : null}
        </form>

        {isLoading ? (
          <p className="muted" style={{ textAlign: "center" }}>
            در حال بارگذاری…
          </p>
        ) : (
          <div className="card-grid centered-grid">
            {(addresses || []).map((address) => (
              <Card
                key={address.id}
                title={address.title || "آدرس"}
                description={
                  <>
                    <p style={{ margin: 0 }}>{address.full_text}</p>
                    <p className="muted" style={{ margin: 0 }}>
                      شهر: {address.city || "—"}
                    </p>
                  </>
                }
                footer={
                  <button
                    className="ghost-button"
                    type="button"
                    onClick={() => removeAddress(address.id)}
                    disabled={!canModify}
                  >
                    حذف
                  </button>
                }
              >
                <p className="muted">شهر: {address.city || "—"}</p>
              </Card>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}
