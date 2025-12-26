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
    <div className="section">
      <h1>Checkout</h1>
      <p className="muted">Confirm your address and payment method.</p>
      <form onSubmit={handleSubmit} style={{ display: "grid", gap: 12, maxWidth: 480 }}>
        <label>
          <span className="muted">Address ID</span>
          <input
            value={addressId}
            onChange={(e) => setAddressId(e.target.value)}
            placeholder="Use your saved address id"
            required
            style={{ width: "100%", padding: 10, borderRadius: 8, border: "1px solid #cbd5e1" }}
          />
        </label>

        <label className="muted">Payment method</label>
        <div style={{ display: "flex", gap: 12 }}>
          <button
            type="button"
            onClick={() => setPaymentMethod("ONLINE")}
            className="button"
            style={{ background: paymentMethod === "ONLINE" ? "#2563eb" : "#cbd5e1", color: "white" }}
          >
            Online
          </button>
          <button
            type="button"
            onClick={() => setPaymentMethod("COD")}
            className="button"
            style={{ background: paymentMethod === "COD" ? "#2563eb" : "#cbd5e1", color: "white" }}
          >
            Cash on delivery
          </button>
        </div>

        <strong>Total: {formatCurrency(total)}</strong>

        <button className="button" type="submit" disabled={loading}>
          {loading ? "Submitting…" : "Place order"}
        </button>
      </form>
    </div>
  );
}

function formatCurrency(amount: number) {
  return Intl.NumberFormat("fa-IR", { style: "currency", currency: "IRR", maximumFractionDigits: 0 }).format(amount);
}
