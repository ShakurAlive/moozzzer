import { Heart, ListPlus, Music, Pause, Play } from "lucide-react";
import { Equalizer } from "@/components/ui/Equalizer";
import { IconButton } from "@/components/ui/IconButton";
import { t } from "@/i18n";
import type { SearchResult } from "@/lib/api";
import { formatDuration } from "@/lib/format";

function sourceLabel(provider: string): string {
  if (provider === "youtube_music") return t("source.youtube_music");
  if (provider === "soundcloud") return t("source.soundcloud");
  return provider;
}

export interface SearchResultRowProps {
  result: SearchResult;
  isPlaying: boolean;
  onPlay: () => void;
  onLike: () => void;
  onMenu: () => void;
}

export function SearchResultRow({
  result,
  isPlaying,
  onPlay,
  onLike,
  onMenu,
}: SearchResultRowProps) {
  const duration = result.duration_ms !== null ? Math.round(result.duration_ms / 1000) : null;

  return (
    <div className="group hover:bg-muted flex items-center gap-3 rounded-md px-2 py-2 transition-colors">
      <div className="relative size-10 shrink-0 overflow-hidden rounded-md">
        {result.cover_url ? (
          <img src={result.cover_url} alt="" className="size-full object-cover" />
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
          <span className="truncate text-sm font-medium">{result.title}</span>
          {result.explicit ? (
            <span className="bg-muted text-muted-foreground rounded px-1 text-[10px] leading-4 font-bold">
              E
            </span>
          ) : null}
          <span className="border-border text-muted-foreground rounded-full border px-2 py-0.5 text-[10px]">
            {sourceLabel(result.provider)}
          </span>
        </div>
        <p className="text-muted-foreground truncate text-xs">{result.artist}</p>
      </div>

      <div className="flex w-12 items-center justify-end">
        {isPlaying ? (
          <Equalizer className="text-foreground" />
        ) : (
          <span className="text-muted-foreground text-xs tabular-nums">
            {duration !== null ? formatDuration(duration) : "--:--"}
          </span>
        )}
      </div>

      <IconButton label={t("search.like")} onClick={onLike}>
        <Heart className="size-5" aria-hidden />
      </IconButton>
      <IconButton label={t("search.addToPlaylist")} onClick={onMenu}>
        <ListPlus className="size-5" aria-hidden />
      </IconButton>
    </div>
  );
}
