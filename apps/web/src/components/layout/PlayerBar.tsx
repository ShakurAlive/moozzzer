import { Play, Repeat, Shuffle, SkipBack, SkipForward, Volume2 } from "lucide-react";
import { IconButton } from "@/components/ui/IconButton";
import { t } from "@/i18n";

export function PlayerBar() {
  return (
    <footer className="glass border-border/50 flex items-center gap-4 border-t px-4 py-3">
      <div className="flex w-64 min-w-0 items-center gap-3">
        <div className="bg-muted size-12 shrink-0 rounded-md" aria-hidden />
        <div className="min-w-0">
          <p className="text-muted-foreground truncate text-sm font-medium">
            {t("player.nothingPlaying")}
          </p>
          <p className="text-muted-foreground truncate text-xs">—</p>
        </div>
      </div>

      <div className="flex flex-1 flex-col items-center gap-1.5">
        <div className="flex items-center gap-1">
          <IconButton label={t("common.shuffle")} disabled>
            <Shuffle className="size-4" aria-hidden />
          </IconButton>
          <IconButton label={t("common.prev")} disabled>
            <SkipBack className="size-5" aria-hidden />
          </IconButton>
          <button
            type="button"
            aria-label={t("common.play")}
            disabled
            className="bg-primary text-primary-foreground flex size-10 items-center justify-center rounded-full transition-colors disabled:opacity-40"
          >
            <Play className="size-5" aria-hidden />
          </button>
          <IconButton label={t("common.next")} disabled>
            <SkipForward className="size-5" aria-hidden />
          </IconButton>
          <IconButton label={t("common.repeat")} disabled>
            <Repeat className="size-4" aria-hidden />
          </IconButton>
        </div>

        <div className="flex w-full max-w-xl items-center gap-2">
          <span className="text-muted-foreground text-xs tabular-nums">0:00</span>
          <div className="bg-muted h-1 flex-1 rounded-full">
            <div className="bg-primary h-full w-0 rounded-full" />
          </div>
          <span className="text-muted-foreground text-xs tabular-nums">0:00</span>
        </div>
      </div>

      <div className="flex w-64 items-center justify-end gap-2">
        <Volume2 className="text-muted-foreground size-4" aria-hidden />
        <div className="bg-muted h-1 w-24 rounded-full">
          <div className="bg-foreground h-full w-2/3 rounded-full" />
        </div>
      </div>
    </footer>
  );
}
