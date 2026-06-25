import { FormEvent, useState } from "react";
import { Activity, KeyRound, LockKeyhole, RadioTower, ShieldCheck } from "lucide-react";

interface LoginPageProps {
  onLogin: (username: string, password: string) => Promise<void>;
  isCheckingSession: boolean;
  sessionError: string | null;
}

export function LoginPage({
  onLogin,
  isCheckingSession,
  sessionError,
}: LoginPageProps) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [formError, setFormError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    setFormError(null);
    setIsSubmitting(true);

    try {
      await onLogin(username.trim(), password);
    } catch (error) {
      setFormError(error instanceof Error ? error.message : "Unable to sign in");
    } finally {
      setIsSubmitting(false);
    }
  }

  const errorMessage = formError ?? sessionError;

  return (
    <main className="login-shell">
      <div className="background-blur background-blur--one" />
      <div className="background-blur background-blur--two" />

      <section className="login-hero" aria-labelledby="login-title">
        <div className="login-brand">
          <div className="brand-mark">
            <RadioTower size={24} />
          </div>
          <div>
            <span className="topbar-label">AI Voice Command Center</span>
            <h1 id="login-title">Sign in to manage voice-agent operations.</h1>
          </div>
        </div>

        <div className="login-security-card">
          <ShieldCheck size={20} />
          <div>
            <strong>Protected control surface</strong>
            <p>Leads, call attempts, agent scripts, and handoff events require an operator session.</p>
          </div>
        </div>

        <div className="login-signal-grid" aria-label="Security posture">
          <div>
            <Activity size={18} />
            <span>Live ops telemetry</span>
          </div>
          <div>
            <KeyRound size={18} />
            <span>Bearer-token access</span>
          </div>
          <div>
            <ShieldCheck size={18} />
            <span>Production guardrails</span>
          </div>
        </div>
      </section>

      <section className="login-card" aria-label="Operator login">
        <div className="login-card-header">
          <div className="login-icon">
            <LockKeyhole size={20} />
          </div>
          <div>
            <span className="panel-eyebrow">Operator Access</span>
            <h2>Login</h2>
            <p>Use your operator credentials to open the command center.</p>
          </div>
        </div>

        <form className="login-form" onSubmit={handleSubmit}>
          <label className="field" htmlFor="login-username">
            <span>Username</span>
            <input
              id="login-username"
              autoComplete="username"
              value={username}
              onChange={(event) => setUsername(event.target.value)}
              required
            />
          </label>

          <label className="field" htmlFor="login-password">
            <span>Password</span>
            <input
              id="login-password"
              type="password"
              autoComplete="current-password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              required
            />
          </label>

          {errorMessage ? <p className="inline-error">{errorMessage}</p> : null}

          <button
            className="primary-button login-submit"
            type="submit"
            disabled={isSubmitting || isCheckingSession}
          >
            {isSubmitting || isCheckingSession ? "Checking..." : "Enter Dashboard"}
          </button>
        </form>
      </section>
    </main>
  );
}
