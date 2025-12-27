import { FormEvent, MouseEvent, useEffect, useMemo, useState } from "react";
import { Link, Navigate, useLocation, useNavigate } from "react-router-dom";

import { useAddressBook } from "../hooks/useAddressBook";
import { LocationPicker } from "../components/LocationPicker";
import { useGeolocation } from "../hooks/useGeolocation";
import { useAuth } from "../state/auth";
import { useCheckout } from "../state/cart";
import { useLocationStore } from "../state/location";

export function CheckoutPage() {
  const navigate = useNavigate();
  const routeLocation = useLocation();
  const { user } = useAuth();
  const { submitOrder, loading, total } = useCheckout();
  const isAuthed = !!user;
  const { addresses, isLoading: isLoadingAddresses, createAddress } = useAddressBook(isAuthed);
  const [addressId, setAddressId] = useState("");
  const [newTitle, setNewTitle] = useState("");
  const [newFullText, setNewFullText] = useState("");
  const { coords, status, requestLocation } = useGeolocation(isAuthed);
  const setCoords = useLocationStore((state) => state.setCoords);
  const [showMap, setShowMap] = useState(false);

  useEffect(() => {
    if (!addresses || addresses.length === 0) return;
    if (addressId) return;
    const defaultAddress = addresses.find((addr) => addr.is_default) ?? addresses[0];
    if (defaultAddress) {
      setAddressId(String(defaultAddress.id));
    }
  }, [addresses, addressId]);

  if (!isAuthed) {
    return <Navigate to="/login" replace state={{ from: routeLocation.pathname }} />;
  }

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    if (!isAuthed) {
      navigate("/login", { replace: true, state: { from: "/checkout" } });
      return;
    }
    const data = await submitOrder({ addressId });
    const paymentUrl = (data?.payment_url as string | undefined) ?? null;
    if (paymentUrl) {
      window.location.href = paymentUrl;
      return;
    }
    navigate("/orders");
  };

  const handleQuickSaveAddress = async (event?: FormEvent | MouseEvent<HTMLButtonElement>) => {
    event?.preventDefault();
    if (!newTitle || !newFullText) return;
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
          <div className="api-card">
            <div className="api-card-head">
              <span className="section-eyebrow">تکمیل سفارش</span>
              <h1>آدرس، موقعیت و پرداخت</h1>
              <p className="api-subtitle">
                برای ثبت نهایی باید وارد حساب شوی، آدرس را انتخاب کنی و اجازه دهی موقعیتت برای پیک ذخیره شود.
              </p>
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
                    به‌روزرسانی موقعیت
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

            <form onSubmit={handleSubmit} className="api-form">
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

              <details className="quick-add">
                <summary>افزودن سریع آدرس جدید</summary>
                <div className="stacked-form" style={{ marginTop: 12 }}>
                  <label className="input-label">
                    <span>عنوان</span>
                    <input
                      className="input-field"
                      value={newTitle}
                      onChange={(e) => setNewTitle(e.target.value)}
                      placeholder="خانه / محل کار"
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
                    />
                  </label>
                  <button className="ghost-button" type="button" onClick={handleQuickSaveAddress}>
                    ذخیره و انتخاب آدرس
                  </button>
                </div>
              </details>

              <div className="api-summary">
                <div>
                  <p className="muted" style={{ margin: 0 }}>
                    مبلغ کل
                  </p>
                  <strong style={{ fontSize: 20 }}>{formatCurrency(total)}</strong>
                </div>
                <p className="muted" style={{ margin: 0 }}>
                  ورود شما الزامی است و آدرس پیش‌فرض به‌صورت خودکار انتخاب می‌شود.
                </p>
              </div>

              <button className="primary-button" type="submit" disabled={loading || !addressId}>
                {loading ? "در حال ثبت…" : "ثبت نهایی سفارش"}
              </button>
              <p className="muted" style={{ textAlign: "center", margin: 0 }}>
                مدیریت کامل آدرس‌ها از <Link to="/addresses">صفحه آدرس‌ها</Link> در دسترس است.
              </p>
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
