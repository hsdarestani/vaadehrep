import { useEffect, useMemo, useRef, useState } from "react";

import { useVendorCatalog } from "../hooks/useCatalog";
import { Card } from "../components/common/Card";
import { useCart } from "../state/cart";

export function MenuPage() {
  const [vendorId, setVendorId] = useState<number | null>(null);
  const { vendors, products, isLoading } = useVendorCatalog(vendorId || undefined);
  const addToCart = useCart((s) => s.add);
  const [feedback, setFeedback] = useState<string | null>(null);
  const timerRef = useRef<number | null>(null);

  useEffect(() => {
    return () => {
      if (timerRef.current) {
        window.clearTimeout(timerRef.current);
      }
    };
  }, []);

  const sortedProducts = useMemo(() => {
    return [...(products || [])].sort((a, b) => (a.sort_order ?? 0) - (b.sort_order ?? 0));
  }, [products]);

  const handleAddToCart = (product: (typeof sortedProducts)[number]) => {
    addToCart({
      productId: product.id,
      title: product.name_fa,
      price: product.base_price || 0,
      quantity: 1,
      options: [],
    });
    if (timerRef.current) {
      window.clearTimeout(timerRef.current);
    }
    setFeedback(`${product.name_fa} به سبد خرید اضافه شد`);
    timerRef.current = window.setTimeout(() => setFeedback(null), 2500);
  };

  return (
    <section className="section">
      <div className="container">
        <div className="section-head" style={{ textAlign: "center" }}>
          <span className="section-eyebrow">منوی امروز</span>
          <h1 className="section-title" style={{ marginBottom: 8 }}>
            انتخاب غذای سالم از منو
          </h1>
          <p className="section-subtitle">ابتدا رستوران را انتخاب کن و سپس آیتم مورد نظرت را به سبد اضافه کن.</p>
        </div>

        {feedback ? <div className="feedback success">{feedback}</div> : null}

        <div className="vendor-switcher">
          {(vendors || []).map((vendor) => (
            <button
              key={vendor.id}
              onClick={() => setVendorId(vendor.id)}
              className={`pill-option ${vendorId === vendor.id ? "active" : ""}`}
              style={{ minWidth: 140 }}
            >
              {vendor.name}
            </button>
          ))}
        </div>

        {isLoading ? (
          <p className="muted" style={{ textAlign: "center" }}>
            در حال بارگذاری منو...
          </p>
        ) : (
          <div className="card-grid centered-grid">
            {sortedProducts.map((product) => (
              <Card
                key={product.id}
                title={product.name_fa}
                description={product.short_description || product.description}
                footer={
                  <button className="primary-button" onClick={() => handleAddToCart(product)}>
                    افزودن به سبد
                  </button>
                }
              >
                <p style={{ marginTop: 8, fontWeight: 600 }}>{formatCurrency(product.base_price)}</p>
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
