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
    <section className="section api-section">
      <div className="container small">
        <div className="api-shell">
          <div className="api-card">
            <div className="api-card-head">
              <span className="section-eyebrow">ورود امن</span>
              <h1>ورود با رمز یکبار مصرف</h1>
              <p className="api-subtitle">
                شماره موبایلت رو وارد کن تا کد پیامکی برات ارسال کنیم؛ بدون رمز، سریع و سالم وارد شو.
              </p>
            </div>

            {step === "request" ? (
              <form onSubmit={handleRequest} className="api-form">
                <label className="input-label">
                  <span>شماره موبایل</span>
                  <input
                    className="input-field"
                    type="tel"
                    value={phone}
                    onChange={(e) => setPhone(e.target.value)}
                    placeholder="مثال: ۰۹۱۲۳۴۵۶۷۸۹"
                    required
                  />
                </label>

                <div className="api-actions">
                  <p className="muted" style={{ margin: 0 }}>
                    پیامک شامل کد تایید برایت ارسال می‌شود.
                  </p>
                  <button className="primary-button" type="submit" disabled={loading}>
                    {loading ? "در حال ارسال…" : "ارسال کد پیامکی"}
                  </button>
                </div>
              </form>
            ) : (
              <form onSubmit={handleVerify} className="api-form">
                <label className="input-label">
                  <span>کد تایید</span>
                  <input
                    className="input-field"
                    value={code}
                    onChange={(e) => setCode(e.target.value)}
                    placeholder="کد ۵ رقمی"
                    required
                  />
                </label>

                <div className="api-actions">
                  <p className="muted" style={{ margin: 0 }}>
                    کد برای {phone || "شماره وارد شده"} ارسال شد.
                  </p>
                  <button className="primary-button" type="submit" disabled={loading}>
                    {loading ? "در حال تایید…" : "ورود به حساب"}
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>
      </div>
    </section>
  );
}
