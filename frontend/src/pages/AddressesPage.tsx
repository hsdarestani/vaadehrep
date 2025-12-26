import { FormEvent, useState } from "react";
import { Navigate, useLocation } from "react-router-dom";

import { useAddressBook } from "../hooks/useAddressBook";
import { useAuth } from "../state/auth";
import { Card } from "../components/common/Card";

export function AddressesPage() {
  const { user } = useAuth();
  const location = useLocation();
  const { addresses, createAddress, isLoading } = useAddressBook(!!user);
  const [title, setTitle] = useState("");
  const [fullText, setFullText] = useState("");

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    const saved = await createAddress({ title, full_text: fullText });
    if (saved && saved.id) {
      setTitle("");
      setFullText("");
    }
  };

  if (!user) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  }

  return (
    <section className="section">
      <div className="container small">
        <div className="section-head" style={{ textAlign: "center" }}>
          <span className="section-eyebrow">دفترچه آدرس</span>
          <h1 className="section-title" style={{ marginBottom: 8 }}>
            آدرس‌های من
          </h1>
          <p className="section-subtitle">بعد از ورود، آدرس‌های ذخیره‌شده‌ات اینجا نمایش داده می‌شوند.</p>
        </div>

        <form onSubmit={handleSubmit} className="stacked-form">
          <label>
            <span className="muted">عنوان</span>
            <input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="خانه / محل کار"
              required
              className="input-field"
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
            />
          </label>
          <button type="submit" className="primary-button" style={{ width: "100%" }}>
            ذخیره آدرس
          </button>
        </form>

        {isLoading ? (
          <p className="muted" style={{ textAlign: "center" }}>
            در حال بارگذاری…
          </p>
        ) : (
          <div className="card-grid centered-grid">
            {(addresses || []).map((address) => (
              <Card key={address.id} title={address.title || "آدرس"} description={address.full_text}>
                <p className="muted">شهر: {address.city || "—"}</p>
              </Card>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}
