import { Link } from "react-router-dom";

export function HomePage() {
  return (
    <div className="section">
      <h1>Welcome to Vaadeh</h1>
      <p className="muted">Start a new order from the menu or continue where you left off.</p>
      <div style={{ marginTop: 16, display: "flex", gap: 12 }}>
        <Link to="/menu" className="button">
          Browse Menu
        </Link>
        <Link to="/orders" className="button" style={{ background: "#0f172a" }}>
          View Orders
        </Link>
      </div>
    </div>
  );
}
