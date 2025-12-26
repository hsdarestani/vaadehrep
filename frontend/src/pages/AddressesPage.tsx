import { FormEvent, useState } from "react";

import { useAddressBook } from "../hooks/useAddressBook";
import { Card } from "../components/common/Card";

export function AddressesPage() {
  const { addresses, createAddress, isLoading } = useAddressBook();
  const [title, setTitle] = useState("");
  const [fullText, setFullText] = useState("");

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    await createAddress({ title, full_text: fullText });
    setTitle("");
    setFullText("");
  };

  return (
    <div className="section">
      <h1>Addresses</h1>
      <form onSubmit={handleSubmit} style={{ display: "grid", gap: 12, maxWidth: 520, marginBottom: 24 }}>
        <label>
          <span className="muted">Title</span>
          <input
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Home / Office"
            required
            style={{ width: "100%", padding: 10, borderRadius: 8, border: "1px solid #cbd5e1" }}
          />
        </label>
        <label>
          <span className="muted">Full address</span>
          <textarea
            value={fullText}
            onChange={(e) => setFullText(e.target.value)}
            required
            rows={3}
            style={{ width: "100%", padding: 10, borderRadius: 8, border: "1px solid #cbd5e1" }}
          />
        </label>
        <button type="submit" className="button">
          Save address
        </button>
      </form>

      {isLoading ? (
        <p className="muted">Loading…</p>
      ) : (
        <div className="card-grid">
          {(addresses || []).map((address) => (
            <Card key={address.id} title={address.title || "Address"} description={address.full_text}>
              <p className="muted">City: {address.city || "N/A"}</p>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
