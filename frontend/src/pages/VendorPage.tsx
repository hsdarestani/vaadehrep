import { FormEvent, useMemo, useState } from "react";

const WORKER_URL = "https://vaadeh-vendor.hsdf7rb.workers.dev/vendor/";

type StatBlock = { title: string; description: string; accent?: "brand" | "brown" | "light" };

const whyUs: StatBlock[] = [
  {
    title: "تمرکز روی پخت و تحویل",
    description: "نیازی نیست درگیر پیج، تبلیغات یا مدیریت چند پلتفرم شوید. شما طبق استاندارد می‌پزید؛ بقیه مسیر دست ماست.",
    accent: "brand",
  },
  {
    title: "درآمد قابل پیش‌بینی",
    description: "منوی محدود یعنی ظرفیت تولید قابل برنامه‌ریزی. هدف ما جریان فروش ثابت است، نه فروش‌های مقطعی.",
    accent: "brown",
  },
  {
    title: "اعتبار مشترک",
    description: "غذای شما با نام «وعده» عرضه می‌شود. ما روی اعتماد مشتری سرمایه‌گذاری می‌کنیم؛ شما با اجرای دقیق استانداردها این اعتماد را حفظ می‌کنید.",
    accent: "light",
  },
];

const steps = [
  { title: "بررسی اولیه", copy: "فرم را پر می‌کنید و ما با توجه به موقعیت، ظرفیت و مجوزها بررسی اولیه انجام می‌دهیم." },
  { title: "طراحی منوی اختصاصی", copy: "یک منوی محدود شامل وزن، دستور پخت و سس‌های مشخص برای شما طراحی می‌شود." },
  { title: "تست و استانداردسازی", copy: "یک دوره تست (مثلاً ۱۰–۲۰ سفارش روزانه) اجرا می‌شود تا کیفیت، سرعت و رضایت سنجیده شود." },
  { title: "افزایش سفارش", copy: "اگر فاز تست موفق باشد، بودجه مارکتینگ افزایش پیدا می‌کند و تعداد سفارش‌ها بالا می‌رود." },
];

const requirements = [
  {
    title: "پخت سالم و قابل کنترل",
    body: "گریل، فر، آب‌پز و سوتِه کم‌چرب در اولویت است. سرخ‌کردن عمیق فقط در موارد محدود.",
  },
  {
    title: "تحویل به‌موقع و نظم کاری",
    body: "سرعت آماده‌سازی، نگهداری درست و بسته‌بندی تمیز از اصول مهم ماست.",
  },
  {
    title: "داشتن مجوز یا امکان دریافت آن",
    body: "برای همکاری طولانی‌مدت، مجوز بهداشتی ضروری است.",
  },
  {
    title: "تعهد به استانداردها",
    body: "وزن، بسته‌بندی و کیفیت باید ثابت و قابل کنترل باشند.",
  },
];

const faqs = [
  {
    q: "مدل تسویه چگونه است؟",
    a: "بسته به توافق، یا درصدی از فروش برای آشپزخانه است، یا مبلغ ثابت برای هر پرس. همه جزئیات شفاف در قرارداد اعلام می‌شود.",
  },
  {
    q: "آیا باید منوی فعلی‌مان را کنار بگذاریم؟",
    a: "خیر. منوی فعلی شما سر جای خودش است. تنها نکته این است که «خط وعده» باید استاندارد و قابل کنترل باشد.",
  },
  {
    q: "اگر استاندارد رعایت نشود چه می‌شود؟",
    a: "کیفیت برای ما حیاتی است. اگر خطا تکرار شود یا شکایت جدی ایجاد شود، همکاری متوقف می‌شود.",
  },
  {
    q: "فعلاً در چه محدوده‌ای همکاری می‌پذیرید؟",
    a: "در فاز اول روی چند محله تهران متمرکز هستیم. اگر خارج از محدوده باشید، امکان همکاری در فازهای بعدی بررسی می‌شود.",
  },
];

export function VendorPage() {
  const [status, setStatus] = useState<"idle" | "success" | "error" | "submitting">("idle");

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const form = event.currentTarget;
    setStatus("submitting");
    const formData = new FormData(form);
    const body = new URLSearchParams();
    formData.forEach((value, key) => body.append(key, value.toString()));

    try {
      const res = await fetch(WORKER_URL, {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body,
      });
      if (res.ok) {
        setStatus("success");
        form.reset();
      } else {
        setStatus("error");
      }
    } catch (error) {
      setStatus("error");
    }
  };

  const statusBox = useMemo(() => {
    if (status === "success") {
      return { className: "vendor-alert success", text: "فرم با موفقیت ارسال شد. بعد از بررسی با شما تماس می‌گیریم." };
    }
    if (status === "error") {
      return { className: "vendor-alert error", text: "ارسال فرم با مشکل مواجه شد. لطفاً کمی بعد دوباره امتحان کنید." };
    }
    return null;
  }, [status]);

  return (
    <div className="app-main vendor-page">
      <header className="vendor-hero" id="apply">
        <div className="container vendor-hero-grid">
          <div className="vendor-hero-text">
            <p className="vendor-badge">
              <span role="img" aria-label="handshake">
                🤝
              </span>
              همکاری با آشپزخانه‌ها و کترینگ‌ها
            </p>
            <h1>
              کاری کنید آشپزخانه‌تان <span>بدون ریسک شلوغ‌تر شود</span>
            </h1>
            <p className="muted">
              وعده برای آشپزخانه‌هایی ساخته شده که کاربلدند، ظرفیت دارند و می‌خواهند فروش بیشتری تجربه کنند، اما وقت اضافه
              برای بازاریابی و مدیریت سفارش‌ها ندارند. ما سفارش می‌آوریم؛ شما فقط غذا را طبق یک منوی ساده و مشخص آماده
              می‌کنید.
            </p>
            <div className="hero-actions">
              <a href="#apply-form" className="primary-button">
                پر کردن فرم همکاری
              </a>
              <a href="#why-us" className="secondary-button">
                چرا وعده؟
              </a>
            </div>
            <p className="muted vendor-note">
              مناسب برای آشپزخانه‌های خانگی مجوزدار، کترینگ‌های کوچک و رستوران‌هایی که ظرفیت خالی در یک شیفت دارند.
            </p>
          </div>

          <div className="vendor-hero-media">
            <div className="vendor-hero-image">
              <img src="/vaade.jpg" alt="نمونه همکاری با وعده" />
            </div>
            <div className="vendor-hero-stats">
              <div className="stat-card primary">
                <p className="muted small">یک سناریوی معمول همکاری</p>
                <p className="stat-number">۵۰–۷۰</p>
                <p className="muted small">سفارش روزانه بعد از دوره تست و تثبیت کیفیت</p>
                <p className="muted micro">بسته به ظرفیت، موقعیت و کیفیت اجرا متغیر است.</p>
              </div>
              <div className="stat-card outline">
                <p className="muted small">ساختار منو</p>
                <p className="stat-number alt">۳–۵ آیتم</p>
                <p className="muted small">بر پایه یک پروتئین (مرغ) + چند سس اختصاصی</p>
                <p className="muted micro">منوی محدود یعنی کار ساده‌تر و تکرارپذیری بیشتر.</p>
              </div>
            </div>
          </div>
        </div>
      </header>

      <section id="why-us" className="section-block vendor-section brand-soft">
        <div className="container">
          <div className="section-head">
            <span className="section-eyebrow with-icon">
              <span role="img" aria-label="chart">
                📈
              </span>
              رشد مطمئن
            </span>
            <h2 className="section-title">وعده برای وندورها چه مزیتی دارد؟</h2>
            <p className="section-subtitle">
              ما از شما فقط یک چیز می‌خواهیم: کیفیت و نظم. در عوض، بازاریابی، برندینگ، طراحی منو و مدیریت سفارش‌ها را ما انجام
              می‌دهیم.
            </p>
          </div>

          <div className="vendor-grid triple">
            {whyUs.map((item, idx) => (
              <div key={item.title} className={`vendor-card feature accent-${item.accent || "brand"}`}>
                <div className="vendor-card-emoji">{["🎯", "💸", "🧱"][idx]}</div>
                <h3>{item.title}</h3>
                <p className="muted">{item.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section id="how-it-works" className="section-block">
        <div className="container">
          <div className="section-head">
            <span className="section-eyebrow">مراحل همکاری</span>
            <h2 className="section-title">از فرم تا اولین سفارش</h2>
            <p className="section-subtitle">فرآیند همکاری کاملاً شفاف و مرحله‌به‌مرحله طراحی شده تا ابهامی باقی نماند.</p>
          </div>
          <div className="vendor-grid quadruple">
            {steps.map((step, i) => (
              <div key={step.title} className="vendor-card step">
                <div className="step-badge">{i + 1}</div>
                <h3>{step.title}</h3>
                <p className="muted">{step.copy}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section id="requirements" className="section-block brand-soft">
        <div className="container vendor-flex">
          <div className="vendor-column">
            <h2 className="section-title">کدام آشپزخانه مناسب وعده است؟</h2>
            <p className="section-subtitle">
              برای حفظ کیفیت غذا و اعتماد مشتری، همکاری با هر نوع آشپزخانه ممکن نیست. چند معیار پایه داریم:
            </p>
            <ul className="vendor-list">
              {requirements.map((req) => (
                <li key={req.title}>
                  <span className="check">✅</span>
                  <div>
                    <p className="vendor-list-title">{req.title}</p>
                    <p className="muted small">{req.body}</p>
                  </div>
                </li>
              ))}
            </ul>
          </div>
          <div className="vendor-column">
            <div className="vendor-card table-card">
              <h3 className="table-title">
                <span role="img" aria-label="chart">
                  📊
                </span>
                نمونه سناریوی مالی
              </h3>
              <div className="vendor-table">
                <div className="vendor-table-row head">
                  <span>شاخص</span>
                  <span>حداقلی</span>
                  <span>هدف</span>
                </div>
                <div className="vendor-table-row">
                  <span>سفارش روزانه</span>
                  <span>۱۵–۱۰</span>
                  <span>۷۰–۵۰</span>
                </div>
                <div className="vendor-table-row">
                  <span>میانگین قیمت</span>
                  <span>۵۰۰ هزار تومان</span>
                  <span>۶۶۰ هزار تومان</span>
                </div>
                <div className="vendor-table-row">
                  <span>حاشیه سود</span>
                  <span>متغیر</span>
                  <span>متغیر</span>
                </div>
              </div>
              <p className="muted micro">
                این اعداد صرفاً برای نمایش ساختار همکاری هستند و بر اساس موقعیت، هزینه مواد اولیه و کیفیت اجرا دقیق‌سازی می‌شوند.
              </p>
            </div>
          </div>
        </div>
      </section>

      <section id="faq" className="section-block">
        <div className="container">
          <div className="section-head">
            <span className="section-eyebrow">سوالات متداول</span>
            <h2 className="section-title">قبل از ارسال فرم، این موارد را بدانید</h2>
          </div>
          <div className="vendor-accordion">
            {faqs.map((faq) => (
              <details key={faq.q} className="vendor-accordion-item">
                <summary>{faq.q}</summary>
                <p className="muted">{faq.a}</p>
              </details>
            ))}
          </div>
        </div>
      </section>

      <section id="apply-form" className="section-block vendor-apply">
        <div className="container small">
          <div className="section-head">
            <h2 className="section-title" style={{ color: "#fff" }}>
              آماده‌اید همکاری را شروع کنیم؟
            </h2>
            <p className="section-subtitle" style={{ color: "rgba(255,255,255,0.8)" }}>
              لطفاً فرم را کامل پر کنید. بعد از بررسی، برای هماهنگی تماس می‌گیریم.
            </p>
          </div>

          {statusBox ? <div className={statusBox.className}>{statusBox.text}</div> : null}

          <form className="vendor-form" onSubmit={handleSubmit}>
            <div className="vendor-form-grid">
              <FormField label="نام آشپزخانه / کترینگ" name="kitchen_name" placeholder="مثلاً: آشپزخانه بهار" required />
              <FormField label="نام و نام خانوادگی مسئول" name="contact_name" required />
            </div>

            <div className="vendor-form-grid">
              <FormField label="شماره تماس مستقیم" name="phone" placeholder="مثلاً: 0912..." required type="tel" />
              <FormField label="لینک اینستاگرام (در صورت وجود)" name="instagram" placeholder="instagram.com/..." />
            </div>

            <div className="vendor-form-grid">
              <FormField label="شهر / محله" name="city" placeholder="مثلاً: تهران، سعادت‌آباد" required />
              <label className="vendor-label">
                <span>نوع آشپزخانه</span>
                <select name="kitchen_type" required>
                  <option value="">انتخاب کنید</option>
                  <option>رستوران</option>
                  <option>کترینگ</option>
                  <option>آشپزخانه خانگی مجوزدار</option>
                  <option>سایر</option>
                </select>
              </label>
            </div>

            <div className="vendor-form-grid">
              <FormField label="ظرفیت تقریبی هر شیفت" name="capacity" placeholder="مثلاً: ۵۰–۸۰ پرس" />
              <label className="vendor-label">
                <span>آیا مجوز بهداشت دارید؟</span>
                <select name="has_health_license" required>
                  <option>بله</option>
                  <option>در حال اقدام</option>
                  <option>خیر</option>
                </select>
              </label>
            </div>

            <FormTextArea
              label="چه غذاهایی بیشتر می‌فروشید؟"
              name="current_menu"
              placeholder="مثلاً: انواع خورشت ایرانی، برنج، مرغ، سالاد و..."
            />
            <FormTextArea label="چرا فکر می‌کنید همکاری با وعده مناسب شماست؟" name="why_fit" />

            <div className="vendor-form-footer">
              <p className="muted micro">ارسال فرم به معنی شروع همکاری قطعی نیست. بعد از بررسی با شما تماس گرفته می‌شود.</p>
              <button className="primary-button" type="submit" disabled={status === "submitting"}>
                {status === "submitting" ? "در حال ارسال..." : "ارسال فرم"}
              </button>
            </div>
          </form>
        </div>
      </section>
    </div>
  );
}

type FormFieldProps = {
  label: string;
  name: string;
  required?: boolean;
  placeholder?: string;
  type?: string;
};

function FormField({ label, name, required, placeholder, type = "text" }: FormFieldProps) {
  return (
    <label className="vendor-label">
      <span>{label}</span>
      <input name={name} type={type} placeholder={placeholder} required={required} />
    </label>
  );
}

type FormTextAreaProps = {
  label: string;
  name: string;
  placeholder?: string;
};

function FormTextArea({ label, name, placeholder }: FormTextAreaProps) {
  return (
    <label className="vendor-label">
      <span>{label}</span>
      <textarea name={name} rows={3} placeholder={placeholder}></textarea>
    </label>
  );
}
