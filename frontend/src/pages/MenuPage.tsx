import { useEffect, useMemo, useRef, useState } from "react";

import type { ServiceabilityResponse } from "../api/types";
import { Card } from "../components/common/Card";
import { LocationPicker } from "../components/LocationPicker";
import { useGeolocation } from "../hooks/useGeolocation";
import { useServiceability } from "../state/serviceability";
import { type ItemModifier, useCart } from "../state/cart";
import { useLocationStore } from "../state/location";

const SAUCE_OPTIONS = [
  { key: "garlic_lemon", label: "سس سیر و لیمو (۳۰ گرم)", sizeGrams: 30 },
  { key: "mango", label: "سس انبه (۳۰ گرم)", sizeGrams: 30 },
  { key: "herby", label: "سس سبزیجات (۳۰ گرم)", sizeGrams: 30 },
  { key: "pepper", label: "سس فلفلی (۳۰ گرم)", sizeGrams: 30 },
  { key: "tomato_roast", label: "سس گوجه کبابی (۳۰ گرم)", sizeGrams: 30 },
  { key: "greek_yogurt", label: "سس ماست یونانی (۳۰ گرم)", sizeGrams: 30 },
  { key: "no_sauce", label: "سس نمی‌خواهم" },
] as const;

const DRINK_OPTIONS = [
  { key: "zero", label: "زیرو" },
  { key: "water", label: "آب معدنی" },
  { key: "malt_delight", label: "مالت دلایت" },
  { key: "no_drink", label: "نمی‌خواهم نوشیدنی" },
] as const;

const NO_SAUCE_KEY = "no_sauce";

type ProductSummary = ServiceabilityResponse["menu_products"][number];
type SelectionState = {
  product: ProductSummary;
  sauceKey: string;
  drinkKey: string;
};

export function MenuPage() {
  const { data: service, loading: serviceLoading, evaluate } = useServiceability();
  const [showMap, setShowMap] = useState(false);
  const { coords, status, requestLocation } = useGeolocation(true);
  const setCoords = useLocationStore((state) => state.setCoords);
  const addToCart = useCart((s) => s.add);
  const [feedback, setFeedback] = useState<string | null>(null);
  const timerRef = useRef<number | null>(null);
  const [selection, setSelection] = useState<SelectionState | null>(null);

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

  const openOptionSelector = (product: ProductSummary) => {
    setSelection({ product, sauceKey: "", drinkKey: "" });
  };

  const closeOptionSelector = () => setSelection(null);

  const handleConfirmSelection = () => {
    if (!selection) return;
    const sauce = SAUCE_OPTIONS.find((opt) => opt.key === selection.sauceKey);
    if (!sauce) return;
    const needsDrink = sauce.key === NO_SAUCE_KEY;
    if (needsDrink && !selection.drinkKey) return;
    const modifiers: ItemModifier[] = [
      { type: "sauce", key: sauce.key, label: sauce.label, size_grams: sauce.sizeGrams },
    ];
    if (needsDrink) {
      const drink = DRINK_OPTIONS.find((opt) => opt.key === selection.drinkKey);
      if (!drink) return;
      modifiers.push({ type: "drink", key: drink.key, label: drink.label });
    }
    addToCart({
      productId: selection.product.id,
      title: selection.product.name_fa,
      price: selection.product.base_price || 0,
      quantity: 1,
      options: modifiers,
    });
    if (timerRef.current) {
      window.clearTimeout(timerRef.current);
    }
    setFeedback(`${selection.product.name_fa} به سبد خرید اضافه شد`);
    timerRef.current = window.setTimeout(() => setFeedback(null), 2500);
    closeOptionSelector();
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
    <>
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
                    <button className="primary-button" onClick={() => openOptionSelector(product)}>
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
      {selection ? (
        <div className="modal-backdrop" role="dialog" aria-modal="true">
          <div className="modal-panel">
            <div className="modal-head">
              <div>
                <p className="muted" style={{ margin: 0 }}>
                  انتخاب‌های الزامی
                </p>
                <h3 style={{ margin: "4px 0 0" }}>{selection.product.name_fa}</h3>
              </div>
              <button type="button" className="ghost-button" onClick={closeOptionSelector}>
                بستن
              </button>
            </div>
            <div className="modal-body">
              <section className="choice-section">
                <p className="muted" style={{ margin: "0 0 8px" }}>
                  ابتدا غذای بدون سس انتخاب می‌شود. یک سس ۳۰ گرمی را الزاما برگزینید:
                </p>
                <div className="choice-list">
                  {SAUCE_OPTIONS.map((opt) => (
                    <label key={opt.key} className="choice-card">
                      <input
                        type="radio"
                        name="sauce"
                        checked={selection.sauceKey === opt.key}
                        onChange={() => setSelection((prev) => (prev ? { ...prev, sauceKey: opt.key, drinkKey: "" } : prev))}
                      />
                      <span>{opt.label}</span>
                    </label>
                  ))}
                </div>
              </section>

              {selection.sauceKey === NO_SAUCE_KEY ? (
                <section className="choice-section">
                  <p className="muted" style={{ margin: "0 0 8px" }}>
                    بدون سس انتخاب شد؛ یکی از نوشیدنی‌های زیر را انتخاب کنید:
                  </p>
                  <div className="choice-list">
                    {DRINK_OPTIONS.map((opt) => (
                      <label key={opt.key} className="choice-card">
                        <input
                          type="radio"
                          name="drink"
                          checked={selection.drinkKey === opt.key}
                          onChange={() => setSelection((prev) => (prev ? { ...prev, drinkKey: opt.key } : prev))}
                        />
                        <span>{opt.label}</span>
                      </label>
                    ))}
                  </div>
                </section>
              ) : null}
            </div>
            <div className="modal-actions">
              <button type="button" className="ghost-button" onClick={closeOptionSelector}>
                انصراف
              </button>
              <button
                type="button"
                className="primary-button"
                disabled={!selection.sauceKey || (selection.sauceKey === NO_SAUCE_KEY && !selection.drinkKey)}
                onClick={handleConfirmSelection}
              >
                افزودن به سبد
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </>
  );
}

function formatCurrency(amount?: number | null) {
  const value = amount ?? 0;
  return Intl.NumberFormat("fa-IR", { style: "currency", currency: "IRR", maximumFractionDigits: 0 }).format(value);
}
