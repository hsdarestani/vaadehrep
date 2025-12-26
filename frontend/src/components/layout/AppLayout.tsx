import { Link, useLocation } from "react-router-dom";
import { ReactNode } from "react";

type Props = {
  children: ReactNode;
};

const navLinks = [
  { to: "/menu", label: "Menu" },
  { to: "/cart", label: "Cart" },
  { to: "/orders", label: "Orders" },
  { to: "/addresses", label: "Addresses" },
  { to: "/profile", label: "Profile" },
];

export function AppLayout({ children }: Props) {
  const location = useLocation();

  return (
    <div className="app-shell">
      <header className="header">
        <nav>
          <Link to="/" className="brand">
            Vaadeh
          </Link>
          {navLinks.map((link) => (
            <Link
              key={link.to}
              to={link.to}
              className="link"
              aria-current={location.pathname.startsWith(link.to) ? "page" : undefined}
            >
              {link.label}
            </Link>
          ))}
          <div style={{ flex: 1 }} />
          <Link to="/login" className="link">
            Login / OTP
          </Link>
        </nav>
      </header>
      <main className="app-main">{children}</main>
    </div>
  );
}
