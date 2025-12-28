export function TermsPage() {
  return (
    <section className="section">
      <div className="container small">
        <div className="section-head" style={{ textAlign: "center" }}>
          <span className="section-eyebrow">قوانین و شرایط</span>
          <h1 className="section-title" style={{ marginBottom: 10 }}>
            تعهد ما به یک تجربه شفاف
          </h1>
          <p className="section-subtitle">لطفاً پیش از تکمیل خرید، شرایط زیر را مطالعه کن.</p>
        </div>

        <div className="card" style={{ display: "grid", gap: 14 }}>
          <div>
            <h3>۱. ثبت و پرداخت سفارش</h3>
            <p className="muted" style={{ margin: 0 }}>
              پرداخت آنلاین برای تایید سفارش ضروری است. در صورت انصراف پیش از آماده‌سازی، امکان لغو و بازگشت وجه طبق قوانین درگاه وجود دارد.
            </p>
          </div>

          <div>
            <h3>۲. زمان و محدوده ارسال</h3>
            <p className="muted" style={{ margin: 0 }}>
              بازه‌های تحویل بر اساس موقعیت ثبت‌شده محاسبه می‌شود. در صورت تغییر آدرس یا تاخیر پیک، پشتیبانی را مطلع کنید.
            </p>
          </div>

          <div>
            <h3>۳. کیفیت و بسته‌بندی</h3>
            <p className="muted" style={{ margin: 0 }}>
              اقلام در بسته‌بندی بهداشتی ارسال می‌شوند. اگر محصول آسیب دیده یا ناقص بود، حداکثر تا ۲ ساعت بعد از تحویل گزارش دهید.
            </p>
          </div>

          <div>
            <h3>۴. حریم خصوصی</h3>
            <p className="muted" style={{ margin: 0 }}>
              اطلاعات تماس و آدرس فقط برای پردازش سفارش و ارسال استفاده می‌شود و بدون اجازه شما به اشتراک گذاشته نخواهد شد.
            </p>
          </div>

          <div>
            <h3>۵. پشتیبانی</h3>
            <p className="muted" style={{ margin: 0 }}>
              در صورت بروز مشکل در پرداخت یا تحویل، از طریق بخش سفارش‌ها گزینه پرداخت مجدد را انتخاب کنید یا با پشتیبانی در ارتباط باشید.
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}
