import { useEffect, useMemo, useRef, useState } from "react";

import type { ServiceabilityResponse } from "../api/types";
import { Card } from "../components/common/Card";
import { LocationPicker } from "../components/LocationPicker";
import { useGeolocation } from "../hooks/useGeolocation";
import { useServiceability } from "../state/serviceability";
import { type ItemModifier, useCart } from "../state/cart";
import { useLocationStore } from "../state/location";

const SAUCE_OPTIONS = [
  { key: "garlic_lemon", label: "سس سیر و لیمو", sizeGrams: 30, price: 15000 },
  { key: "mango", label: "سس انبه", sizeGrams: 30, price: 15000 },
  { key: "herby", label: "سس سبزیجات", sizeGrams: 30, price: 15000 },
  { key: "pepper", label: "سس فلفلی", sizeGrams: 30, price: 15000 },
  { key: "tomato_roast", label: "سس گوجه کبابی", sizeGrams: 30, price: 15000 },
  { key: "greek_yogurt", label: "سس ماست یونانی", sizeGrams: 30, price: 15000 },
  { key: "no_sauce", label: "سس نمی‌خواهم", price: 0 },
] as const;

const DRINK_OPTIONS = [
  { key: "zero", label: "زیرو", price: 25000 },
  { key: "water", label: "آب معدنی", price: 10000 },
  { key: "malt_delight", label: "مالت دلایت", price: 28000 },
  { key: "no_drink", label: "نمی‌خواهم نوشیدنی", price: 0 },
] as const;

const NO_SAUCE_KEY = "no_sauce";
const NO_DRINK_KEY = "no_drink";

type ProductSummary = ServiceabilityResponse["menu_products"][number];
type SelectionState = {
  product: ProductSummary;
  sauces: Record<string, number>;
  drinks: Record<string, number>;
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
    setSelection({ product, sauces: {}, drinks: {} });
  };

  const closeOptionSelector = () => setSelection(null);

  const updateSauce = (key: string, qty: number) => {
    setSelection((prev) => {
      if (!prev) return prev;
      const nextSauces = { ...(prev.sauces || {}) };
      if (key === NO_SAUCE_KEY) {
        if (qty > 0) {
          nextSauces[NO_SAUCE_KEY] = 1;
          Object.keys(nextSauces).forEach((sauceKey) => {
            if (sauceKey !== NO_SAUCE_KEY) delete nextSauces[sauceKey];
          });
        } else {
          delete nextSauces[NO_SAUCE_KEY];
        }
      } else {
        if (nextSauces[NO_SAUCE_KEY]) {
          delete nextSauces[NO_SAUCE_KEY];
        }
        if (qty > 0) {
          nextSauces[key] = qty;
        } else {
          delete nextSauces[key];
        }
      }
      return { ...prev, sauces: nextSauces };
    });
  };

  const updateDrink = (key: string, qty: number) => {
    setSelection((prev) => {
      if (!prev) return prev;
      const nextDrinks = { ...(prev.drinks || {}) };
      if (key === NO_DRINK_KEY) {
        if (qty > 0) {
          nextDrinks[NO_DRINK_KEY] = 1;
          Object.keys(nextDrinks).forEach((drinkKey) => {
            if (drinkKey !== NO_DRINK_KEY) delete nextDrinks[drinkKey];
          });
        } else {
          delete nextDrinks[NO_DRINK_KEY];
        }
      } else {
        if (nextDrinks[NO_DRINK_KEY]) {
          delete nextDrinks[NO_DRINK_KEY];
        }
        if (qty > 0) {
          nextDrinks[key] = qty;
        } else {
          delete nextDrinks[key];
        }
      }
      return { ...prev, drinks: nextDrinks };
    });
  };

  const handleConfirmSelection = () => {
    if (!selection) return;
    const modifiers = buildModifiers(selection);
    const { valid, error } = validateSelection(modifiers);
    if (!valid) {
      setFeedback(error || "انتخاب‌ها کامل نیست.");
      return;
    }
    const modifiersTotal = modifiers.reduce(
      (sum, mod) => sum + (mod.price || 0) * (mod.quantity ?? 1),
      0,
    );
    addToCart({
      productId: selection.product.id,
      title: selection.product.name_fa,
      price: (selection.product.base_price || 0) + modifiersTotal,
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
                  ابتدا غذای بدون سس انتخاب می‌شود. یک یا چند سس ۳۰ گرمی را برگزینید (امکان انتخاب چندباره یک سس نیز هست):
                </p>
                <div className="choice-list">
                  {SAUCE_OPTIONS.map((opt) => {
                    const qty = selection.sauces[opt.key] || 0;
                    const isNoSauce = opt.key === NO_SAUCE_KEY;
                    const disabled = isNoSauce ? false : selection.sauces[NO_SAUCE_KEY] > 0;
                    return (
                      <label key={opt.key} className="choice-card">
                        <input
                          type="checkbox"
                          checked={qty > 0}
                          disabled={disabled}
                          onChange={(e) => updateSauce(opt.key, e.target.checked ? 1 : 0)}
                        />
                        <div className="choice-meta">
                          <strong>{opt.label}</strong>
                          <p className="muted" style={{ margin: "4px 0 0" }}>
                            {isNoSauce ? "بدون سس" : `${opt.sizeGrams ?? 30} گرم`} • {formatCurrency(opt.price)}
                          </p>
                        </div>
                        {!isNoSauce ? (
                          <input
                            type="number"
                            min={1}
                            max={5}
                            value={qty > 0 ? qty : ""}
                            placeholder="تعداد"
                            onChange={(e) => updateSauce(opt.key, Math.max(0, Number(e.target.value) || 0))}
                            className="input-field dense"
                            style={{ width: 80 }}
                            disabled={disabled}
                          />
                        ) : null}
                      </label>
                    );
                  })}
                </div>
              </section>

              <section className="choice-section">
                <p className="muted" style={{ margin: "0 0 8px" }}>
                  نوشیدنی را انتخاب کنید (امکان چند گزینه و چند عدد وجود دارد). اگر «بدون سس» را زده‌اید، انتخاب نوشیدنی الزامی است.
                </p>
                <div className="choice-list">
                  {DRINK_OPTIONS.map((opt) => {
                    const qty = selection.drinks[opt.key] || 0;
                    const isNoDrink = opt.key === NO_DRINK_KEY;
                    const hasOtherDrinks = Object.entries(selection.drinks).some(
                      ([key, val]) => key !== NO_DRINK_KEY && val > 0,
                    );
                    const disabled = isNoDrink ? hasOtherDrinks : selection.drinks[NO_DRINK_KEY] > 0;
                    return (
                      <label key={opt.key} className="choice-card">
                        <input
                          type="checkbox"
                          checked={qty > 0}
                          disabled={disabled}
                          onChange={(e) => updateDrink(opt.key, e.target.checked ? 1 : 0)}
                        />
                        <div className="choice-meta">
                          <strong>{opt.label}</strong>
                          <p className="muted" style={{ margin: "4px 0 0" }}>
                            {formatCurrency(opt.price)}
                          </p>
                        </div>
                        {!isNoDrink ? (
                          <input
                            type="number"
                            min={1}
                            max={5}
                            value={qty > 0 ? qty : ""}
                            placeholder="تعداد"
                            onChange={(e) => updateDrink(opt.key, Math.max(0, Number(e.target.value) || 0))}
                            className="input-field dense"
                            style={{ width: 80 }}
                            disabled={disabled}
                          />
                        ) : null}
                      </label>
                    );
                  })}
                </div>
              </section>
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

function findSauceOption(key: string) {
  return SAUCE_OPTIONS.find((opt) => opt.key === key);
}

function findDrinkOption(key: string) {
  return DRINK_OPTIONS.find((opt) => opt.key === key);
}

function buildModifiers(selection: SelectionState): ItemModifier[] {
  const sauceEntries = Object.entries(selection.sauces || {}).filter(([, qty]) => qty > 0);
  const drinkEntries = Object.entries(selection.drinks || {}).filter(([, qty]) => qty > 0);
  const modifiers: ItemModifier[] = [];

  sauceEntries.forEach(([key, qty]) => {
    const opt = findSauceOption(key);
    modifiers.push({
      type: "sauce",
      key,
      label: opt?.label || "سس",
      size_grams: opt?.sizeGrams,
      price: opt?.price,
      quantity: qty,
    });
  });

  drinkEntries.forEach(([key, qty]) => {
    const opt = findDrinkOption(key);
    modifiers.push({
      type: "drink",
      key,
      label: opt?.label || "نوشیدنی",
      price: opt?.price,
      quantity: qty,
    });
  });

  return modifiers.sort((a, b) => `${a.type}-${a.key}`.localeCompare(`${b.type}-${b.key}`));
}

function validateSelection(modifiers: ItemModifier[]): { valid: boolean; error?: string } {
  const hasSauce = modifiers.some((m) => m.type === "sauce" && m.key !== NO_SAUCE_KEY && (m.quantity ?? 0) > 0);
  const noSauce = modifiers.some((m) => m.type === "sauce" && m.key === NO_SAUCE_KEY && (m.quantity ?? 0) > 0);
  const drinks = modifiers.filter((m) => m.type === "drink" && m.key !== NO_DRINK_KEY && (m.quantity ?? 0) > 0);
  const noDrink = modifiers.some((m) => m.type === "drink" && m.key === NO_DRINK_KEY && (m.quantity ?? 0) > 0);

  if (!hasSauce && !noSauce) {
    return { valid: false, error: "انتخاب حداقل یک سس الزامی است." };
  }
  if (noDrink && drinks.length) {
    return { valid: false, error: "یا نوشیدنی انتخاب کنید یا گزینه «نمی‌خواهم»، هر دو با هم ممکن نیست." };
  }
  if (noSauce) {
    if (noDrink) {
      return { valid: false, error: "برای حالت بدون سس باید نوشیدنی واقعی انتخاب شود." };
    }
    if (drinks.length === 0) {
      return { valid: false, error: "بدون سس انتخاب شده است؛ لطفاً حداقل یک نوشیدنی اضافه کنید." };
    }
  }
  return { valid: true };
}
