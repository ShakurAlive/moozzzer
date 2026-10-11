import {
  Music,
  Pause,
  Play,
  Repeat,
  Repeat1,
  Shuffle,
  SkipBack,
  SkipForward,
  Volume2,
  VolumeX,
} from "lucide-react";
import type { MouseEvent } from "react";
import { IconButton } from "@/components/ui/IconButton";
import { t } from "@/i18n";
import { cn } from "@/lib/cn";
import { formatDuration } from "@/lib/format";
import { usePlayerStore } from "@/stores/player";

export function PlayerBar() {
  const queue = usePlayerStore((state) => state.queue);
  const index = usePlayerStore((state) => state.index);
  const isPlaying = usePlayerStore((state) => state.isPlaying);
  const shuffle = usePlayerStore((state) => state.shuffle);
  const repeat = usePlayerStore((state) => state.repeat);
  const volume = usePlayerStore((state) => state.volume);
  const muted = usePlayerStore((state) => state.muted);
  const currentTime = usePlayerStore((state) => state.currentTime);
  const duration = usePlayerStore((state) => state.duration);

  const togglePlay = usePlayerStore((state) => state.togglePlay);
  const next = usePlayerStore((state) => state.next);
  const prev = usePlayerStore((state) => state.prev);
  const seek = usePlayerStore((state) => state.seek);
  const setVolume = usePlayerStore((state) => state.setVolume);
  const toggleMute = usePlayerStore((state) => state.toggleMute);
  const toggleShuffle = usePlayerStore((state) => state.toggleShuffle);
  const cycleRepeat = usePlayerStore((state) => state.cycleRepeat);

  const current = index >= 0 ? queue[index] : undefined;
  const progress = duration > 0 ? (currentTime / duration) * 100 : 0;

  const handleSeek = (event: MouseEvent<HTMLDivElement>) => {
    if (duration <= 0) return;
    const rect = event.currentTarget.getBoundingClientRect();
    const ratio = (event.clientX - rect.left) / Math.max(rect.width, 1);
    seek(Math.max(0, Math.min(ratio, 1)) * duration);
  };

  return (
    <footer className="glass border-border/50 flex items-center gap-4 border-t px-4 py-3">
      <div className="flex w-64 min-w-0 items-center gap-3">
        <div className="bg-muted flex size-12 shrink-0 items-center justify-center overflow-hidden rounded-md">
          {current?.coverUrl ? (
            <img src={current.coverUrl} alt="" className="size-full object-cover" />
          ) : (
            <Music className="text-muted-foreground size-5" aria-hidden />
          )}
        </div>
        <div className="min-w-0">
          <p className="truncate text-sm font-medium">
            {current?.title ?? t("player.nothingPlaying")}
          </p>
          <p className="text-muted-foreground truncate text-xs">{current?.artist ?? "—"}</p>
        </div>
      </div>

      <div className="flex flex-1 flex-col items-center gap-1.5">
        <div className="flex items-center gap-1">
          <IconButton
            label={t("common.shuffle")}
            onClick={toggleShuffle}
            disabled={!current}
            className={cn(shuffle && "text-foreground")}
          >
            <Shuffle className="size-4" aria-hidden />
          </IconButton>
          <IconButton label={t("common.prev")} onClick={prev} disabled={!current}>
            <SkipBack className="size-5" aria-hidden />
          </IconButton>
          <button
            type="button"
            aria-label={isPlaying ? t("common.pause") : t("common.play")}
            onClick={togglePlay}
            disabled={!current}
            className="bg-primary text-primary-foreground flex size-10 items-center justify-center rounded-full transition-colors hover:opacity-90 disabled:opacity-40"
          >
            {isPlaying ? (
              <Pause className="size-5" aria-hidden />
            ) : (
              <Play className="size-5" aria-hidden />
            )}
          </button>
          <IconButton label={t("common.next")} onClick={next} disabled={!current}>
            <SkipForward className="size-5" aria-hidden />
          </IconButton>
          <IconButton
            label={t("common.repeat")}
            onClick={cycleRepeat}
            className={cn(repeat !== "off" && "text-foreground")}
          >
            {repeat === "one" ? (
              <Repeat1 className="size-4" aria-hidden />
            ) : (
              <Repeat className="size-4" aria-hidden />
            )}
          </IconButton>
        </div>

        <div className="flex w-full max-w-xl items-center gap-2">
          <span className="text-muted-foreground text-xs tabular-nums">
            {formatDuration(currentTime)}
          </span>
          <div
            className="bg-muted group relative h-1 flex-1 cursor-pointer rounded-full"
            onClick={handleSeek}
            role="slider"
            aria-label={t("player.seek")}
            aria-valuemin={0}
            aria-valuemax={Math.round(duration)}
            aria-valuenow={Math.round(currentTime)}
          >
            <div
              className="bg-primary absolute inset-y-0 left-0 rounded-full"
              style={{ width: `${String(progress)}%` }}
            />
          </div>
          <span className="text-muted-foreground text-xs tabular-nums">
            {formatDuration(duration)}
          </span>
        </div>
      </div>

      <div className="flex w-64 items-center justify-end gap-2">
        <IconButton
          label={muted ? t("player.unmute") : t("player.mute")}
          onClick={toggleMute}
          variant="ghost"
        >
          {muted || volume === 0 ? (
            <VolumeX className="size-4" aria-hidden />
          ) : (
            <Volume2 className="size-4" aria-hidden />
          )}
        </IconButton>
        <input
          type="range"
          min={0}
          max={1}
          step={0.01}
          value={muted ? 0 : volume}
          onChange={(event) => {
            setVolume(Number(event.target.value));
          }}
          aria-label={t("player.volume")}
          className="accent-foreground h-1 w-24 cursor-pointer"
        />
      </div>
    </footer>
  );
}
