import { Link, useLocation } from "react-router-dom";
import { useMemo } from "react";

export function PaymentResultPage() {
  const location = useLocation();
  const query = useMemo(() => new URLSearchParams(location.search), [location.search]);

  const paymentStatusRaw = (query.get("payment_status") ?? query.get("paymentStatus") ?? "").toUpperCase();
  const orderStatusRaw = (query.get("order_status") ?? query.get("orderStatus") ?? "").toUpperCase();
  const orderId = query.get("order_id") ?? query.get("orderId") ?? "";
  const orderCode = query.get("order_code") ?? query.get("orderCode") ?? "";
  const trackId = query.get("track_id") ?? query.get("trackId") ?? "";
  const refNumber = query.get("ref_number") ?? query.get("refNumber") ?? "";
  const gatewayMessage = query.get("message") ?? "";

  const isSuccess = paymentStatusRaw === "PAID" || orderStatusRaw === "CONFIRMED";
  const paymentStatusLabel = translatePaymentStatus(paymentStatusRaw || "UNKNOWN");
  const orderStatusLabel = translateOrderStatus(orderStatusRaw || "UNKNOWN");

  const details = [
    { label: "وضعیت پرداخت", value: paymentStatusLabel },
    { label: "وضعیت سفارش", value: orderStatusLabel },
    { label: "کد سفارش", value: orderCode || orderId },
    { label: "کد پیگیری درگاه", value: trackId },
    { label: "شماره مرجع", value: refNumber },
    { label: "پیام درگاه", value: gatewayMessage },
  ].filter((item) => !!item.value);

  return (
    <section className="section">
      <div className="container small">
        <div className="section-head" style={{ textAlign: "center" }}>
          <span className="section-eyebrow">نتیجه پرداخت</span>
          <h1 className="section-title" style={{ marginBottom: 8 }}>
            {isSuccess ? "پرداخت با موفقیت انجام شد" : "پرداخت ناموفق بود"}
          </h1>
          <p className="section-subtitle">
            {isSuccess
              ? "اطلاعات پرداخت و سفارش شما در زیر نمایش داده شده است."
              : "اطلاعات وضعیت پرداخت شما در زیر نمایش داده شده است. در صورت بروز مشکل، لطفاً دوباره تلاش کنید یا با پشتیبانی تماس بگیرید."}
          </p>
        </div>

        <div className="card" style={{ marginBottom: 16 }}>
          <p style={{ margin: 0, fontWeight: 700, color: isSuccess ? "#18794e" : "#d14343" }}>
            {isSuccess ? "پرداخت ثبت شد" : "پرداخت تایید نشد"}
          </p>
          <p className="muted" style={{ margin: "4px 0 0" }}>
            وضعیت پرداخت: {paymentStatusLabel}
          </p>
        </div>

        {details.length > 0 ? (
          <div className="card">
            <p style={{ margin: 0, fontWeight: 700 }}>جزئیات</p>
            <ul style={{ margin: "8px 0 0", paddingInlineStart: 16 }}>
              {details.map((item) => (
                <li key={item.label} style={{ marginBottom: 4 }}>
                  <span style={{ fontWeight: 600 }}>{item.label}:</span>{" "}
                  <span className="muted" style={{ direction: "ltr" }}>
                    {item.value}
                  </span>
                </li>
              ))}
            </ul>
          </div>
        ) : null}

        <div style={{ display: "flex", gap: 12, marginTop: 16, flexWrap: "wrap" }}>
          <Link to="/orders" className="primary-button">
            مشاهده سفارش‌ها
          </Link>
          <Link to="/" className="secondary-button">
            بازگشت به صفحه اصلی
          </Link>
        </div>
      </div>
    </section>
  );
}

function translatePaymentStatus(status: string) {
  const map: Record<string, string> = {
    PAID: "پرداخت شده",
    FAILED: "ناموفق",
    UNPAID: "در انتظار پرداخت",
    REFUNDED: "عودت داده شده",
  };
  return map[status] ?? status;
}

function translateOrderStatus(status: string) {
  const map: Record<string, string> = {
    CONFIRMED: "تایید شده",
    FAILED: "ناموفق",
    PENDING_PAYMENT: "در انتظار پرداخت",
    PLACED: "ثبت شده",
    PREPARING: "در حال آماده‌سازی",
    READY: "آماده تحویل",
    OUT_FOR_DELIVERY: "در حال ارسال",
    DELIVERED: "تحویل داده شده",
    CANCELLED: "لغو شده",
  };
  return map[status] ?? status;
}
