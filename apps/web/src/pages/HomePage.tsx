import { useNavigate } from "react-router-dom";
import { t } from "@/i18n";
import { useAuthStore } from "@/stores/auth";

export function HomePage() {
  const user = useAuthStore((state) => state.user);
  const logout = useAuthStore((state) => state.logout);
  const navigate = useNavigate();

  const handleLogout = () => {
    void logout();
    void navigate("/login", { replace: true });
  };

  return (
    <main className="flex h-full flex-col items-center justify-center gap-4">
      <h1 className="text-4xl font-bold tracking-tight">{t("app.title")}</h1>
      <p className="text-lg text-neutral-300">
        {t("home.loggedInAs")}{" "}
        <span className="font-semibold text-neutral-100">{user?.username}</span>
      </p>
      <button
        type="button"
        onClick={handleLogout}
        className="rounded-lg border border-neutral-800 px-4 py-2 text-sm font-medium text-neutral-200 transition-colors hover:bg-neutral-900"
      >
        {t("auth.button.logout")}
      </button>
    </main>
  );
}
