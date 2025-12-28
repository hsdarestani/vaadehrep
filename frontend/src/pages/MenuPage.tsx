import { useEffect, useMemo, useRef, useState } from "react";

import { Card } from "../components/common/Card";
import { LocationPicker } from "../components/LocationPicker";
import type { OptionGroup, OptionItem, Product } from "../api/types";
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
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null);
  const [optionSelections, setOptionSelections] = useState<Record<number, Record<number, number>>>({});
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
    const optionGroups = product.option_groups ?? [];
    if (!optionGroups.length) {
      addToCart({
        id: createCartItemId(),
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
      return;
    }
    setSelectedProduct(product);
    const initialSelections: Record<number, Record<number, number>> = {};
    optionGroups.forEach((group) => {
      initialSelections[group.id] = {};
    });
    setOptionSelections(initialSelections);
  };

  const closeOptionModal = () => {
    setSelectedProduct(null);
    setOptionSelections({});
  };

  const updateSelection = (group: OptionGroup, item: OptionItem, delta: number) => {
    setOptionSelections((prev) => {
      const groupSelections = { ...(prev[group.id] ?? {}) };
      const currentQty = groupSelections[item.id] ?? 0;
      if (delta > 0) {
        if (NO_OPTION_ITEM_NAMES.has(item.name)) {
          return { ...prev, [group.id]: { [item.id]: 1 } };
        }
        for (const selectedId of Object.keys(groupSelections)) {
          const selectedItem = group.items.find((gItem) => gItem.id === Number(selectedId));
          if (selectedItem && NO_OPTION_ITEM_NAMES.has(selectedItem.name)) {
            delete groupSelections[selectedItem.id];
          }
        }
        groupSelections[item.id] = currentQty + 1;
      } else if (currentQty > 0) {
        if (currentQty === 1) {
          delete groupSelections[item.id];
        } else {
          groupSelections[item.id] = currentQty - 1;
        }
      }
      return { ...prev, [group.id]: groupSelections };
    });
  };

  const handleConfirmOptions = () => {
    if (!selectedProduct) return;
    const optionGroups = selectedProduct.option_groups ?? [];
    const modifiers = optionGroups.map((group) => {
      const selections = optionSelections[group.id] ?? {};
      const items = Object.entries(selections).map(([id, quantity]) => {
        const item = group.items.find((entry) => entry.id === Number(id));
        return {
          id: Number(id),
          name: item?.name ?? "",
          price_delta_amount: item?.price_delta_amount ?? 0,
          quantity,
        };
      });
      return { group_id: group.id, group_name: group.name, items };
    });
    const modifiersTotal = modifiers.reduce(
      (sum, group) =>
        sum +
        group.items.reduce((groupSum, item) => groupSum + item.price_delta_amount * item.quantity, 0),
      0,
    );
    addToCart({
      id: createCartItemId(),
      productId: selectedProduct.id,
      title: selectedProduct.name_fa,
      price: (selectedProduct.base_price || 0) + modifiersTotal,
      quantity: 1,
      options: modifiers,
    });
    if (timerRef.current) {
      window.clearTimeout(timerRef.current);
    }
    setFeedback(`${selectedProduct.name_fa} به سبد خرید اضافه شد`);
    timerRef.current = window.setTimeout(() => setFeedback(null), 2500);
    closeOptionModal();
  };

  const optionErrors = useMemo(() => {
    if (!selectedProduct) return [];
    const errors: string[] = [];
    (selectedProduct.option_groups ?? []).forEach((group) => {
      const selections = optionSelections[group.id] ?? {};
      const selectedCount = Object.values(selections).reduce((sum, value) => sum + value, 0);
      const minSelect = group.min_select ?? 0;
      const requiredMin = minSelect > 0 ? minSelect : group.is_required ? 1 : 0;
      if (requiredMin && selectedCount < requiredMin) {
        errors.push(`انتخاب ${group.name} الزامی است.`);
      }
      if (group.max_select && selectedCount > group.max_select) {
        errors.push(`حداکثر انتخاب برای ${group.name} ${group.max_select} است.`);
      }
    });
    return errors;
  }, [optionSelections, selectedProduct]);

  const optionTotal = useMemo(() => {
    if (!selectedProduct) return 0;
    const optionGroups = selectedProduct.option_groups ?? [];
    return optionGroups.reduce((sum, group) => {
      const selections = optionSelections[group.id] ?? {};
      return (
        sum +
        Object.entries(selections).reduce((groupSum, [id, qty]) => {
          const item = group.items.find((entry) => entry.id === Number(id));
          return groupSum + (item?.price_delta_amount ?? 0) * qty;
        }, 0)
      );
    }, 0);
  }, [optionSelections, selectedProduct]);

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

      {selectedProduct ? (
        <div className="modal-overlay" role="dialog" aria-modal="true">
          <div className="modal-card">
            <div className="modal-header">
              <div>
                <h2>افزودن {selectedProduct.name_fa}</h2>
                <p className="muted" style={{ margin: 0 }}>
                  ابتدا سس‌ها را انتخاب کنید، سپس نوشیدنی را مشخص کنید.
                </p>
              </div>
              <button type="button" className="icon-button" onClick={closeOptionModal} aria-label="بستن">
                ✕
              </button>
            </div>

            <div className="modal-body">
              {(selectedProduct.option_groups ?? []).map((group) => {
                const selections = optionSelections[group.id] ?? {};
                const selectedCount = Object.values(selections).reduce((sum, value) => sum + value, 0);
                const minSelect = group.min_select ?? 0;
                const requiredMin = minSelect > 0 ? minSelect : group.is_required ? 1 : 0;
                return (
                  <div key={group.id} className="option-group">
                    <div className="option-group-header">
                      <div>
                        <h3>{group.name}</h3>
                        {group.description ? <p className="muted">{group.description}</p> : null}
                      </div>
                      <span className="pill soft">
                        {requiredMin ? `حداقل ${requiredMin}` : "اختیاری"} • انتخاب شده {selectedCount}
                      </span>
                    </div>
                    <div className="option-items">
                      {group.items.map((item) => {
                        const itemQty = selections[item.id] ?? 0;
                        const maxedOut = Boolean(group.max_select && selectedCount >= group.max_select);
                        return (
                          <div key={item.id} className="option-item">
                            <div>
                              <strong>{item.name}</strong>
                              {item.description ? <p className="muted">{item.description}</p> : null}
                              {item.price_delta_amount ? (
                                <p className="muted">افزایش قیمت: {formatCurrency(item.price_delta_amount)}</p>
                              ) : null}
                            </div>
                            <div className="option-qty">
                              <button
                                type="button"
                                className="ghost-button"
                                onClick={() => updateSelection(group, item, -1)}
                                disabled={itemQty === 0}
                              >
                                −
                              </button>
                              <span>{itemQty}</span>
                              <button
                                type="button"
                                className="ghost-button"
                                onClick={() => updateSelection(group, item, 1)}
                                disabled={maxedOut}
                              >
                                +
                              </button>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                );
              })}
            </div>

            <div className="modal-footer">
              <div>
                <p className="muted" style={{ margin: 0 }}>
                  قیمت نهایی
                </p>
                <strong>
                  {formatCurrency((selectedProduct.base_price || 0) + optionTotal)}
                </strong>
              </div>
              <div className="modal-actions">
                {optionErrors.length ? <span className="error-text">{optionErrors[0]}</span> : null}
                <button type="button" className="secondary-button" onClick={closeOptionModal}>
                  انصراف
                </button>
                <button
                  type="button"
                  className="primary-button"
                  onClick={handleConfirmOptions}
                  disabled={optionErrors.length > 0}
                >
                  افزودن به سبد
                </button>
              </div>
            </div>
          </div>
        </div>
      ) : null}
    </section>
  );
}

function formatCurrency(amount?: number | null) {
  const value = amount ?? 0;
  return Intl.NumberFormat("fa-IR", { style: "currency", currency: "IRR", maximumFractionDigits: 0 }).format(value);
}

const NO_OPTION_ITEM_NAMES = new Set(["بدون سس", "بدون نوشیدنی", "بدون نوشابه"]);

function createCartItemId() {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID();
  }
  return `item_${Date.now()}_${Math.random().toString(16).slice(2)}`;
}
