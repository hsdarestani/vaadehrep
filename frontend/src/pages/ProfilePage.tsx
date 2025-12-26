import { useAuth } from "../state/auth";

export function ProfilePage() {
  const { user, logout } = useAuth();

  return (
    <div className="section">
      <h1>Profile</h1>
      {user ? (
        <>
          <p className="muted">Logged in as {user.phone}</p>
          <button className="button" onClick={logout}>
            Logout
          </button>
        </>
      ) : (
        <p className="muted">Not logged in.</p>
      )}
    </div>
  );
}
