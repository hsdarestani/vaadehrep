import { Link } from "react-router-dom";
import { useMemo, useState } from "react";

type Variant = {
  code: string;
  name: string;
  price: number;
  details: string;
};

type MenuItem = {
  id: string;
  name_fa: string;
  category: string;
  emoji: string;
  selectedVariant: string;
  variants: Variant[];
};

const categories = [
  { id: "Breakfast", name: "صبحانه", emoji: "🍳" },
  { id: "Main", name: "غذای اصلی", emoji: "🍗" },
  { id: "Salad", name: "سالاد", emoji: "🥗" },
  { id: "Snack", name: "میان‌وعده", emoji: "🍪" },
];

const menuItems: MenuItem[] = [
  {
    id: "salad-caesar",
    name_fa: "سالاد سزار",
    category: "Salad",
    emoji: "🥗",
    selectedVariant: "B",
    variants: [
      { code: "B", name: "استاندارد", price: 190000, details: "کاهو، مرغ گریل، نان تست، پارمزان، سس" },
      { code: "C", name: "ویژه (بزرگ)", price: 256000, details: "کاهو، مرغ گریل (بیشتر)، نان تست، پارمزان، سس" },
    ],
  },
  {
    id: "wrap-chicken",
    name_fa: "رپ مرغ",
    category: "Main",
    emoji: "🍗",
    selectedVariant: "B",
    variants: [
      { code: "B", name: "استاندارد", price: 240000, details: "نان تورتیلا، مرغ گریل، کاهو، گوجه، سس سالم" },
      { code: "C", name: "ویژه (بزرگ)", price: 324000, details: "نان تورتیلا بزرگ، مرغ گریل، کاهو، گوجه، سس سالم" },
    ],
  },
  {
    id: "french-toast",
    name_fa: "فرنچ تست",
    category: "Breakfast",
    emoji: "🍳",
    selectedVariant: "B",
    variants: [
      { code: "B", name: "استاندارد", price: 110000, details: "نان تست، تخم مرغ، شیر، شکر، کره" },
      { code: "C", name: "ویژه (بزرگ)", price: 148000, details: "نان تست (۳ عدد)، تخم مرغ، شیر، شکر، کره" },
    ],
  },
  {
    id: "fried-eggs",
    name_fa: "نیمرو",
    category: "Breakfast",
    emoji: "🍳",
    selectedVariant: "B",
    variants: [
      { code: "B", name: "استاندارد", price: 110000, details: "تخم مرغ (۲ عدد)، روغن/کره، ادویه" },
      { code: "C", name: "ویژه (بزرگ)", price: 148000, details: "تخم مرغ (۳ عدد)، کره، ادویه" },
    ],
  },
  {
    id: "grilled-chicken",
    name_fa: "خوراک مرغ گریل",
    category: "Main",
    emoji: "🍗",
    selectedVariant: "B",
    variants: [
      { code: "B", name: "استاندارد", price: 240000, details: "سینه مرغ (۱۵۰ گرم)، روغن زیتون، لیمو، سبزیجات گریل" },
      { code: "C", name: "ویژه (بزرگ)", price: 324000, details: "سینه مرغ (۲۰۰ گرم)، روغن زیتون، لیمو، سبزیجات گریل" },
    ],
  },
  {
    id: "veggie-salad",
    name_fa: "سالاد سبزیجات گریل",
    category: "Salad",
    emoji: "🥗",
    selectedVariant: "B",
    variants: [
      { code: "B", name: "استاندارد", price: 190000, details: "کدو، هویج، قارچ، فلفل دلمه‌ای، سس بالزامیک" },
      { code: "C", name: "ویژه (بزرگ)", price: 256000, details: "کدو، هویج، قارچ، فلفل دلمه‌ای، سس بالزامیک (حجم بیشتر)" },
    ],
  },
  {
    id: "oat-cookie",
    name_fa: "کوکی جو",
    category: "Snack",
    emoji: "🍪",
    selectedVariant: "B",
    variants: [
      { code: "B", name: "استاندارد", price: 45000, details: "کوکی جو سالم" },
      { code: "C", name: "ویژه (بزرگ)", price: 60000, details: "کوکی جو سالم بزرگ" },
    ],
  },
  {
    id: "omelette",
    name_fa: "املت گوجه",
    category: "Breakfast",
    emoji: "🍳",
    selectedVariant: "B",
    variants: [
      { code: "B", name: "استاندارد", price: 110000, details: "تخم مرغ (۲ عدد)، گوجه، پیاز، رب، روغن" },
      { code: "C", name: "ویژه (بزرگ)", price: 148000, details: "تخم مرغ (۳ عدد)، گوجه، پیاز، رب، روغن" },
    ],
  },
  {
    id: "orange-cake",
    name_fa: "کیک پرتقال",
    category: "Snack",
    emoji: "🍪",
    selectedVariant: "B",
    variants: [
      { code: "B", name: "استاندارد", price: 45000, details: "اسلایس کیک پرتقالی خانگی" },
      { code: "C", name: "ویژه (بزرگ)", price: 60000, details: "اسلایس بزرگ" },
    ],
  },
  {
    id: "pb-banana",
    name_fa: "تست بادام‌زمینی و موز",
    category: "Breakfast",
    emoji: "🍳",
    selectedVariant: "B",
    variants: [
      { code: "B", name: "استاندارد", price: 110000, details: "نان تست، کره بادام زمینی، موز" },
      { code: "C", name: "ویژه (بزرگ)", price: 148000, details: "نان تست (۲ عدد)، کره بادام زمینی، موز" },
    ],
  },
  {
    id: "shredded-sandwich",
    name_fa: "ساندویچ مرغ ریش‌ریش",
    category: "Main",
    emoji: "🍗",
    selectedVariant: "B",
    variants: [
      { code: "B", name: "استاندارد", price: 240000, details: "مرغ ریش‌ریش، مایونز لایت، کاهو، خیارشور، نان" },
      { code: "C", name: "ویژه (بزرگ)", price: 324000, details: "مرغ ریش‌ریش (۲۰۰ گرم)، مایونز لایت، کاهو، خیارشور، نان" },
    ],
  },
];

export function HomePage() {
  const [activeCategory, setActiveCategory] = useState(categories[0].id);
  const [selectedVariants, setSelectedVariants] = useState<Record<string, string>>(
    () => Object.fromEntries(menuItems.map((item) => [item.id, item.selectedVariant])),
  );

  const filteredItems = useMemo(
    () => menuItems.filter((item) => item.category === activeCategory),
    [activeCategory],
  );

  return (
    <>
      <section className="landing-hero">
        <div className="container hero">
          <div className="hero-text">
            <span className="pill">آرامش در یک لقمه</span>
            <h1>
              وقتت ارزشمنده؛ <span style={{ color: "#2a6640" }}>غذا</span> هم باید سالم باشه.
            </h1>
            <p>
              «وعده» برای وقتیه که می‌خوای غذای ساده و سالم بخوری. ما غذا رو آماده می‌کنیم، تو وقتت رو بذار
              برای کار و زندگی.
            </p>
            <div className="hero-actions">
              <Link to="/menu" className="primary-button">
                سفارش اولین وعده
              </Link>
              <a href="#mission" className="secondary-button">
                چرا وعده؟
              </a>
            </div>
            <p className="muted" style={{ marginTop: 8 }}>
              ارسال سریع در محدوده ونک و صادقیه | قیمت‌ها به تومان نمایش داده می‌شود.
            </p>
          </div>

          <div className="hero-card">
            <div className="hero-card-content">
              <span className="hero-chip">آماده‌ی سرو • پخت سالم</span>
              <div style={{ display: "grid", gap: 6 }}>
                <p style={{ margin: 0, color: "#0f172a", fontWeight: 900, fontSize: 18 }}>غذای امروز</p>
                <p style={{ margin: 0, color: "#475569" }}>ساده، بدون سس صنعتی، با روغن کم.</p>
              </div>
              <div className="variant-toggle" aria-label="نمونه انتخاب اندازه">
                <button className="variant-button active">استاندارد</button>
                <button className="variant-button">ویژه</button>
              </div>
            </div>
            <div className="stamp">
              <div className="hero-chip" style={{ borderStyle: "solid", fontWeight: 900 }}>
                🌱 سالم و در دسترس
              </div>
              <div style={{ display: "grid", gap: 2 }}>
                <span style={{ fontSize: 12, color: "#475569" }}>یه وقفه‌ کوتاه</span>
                <strong style={{ color: "#0f172a" }}>A Bite of Calm</strong>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section id="menu" className="section-block">
        <div className="container">
          <div className="section-head">
            <span className="section-eyebrow">منوی روزانه</span>
            <h2 className="section-title">ساده، شفاف و دقیقا همون چیزی که بدنت لازم داره</h2>
            <p className="section-subtitle">اندازه‌ها و قیمت‌ها برای سفارش تکراری طراحی شده‌اند.</p>
          </div>

          <div className="tab-list">
            {categories.map((cat) => (
              <button
                key={cat.id}
                className={`tab ${activeCategory === cat.id ? "active" : ""}`}
                onClick={() => setActiveCategory(cat.id)}
              >
                <span aria-hidden>{cat.emoji}</span> {cat.name}
              </button>
            ))}
          </div>

          <div className="menu-grid">
            {filteredItems.map((item) => {
              const variant = item.variants.find((v) => v.code === selectedVariants[item.id]) || item.variants[0];
              return (
                <article key={item.id} className="menu-card">
                  <div className="menu-title">
                    <span>{item.name_fa}</span>
                    <span aria-hidden>{item.emoji}</span>
                  </div>
                  <p className="menu-desc">{variant.details}</p>

                  {item.variants.length > 1 && (
                    <div className="variant-toggle" role="group" aria-label={`انتخاب اندازه ${item.name_fa}`}>
                      {item.variants.map((v) => (
                        <button
                          key={v.code}
                          className={`variant-button ${variant.code === v.code ? "active" : ""}`}
                          onClick={() => setSelectedVariants((prev) => ({ ...prev, [item.id]: v.code }))}
                        >
                          {v.name}
                        </button>
                      ))}
                    </div>
                  )}

                  <div className="menu-footer">
                    <div className="price">
                      <small>قیمت برای شما</small>
                      <div>
                        {formatPrice(variant.price)} <small>تومان</small>
                      </div>
                    </div>
                    <Link to="/menu" className="ghost-link">
                      سفارش از منو →
                    </Link>
                  </div>
                </article>
              );
            })}
          </div>
        </div>
      </section>

      <section id="mission" className="section-block" style={{ background: "#f9fbf9" }}>
        <div className="container">
          <div className="section-head">
            <span className="section-eyebrow">رسالت ما</span>
            <h2 className="section-title">جایی بین فست‌فود سنگین و رژیمی لاکچری</h2>
            <p className="section-subtitle">نه اونقدر چرب که سنگین بشی، نه اونقدر گرون و کم‌حجم که سیر نشی.</p>
          </div>

          <div className="balance-grid">
            <div className="balance-card" aria-label="فست فود چرب">
              <div style={{ fontSize: 42 }}>🍔</div>
              <div>
                <h3 style={{ margin: "6px 0", color: "#0f172a" }}>فست‌فود چرب</h3>
                <p className="muted">خواب‌آلودگی بعد از غذا و ضرر برای بدن در طولانی‌مدت.</p>
              </div>
              <span className="label" style={{ background: "#fef2f2", color: "#ef4444" }}>
                ❌ مناسب هر روز نیست
              </span>
            </div>

            <div className="balance-card highlight" aria-label="وعده">
              <div style={{ fontSize: 48 }}>🌱</div>
              <div>
                <h3 style={{ margin: "6px 0" }}>سالم و در دسترس</h3>
                <p style={{ margin: 0, color: "#e2f6e8" }}>
                  غذایی که می‌تونی هر روز بخوری. مواد اولیه ساده، پخت سالم و قیمتی که جیبت رو خالی نمی‌کنه.
                </p>
              </div>
              <span className="label" style={{ background: "#c6f6d5", color: "#1c4532" }}>
                ✅ نقطه تعادل
              </span>
            </div>

            <div className="balance-card" aria-label="رژیمی لوکس">
              <div style={{ fontSize: 42 }}>🥗</div>
              <div>
                <h3 style={{ margin: "6px 0", color: "#0f172a" }}>رژیمی لوکس</h3>
                <p className="muted">خیلی گرون یا خیلی کم‌حجم؛ بیشتر حس تنبیه داره تا غذا!</p>
              </div>
              <span className="label" style={{ background: "#eff6ff", color: "#3b82f6" }}>
                ❌ سخت برای هر روز
              </span>
            </div>
          </div>
        </div>
      </section>

      <section className="section-block">
        <div className="container">
          <h2 className="section-title" style={{ textAlign: "center", marginBottom: 28 }}>
            قول‌های ما به شما
          </h2>
          <div className="promise-grid">
            <PromiseCard icon="⏳" title="وقتت طلاست" description="غذا آماده‌ست، نه تازه شروعِ پخت." />
            <PromiseCard icon="🌿" title="مواد واقعی" description="بدون سس‌های عجیب و پرچرب صنعتی." />
            <PromiseCard icon="💰" title="قیمت برای تکرار" description="مناسب برای چند بار سفارش در هفته." />
            <PromiseCard icon="❤️" title="آرامش در یک لقمه" description="یه وقفه کوتاه و آروم وسط روز شلوغت." />
          </div>
        </div>
      </section>

      <section id="cooperation" className="section-block">
        <div className="container">
          <div className="b2b-block">
            <div className="b2b-content">
              <span className="section-eyebrow" style={{ margin: "0 auto" }}>
                همکاری B2B
              </span>
              <h2 className="section-title" style={{ color: "#fff", margin: "10px 0" }}>
                آشپزخانه دارید؟ با «وعده» رشد کنید
              </h2>
              <p style={{ margin: 0, color: "rgba(255,255,255,0.8)" }}>
                ما دنبال پارتنرهایی هستیم که به کیفیت اهمیت میدن. منوی مشخص، دستورالعمل شفاف و فروش پایدار.
              </p>
              <Link to="/vendor" className="ghost-button" style={{ margin: "12px auto 0" }}>
                درخواست همکاری
              </Link>
            </div>
          </div>
        </div>
      </section>

      <footer className="footer">
        <div className="container">
          <div>
            <div style={{ fontWeight: 900, fontSize: 20, color: "#c6f6d5" }}>وعده</div>
            <div className="muted" style={{ fontSize: 12 }}>
              A Bite of Calm
            </div>
          </div>
          <div className="footer-links">
            <a href="#menu">منو</a>
            <a href="#mission">داستان ما</a>
            <Link to="/orders">پیگیری سفارش</Link>
          </div>
          <div className="muted" style={{ fontSize: 12 }}>
            © ۱۴۰۳ تمامی حقوق محفوظ است.
          </div>
        </div>
      </footer>
    </>
  );
}

type PromiseCardProps = {
  icon: string;
  title: string;
  description: string;
};

function PromiseCard({ icon, title, description }: PromiseCardProps) {
  return (
    <div className="promise">
      <div className="promise-icon" aria-hidden>
        {icon}
      </div>
      <div>
        <h3>{title}</h3>
        <p>{description}</p>
      </div>
    </div>
  );
}

function formatPrice(price: number) {
  return price.toLocaleString("fa-IR");
}
