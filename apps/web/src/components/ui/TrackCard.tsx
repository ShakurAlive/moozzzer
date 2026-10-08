import { Music, Play } from "lucide-react";
import { t } from "@/i18n";
import type { Track } from "@/lib/types";

export interface TrackCardProps {
  track: Track;
  onPlay?: () => void;
}

export function TrackCard({ track, onPlay }: TrackCardProps) {
  return (
    <div className="group w-full">
      <div className="bg-card relative aspect-square overflow-hidden rounded-lg">
        {track.coverUrl ? (
          <img src={track.coverUrl} alt="" className="size-full object-cover" />
        ) : (
          <div className="flex size-full items-center justify-center">
            <Music className="text-muted-foreground size-8" aria-hidden />
          </div>
        )}
        <button
          type="button"
          aria-label={t("common.play")}
          onClick={onPlay}
          className="bg-primary text-primary-foreground shadow-panel absolute right-2 bottom-2 flex size-10 items-center justify-center rounded-full opacity-0 transition-opacity group-hover:opacity-100 hover:opacity-100 focus-visible:opacity-100"
        >
          <Play className="size-5" aria-hidden />
        </button>
      </div>
      <div className="mt-2 space-y-0.5">
        <p className="truncate text-sm font-medium">{track.title}</p>
        <p className="text-muted-foreground truncate text-xs">{track.artist}</p>
      </div>
    </div>
  );
}
