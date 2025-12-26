import { Link } from "react-router-dom";

import { useCart } from "../state/cart";

export function CartPage() {
  const items = useCart((s) => s.items);
  const updateQty = useCart((s) => s.updateQty);
  const remove = useCart((s) => s.remove);
  const total = items.reduce((sum, item) => sum + item.price * item.quantity, 0);

  return (
    <section className="section">
      <div className="container small">
        <div className="section-head" style={{ textAlign: "center" }}>
          <span className="section-eyebrow">سبد خرید</span>
          <h1 className="section-title" style={{ marginBottom: 10 }}>
            انتخاب‌های تازه و سالمت
          </h1>
          <p className="section-subtitle">اقلامی که آماده رسیدن به میز تو هستند.</p>
        </div>

        {items.length === 0 ? (
          <div className="card" style={{ textAlign: "center", padding: 24 }}>
            <p className="muted" style={{ marginBottom: 16 }}>
              سبد خریدت خالیه. <Link to="/menu">منو را ببین</Link> و یک وعده سالم انتخاب کن.
            </p>
            <Link to="/menu" className="primary-button">
              رفتن به منو
            </Link>
          </div>
        ) : (
          <>
            <div className="card" style={{ display: "grid", gap: 12 }}>
              {items.map((item) => (
                <div key={item.productId} className="cart-row">
                  <div style={{ flex: 1 }}>
                    <h3>{item.title}</h3>
                    <p className="muted">{formatCurrency(item.price)}</p>
                  </div>
                  <input
                    type="number"
                    min={1}
                    value={item.quantity}
                    onChange={(e) => updateQty(item.productId, Number(e.target.value))}
                    className="input-field"
                    style={{ width: 90 }}
                  />
                  <button className="link" onClick={() => remove(item.productId)}>
                    حذف
                  </button>
                </div>
              ))}
            </div>
            <div className="card cart-summary">
              <div>
                <p className="muted" style={{ margin: 0 }}>
                  مجموع سفارش
                </p>
                <strong style={{ fontSize: 20 }}>{formatCurrency(total)}</strong>
              </div>
              <Link to="/checkout" className="primary-button">
                تکمیل خرید
              </Link>
            </div>
          </>
        )}
      </div>
    </section>
  );
}

function formatCurrency(amount: number) {
  return Intl.NumberFormat("fa-IR", { style: "currency", currency: "IRR", maximumFractionDigits: 0 }).format(amount);
}
