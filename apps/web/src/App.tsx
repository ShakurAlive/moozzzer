import { useEffect, useState } from "react";
import { t } from "@/i18n";

type HealthState = "loading" | "ok" | "error";

function useApiHealth(): HealthState {
  const [state, setState] = useState<HealthState>("loading");

  useEffect(() => {
    const controller = new AbortController();
    fetch("/api/health", { signal: controller.signal })
      .then((res) => {
        setState(res.ok ? "ok" : "error");
      })
      .catch((err: unknown) => {
        if (!controller.signal.aborted) {
          console.error(err);
          setState("error");
        }
      });
    return () => {
      controller.abort();
    };
  }, []);

  return state;
}

const statusColor: Record<HealthState, string> = {
  loading: "text-neutral-400",
  ok: "text-emerald-400",
  error: "text-red-400",
};

export function App() {
  const health = useApiHealth();

  return (
    <main className="flex h-full flex-col items-center justify-center gap-4">
      <h1 className="text-4xl font-bold tracking-tight">{t("app.title")}</h1>
      <p className="text-lg" data-testid="api-status">
        {t("health.label")}: <span className={statusColor[health]}>{t(`health.${health}`)}</span>
      </p>
    </main>
  );
}
