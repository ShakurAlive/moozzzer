import { Ellipsis, Music, Pause, Play } from "lucide-react";
import { Equalizer } from "@/components/ui/Equalizer";
import { IconButton } from "@/components/ui/IconButton";
import { t } from "@/i18n";
import { cn } from "@/lib/cn";
import { formatDuration } from "@/lib/format";
import type { Track } from "@/lib/types";

export interface TrackRowProps {
  track: Track;
  isActive?: boolean;
  isPlaying?: boolean;
  onPlay?: () => void;
  onMenu?: () => void;
}

export function TrackRow({
  track,
  isActive = false,
  isPlaying = false,
  onPlay,
  onMenu,
}: TrackRowProps) {
  return (
    <div
      className={cn(
        "group hover:bg-muted flex items-center gap-3 rounded-md px-2 py-2 transition-colors",
        isActive && "bg-muted",
      )}
    >
      <div className="relative size-10 shrink-0 overflow-hidden rounded-md">
        {track.coverUrl ? (
          <img src={track.coverUrl} alt="" className="size-full object-cover" />
        ) : (
          <div className="bg-muted flex size-full items-center justify-center">
            <Music className="text-muted-foreground size-4" aria-hidden />
          </div>
        )}
        <button
          type="button"
          aria-label={isPlaying ? t("common.pause") : t("common.play")}
          onClick={onPlay}
          className="absolute inset-0 flex items-center justify-center bg-black/40 opacity-0 transition-opacity group-hover:opacity-100 focus-visible:opacity-100"
        >
          {isPlaying ? (
            <Pause className="size-4 text-white" aria-hidden />
          ) : (
            <Play className="size-4 text-white" aria-hidden />
          )}
        </button>
      </div>

      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2">
          <span className="truncate text-sm font-medium">{track.title}</span>
          {track.explicit ? (
            <span className="bg-muted text-muted-foreground rounded px-1 text-[10px] leading-4 font-bold">
              E
            </span>
          ) : null}
        </div>
        <p className="text-muted-foreground truncate text-xs">{track.artist}</p>
      </div>

      <div className="flex w-12 items-center justify-end">
        {isPlaying ? (
          <Equalizer className="text-foreground" />
        ) : (
          <span className="text-muted-foreground text-xs tabular-nums">
            {formatDuration(track.duration)}
          </span>
        )}
      </div>

      <IconButton label={t("common.more")} onClick={onMenu}>
        <Ellipsis className="size-5" aria-hidden />
      </IconButton>
    </div>
  );
}
