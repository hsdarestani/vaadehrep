import { FormEvent, useState } from "react";

import { useAuth } from "../state/auth";

export function LoginPage() {
  const [phone, setPhone] = useState("");
  const [code, setCode] = useState("");
  const [step, setStep] = useState<"request" | "verify">("request");
  const { requestOtp, verifyOtp, loading } = useAuth();

  const handleRequest = async (event: FormEvent) => {
    event.preventDefault();
    await requestOtp(phone);
    setStep("verify");
  };

  const handleVerify = async (event: FormEvent) => {
    event.preventDefault();
    await verifyOtp(phone, code);
  };

  return (
    <div className="section">
      <h1>OTP Login</h1>
      {step === "request" ? (
        <form onSubmit={handleRequest} style={{ display: "grid", gap: 12, maxWidth: 360 }}>
          <label>
            <span className="muted">Phone number</span>
            <input
              type="tel"
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              required
              style={{ width: "100%", padding: 10, borderRadius: 8, border: "1px solid #cbd5e1" }}
            />
          </label>
          <button className="button" type="submit" disabled={loading}>
            {loading ? "Sending..." : "Send OTP"}
          </button>
        </form>
      ) : (
        <form onSubmit={handleVerify} style={{ display: "grid", gap: 12, maxWidth: 360 }}>
          <label>
            <span className="muted">OTP Code</span>
            <input
              value={code}
              onChange={(e) => setCode(e.target.value)}
              required
              style={{ width: "100%", padding: 10, borderRadius: 8, border: "1px solid #cbd5e1" }}
            />
          </label>
          <button className="button" type="submit" disabled={loading}>
            {loading ? "Verifying..." : "Verify"}
          </button>
        </form>
      )}
    </div>
  );
}
