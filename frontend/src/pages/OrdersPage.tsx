import { Navigate, useLocation } from "react-router-dom";

import { useAuth } from "../state/auth";
import { useOrders } from "../hooks/useOrders";
import { Card } from "../components/common/Card";

export function OrdersPage() {
  const { user } = useAuth();
  const { orders, isLoading } = useOrders(!!user);
  const location = useLocation();

  if (!user) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  }

  return (
    <section className="section">
      <div className="container small">
        <div className="section-head" style={{ textAlign: "center" }}>
          <span className="section-eyebrow">پیگیری سفارش</span>
          <h1 className="section-title" style={{ marginBottom: 8 }}>
            سفارش‌های ثبت شده
          </h1>
          <p className="section-subtitle">لیست سفارش‌ها بعد از ورود نمایش داده می‌شود.</p>
        </div>

        {isLoading ? (
          <p className="muted" style={{ textAlign: "center" }}>
            در حال بارگذاری…
          </p>
        ) : (
          <div className="card-grid centered-grid">
            {(orders || []).map((order) => (
              <Card
                key={order.id}
                title={`سفارش ${order.id}`}
                description={`وضعیت: ${order.status}`}
                footer={<span className="muted">{formatCurrency(order.total_amount)}</span>}
              >
                <p className="muted">ثبت شده در: {new Date(order.placed_at).toLocaleString("fa-IR")}</p>
              </Card>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}

function formatCurrency(amount?: number | null) {
  const value = amount ?? 0;
  return Intl.NumberFormat("fa-IR", { style: "currency", currency: "IRR", maximumFractionDigits: 0 }).format(value);
}
