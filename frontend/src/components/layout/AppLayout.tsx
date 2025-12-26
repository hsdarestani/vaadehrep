import { Link, useLocation } from "react-router-dom";
import { ReactNode } from "react";

import { useAuth } from "../../state/auth";

type Props = {
  children: ReactNode;
};

const publicLinks = [
  { to: "/#menu", label: "منوی روز" },
  { to: "/#mission", label: "داستان ما" },
  { to: "/vendor", label: "همکاری با وعده" },
];

const authedLinks = [
  { to: "/orders", label: "سفارش‌ها" },
  { to: "/addresses", label: "آدرس‌ها" },
  { to: "/profile", label: "پروفایل" },
];

function isActiveLink(
  location: { pathname: string; hash: string },
  target: string,
) {
  const [targetPath, targetHash] = target.split("#");
  if (target.startsWith("/#")) {
    const expectedHash = targetHash ? `#${targetHash}` : "";
    return location.pathname === targetPath && location.hash === expectedHash;
  }
  return location.pathname.startsWith(targetPath);
}

export function AppLayout({ children }: Props) {
  const location = useLocation();
  const { user, logout } = useAuth();
  const navLinks = user ? [...publicLinks, ...authedLinks] : publicLinks;

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="container topbar-nav">
          <Link to="/" className="brand-mark" aria-label="وعده">
            <span className="brand-icon">🌱</span>
            <span className="brand-text">
              <span className="brand-title">وعده</span>
              <span className="brand-subtitle">A Bite of Calm</span>
            </span>
          </Link>

          <div className="nav-links">
            {navLinks.map((link) => (
              <Link
                key={link.to}
                to={link.to}
                className="nav-link"
                aria-current={isActiveLink(location, link.to) ? "page" : undefined}
              >
                {link.label}
              </Link>
            ))}
          </div>

          <div className="cta-group">
            <Link to="/cart" className="primary-button" aria-label="سبد خرید">
              سبد خرید
            </Link>
            {user ? (
              <>
                <Link to="/profile" className="secondary-button">
                  پروفایل
                </Link>
                <button className="ghost-button" type="button" onClick={logout}>
                  خروج
                </button>
              </>
            ) : (
              <Link to="/login" className="secondary-button">
                ورود / کد پیامکی
              </Link>
            )}
          </div>
        </div>
      </header>
      <main className="app-main">{children}</main>
    </div>
  );
}
