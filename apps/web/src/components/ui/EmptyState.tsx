import type { LucideIcon } from "lucide-react";
import type { ReactNode } from "react";
import { cn } from "@/lib/cn";

export interface EmptyStateProps {
  icon: LucideIcon;
  title: string;
  description?: string;
  action?: ReactNode;
  className?: string;
}

export function EmptyState({ icon: Icon, title, description, action, className }: EmptyStateProps) {
  return (
    <div
      className={cn("flex flex-col items-center justify-center gap-3 py-16 text-center", className)}
    >
      <div className="bg-muted flex size-14 items-center justify-center rounded-full">
        <Icon className="text-muted-foreground size-7" aria-hidden />
      </div>
      <h2 className="text-lg font-semibold">{title}</h2>
      {description ? <p className="text-muted-foreground max-w-sm text-sm">{description}</p> : null}
      {action}
    </div>
  );
}
