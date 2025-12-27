import { useEffect, useMemo, useRef, useState } from "react";

import { Card } from "../components/common/Card";
import { LocationPicker } from "../components/LocationPicker";
import { useGeolocation } from "../hooks/useGeolocation";
import { useServiceability } from "../state/serviceability";
import { useCart } from "../state/cart";
import { useLocationStore } from "../state/location";

export function MenuPage() {
  const { data: service, loading: serviceLoading, evaluate } = useServiceability();
  const [showMap, setShowMap] = useState(false);
  const { coords, status, requestLocation } = useGeolocation(true);
  const setCoords = useLocationStore((state) => state.setCoords);
  const addToCart = useCart((s) => s.add);
  const [feedback, setFeedback] = useState<string | null>(null);
  const timerRef = useRef<number | null>(null);

  useEffect(() => {
    return () => {
      if (timerRef.current) {
        window.clearTimeout(timerRef.current);
      }
    };
  }, []);

  useEffect(() => {
    if (coords) {
      void evaluate({ coords });
    }
  }, [coords, evaluate]);

  const sortedProducts = useMemo(() => {
    if (service?.menu_products?.length) {
      return [...service.menu_products].sort((a, b) => (a.sort_order ?? 0) - (b.sort_order ?? 0));
    }
    return [];
  }, [service?.menu_products]);

  const handleAddToCart = (product: (typeof sortedProducts)[number]) => {
    addToCart({
      productId: product.id,
      title: product.name_fa,
      price: product.base_price || 0,
      quantity: 1,
      options: [],
    });
    if (timerRef.current) {
      window.clearTimeout(timerRef.current);
    }
    setFeedback(`${product.name_fa} به سبد خرید اضافه شد`);
    timerRef.current = window.setTimeout(() => setFeedback(null), 2500);
  };

  const handleManualLocation = (lat: number, lng: number) => {
    setCoords({ latitude: lat, longitude: lng });
    void evaluate({ coords: { latitude: lat, longitude: lng } });
  };

  const locationStatusText = useMemo(() => {
    if (status === "granted" && coords) return "موقعیت شما ثبت شد و منو بر اساس آن فیلتر شده است.";
    if (status === "prompting") return "در حال دریافت موقعیت...";
    if (status === "denied") return "اجازه دسترسی داده نشد. می‌توانید روی نقشه انتخاب کنید.";
    if (status === "error") return "دریافت موقعیت با خطا مواجه شد.";
    if (status === "unsupported") return "مرورگر از موقعیت مکانی پشتیبانی نمی‌کند.";
    return "برای دیدن نزدیک‌ترین آشپزخانه، موقعیت خود را مشخص کنید.";
  }, [coords, status]);

  return (
    <section className="section">
      <div className="container">
        <div className="section-head" style={{ textAlign: "center" }}>
          <span className="section-eyebrow">منوی امروز</span>
          <h1 className="section-title" style={{ marginBottom: 8 }}>
            انتخاب غذای سالم از منو
          </h1>
          <p className="section-subtitle">ابتدا رستوران را انتخاب کن و سپس آیتم مورد نظرت را به سبد اضافه کن.</p>
        </div>

        {feedback ? <div className="feedback success">{feedback}</div> : null}

        <div className="location-banner">
          <div>
            <p className="muted" style={{ margin: 0, fontWeight: 700 }}>
              موقعیت شما
            </p>
            <strong>{locationStatusText}</strong>
            {service?.vendor ? (
              <p className="muted" style={{ margin: 0 }}>
                نزدیک‌ترین آشپزخانه: {service.vendor.name} • ارسال: {service.delivery_label}{" "}
                {service.delivery_type === "IN_ZONE" ? formatCurrency(service.delivery_fee_amount) : "پس‌کرایه"}
              </p>
            ) : null}
          </div>
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            <button className="secondary-button" type="button" onClick={requestLocation}>
              دریافت موقعیت خودکار
            </button>
            <button className="ghost-button" type="button" onClick={() => setShowMap((v) => !v)}>
              {showMap ? "بستن نقشه" : "انتخاب روی نقشه"}
            </button>
            <button className="ghost-button" type="button" onClick={() => evaluate()}>
              به‌روزرسانی سرویس
            </button>
          </div>
        </div>

        {showMap ? (
          <div className="stacked-form" style={{ marginTop: 16 }}>
            <LocationPicker
              value={coords ? { latitude: coords.latitude, longitude: coords.longitude } : undefined}
              onChange={(nextCoords) => handleManualLocation(nextCoords.latitude, nextCoords.longitude)}
            />
            {coords ? (
              <p className="muted" style={{ margin: 0 }}>
                مختصات انتخاب‌شده: {coords.latitude.toFixed(6)}, {coords.longitude.toFixed(6)}
              </p>
            ) : (
              <p className="muted" style={{ margin: 0 }}>
                برای فیلتر منو، روی نقشه نقطه‌ی مدنظر را انتخاب کنید.
              </p>
            )}
          </div>
        ) : null}

        {serviceLoading ? (
          <p className="muted" style={{ textAlign: "center" }}>
            در حال بارگذاری منو...
          </p>
        ) : !service?.is_serviceable ? (
          <div className="card" style={{ marginTop: 16 }}>
            <p className="muted" style={{ margin: 0 }}>
              هنوز موقعیت شما مشخص نشده است یا در محدوده‌ی پوشش نیستید. لطفا موقعیت خود را تعیین کنید.
            </p>
          </div>
        ) : (
          <div className="card-grid centered-grid">
            {sortedProducts.map((product) => (
              <Card
                key={product.id}
                title={product.name_fa}
                description={product.short_description || product.description}
                footer={
                  <button className="primary-button" onClick={() => handleAddToCart(product)}>
                    افزودن به سبد
                  </button>
                }
              >
                <p style={{ marginTop: 8, fontWeight: 600 }}>{formatCurrency(product.base_price)}</p>
                {service?.suggested_product_ids?.includes(product.id) ? (
                  <p className="pill small" style={{ display: "inline-block", marginTop: 8 }}>
                    پیشنهادی برای شما
                  </p>
                ) : null}
              </Card>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}

function formatCurrency(amount?: number | null) {
  const value = amount ?? 0;
  return Intl.NumberFormat("fa-IR", { style: "currency", currency: "IRR", maximumFractionDigits: 0 }).format(value);
}
