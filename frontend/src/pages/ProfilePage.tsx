import { Navigate, useLocation } from "react-router-dom";

import { useAuth } from "../state/auth";

export function ProfilePage() {
  const { user, logout } = useAuth();
  const location = useLocation();

  if (!user) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  }

  return (
    <section className="section">
      <div className="container small">
        <div className="section-head" style={{ textAlign: "center" }}>
          <span className="section-eyebrow">پروفایل</span>
          <h1 className="section-title" style={{ marginBottom: 8 }}>
            خوش آمدی
          </h1>
          <p className="section-subtitle">اطلاعات ورود و خروج خود را اینجا مدیریت کن.</p>
        </div>

        <div className="card" style={{ textAlign: "center", display: "grid", gap: 12 }}>
          <p className="muted" style={{ margin: 0 }}>
            وارد شده با شماره {user.phone}
          </p>
          <button className="primary-button" onClick={logout}>
            خروج
          </button>
        </div>
      </div>
    </section>
  );
}
