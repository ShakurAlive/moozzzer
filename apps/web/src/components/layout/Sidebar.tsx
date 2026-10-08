import { AudioWaveform, Library, ListMusic, LogOut, Music2, Search } from "lucide-react";
import { NavLink, useNavigate } from "react-router-dom";
import { IconButton } from "@/components/ui/IconButton";
import { t, type MessageKey } from "@/i18n";
import { cn } from "@/lib/cn";
import { useAuthStore } from "@/stores/auth";

const navItems: { to: string; icon: typeof Music2; labelKey: MessageKey }[] = [
  { to: "/wave", icon: AudioWaveform, labelKey: "nav.wave" },
  { to: "/search", icon: Search, labelKey: "nav.search" },
  { to: "/library", icon: Library, labelKey: "nav.library" },
  { to: "/playlists", icon: ListMusic, labelKey: "nav.playlists" },
];

export function Sidebar() {
  const user = useAuthStore((state) => state.user);
  const logout = useAuthStore((state) => state.logout);
  const navigate = useNavigate();

  const handleLogout = () => {
    void logout();
    void navigate("/login", { replace: true });
  };

  return (
    <aside className="glass border-border/50 flex w-60 shrink-0 flex-col border-r p-4">
      <div className="mb-6 flex items-center gap-2 px-2">
        <Music2 className="text-foreground size-6" aria-hidden />
        <span className="text-lg font-bold tracking-tight">{t("app.title")}</span>
      </div>

      <nav className="flex flex-1 flex-col gap-1">
        {navItems.map(({ to, icon: Icon, labelKey }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              cn(
                "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                isActive
                  ? "bg-muted text-foreground"
                  : "text-muted-foreground hover:bg-muted hover:text-foreground",
              )
            }
          >
            <Icon className="size-5" aria-hidden />
            {t(labelKey)}
          </NavLink>
        ))}
      </nav>

      <div className="border-border/50 flex items-center gap-2 border-t pt-4">
        <div className="min-w-0 flex-1">
          <p className="truncate text-sm font-medium">{user?.username}</p>
        </div>
        <IconButton label={t("auth.button.logout")} onClick={handleLogout}>
          <LogOut className="size-5" aria-hidden />
        </IconButton>
      </div>
    </aside>
  );
}
