import { FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";

import { useCheckout } from "../state/cart";

export function CheckoutPage() {
  const navigate = useNavigate();
  const { submitOrder, loading, total } = useCheckout();
  const [addressId, setAddressId] = useState("");
  const [paymentMethod, setPaymentMethod] = useState<"ONLINE" | "COD">("ONLINE");

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    await submitOrder({ addressId, paymentMethod });
    navigate("/orders");
  };

  return (
    <section className="section api-section">
      <div className="container small">
        <div className="api-shell">
          <div className="api-card">
            <div className="api-card-head">
              <span className="section-eyebrow">تکمیل سفارش</span>
              <h1>آدرس و پرداخت</h1>
              <p className="api-subtitle">
                جزئیات سفارش را مرور کن و روش پرداختت را انتخاب کن تا غذای سالم به سمتت حرکت کند.
              </p>
            </div>

            <form onSubmit={handleSubmit} className="api-form">
              <label className="input-label">
                <span>کد آدرس ذخیره‌شده</span>
                <input
                  className="input-field"
                  value={addressId}
                  onChange={(e) => setAddressId(e.target.value)}
                  placeholder="مثال: addr_123"
                  required
                />
              </label>

              <div className="input-label">
                <span style={{ display: "block", marginBottom: 6 }}>روش پرداخت</span>
                <div className="pill-switch">
                  <button
                    type="button"
                    onClick={() => setPaymentMethod("ONLINE")}
                    className={`pill-option ${paymentMethod === "ONLINE" ? "active" : ""}`}
                  >
                    پرداخت آنلاین
                  </button>
                  <button
                    type="button"
                    onClick={() => setPaymentMethod("COD")}
                    className={`pill-option ${paymentMethod === "COD" ? "active" : ""}`}
                  >
                    پرداخت در محل
                  </button>
                </div>
              </div>

              <div className="api-summary">
                <div>
                  <p className="muted" style={{ margin: 0 }}>
                    مبلغ کل
                  </p>
                  <strong style={{ fontSize: 20 }}>{formatCurrency(total)}</strong>
                </div>
              </div>

              <button className="primary-button" type="submit" disabled={loading}>
                {loading ? "در حال ثبت…" : "ثبت نهایی سفارش"}
              </button>
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
