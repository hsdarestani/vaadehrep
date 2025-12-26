import { useOrders } from "../hooks/useOrders";
import { Card } from "../components/common/Card";

export function OrdersPage() {
  const { orders, isLoading } = useOrders();

  return (
    <div className="section">
      <h1>Orders</h1>
      {isLoading ? (
        <p className="muted">Loading…</p>
      ) : (
        <div className="card-grid">
          {(orders || []).map((order) => (
            <Card
              key={order.id}
              title={`Order ${order.id}`}
              description={`Status: ${order.status}`}
              footer={<span className="muted">{formatCurrency(order.total_amount)}</span>}
            >
              <p className="muted">Placed: {new Date(order.placed_at).toLocaleString()}</p>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}

function formatCurrency(amount?: number | null) {
  const value = amount ?? 0;
  return Intl.NumberFormat("fa-IR", { style: "currency", currency: "IRR", maximumFractionDigits: 0 }).format(value);
}
