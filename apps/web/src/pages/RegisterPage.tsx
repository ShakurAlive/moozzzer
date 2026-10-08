import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { t } from "@/i18n";
import { type RegisterRequest } from "@/lib/api";
import { authErrorMessage } from "@/lib/errors";
import { useAuthStore } from "@/stores/auth";

const inputClass =
  "w-full rounded-md border border-input bg-muted px-3 py-2 text-sm " +
  "text-foreground placeholder-muted-foreground outline-none transition-colors focus:border-ring";

const EMAIL_RE = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;
const USERNAME_RE = /^[A-Za-z0-9_.-]{3,32}$/;

export function RegisterPage() {
  const navigate = useNavigate();
  const register = useAuthStore((state) => state.register);

  const [email, setEmail] = useState("");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [inviteCode, setInviteCode] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    void submit();
  };

  async function submit(): Promise<void> {
    const trimmedEmail = email.trim();
    const trimmedUsername = username.trim();
    const trimmedInvite = inviteCode.trim();

    if (trimmedEmail === "" || trimmedUsername === "" || password === "" || trimmedInvite === "") {
      setError(t("auth.validation.required"));
      return;
    }
    if (!EMAIL_RE.test(trimmedEmail)) {
      setError(t("auth.validation.email"));
      return;
    }
    if (!USERNAME_RE.test(trimmedUsername)) {
      setError(t("auth.validation.username"));
      return;
    }
    if (password.length < 8) {
      setError(t("auth.validation.password"));
      return;
    }

    setSubmitting(true);
    setError(null);
    try {
      const input: RegisterRequest = {
        email: trimmedEmail,
        username: trimmedUsername,
        password,
        invite_code: trimmedInvite,
      };
      await register(input);
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
          <h1 className="text-2xl font-bold tracking-tight">{t("auth.title.register")}</h1>
        </header>

        {error !== null ? <p className="text-destructive text-sm">{error}</p> : null}

        <label className="block space-y-1.5">
          <span className="text-muted-foreground text-sm">{t("auth.label.email")}</span>
          <input
            className={inputClass}
            type="email"
            autoComplete="email"
            value={email}
            onChange={(event) => {
              setEmail(event.target.value);
            }}
          />
        </label>

        <label className="block space-y-1.5">
          <span className="text-muted-foreground text-sm">{t("auth.label.username")}</span>
          <input
            className={inputClass}
            type="text"
            autoComplete="username"
            value={username}
            onChange={(event) => {
              setUsername(event.target.value);
            }}
          />
        </label>

        <label className="block space-y-1.5">
          <span className="text-muted-foreground text-sm">{t("auth.label.password")}</span>
          <input
            className={inputClass}
            type="password"
            autoComplete="new-password"
            value={password}
            onChange={(event) => {
              setPassword(event.target.value);
            }}
          />
        </label>

        <label className="block space-y-1.5">
          <span className="text-muted-foreground text-sm">{t("auth.label.inviteCode")}</span>
          <input
            className={inputClass}
            type="text"
            autoComplete="off"
            value={inviteCode}
            onChange={(event) => {
              setInviteCode(event.target.value);
            }}
          />
        </label>

        <button
          type="submit"
          disabled={submitting}
          className="bg-primary text-primary-foreground w-full rounded-md px-3 py-2 text-sm font-medium transition-colors hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {submitting ? t("auth.button.submitting") : t("auth.button.register")}
        </button>

        <p className="text-muted-foreground text-center text-sm">
          {t("auth.link.haveAccount")}{" "}
          <Link to="/login" className="text-foreground underline underline-offset-2">
            {t("auth.link.toLogin")}
          </Link>
        </p>
      </form>
    </main>
  );
}
