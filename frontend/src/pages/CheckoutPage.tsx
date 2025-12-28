import { FormEvent, MouseEvent, useEffect, useMemo, useState } from "react";
import { Link, Navigate, useLocation, useNavigate } from "react-router-dom";

import { useAddressBook } from "../hooks/useAddressBook";
import { LocationPicker } from "../components/LocationPicker";
import { useGeolocation } from "../hooks/useGeolocation";
import { useAuth } from "../state/auth";
import { useCart, useCheckout } from "../state/cart";
import { useLocationStore } from "../state/location";
import { useServiceability } from "../state/serviceability";

export function CheckoutPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, activeOrder } = useAuth();
  const { submitOrder, loading } = useCheckout();
  const isAuthed = !!user;
  const { addresses, isLoading: isLoadingAddresses, createAddress } = useAddressBook(isAuthed);
  const canEditAddresses = isAuthed && !activeOrder;
  const cartItems = useCart((state) => state.items);
  const [addressId, setAddressId] = useState("");
  const [newTitle, setNewTitle] = useState("");
  const [newFullText, setNewFullText] = useState("");
  const [addressSaved, setAddressSaved] = useState(false);
  const [addressSaveError, setAddressSaveError] = useState("");
  const [phone, setPhone] = useState(user?.phone || "");
  const [acceptTerms, setAcceptTerms] = useState(false);
  const { coords, status, requestLocation } = useGeolocation(true);
  const setCoords = useLocationStore((state) => state.setCoords);
  const [showMap, setShowMap] = useState(false);
  const { data: service, loading: serviceabilityLoading, evaluate } = useServiceability();
  const itemCount = useMemo(() => cartItems.reduce((sum, item) => sum + item.quantity, 0), [cartItems]);

  useEffect(() => {
    if (!addresses || addresses.length === 0) return;
    if (addressId) return;
    const defaultAddress = addresses.find((addr) => addr.is_default) ?? addresses[0];
    if (defaultAddress) {
      setAddressId(String(defaultAddress.id));
    }
  }, [addresses, addressId]);

  useEffect(() => {
    if (addressId) {
      void evaluate({ addressId: Number(addressId) });
    } else if (coords) {
      void evaluate({ coords });
    }
  }, [addressId, coords, evaluate]);

  const cartSubtotal = useMemo(
    () => cartItems.reduce((sum, item) => sum + item.price * item.quantity, 0),
    [cartItems],
  );
  const deliveryFee =
    service?.delivery_type === "IN_ZONE" && service.is_serviceable ? service.delivery_fee_amount || 0 : 0;
  const payableTotal = cartSubtotal + deliveryFee;

  if (!user) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  }

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    const data = await submitOrder({
      addressId: addressId || undefined,
      addressInput: addressId
        ? undefined
        : {
            title: newTitle,
            full_text: newFullText,
            latitude: coords?.latitude,
            longitude: coords?.longitude,
          },
      phone,
      acceptTerms,
    });
    const paymentUrl = (data?.payment_url as string | undefined) ?? null;
    if (paymentUrl) {
      window.location.href = paymentUrl;
      return;
    }
    navigate("/orders");
  };

  const handleQuickSaveAddress = async (event?: FormEvent | MouseEvent<HTMLButtonElement>) => {
    event?.preventDefault();
    setAddressSaved(false);
    setAddressSaveError("");
    if (!newTitle || !newFullText) return;
    if (!isAuthed) {
      setAddressSaved(true);
      return;
    }
    try {
      const saved = await createAddress({
        title: newTitle,
        full_text: newFullText,
        latitude: coords?.latitude,
        longitude: coords?.longitude,
      });
      if (saved?.id) {
        setAddressId(String(saved.id));
        setNewTitle("");
        setNewFullText("");
        setAddressSaved(true);
      }
    } catch {
      setAddressSaveError("ذخیره آدرس با مشکل مواجه شد. دوباره تلاش کن.");
    }
  };

  const locationStatusText = useMemo(() => {
    if (status === "granted" && coords) {
      return "موقعیت دریافت شد.";
    }
    if (status === "prompting") return "در حال دریافت موقعیت...";
    if (status === "denied") return "اجازه دسترسی به موقعیت داده نشد.";
    if (status === "unsupported") return "مرورگر از موقعیت مکانی پشتیبانی نمی‌کند.";
    if (status === "error") return "دریافت موقعیت با خطا روبه‌رو شد.";
    return "برای کمک به رساندن سفارش، موقعیتت را فعال کن.";
  }, [coords, status]);

  return (
    <section className="section api-section">
      <div className="container small">
        <div className="api-shell">
          <div className="api-card checkout-card">
            <div className="api-card-head">
              <span className="section-eyebrow">تکمیل سفارش</span>
              <h1>آدرس، موقعیت و پرداخت</h1>
              <p className="api-subtitle">
                چند جزئیات کوتاه را پر کن تا سفارش به‌سرعت ثبت شود. اطلاعات تماس، آدرس منتخب و وضعیت ارسال در یک نگاه در دسترس است.
              </p>
            </div>

            <form onSubmit={handleSubmit} className="api-form checkout-grid">
              <div className="checkout-main">
                <div className="checkout-panel">
                  <div className="panel-head">
                    <div>
                      <p className="muted" style={{ margin: 0 }}>
                        اطلاعات تماس
                      </p>
                      <strong>شماره برای هماهنگی</strong>
                    </div>
                    <span className="pill soft">گام ۱</span>
                  </div>
                  <label className="input-label">
                    <span>شماره موبایل</span>
                    <input
                      className="input-field"
                      type="tel"
                      value={phone}
                      onChange={(e) => setPhone(e.target.value)}
                      placeholder="مثال: ۰۹۱۲۳۴۵۶۷۸۹"
                      required
                    />
                  </label>
                </div>

                <div className="checkout-panel">
                  <div className="panel-head">
                    <div>
                      <p className="muted" style={{ margin: 0 }}>
                        موقعیت شما
                      </p>
                      <strong>انتخاب نزدیک‌ترین آشپزخانه</strong>
                    </div>
                    <span className="pill soft">گام ۲</span>
                  </div>
                  <div className="location-banner elevated">
                    <div>
                      <p className="muted" style={{ margin: 0, fontWeight: 700 }}>
                        وضعیت موقعیت
                      </p>
                      <strong>{locationStatusText}</strong>
                    </div>
                    <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                      <button className="secondary-button" type="button" onClick={requestLocation}>
                        به‌روزرسانی موقعیت
                      </button>
                      <button className="ghost-button" type="button" onClick={() => setShowMap((v) => !v)}>
                        {showMap ? "بستن نقشه" : "انتخاب روی نقشه"}
                      </button>
                    </div>
                  </div>

                  {showMap ? (
                    <div className="stacked-form" style={{ marginTop: 4 }}>
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
                </div>

                <div className="checkout-panel">
                  <div className="panel-head">
                    <div>
                      <p className="muted" style={{ margin: 0 }}>
                        آدرس تحویل
                      </p>
                      <strong>یک آدرس انتخاب یا اضافه کن</strong>
                    </div>
                    <span className="pill soft">گام ۳</span>
                  </div>

                  <div className="input-label">
                    <span style={{ display: "block", marginBottom: 6 }}>آدرس ثبت‌شده</span>
                    {isLoadingAddresses ? (
                      <p className="muted">در حال بارگذاری آدرس‌ها…</p>
                    ) : (addresses || []).length > 0 ? (
                      <div className="address-grid">
                        {addresses?.map((address) => (
                          <label key={address.id} className="address-tile">
                            <input
                              type="radio"
                              name="address"
                              value={address.id}
                              checked={String(address.id) === addressId}
                              onChange={() => setAddressId(String(address.id))}
                            />
                            <div className="address-body">
                              <div className="address-title">
                                <strong>{address.title || "آدرس"}</strong>
                                {address.is_default ? <span className="pill small">پیش‌فرض</span> : null}
                              </div>
                              <p className="muted" style={{ margin: 0 }}>
                                {address.full_text}
                              </p>
                            </div>
                          </label>
                        ))}
                      </div>
                    ) : (
                      <p className="muted">هیچ آدرسی ذخیره نشده است. می‌توانی همین‌جا اضافه کنی.</p>
                    )}
                  </div>

                  <details className="quick-add" open={!isAuthed || !addresses?.length}>
                    <summary>افزودن آدرس جدید</summary>
                    <div className="stacked-form" style={{ marginTop: 12 }}>
                      <label className="input-label">
                        <span>عنوان</span>
                        <input
                          className="input-field"
                          value={newTitle}
                          onChange={(e) => setNewTitle(e.target.value)}
                          placeholder="خانه / محل کار"
                          required={!addressId}
                          disabled={!canEditAddresses && isAuthed}
                        />
                      </label>
                      <label className="input-label">
                        <span>آدرس کامل</span>
                        <textarea
                          className="input-field"
                          rows={3}
                          value={newFullText}
                          onChange={(e) => setNewFullText(e.target.value)}
                          placeholder="خیابان، کوچه، پلاک..."
                          required={!addressId}
                          disabled={!canEditAddresses && isAuthed}
                        />
                      </label>
                      <button
                        className="ghost-button"
                        type="button"
                        onClick={handleQuickSaveAddress}
                        disabled={!canEditAddresses && isAuthed}
                      >
                        ذخیره و انتخاب آدرس
                      </button>
                      {addressSaved ? (
                        <p className="muted" style={{ margin: 0 }}>
                          آدرس واردشده برای همین سفارش انتخاب شد.
                        </p>
                      ) : null}
                      {addressSaveError ? (
                        <p className="muted" style={{ margin: 0, color: "var(--color-danger, #d14343)" }}>
                          {addressSaveError}
                        </p>
                      ) : null}
                      {!canEditAddresses && isAuthed ? (
                        <p className="muted" style={{ margin: 0 }}>
                          ویرایش آدرس در زمان داشتن سفارش فعال امکان‌پذیر نیست.
                        </p>
                      ) : null}
                    </div>
                  </details>
                </div>
              </div>

              <aside className="checkout-aside">
                <div className="checkout-summary-card">
                  <div className="panel-head" style={{ alignItems: "flex-start" }}>
                    <div>
                      <p className="muted" style={{ margin: 0 }}>
                        مرور سفارش
                      </p>
                      <strong>{itemCount} مورد در سبد</strong>
                    </div>
                    <span className="pill soft">{service?.is_serviceable ? "آماده ارسال" : "نیاز به بررسی"}</span>
                  </div>

                  <div className="summary-items">
                    {cartItems.length === 0 ? (
                      <p className="muted" style={{ margin: 0 }}>
                        هنوز سفارشی انتخاب نشده است.
                      </p>
                    ) : (
                      cartItems.map((item) => (
                        <div key={item.productId} className="summary-item">
                          <div>
                            <strong>{item.title}</strong>
                            <p className="muted" style={{ margin: 0 }}>
                              ×{item.quantity} • {formatCurrency(item.price)}
                            </p>
                          </div>
                          <strong>{formatCurrency(item.price * item.quantity)}</strong>
                        </div>
                      ))
                    )}
                  </div>

                  <div className="summary-row">
                    <span>جمع سفارش</span>
                    <strong>{formatCurrency(cartSubtotal)}</strong>
                  </div>
                  <div className="summary-row">
                    <span>
                      هزینه ارسال{" "}
                      <small className="muted">
                        {service?.delivery_label ||
                          (service?.delivery_type === "OUT_OF_ZONE_SNAPP"
                            ? "ارسال با اسنپ (پس‌کرایه)"
                            : "پیک داخلی")}
                      </small>
                    </span>
                    {serviceabilityLoading ? (
                      <span className="muted">در حال محاسبه…</span>
                    ) : (
                      <strong>
                        {service?.delivery_type === "IN_ZONE"
                          ? formatCurrency(service?.delivery_fee_amount || 0)
                          : "پس‌کرایه"}
                      </strong>
                    )}
                  </div>
                  <div className="summary-row total">
                    <span>مبلغ قابل پرداخت</span>
                    <strong>{formatCurrency(payableTotal)}</strong>
                  </div>
                </div>

                <label className="input-label inline-check">
                  <input type="checkbox" checked={acceptTerms} onChange={(e) => setAcceptTerms(e.target.checked)} />
                  <div>
                    <strong>
                      <Link to="/terms">قوانین و شرایط سفارش</Link> را می‌پذیرم
                    </strong>
                    <p className="muted" style={{ margin: 0 }}>
                      تایید برای ثبت و پرداخت آنلاین ضروری است.
                    </p>
                  </div>
                </label>

                <button
                  className="primary-button"
                  type="submit"
                  disabled={
                    loading ||
                    cartItems.length === 0 ||
                    (!addressId && (!newTitle || !newFullText)) ||
                    !phone ||
                    !acceptTerms ||
                    !service?.is_serviceable
                  }
                >
                  {loading ? "در حال ثبت…" : "ثبت نهایی سفارش"}
                </button>
                <p className="muted" style={{ textAlign: "center", margin: 0 }}>
                  مدیریت کامل آدرس‌ها از <Link to="/addresses">صفحه آدرس‌ها</Link> در دسترس است.
                </p>
              </aside>
            </form>
          </div>
        </div>
      </div>
    </section>
  );
}

function formatCurrency(amount: number) {
  return Intl.NumberFormat("fa-IR", { style: "currency", currency: "IRR", maximumFractionDigits: 0 }).format(amount);
}
