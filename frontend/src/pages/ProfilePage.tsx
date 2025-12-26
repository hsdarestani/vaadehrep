import { useAuth } from "../state/auth";

export function ProfilePage() {
  const { user, logout } = useAuth();

  return (
    <div className="section">
      <h1>پروفایل</h1>
      {user ? (
        <>
          <p className="muted">وارد شده با شماره {user.phone}</p>
          <button className="button" onClick={logout}>
            خروج
          </button>
        </>
      ) : (
        <p className="muted">حساب کاربری فعال نیست.</p>
      )}
    </div>
  );
}
