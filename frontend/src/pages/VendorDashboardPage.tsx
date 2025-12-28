import { useCallback, useEffect, useMemo, useState } from "react";
import { Navigate } from "react-router-dom";

import { endpoints } from "../api/endpoints";
import type { VendorOrder } from "../api/types";
import { useAuth } from "../state/auth";

type VendorStatus = "PREPARING" | "OUT_FOR_DELIVERY";

const STATUS_LABELS: Record<string, string> = {
  PENDING_PAYMENT: "در انتظار پرداخت",
  PLACED: "ثبت شده",
  CONFIRMED: "تایید شده",
  PREPARING: "در حال آماده‌سازی",
  READY: "آماده تحویل",
  OUT_FOR_DELIVERY: "ارسال شد",
  DELIVERED: "تحویل داده شده",
  CANCELLED: "لغو شده",
  FAILED: "ناموفق",
};

function statusLabel(status: string) {
  return STATUS_LABELS[status] ?? status;
}

function canMarkPreparing(order: VendorOrder) {
  return ["PLACED", "CONFIRMED"].includes(order.status);
}

function canMarkOutForDelivery(order: VendorOrder) {
  return order.status === "PREPARING";
}

function mapLink(order: VendorOrder) {
  if (order.delivery_lat != null && order.delivery_lng != null) {
    return `https://maps.google.com/?q=${order.delivery_lat},${order.delivery_lng}`;
  }
  return null;
}

function formatCurrency(amount?: number | null) {
  const value = amount ?? 0;
  return Intl.NumberFormat("fa-IR", { style: "currency", currency: "IRR", maximumFractionDigits: 0 }).format(value);
}

export function VendorDashboardPage() {
  const { user } = useAuth();
  const vendorRole = user?.vendor_role;
  const [orders, setOrders] = useState<VendorOrder[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [actionOrder, setActionOrder] = useState<string | null>(null);

  const fetchOrders = useCallback(async () => {
    if (!vendorRole) return;
    setLoading(true);
    try {
      const { data } = await endpoints.vendorOrders();
      setOrders(data);
      setError(null);
    } catch (err) {
      console.error(err);
      setError("خطا در دریافت سفارش‌ها. لطفاً دوباره تلاش کنید.");
    } finally {
      setLoading(false);
    }
  }, [vendorRole]);

  useEffect(() => {
    if (!vendorRole) return;
    void fetchOrders();
    const interval = setInterval(fetchOrders, 15000);
    return () => clearInterval(interval);
  }, [fetchOrders, vendorRole]);

  const handleStatusChange = async (orderId: string, status: VendorStatus) => {
    setActionOrder(`${orderId}:${status}`);
    try {
      await endpoints.updateVendorOrderStatus(orderId, status);
      await fetchOrders();
      setError(null);
    } catch (err) {
      console.error(err);
      setError("به‌روزرسانی وضعیت سفارش ناموفق بود.");
    } finally {
      setActionOrder(null);
    }
  };

  const visibleOrders = useMemo(() => {
    const sorted = [...(orders || [])];
    sorted.sort((a, b) => new Date(b.placed_at).getTime() - new Date(a.placed_at).getTime());
    return sorted;
  }, [orders]);

  if (!vendorRole) {
    return <Navigate to="/login" replace />;
  }

  return (
    <section className="section" style={{ paddingTop: 32 }}>
      <div className="container small" style={{ maxWidth: 720 }}>
        <div className="section-head" style={{ textAlign: "center" }}>
          <span className="section-eyebrow">پنل فروشنده</span>
          <h1 className="section-title" style={{ marginBottom: 8 }}>
            سفارش‌های فعال {vendorRole.vendor_name}
          </h1>
          <p className="section-subtitle">
            این صفحه هر ۱۵ ثانیه تازه می‌شود. از اینجا سفارش را «در حال آماده‌سازی» کنید و بعد روی «ارسال شد» بزنید.
          </p>
        </div>

        {error ? (
          <div className="card" style={{ border: "1px solid var(--color-danger, #d14343)", marginBottom: 12 }}>
            <p style={{ margin: 0 }}>{error}</p>
          </div>
        ) : null}

        {loading && !visibleOrders.length ? (
          <p className="muted" style={{ textAlign: "center" }}>
            در حال بارگذاری سفارش‌ها…
          </p>
        ) : null}

        {!loading && !visibleOrders.length ? (
          <p className="muted" style={{ textAlign: "center" }}>
            سفارشی برای نمایش وجود ندارد.
          </p>
        ) : null}

        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          {visibleOrders.map((order) => {
            const phone = order.customer_phone || "-";
            const locationUrl = mapLink(order);
            const orderActionKeyPreparing = `${order.id}:PREPARING`;
            const orderActionKeyDelivery = `${order.id}:OUT_FOR_DELIVERY`;
            const status = statusLabel(order.status);
            const statusTone =
              order.status === "PREPARING"
                ? "var(--color-warning, #b07900)"
                : order.status === "OUT_FOR_DELIVERY"
                  ? "var(--color-primary, #1a8f2b)"
                  : "var(--color-muted, #6b7280)";

            return (
              <div key={order.id} className="card" style={{ textAlign: "right" }}>
                <div className="card-head" style={{ marginBottom: 8, display: "flex", justifyContent: "space-between", gap: 12 }}>
                  <h3 style={{ margin: 0 }}>کد سفارش: {order.short_code}</h3>
                  <span
                    style={{
                      alignSelf: "flex-start",
                      background: `${statusTone}22`,
                      color: statusTone,
                      borderRadius: 999,
                      padding: "6px 12px",
                      fontSize: 12,
                      fontWeight: 700,
                    }}
                  >
                    {status}
                  </span>
                </div>
                <div className="muted" style={{ margin: "0 0 8px" }}>
                  <span style={{ display: "inline-block", minWidth: 140 }}>ثبت شده:</span>{" "}
                  {new Date(order.placed_at).toLocaleString("fa-IR")}
                </div>
                <div className="muted" style={{ margin: "0 0 12px" }}>
                  مبلغ: {formatCurrency(order.total_amount)}
                </div>

                <div style={{ marginBottom: 12 }}>
                  <p style={{ margin: "0 0 4px", fontWeight: 700 }}>اطلاعات مشتری</p>
                  <p className="muted" style={{ margin: 0 }}>
                    {order.customer_name || "مشتری"} •{" "}
                    {phone ? (
                      <a href={`tel:${phone}`} className="muted">
                        {phone}
                      </a>
                    ) : (
                      "شماره موجود نیست"
                    )}
                  </p>
                </div>

                <div style={{ marginBottom: 12 }}>
                  <p style={{ margin: "0 0 4px", fontWeight: 700 }}>آدرس و لوکیشن</p>
                  <p className="muted" style={{ margin: "0 0 4px" }}>{order.delivery_address_text || "—"}</p>
                  {order.delivery_notes ? (
                    <p className="muted" style={{ margin: "0 0 4px" }}>یادداشت: {order.delivery_notes}</p>
                  ) : null}
                  {locationUrl ? (
                    <a href={locationUrl} className="secondary-button" target="_blank" rel="noreferrer">
                      مشاهده لوکیشن روی نقشه
                    </a>
                  ) : (
                    <span className="muted">لوکیشن ثبت نشده است.</span>
                  )}
                </div>

                {order.items && order.items.length ? (
                  <div style={{ marginBottom: 12 }}>
                    <p style={{ margin: "0 0 4px", fontWeight: 700 }}>اقلام سفارش</p>
                    <ul style={{ margin: 0, paddingInlineStart: 16 }}>
                      {order.items.map((item) => (
                        <li key={item.id} style={{ marginBottom: 4 }}>
                          {item.product_title_snapshot} <span className="muted">×{item.quantity}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                ) : null}

                <div className="vendor-flex" style={{ gap: 8 }}>
                  <button
                    type="button"
                    className="secondary-button"
                    disabled={!canMarkPreparing(order) || actionOrder === orderActionKeyPreparing}
                    onClick={() => handleStatusChange(order.id, "PREPARING")}
                  >
                    {actionOrder === orderActionKeyPreparing ? "در حال ثبت…" : "در حال آماده‌سازی"}
                  </button>
                  <button
                    type="button"
                    className="primary-button"
                    disabled={!canMarkOutForDelivery(order) || actionOrder === orderActionKeyDelivery}
                    onClick={() => handleStatusChange(order.id, "OUT_FOR_DELIVERY")}
                  >
                    {actionOrder === orderActionKeyDelivery ? "در حال ارسال…" : "ارسال شد"}
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
