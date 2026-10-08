import { AnimatePresence, motion } from "framer-motion";
import { CheckCircle2, CircleAlert, Info, X, type LucideIcon } from "lucide-react";
import { useEffect } from "react";
import { t } from "@/i18n";
import { toastItemVariants } from "@/lib/motion";
import { useToastStore, type Toast as ToastData, type ToastVariant } from "@/stores/toast";

const icons: Record<ToastVariant, LucideIcon> = {
  default: Info,
  success: CheckCircle2,
  error: CircleAlert,
};

export function ToastViewport() {
  const toasts = useToastStore((state) => state.toasts);

  return (
    <div className="pointer-events-none fixed right-4 bottom-24 z-50 flex w-80 flex-col gap-2">
      <AnimatePresence>
        {toasts.map((toast) => (
          <ToastItem key={toast.id} toast={toast} />
        ))}
      </AnimatePresence>
    </div>
  );
}

function ToastItem({ toast }: { toast: ToastData }) {
  const dismiss = useToastStore((state) => state.dismiss);
  const Icon = icons[toast.variant ?? "default"];

  useEffect(() => {
    const timer = setTimeout(() => {
      dismiss(toast.id);
    }, 4000);
    return () => {
      clearTimeout(timer);
    };
  }, [dismiss, toast.id]);

  return (
    <motion.div
      layout
      variants={toastItemVariants}
      initial="hidden"
      animate="visible"
      exit="exit"
      className="glass border-border/50 shadow-panel pointer-events-auto flex items-start gap-3 rounded-md border p-3"
    >
      <Icon className="text-muted-foreground mt-0.5 size-5 shrink-0" aria-hidden />
      <div className="min-w-0 flex-1">
        <p className="text-foreground text-sm font-medium">{toast.title}</p>
        {toast.description ? (
          <p className="text-muted-foreground mt-0.5 text-xs">{toast.description}</p>
        ) : null}
      </div>
      <button
        type="button"
        aria-label={t("common.dismiss")}
        onClick={() => {
          dismiss(toast.id);
        }}
        className="text-muted-foreground hover:bg-muted hover:text-foreground rounded-md p-1 transition-colors"
      >
        <X className="size-4" aria-hidden />
      </button>
    </motion.div>
  );
}
