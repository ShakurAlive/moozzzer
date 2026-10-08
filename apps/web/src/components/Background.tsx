import { useReducedMotion } from "framer-motion";
import { cn } from "@/lib/cn";

type Palette = readonly [string, string, string];

const DEFAULT_PALETTE: Palette = ["hsl(245 55% 55%)", "hsl(280 55% 60%)", "hsl(200 60% 50%)"];

export interface BackgroundProps {
  /** Accent colors of the ambient blobs; later driven by the current track's cover. */
  palette?: Palette;
  className?: string;
}

interface BlobProps {
  color: string;
  className?: string;
  reduced: boolean | null;
  delay: string;
  duration: string;
}

function Blob({ color, className, reduced, delay, duration }: BlobProps) {
  return (
    <div
      className={cn(
        "absolute rounded-full opacity-30 blur-[120px]",
        className,
        !reduced && "animate-blob",
      )}
      style={{
        background: `radial-gradient(circle, ${color}, transparent 65%)`,
        animationDelay: delay,
        animationDuration: duration,
      }}
    />
  );
}

export function Background({ palette = DEFAULT_PALETTE, className }: BackgroundProps) {
  const reduced = useReducedMotion();
  const [a, b, c] = palette;

  return (
    <div
      aria-hidden
      className={cn("pointer-events-none absolute inset-0 overflow-hidden", className)}
    >
      <Blob
        color={a}
        reduced={reduced}
        delay="0s"
        duration="26s"
        className="-top-32 -left-32 size-[42rem]"
      />
      <Blob
        color={b}
        reduced={reduced}
        delay="-9s"
        duration="30s"
        className="top-1/4 -right-24 size-[38rem]"
      />
      <Blob
        color={c}
        reduced={reduced}
        delay="-17s"
        duration="24s"
        className="-bottom-32 left-1/3 size-[40rem]"
      />
    </div>
  );
}
