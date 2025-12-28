import { Navigate, useLocation } from "react-router-dom";
import { useState } from "react";

import { useAuth } from "../state/auth";
import { useOrders } from "../hooks/useOrders";
import { Card } from "../components/common/Card";
import { endpoints } from "../api/endpoints";

export function OrdersPage() {
  const { user, activeOrder } = useAuth();
  const { orders, isLoading } = useOrders(!!user);
  const location = useLocation();
  const [payingId, setPayingId] = useState<string | null>(null);
  const [paymentError, setPaymentError] = useState<{ orderId: string; message: string } | null>(null);

  if (!user && !activeOrder) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  }

  const handlePay = async (orderId: string) => {
    setPaymentError(null);
    setPayingId(orderId);
    try {
      const res = await endpoints.payForOrder(orderId);
      const nextUrl = (res.data as { payment_url?: string | null }).payment_url ?? null;
      if (nextUrl) {
        window.location.href = nextUrl;
        return;
      }
      setPaymentError({ orderId, message: "لینک پرداخت پیدا نشد. لطفاً دوباره تلاش کنید." });
    } catch {
      setPaymentError({ orderId, message: "خطا در ایجاد لینک پرداخت. لطفاً دوباره تلاش کنید." });
    } finally {
      setPayingId(null);
    }
  };

  return (
    <section className="section">
      <div className="container small">
        <div className="section-head" style={{ textAlign: "center" }}>
          <span className="section-eyebrow">پیگیری سفارش</span>
          <h1 className="section-title" style={{ marginBottom: 8 }}>
            سفارش‌های ثبت شده
          </h1>
          <p className="section-subtitle">همه سفارش‌های شما در این صفحه نمایش داده می‌شود.</p>
        </div>

        {activeOrder ? (
          <div className="card" style={{ marginBottom: 12 }}>
            <p style={{ margin: 0, fontWeight: 700 }}>سفارش در حال پردازش</p>
            <p className="muted" style={{ margin: "4px 0 8px" }}>
              کد: {activeOrder.short_code} • وضعیت: {translateStatus(activeOrder.status)}
            </p>
          </div>
        ) : null}

        {isLoading ? (
          <p className="muted" style={{ textAlign: "center" }}>
            در حال بارگذاری…
          </p>
        ) : (
          <div className="card-grid centered-grid">
            {(orders || []).map((order) => (
              <Card
                key={order.id}
                title={`سفارش ${order.short_code}`}
                description={`وضعیت: ${translateStatus(order.status)} • پرداخت: ${translatePaymentStatus(order.payment_status || "UNPAID")}`}
                footer={<span className="muted">{formatCurrency(order.total_amount)}</span>}
              >
                <p className="muted" style={{ marginBottom: 8 }}>
                  ثبت شده در: {new Date(order.placed_at).toLocaleString("fa-IR")}
                </p>
                {order.items && order.items.length > 0 ? (
                  <div>
                    <p style={{ margin: "0 0 4px", fontWeight: 700 }}>جزئیات سفارش</p>
                    <ul style={{ margin: 0, paddingInlineStart: 16 }}>
                      {order.items.map((item) => (
                        <li key={item.id} style={{ marginBottom: 4 }}>
                          <span>{item.product_title_snapshot}</span>{" "}
                          <span className="muted">
                            ×{item.quantity} — {formatCurrency(item.line_subtotal ?? item.unit_price_snapshot * item.quantity)}
                          </span>
                        </li>
                      ))}
                    </ul>
                  </div>
                ) : null}
                {order.delivery ? (
                  <p className="muted" style={{ marginTop: 8 }}>
                    نوع ارسال: {translateDelivery(order.delivery.delivery_type || order.delivery_type)}{" "}
                    {order.delivery.tracking_code ? `• کد پیگیری: ${order.delivery.tracking_code}` : ""}
                  </p>
                ) : null}
                {order.status === "PENDING_PAYMENT" && order.payment_status !== "PAID" ? (
                  <div style={{ marginTop: 8 }}>
                    <button
                      className="secondary-button"
                      type="button"
                      onClick={() => handlePay(order.id)}
                      disabled={payingId === order.id}
                    >
                      {payingId === order.id ? "در حال اتصال به درگاه…" : "پرداخت سفارش"}
                    </button>
                    {paymentError?.orderId === order.id ? (
                      <p className="muted" style={{ margin: "4px 0 0", color: "var(--color-danger, #d14343)" }}>
                        {paymentError.message}
                      </p>
                    ) : null}
                  </div>
                ) : null}
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

function translateStatus(status: string) {
  const map: Record<string, string> = {
    PENDING_PAYMENT: "در انتظار پرداخت",
    PLACED: "ثبت شده",
    CONFIRMED: "تایید شده",
    PREPARING: "در حال آماده‌سازی",
    READY: "آماده تحویل",
    OUT_FOR_DELIVERY: "در حال ارسال",
    DELIVERED: "تحویل داده شده",
    CANCELLED: "لغو شده",
    FAILED: "ناموفق",
  };
  return map[status] ?? status;
}

function translatePaymentStatus(status: string) {
  const map: Record<string, string> = {
    UNPAID: "در انتظار پرداخت",
    PAID: "پرداخت شده",
    REFUNDED: "عودت داده شده",
    FAILED: "ناموفق",
  };
  return map[status] ?? status;
}

function translateDelivery(deliveryType?: string) {
  const map: Record<string, string> = {
    IN_ZONE: "ارسال داخلی",
    OUT_OF_ZONE_SNAPP: "ارسال با اسنپ",
  };
  return map[deliveryType || ""] ?? "ارسال";
}
