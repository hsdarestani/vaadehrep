import { Link } from "react-router-dom";

import { useCart } from "../state/cart";

export function CartPage() {
  const items = useCart((s) => s.items);
  const updateQty = useCart((s) => s.updateQty);
  const remove = useCart((s) => s.remove);
  const total = items.reduce((sum, item) => sum + item.price * item.quantity, 0);

  return (
    <div className="section">
      <h1>Your Cart</h1>
      {items.length === 0 ? (
        <p className="muted">
          Cart is empty. <Link to="/menu">Browse the menu</Link>.
        </p>
      ) : (
        <>
          <div style={{ display: "grid", gap: 12 }}>
            {items.map((item) => (
              <div key={item.productId} className="card" style={{ display: "flex", gap: 12, alignItems: "center" }}>
                <div style={{ flex: 1 }}>
                  <h3>{item.title}</h3>
                  <p className="muted">{formatCurrency(item.price)}</p>
                </div>
                <input
                  type="number"
                  min={1}
                  value={item.quantity}
                  onChange={(e) => updateQty(item.productId, Number(e.target.value))}
                  style={{ width: 80, padding: 8, borderRadius: 8, border: "1px solid #cbd5e1" }}
                />
                <button className="link" onClick={() => remove(item.productId)}>
                  Remove
                </button>
              </div>
            ))}
          </div>
          <div style={{ marginTop: 20, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <strong>Total: {formatCurrency(total)}</strong>
            <Link to="/checkout" className="button">
              Checkout
            </Link>
          </div>
        </>
      )}
    </div>
  );
}

function formatCurrency(amount: number) {
  return Intl.NumberFormat("fa-IR", { style: "currency", currency: "IRR", maximumFractionDigits: 0 }).format(amount);
}
