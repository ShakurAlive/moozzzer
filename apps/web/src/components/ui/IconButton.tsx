import type { ButtonHTMLAttributes } from "react";
import { cn } from "@/lib/cn";

type Variant = "ghost" | "filled";

const variantClasses: Record<Variant, string> = {
  ghost: "text-muted-foreground hover:bg-muted hover:text-foreground",
  filled: "bg-primary text-primary-foreground hover:opacity-90",
};

export interface IconButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  label: string;
  variant?: Variant;
}

export function IconButton({
  className,
  label,
  variant = "ghost",
  children,
  ...props
}: IconButtonProps) {
  return (
    <button
      type="button"
      aria-label={label}
      className={cn(
        "focus-visible:ring-ring inline-flex size-9 shrink-0 items-center justify-center rounded-full transition-colors focus-visible:ring-2 focus-visible:outline-none disabled:pointer-events-none disabled:opacity-40",
        variantClasses[variant],
        className,
      )}
      {...props}
    >
      {children}
    </button>
  );
}
