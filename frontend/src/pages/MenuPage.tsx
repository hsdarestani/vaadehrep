import { useMemo, useState } from "react";

import { useVendorCatalog } from "../hooks/useCatalog";
import { Card } from "../components/common/Card";
import { useCart } from "../state/cart";

export function MenuPage() {
  const [vendorId, setVendorId] = useState<number | null>(null);
  const { vendors, products, isLoading } = useVendorCatalog(vendorId || undefined);
  const addToCart = useCart((s) => s.add);

  const sortedProducts = useMemo(() => {
    return [...(products || [])].sort((a, b) => (a.sort_order ?? 0) - (b.sort_order ?? 0));
  }, [products]);

  return (
    <div className="section">
      <h1>Menu</h1>
      <p className="muted">Choose a vendor then browse categories and products.</p>

      <div style={{ margin: "16px 0", display: "flex", gap: 8, flexWrap: "wrap" }}>
        {(vendors || []).map((vendor) => (
          <button
            key={vendor.id}
            onClick={() => setVendorId(vendor.id)}
            className="button"
            style={{
              background: vendorId === vendor.id ? "#0f172a" : "#2563eb",
            }}
          >
            {vendor.name}
          </button>
        ))}
      </div>

      {isLoading ? (
        <p className="muted">Loading menu…</p>
      ) : (
        <div className="card-grid">
          {sortedProducts.map((product) => (
            <Card
              key={product.id}
              title={product.name}
              description={product.short_description || product.description}
              footer={
                <button
                  className="button"
                  onClick={() =>
                    addToCart({
                      productId: product.id,
                      title: product.name,
                      price: product.price_amount || 0,
                      quantity: 1,
                      options: [],
                    })
                  }
                >
                  Add to cart
                </button>
              }
            >
              <p style={{ marginTop: 8, fontWeight: 600 }}>{formatCurrency(product.price_amount)}</p>
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
