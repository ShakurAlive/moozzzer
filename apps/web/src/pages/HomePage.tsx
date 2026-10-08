import { motion } from "framer-motion";
import { Music2 } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { t } from "@/i18n";
import { fadeInUp } from "@/lib/motion";
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
      <motion.div
        variants={fadeInUp}
        initial="hidden"
        animate="visible"
        className="flex flex-col items-center gap-4"
      >
        <Music2 className="text-muted-foreground size-8" aria-hidden />
        <h1 className="text-4xl font-bold tracking-tight">{t("app.title")}</h1>
        <p className="text-muted-foreground text-lg">
          {t("home.loggedInAs")}{" "}
          <span className="text-foreground font-semibold">{user?.username}</span>
        </p>
        <button
          type="button"
          onClick={handleLogout}
          className="border-border text-foreground hover:bg-muted rounded-md border px-4 py-2 text-sm font-medium transition-colors"
        >
          {t("auth.button.logout")}
        </button>
      </motion.div>
    </main>
  );
}
