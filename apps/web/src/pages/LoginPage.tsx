import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { t } from "@/i18n";
import { type LoginRequest } from "@/lib/api";
import { authErrorMessage } from "@/lib/errors";
import { useAuthStore } from "@/stores/auth";

const inputClass =
  "w-full rounded-md border border-input bg-muted px-3 py-2 text-sm " +
  "text-foreground placeholder-muted-foreground outline-none transition-colors focus:border-ring";

export function LoginPage() {
  const navigate = useNavigate();
  const login = useAuthStore((state) => state.login);

  const [emailOrUsername, setEmailOrUsername] = useState("");
  const [password, setPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    void submit();
  };

  async function submit(): Promise<void> {
    if (emailOrUsername.trim() === "" || password === "") {
      setError(t("auth.validation.required"));
      return;
    }

    setSubmitting(true);
    setError(null);
    try {
      const input: LoginRequest = { email_or_username: emailOrUsername.trim(), password };
      await login(input);
      void navigate("/", { replace: true });
    } catch (err: unknown) {
      setError(authErrorMessage(err));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="flex h-full items-center justify-center p-6">
      <form onSubmit={handleSubmit} className="w-full max-w-sm space-y-5">
        <header>
          <h1 className="text-2xl font-bold tracking-tight">{t("auth.title.login")}</h1>
        </header>

        {error !== null ? <p className="text-destructive text-sm">{error}</p> : null}

        <label className="block space-y-1.5">
          <span className="text-muted-foreground text-sm">{t("auth.label.emailOrUsername")}</span>
          <input
            className={inputClass}
            type="text"
            autoComplete="username"
            value={emailOrUsername}
            onChange={(event) => {
              setEmailOrUsername(event.target.value);
            }}
          />
        </label>

        <label className="block space-y-1.5">
          <span className="text-muted-foreground text-sm">{t("auth.label.password")}</span>
          <input
            className={inputClass}
            type="password"
            autoComplete="current-password"
            value={password}
            onChange={(event) => {
              setPassword(event.target.value);
            }}
          />
        </label>

        <button
          type="submit"
          disabled={submitting}
          className="bg-primary text-primary-foreground w-full rounded-md px-3 py-2 text-sm font-medium transition-colors hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {submitting ? t("auth.button.submitting") : t("auth.button.login")}
        </button>

        <p className="text-muted-foreground text-center text-sm">
          {t("auth.link.noAccount")}{" "}
          <Link to="/register" className="text-foreground underline underline-offset-2">
            {t("auth.link.toRegister")}
          </Link>
        </p>
      </form>
    </main>
  );
}
