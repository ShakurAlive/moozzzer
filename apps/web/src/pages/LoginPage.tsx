import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { t } from "@/i18n";
import { type LoginRequest } from "@/lib/api";
import { authErrorMessage } from "@/lib/errors";
import { useAuthStore } from "@/stores/auth";

const inputClass =
  "w-full rounded-lg border border-neutral-800 bg-neutral-900 px-3 py-2 text-sm " +
  "text-neutral-100 placeholder-neutral-500 outline-none transition-colors focus:border-neutral-600";

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

        {error !== null ? <p className="text-sm text-red-400">{error}</p> : null}

        <label className="block space-y-1.5">
          <span className="text-sm text-neutral-400">{t("auth.label.emailOrUsername")}</span>
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
          <span className="text-sm text-neutral-400">{t("auth.label.password")}</span>
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
          className="w-full rounded-lg bg-neutral-100 px-3 py-2 text-sm font-medium text-neutral-900 transition-colors hover:bg-white disabled:cursor-not-allowed disabled:opacity-60"
        >
          {submitting ? t("auth.button.submitting") : t("auth.button.login")}
        </button>

        <p className="text-center text-sm text-neutral-400">
          {t("auth.link.noAccount")}{" "}
          <Link to="/register" className="text-neutral-200 underline underline-offset-2">
            {t("auth.link.toRegister")}
          </Link>
        </p>
      </form>
    </main>
  );
}
