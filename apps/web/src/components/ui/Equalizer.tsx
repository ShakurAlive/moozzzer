import { motion } from "framer-motion";
import { cn } from "@/lib/cn";

export function Equalizer({ className }: { className?: string }) {
  return (
    <span className={cn("flex h-4 items-end gap-0.5", className)} aria-hidden>
      {[0, 1, 2].map((bar) => (
        <motion.span
          key={bar}
          className="h-full w-0.5 origin-bottom rounded-full bg-current"
          animate={{ scaleY: [0.4, 1, 0.6, 0.4] }}
          transition={{ duration: 0.9, repeat: Infinity, delay: bar * 0.15, ease: "easeInOut" }}
        />
      ))}
    </span>
  );
}
