import { FormEvent, useMemo, useState } from "react";
import { Navigate, useLocation } from "react-router-dom";

import { useAddressBook } from "../hooks/useAddressBook";
import { LocationPicker } from "../components/LocationPicker";
import { AddressPinsMap } from "../components/AddressPinsMap";
import { useGeolocation } from "../hooks/useGeolocation";
import { useAuth } from "../state/auth";
import { useLocationStore } from "../state/location";
import { Card } from "../components/common/Card";
import type { Address } from "../api/types";

export function AddressesPage() {
  const { user, activeOrder } = useAuth();
  const location = useLocation();
  const { addresses, createAddress, isLoading, removeAddress, updateAddress } = useAddressBook(!!user);
  const [title, setTitle] = useState("");
  const [fullText, setFullText] = useState("");
  const { coords, status, requestLocation } = useGeolocation(!!user);
  const setCoords = useLocationStore((state) => state.setCoords);
  const [showMap, setShowMap] = useState(false);
  const canModify = !!user && !activeOrder;
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editingTitle, setEditingTitle] = useState("");
  const [editingFullText, setEditingFullText] = useState("");
  const [editingCoords, setEditingCoords] = useState<{ latitude: number; longitude: number } | undefined>();
  const [editingError, setEditingError] = useState("");
  const [isSavingEdit, setIsSavingEdit] = useState(false);

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

  const startEdit = (address: Address) => {
    setEditingId(address.id);
    setEditingTitle(address.title || "");
    setEditingFullText(address.full_text || "");
    if (address.latitude != null && address.longitude != null) {
      setEditingCoords({ latitude: Number(address.latitude), longitude: Number(address.longitude) });
    } else {
      setEditingCoords(undefined);
    }
    setEditingError("");
  };

  const cancelEdit = () => {
    setEditingId(null);
    setEditingTitle("");
    setEditingFullText("");
    setEditingCoords(undefined);
    setEditingError("");
  };

  const handleUpdate = async (event: FormEvent) => {
    event.preventDefault();
    if (!editingId) return;
    setIsSavingEdit(true);
    setEditingError("");
    try {
      await updateAddress(editingId, {
        title: editingTitle,
        full_text: editingFullText,
        latitude: editingCoords?.latitude,
        longitude: editingCoords?.longitude,
      });
      cancelEdit();
    } catch (err) {
      setEditingError("خطا در ذخیره تغییرات آدرس. لطفاً دوباره تلاش کنید.");
    } finally {
      setIsSavingEdit(false);
    }
  };

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

        {!!addresses?.length ? (
          <div className="stacked-form" style={{ marginTop: 16 }}>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
              <h3 style={{ margin: 0 }}>نمایش روی نقشه</h3>
              {editingId ? <span className="pill small">در حال ویرایش آدرس {editingId}</span> : null}
            </div>
            <AddressPinsMap addresses={addresses} highlightId={editingId ?? undefined} />
          </div>
        ) : null}

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
                    {address.latitude != null && address.longitude != null ? (
                      <p className="muted" style={{ margin: 0 }}>
                        مختصات: {Number(address.latitude).toFixed(6)}, {Number(address.longitude).toFixed(6)}
                      </p>
                    ) : null}
                  </>
                }
                footer={
                  editingId === address.id ? (
                    <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                      <button
                        className="secondary-button"
                        type="submit"
                        form={`edit-address-form-${address.id}`}
                        disabled={!canModify || isSavingEdit}
                      >
                        ذخیره تغییرات
                      </button>
                      <button className="ghost-button" type="button" onClick={cancelEdit}>
                        انصراف
                      </button>
                    </div>
                  ) : (
                    <div style={{ display: "flex", gap: 8 }}>
                      <button
                        className="secondary-button"
                        type="button"
                        onClick={() => startEdit(address)}
                        disabled={!canModify}
                      >
                        ویرایش
                      </button>
                      <button
                        className="ghost-button"
                        type="button"
                        onClick={() => removeAddress(address.id)}
                        disabled={!canModify}
                      >
                        حذف
                      </button>
                    </div>
                  )
                }
              >
                {editingId === address.id ? (
                  <form id={`edit-address-form-${address.id}`} onSubmit={handleUpdate} className="stacked-form">
                    <label>
                      <span className="muted">عنوان</span>
                      <input
                        value={editingTitle}
                        onChange={(e) => setEditingTitle(e.target.value)}
                        required
                        className="input-field"
                        disabled={!canModify}
                      />
                    </label>
                    <label>
                      <span className="muted">آدرس کامل</span>
                      <textarea
                        value={editingFullText}
                        onChange={(e) => setEditingFullText(e.target.value)}
                        required
                        rows={3}
                        className="input-field"
                        disabled={!canModify}
                      />
                    </label>
                    <div className="stacked-form">
                      <span className="muted">انتخاب موقعیت روی نقشه</span>
                      <LocationPicker value={editingCoords} onChange={(nextCoords) => setEditingCoords(nextCoords)} />
                      {editingCoords ? (
                        <p className="muted" style={{ margin: 0 }}>
                          مختصات جدید: {editingCoords.latitude.toFixed(6)}, {editingCoords.longitude.toFixed(6)}
                        </p>
                      ) : (
                        <p className="muted" style={{ margin: 0 }}>
                          برای ثبت موقعیت، روی نقشه کلیک کنید.
                        </p>
                      )}
                    </div>
                    {editingError ? (
                      <p className="muted" style={{ margin: 0, color: "#b91c1c", fontWeight: 700 }}>
                        {editingError}
                      </p>
                    ) : null}
                  </form>
                ) : (
                  <p className="muted">شهر: {address.city || "—"}</p>
                )}
              </Card>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}
